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


# ─── Electrolyte VLE Tests ─────────────────────────────────────────────────────

class TestElectrolyteVLE:
    """Tests for boiling point elevation and vapor pressure depression of electrolyte solutions."""

    def test_naoh_20pct_at_1atm(self):
        """NaOH 20 wt% at 1 atm → ~111°C from OxyChem handbook."""
        from engine.thermo.electrolyte_vle import boiling_point
        T = boiling_point("NaOH", 20.0, 101325.0)
        assert abs(T - 111.0) < 1.5, f"NaOH 20%: expected ~111°C, got {T:.1f}°C"

    def test_k2co3_25pct_at_1atm(self):
        """K₂CO₃ 25 wt% at 1 atm → ~105°C from Armand Products handbook."""
        from engine.thermo.electrolyte_vle import boiling_point
        T = boiling_point("K2CO3", 25.0, 101325.0)
        assert abs(T - 105.0) < 1.5, f"K2CO3 25%: expected ~105°C, got {T:.1f}°C"

    def test_pure_water_limit(self):
        """0 wt% electrolyte → boiling point = pure water (100°C at 1 atm)."""
        from engine.thermo.electrolyte_vle import boiling_point
        T = boiling_point("NaOH", 0.0, 101325.0)
        assert abs(T - 100.0) < 0.5, f"Pure water: expected 100°C, got {T:.1f}°C"

    def test_vp_depression(self):
        """NaOH 20% at 100°C → vapor pressure less than pure water."""
        from engine.thermo.electrolyte_vle import vapor_pressure
        P = vapor_pressure("NaOH", 20.0, 100.0)
        assert P < 101325.0, f"VP should be < 101325 Pa, got {P:.0f} Pa"
        assert P > 50000.0, f"VP suspiciously low: {P:.0f} Pa"

    def test_bpe_curve_shape(self):
        """BPE curve should be monotonically increasing with concentration."""
        from engine.thermo.electrolyte_vle import generate_bpe_curve
        data = generate_bpe_curve("NaOH")
        temps = data["T_boil"]
        for i in range(1, len(temps)):
            assert temps[i] >= temps[i - 1], f"BPE curve not monotonic at index {i}"

    def test_vp_curve_shape(self):
        """VP curve should be monotonically decreasing with concentration."""
        from engine.thermo.electrolyte_vle import generate_vp_curve
        data = generate_vp_curve("K2CO3", 100.0)
        pressures = data["P_water"]
        for i in range(1, len(pressures)):
            assert pressures[i] <= pressures[i - 1], f"VP curve not monotonic at index {i}"

    def test_operating_point_consistency(self):
        """Operating point at 1 atm should match BPE function."""
        from engine.thermo.electrolyte_vle import boiling_point, calculate_operating_point
        T_direct = boiling_point("K2CO3", 30.0, 101325.0)
        op = calculate_operating_point("K2CO3", 30.0, P_pa=101325.0)
        assert abs(T_direct - op["T_boil_celsius"]) < 0.1

    def test_available_electrolytes(self):
        """Should have at least NaOH and K2CO3."""
        from engine.thermo.electrolyte_vle import get_available_electrolytes
        solutes = get_available_electrolytes()
        ids = [s["id"] for s in solutes]
        assert "NaOH" in ids
        assert "K2CO3" in ids

    def test_unicode_normalization(self):
        """Should accept K₂CO₃ with subscript digits."""
        from engine.thermo.electrolyte_vle import boiling_point
        T = boiling_point("K₂CO₃", 25.0, 101325.0)
        assert T > 100.0


# ─── Amine-Water VLE Tests ────────────────────────────────────────────────────

class TestAmineWaterVLE:
    """Tests for MEA-water and MDEA-water binary VLE using NRTL."""

    def test_mea_water_nrtl_params_exist(self):
        """MEA-water NRTL parameters should be available."""
        from engine.thermo.nrtl import get_nrtl_params
        params = get_nrtl_params("mea", "water")
        assert params is not None, "MEA-water NRTL params not found"
        dg12, dg21, alpha = params
        assert alpha > 0

    def test_mdea_water_nrtl_params_exist(self):
        """MDEA-water NRTL parameters should be available."""
        from engine.thermo.nrtl import get_nrtl_params
        params = get_nrtl_params("mdea", "water")
        assert params is not None, "MDEA-water NRTL params not found"

    def test_mea_water_txy_endpoints(self):
        """MEA-water Txy at 1 atm: x=0 → 100°C, x=1 → ~171°C."""
        from engine.api.routes.vle import bubble_point_temperature
        P = 101325.0
        r0 = bubble_point_temperature(0.0, P, "mea", "water")
        r1 = bubble_point_temperature(1.0, P, "mea", "water")
        assert abs(r0["T_celsius"] - 100.0) < 1.0, f"x=0 should be ~100°C, got {r0['T_celsius']}"
        assert abs(r1["T_celsius"] - 171.6) < 2.0, f"x=1 should be ~171°C, got {r1['T_celsius']}"

    def test_mdea_water_txy_endpoints(self):
        """MDEA-water Txy at 1 atm: x=0 → 100°C, x=1 → ~247°C."""
        from engine.api.routes.vle import bubble_point_temperature
        P = 101325.0
        r0 = bubble_point_temperature(0.0, P, "mdea", "water")
        r1 = bubble_point_temperature(1.0, P, "mdea", "water")
        assert abs(r0["T_celsius"] - 100.0) < 1.0
        assert abs(r1["T_celsius"] - 247.0) < 3.0, f"x=1 should be ~247°C, got {r1['T_celsius']}"

    def test_mea_water_txy_monotonic(self):
        """MEA-water Txy should increase monotonically with x_MEA."""
        from engine.api.routes.vle import generate_txy_diagram
        data = generate_txy_diagram(101325.0, "mea", "water", n_points=21)
        temps = data["T_celsius"]
        for i in range(1, len(temps)):
            assert temps[i] >= temps[i - 1] - 0.1, f"Txy not monotonic at index {i}"

    def test_mea_water_low_volatility(self):
        """At x_MEA=0.3, vapor should be mostly water (y_MEA << x_MEA)."""
        from engine.api.routes.vle import bubble_point_temperature
        r = bubble_point_temperature(0.3, 101325.0, "mea", "water")
        assert r["y1"] < 0.10, f"MEA too volatile: y={r['y1']}"
