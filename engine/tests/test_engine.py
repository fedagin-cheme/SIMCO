"""
Test suite for SIMCO thermodynamic models.

Covers: Antoine, NRTL, Ideal Gas, Henry's Law, Database.
"""

import pytest
import math
import os
import tempfile

# ── Antoine Tests ─────────────────────────────────────

from engine.thermo.antoine import (
    antoine_pressure,
    antoine_temperature,
    get_antoine_coefficients,
    MMHG_TO_PA,
)


class TestAntoine:
    """Antoine equation tests validated against NIST data."""

    def test_water_boiling_point(self):
        """Water should boil at ~100°C at 1 atm (101325 Pa)."""
        A, B, C, _, _ = get_antoine_coefficients("water")
        P = antoine_pressure(100.0, A, B, C)
        assert abs(P - 101325) < 1500, f"Water BP pressure: {P} Pa (expected ~101325)"

    def test_water_inverse(self):
        """Inverse Antoine should recover temperature."""
        A, B, C, _, _ = get_antoine_coefficients("water")
        T = antoine_temperature(101325, A, B, C)
        assert abs(T - 100.0) < 1.5, f"Water BP temp: {T}°C (expected ~100)"

    def test_benzene_boiling_point(self):
        """Benzene should boil at ~80.1°C at 1 atm."""
        A, B, C, _, _ = get_antoine_coefficients("benzene")
        T = antoine_temperature(101325, A, B, C)
        assert abs(T - 80.1) < 2.0, f"Benzene BP: {T}°C (expected ~80.1)"

    def test_methanol_boiling_point(self):
        """Methanol should boil at ~64.7°C at 1 atm."""
        A, B, C, _, _ = get_antoine_coefficients("methanol")
        T = antoine_temperature(101325, A, B, C)
        assert abs(T - 64.7) < 2.0, f"Methanol BP: {T}°C (expected ~64.7)"

    def test_roundtrip_consistency(self):
        """P → T → P should be self-consistent."""
        A, B, C, _, _ = get_antoine_coefficients("ethanol")
        P_original = 50000.0
        T = antoine_temperature(P_original, A, B, C)
        P_recovered = antoine_pressure(T, A, B, C)
        assert abs(P_recovered - P_original) < 1.0

    def test_negative_pressure_raises(self):
        """Non-positive pressure should raise ValueError."""
        A, B, C, _, _ = get_antoine_coefficients("water")
        with pytest.raises(ValueError):
            antoine_temperature(-100, A, B, C)

    def test_all_compounds_have_coefficients(self):
        """All built-in compounds should return valid coefficients."""
        compounds = ["water", "methanol", "ethanol", "benzene", "toluene",
                      "acetone", "n_hexane", "n_heptane", "chloroform"]
        for c in compounds:
            result = get_antoine_coefficients(c)
            assert result is not None, f"Missing coefficients for {c}"
            assert len(result) == 5


# ── NRTL Tests ────────────────────────────────────────

from engine.thermo.nrtl import nrtl_gamma, get_nrtl_params


class TestNRTL:
    """NRTL activity coefficient tests."""

    def test_pure_component_gamma_is_one(self):
        """At x1=1, γ1 should be 1.0."""
        gamma1, gamma2 = nrtl_gamma(1.0, 353.15, 228.46, -228.46, 0.3)
        assert abs(gamma1 - 1.0) < 1e-6

    def test_pure_component2_gamma_is_one(self):
        """At x1=0, γ2 should be 1.0."""
        gamma1, gamma2 = nrtl_gamma(0.0, 353.15, 228.46, -228.46, 0.3)
        assert abs(gamma2 - 1.0) < 1e-6

    def test_benzene_toluene_near_ideal(self):
        """Benzene-toluene is nearly ideal; gammas ≈ 1."""
        params = get_nrtl_params("benzene", "toluene")
        gamma1, gamma2 = nrtl_gamma(0.5, 363.15, *params)
        assert 0.95 < gamma1 < 1.10
        assert 0.95 < gamma2 < 1.10

    def test_methanol_benzene_non_ideal(self):
        """Methanol-benzene is highly non-ideal; large gammas expected."""
        params = get_nrtl_params("methanol", "benzene")
        gamma1, gamma2 = nrtl_gamma(0.5, 333.15, *params)
        assert gamma1 > 1.5, f"Expected non-ideal γ1, got {gamma1}"
        assert gamma2 > 1.3, f"Expected non-ideal γ2, got {gamma2}"

    def test_symmetry_at_equimolar(self):
        """For symmetric parameters, γ1(0.5) should equal γ2(0.5)."""
        gamma1, gamma2 = nrtl_gamma(0.5, 353.15, 500.0, 500.0, 0.3)
        assert abs(gamma1 - gamma2) < 1e-6

    def test_invalid_composition_raises(self):
        """x1 outside [0,1] should raise ValueError."""
        with pytest.raises(ValueError):
            nrtl_gamma(1.5, 353.15, 228.46, -228.46, 0.3)

    def test_negative_temperature_raises(self):
        """Negative temperature should raise ValueError."""
        with pytest.raises(ValueError):
            nrtl_gamma(0.5, -10.0, 228.46, -228.46, 0.3)

    def test_reverse_pair_lookup(self):
        """Getting params for (toluene, benzene) should swap correctly."""
        params_fwd = get_nrtl_params("benzene", "toluene")
        params_rev = get_nrtl_params("toluene", "benzene")
        assert params_fwd[0] == params_rev[1]  # dg12 ↔ dg21
        assert params_fwd[1] == params_rev[0]


# ── Ideal Gas Tests ───────────────────────────────────

from engine.thermo.ideal_gas import (
    ideal_gas_pressure,
    ideal_gas_volume,
    ideal_gas_temperature,
    ideal_gas_moles,
    ideal_gas_density,
)


class TestIdealGas:
    """Ideal gas law tests."""

    def test_standard_conditions(self):
        """1 mol at STP should occupy ~22.4 L."""
        V = ideal_gas_volume(1.0, 273.15, 101325)
        assert abs(V - 0.02241) < 0.001, f"Molar volume: {V} m³ (expected ~0.02241)"

    def test_pressure_roundtrip(self):
        """P → V → P should be self-consistent."""
        P = ideal_gas_pressure(2.0, 300.0, 0.05)
        V = ideal_gas_volume(2.0, 300.0, P)
        assert abs(V - 0.05) < 1e-10

    def test_temperature_calculation(self):
        """PV/(nR) should give correct temperature."""
        T = ideal_gas_temperature(1.0, 101325, 0.02241)
        assert abs(T - 273.15) < 1.0

    def test_zero_volume_raises(self):
        with pytest.raises(ValueError):
            ideal_gas_pressure(1.0, 300.0, 0.0)

    def test_air_density_at_stp(self):
        """Air density at STP should be ~1.29 kg/m³."""
        rho = ideal_gas_density(0.02897, 101325, 273.15)
        assert abs(rho - 1.29) < 0.05


# ── Henry's Law Tests ────────────────────────────────

from engine.thermo.henry import (
    henry_constant_pressure,
    henry_solubility,
    henry_temperature_correction,
    get_henry_data,
)


class TestHenry:
    """Henry's law tests."""

    def test_co2_henry_constant(self):
        """CO2 Henry's constant should be ~1.61e8 Pa."""
        data = get_henry_data("co2")
        assert data is not None
        assert abs(data["H_pa"] - 1.61e8) < 1e6

    def test_pressure_calculation(self):
        """P = H * x should work correctly."""
        P = henry_constant_pressure(0.001, 1.61e8)
        assert abs(P - 161000) < 1.0

    def test_solubility_roundtrip(self):
        """x → P → x should be consistent."""
        x_original = 0.0005
        P = henry_constant_pressure(x_original, 1.61e8)
        x_recovered = henry_solubility(P, 1.61e8)
        assert abs(x_recovered - x_original) < 1e-10

    def test_temperature_correction(self):
        """Henry's constant should increase with temperature for most gases."""
        H_25 = 1.61e8
        H_50 = henry_temperature_correction(H_25, 323.15, 298.15, -19400)
        assert H_50 > H_25, "CO2 solubility should decrease (H increase) with temperature"

    def test_all_gases_present(self):
        """All common industrial gases should be in the database."""
        gases = ["co2", "o2", "n2", "h2s", "so2", "nh3", "cl2", "ch4", "co"]
        for g in gases:
            assert get_henry_data(g) is not None, f"Missing Henry data for {g}"


# ── Database Tests ────────────────────────────────────

from engine.database.db import ChemicalDatabase
from engine.database.seed import seed_database


class TestDatabase:
    """Chemical database tests."""

    @pytest.fixture
    def seeded_db(self, tmp_path):
        """Create and seed a temporary database."""
        db_path = str(tmp_path / "test.db")
        seed_database(db_path)
        return db_path

    def test_compound_lookup(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            water = db.get_compound("Water")
            assert water is not None
            assert abs(water["mw"] - 18.015) < 0.01

    def test_compound_search(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            results = db.search_compounds("eth")
            names = [r["name"].lower() for r in results]
            assert any("ethanol" in n for n in names)

    def test_antoine_retrieval(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            antoine = db.get_antoine("Benzene")
            assert antoine is not None
            assert abs(antoine["A"] - 6.90565) < 0.001

    def test_nrtl_retrieval(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            nrtl = db.get_nrtl("Benzene", "Toluene")
            assert nrtl is not None
            assert abs(nrtl["alpha12"] - 0.30) < 0.01

    def test_nrtl_reverse_lookup(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            fwd = db.get_nrtl("Benzene", "Toluene")
            rev = db.get_nrtl("Toluene", "Benzene")
            assert fwd["dg12"] == rev["dg21"]

    def test_henry_retrieval(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            h = db.get_henry("CO2", "water")
            assert h is not None
            assert abs(h["H_pa"] - 1.61e8) < 1e6

    def test_packing_list(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            packings = db.list_packings()
            assert len(packings) >= 10

    def test_packing_filter_by_type(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            structured = db.list_packings("structured")
            assert all(p["type"] == "structured" for p in structured)
            assert len(structured) >= 3

    def test_category_filter(self, seeded_db):
        with ChemicalDatabase(seeded_db) as db:
            gases = db.list_compounds("gas")
            assert len(gases) >= 5
            solvents = db.list_compounds("solvent")
            assert len(solvents) >= 5
