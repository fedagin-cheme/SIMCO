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


# ─── Packed Column Hydraulics Tests ────────────────────────────────────────

from engine.thermo.column_hydraulics import (
    flow_parameter,
    flooding_velocity,
    column_diameter,
    pressure_drop_irrigated,
    minimum_wetting_rate,
    design_column,
)


class TestColumnHydraulics:
    """Tests for packed column hydraulic design calculations."""

    # Reference system: air-water at 20°C, 1 atm
    # ρ_G = 1.2 kg/m³, ρ_L = 998 kg/m³, μ_L = 1e-3 Pa·s
    RHO_G = 1.2
    RHO_L = 998.0
    MU_L = 1.0e-3

    def test_flow_parameter_air_water(self):
        """Flow parameter for L/G=1 air-water should be ~0.035."""
        X = flow_parameter(L_mass=1.0, G_mass=1.0, rho_G=1.2, rho_L=998.0)
        assert 0.01 < X < 0.1, f"Flow parameter X={X}, expected ~0.035"

    def test_flow_parameter_high_LG(self):
        """Higher L/G → higher flow parameter."""
        X_low = flow_parameter(1.0, 1.0, 1.2, 998.0)
        X_high = flow_parameter(10.0, 1.0, 1.2, 998.0)
        assert X_high > X_low

    def test_flooding_velocity_pall_ring_50mm(self):
        """Pall Ring 50mm, air-water: u_flood should be in 1–4 m/s range.

        Perry's 8th ed.: typical flooding velocities for metal Pall Rings
        at moderate L/G are 1.5–3.5 m/s.
        """
        F_p = 66  # Pall Ring 50mm, m⁻¹
        u_flood = flooding_velocity(
            F_p=F_p, rho_G=1.2, rho_L=998.0,
            L_mass=2.0, G_mass=1.0, mu_L=1e-3,
        )
        assert 1.0 < u_flood < 5.0, f"u_flood={u_flood:.2f} m/s, expected 1–4 range"

    def test_flooding_velocity_structured_higher(self):
        """Structured packing (lower F_p) should flood at higher velocity than random."""
        # Mellapak 250Y: F_p=66, Raschig Ring 25mm: F_p=580
        u_structured = flooding_velocity(66, 1.2, 998.0, 2.0, 1.0)
        u_random = flooding_velocity(580, 1.2, 998.0, 2.0, 1.0)
        assert u_structured > u_random, "Structured packing should have higher flooding velocity"

    def test_column_diameter_reasonable(self):
        """1 m³/s gas at u_flood=2 m/s, 70% → D ≈ 0.95 m."""
        result = column_diameter(Q_gas_m3s=1.0, u_flood=2.0, flooding_fraction=0.7)
        D = result["D_column_m"]
        assert 0.5 < D < 2.0, f"D={D:.2f} m, expected ~0.95"
        # Verify consistency: A = Q/u_design
        assert abs(result["A_column_m2"] - 1.0 / (0.7 * 2.0)) < 0.001

    def test_column_diameter_higher_flooding_fraction_gives_smaller(self):
        """Higher flooding fraction → smaller column."""
        d70 = column_diameter(1.0, 2.0, 0.70)["D_column_m"]
        d80 = column_diameter(1.0, 2.0, 0.80)["D_column_m"]
        assert d80 < d70

    def test_pressure_drop_positive(self):
        """Pressure drop must be positive at design conditions."""
        dP = pressure_drop_irrigated(
            u_G=1.5, F_p=66, rho_G=1.2, rho_L=998.0,
            L_mass=2.0, G_mass=1.0, mu_L=1e-3,
        )
        assert dP > 0, f"Pressure drop must be positive, got {dP}"

    def test_pressure_drop_order_of_magnitude(self):
        """Typical absorber ΔP/Z is 100–2000 Pa/m."""
        dP = pressure_drop_irrigated(
            u_G=1.5, F_p=66, rho_G=1.2, rho_L=998.0,
            L_mass=2.0, G_mass=1.0, mu_L=1e-3,
        )
        assert 10 < dP < 5000, f"ΔP/Z={dP:.0f} Pa/m, outside expected range"

    def test_pressure_drop_increases_with_velocity(self):
        """Higher gas velocity → higher pressure drop."""
        common = dict(F_p=66, rho_G=1.2, rho_L=998.0, L_mass=2.0, G_mass=1.0)
        dP_low = pressure_drop_irrigated(u_G=1.0, **common)
        dP_high = pressure_drop_irrigated(u_G=2.0, **common)
        assert dP_high > dP_low

    def test_minimum_wetting_rate_positive(self):
        """MWR should be a small positive number."""
        MWR = minimum_wetting_rate(a_p=250)
        assert MWR > 0
        assert MWR < 0.01, f"MWR={MWR}, suspiciously high"

    def test_design_column_full_integration(self):
        """Full design calculation should produce consistent results."""
        packing = {
            "name": "Pall Ring 50mm",
            "type": "random",
            "packing_factor": 66,
            "specific_area": 105,
            "void_fraction": 0.96,
        }
        result = design_column(
            G_mass=1.0, L_mass=3.0,
            rho_G=1.2, rho_L=998.0,
            T_celsius=25.0, P_bar=1.01325,
            packing=packing, flooding_fraction=0.7,
        )
        # Check all required keys present
        assert "D_column_m" in result
        assert "u_flood_ms" in result
        assert "pressure_drop_Pa_m" in result
        assert "wetting_adequate" in result
        # Diameter should be reasonable for 1 kg/s gas
        assert 0.3 < result["D_column_m"] < 3.0
        # Design velocity should be 70% of flooding
        assert abs(result["u_design_ms"] - 0.7 * result["u_flood_ms"]) < 0.001

    def test_design_column_with_db_packing(self):
        """Design with actual packing from the JSON database."""
        from engine.database.db import get_db
        db = get_db()
        packing = db.get_packing("Mellapak 250Y")
        assert packing is not None, "Mellapak 250Y not found in DB"
        result = design_column(
            G_mass=0.5, L_mass=2.0,
            rho_G=1.2, rho_L=998.0,
            T_celsius=30.0, P_bar=1.01325,
            packing=packing, flooding_fraction=0.65,
        )
        assert result["packing_name"] == "Mellapak 250Y"
        assert result["D_column_m"] > 0


# ─── Mass Transfer Tests ──────────────────────────────────────────────────

from engine.thermo.mass_transfer import (
    kremser_NTU,
    kremser_y_out,
    absorption_factor,
    hetp_height,
    onda_kG_a,
    onda_kL_a,
    overall_HTU,
    design_packed_height,
    operating_equilibrium_lines,
)


class TestMassTransfer:
    """Tests for packed column mass transfer calculations."""

    def test_kremser_ntu_basic(self):
        """90% removal with A=1.5 → N_OG ≈ 4.5 (textbook example)."""
        # y_in=0.10, y_out=0.01, A=1.5
        N = kremser_NTU(0.10, 0.01, 1.5)
        assert 3.0 < N < 7.0, f"N_OG={N:.2f}, expected ~4-5 for 90% removal"

    def test_kremser_ntu_high_A(self):
        """High A (easy absorption) → fewer transfer units."""
        N_low_A = kremser_NTU(0.10, 0.01, 1.2)
        N_high_A = kremser_NTU(0.10, 0.01, 3.0)
        assert N_high_A < N_low_A, "Higher A should give fewer NTU"

    def test_kremser_ntu_A_equals_1(self):
        """Special case A=1: N_OG = y_in/y_out - 1."""
        N = kremser_NTU(0.10, 0.01, 1.0)
        expected = 0.10 / 0.01 - 1.0  # = 9.0
        assert abs(N - expected) < 0.1, f"A=1: N_OG={N:.2f}, expected {expected}"

    def test_kremser_ntu_99_removal(self):
        """99% removal needs more transfer units than 90%."""
        N_90 = kremser_NTU(0.10, 0.01, 1.5)
        N_99 = kremser_NTU(0.10, 0.001, 1.5)
        assert N_99 > N_90

    def test_absorption_factor(self):
        """A = L/(m·G) basic check."""
        A = absorption_factor(L_mol=100.0, G_mol=50.0, m=1.0)
        assert abs(A - 2.0) < 0.001

    def test_hetp_height(self):
        """Z = 5 stages × 0.4 m = 2.0 m."""
        Z = hetp_height(5.0, 0.4)
        assert abs(Z - 2.0) < 0.001

    def test_onda_kG_a_positive(self):
        """Gas-phase mass transfer coefficient should be positive."""
        kG_a = onda_kG_a(
            G_mass_flux=1.0, a_p=200, D_G=1.5e-5,
            mu_G=1.8e-5, rho_G=1.2,
        )
        assert kG_a > 0

    def test_onda_kG_a_order_of_magnitude(self):
        """kG·a typically 0.01–10 s⁻¹ for packed columns."""
        kG_a = onda_kG_a(
            G_mass_flux=1.5, a_p=250, D_G=1.5e-5,
            mu_G=1.8e-5, rho_G=1.2,
        )
        assert 0.001 < kG_a < 100, f"kG_a={kG_a}, outside expected range"

    def test_onda_kL_a_positive(self):
        """Liquid-phase mass transfer coefficient should be positive."""
        kL_a = onda_kL_a(
            L_mass_flux=5.0, a_p=250, D_L=1.5e-9,
            mu_L=1e-3, rho_L=998.0,
        )
        assert kL_a > 0

    def test_overall_htu_reasonable(self):
        """H_OG typically 0.3–3.0 m for gas absorption."""
        htu = overall_HTU(
            G_mol_flux=40.0, L_mol_flux=200.0, m=0.8,
            kG_a=0.5, kL_a=0.01,
        )
        assert 0.05 < htu["H_OG_m"] < 10.0, f"H_OG={htu['H_OG_m']}"

    def test_operating_lines_shape(self):
        """Operating and equilibrium lines should have correct shape."""
        lines = operating_equilibrium_lines(
            y_in=0.10, y_out=0.01, m=1.0, A=1.5,
        )
        assert len(lines["x_eq"]) == 51
        assert len(lines["y_op"]) == 51
        # Equilibrium line starts at origin
        assert abs(lines["y_eq"][0]) < 1e-10
        # Operating line starts at (x_out, y_out)
        assert abs(lines["y_op"][0] - 0.01) < 1e-6
        # Operating line ends at (x_in, y_in)
        assert abs(lines["y_op"][-1] - 0.10) < 0.001

    def test_design_packed_height_integration(self):
        """Full mass transfer design should produce consistent results."""
        packing = {
            "name": "Mellapak 250Y",
            "type": "structured",
            "packing_factor": 66,
            "specific_area": 250,
            "void_fraction": 0.98,
            "hetp": 0.35,
        }
        result = design_packed_height(
            y_in=0.05, y_out=0.005,  # 90% removal
            m=0.8,
            G_mol=40.0, L_mol=100.0,
            A_column=0.5,
            packing=packing,
            dP_per_m=15.0,
        )
        assert result["removal_percent"] == 90.0
        assert result["Z_htu_ntu_m"] > 0
        assert result["Z_hetp_m"] > 0
        assert result["N_OG"] > 0
        assert result["absorption_factor_A"] > 1.0  # feasible absorption
        assert result["total_dP_Pa"] > 0
        assert "lines" in result

    def test_design_packed_height_with_db_packing(self):
        """Design with actual packing from JSON database."""
        from engine.database.db import get_db
        db = get_db()
        packing = db.get_packing("Pall Ring 50mm")
        assert packing is not None

        result = design_packed_height(
            y_in=0.10, y_out=0.01,
            m=1.0,
            G_mol=30.0, L_mol=100.0,
            A_column=0.5,
            packing=packing,
        )
        assert result["Z_htu_ntu_m"] > 0
        assert result["absorption_factor_A"] > 0

    # ── Kremser inverse (kremser_y_out) tests ──

    def test_kremser_y_out_roundtrip(self):
        """kremser_y_out should be the exact inverse of kremser_NTU."""
        y_in, y_out_expected, A = 0.10, 0.01, 2.0
        NTU = kremser_NTU(y_in, y_out_expected, A)
        y_out_recovered = kremser_y_out(y_in, A, NTU)
        assert abs(y_out_recovered - y_out_expected) < 1e-8

    def test_kremser_y_out_A_equals_1(self):
        """Special case A=1: y_out = y_in / (1 + NTU)."""
        y_out = kremser_y_out(0.10, 1.0, 9.0)
        assert abs(y_out - 0.01) < 1e-8

    def test_kremser_roundtrip_various_A(self):
        """Roundtrip NTU → y_out for several A values where 90% removal is feasible."""
        for A in [1.0, 1.2, 1.5, 2.0, 5.0]:
            NTU = kremser_NTU(0.10, 0.01, A)
            y_out = kremser_y_out(0.10, A, NTU)
            assert abs(y_out - 0.01) < 1e-6, f"Roundtrip failed for A={A}: y_out={y_out}"


# ─── Scrubber Design Tests ────────────────────────────────────────────────

from engine.thermo.scrubber import design_scrubber, henry_at_T


class TestScrubber:
    """Tests for multi-component gas scrubber design."""

    def test_henry_at_T_increases_with_temperature(self):
        """Henry's constant should increase with T for CO2 (exothermic dissolution)."""
        H_25 = henry_at_T(161e6, -19400, 298.15, 298.15)
        H_40 = henry_at_T(161e6, -19400, 298.15, 313.15)
        assert H_40 < H_25  # dH_sol negative → H decreases (more soluble at lower T)

    def test_flue_gas_mea_co2_removal(self):
        """Flue gas + MEA: CO2 should be partially removed."""
        result = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 73},
                {"name": "Carbon dioxide", "mol_percent": 12},
                {"name": "Water", "mol_percent": 12},
                {"name": "Oxygen", "mol_percent": 3},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            removal_target_pct=90.0,
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            T_celsius=40, P_bar=1.01325,
            rho_L_kgm3=1012,
        )
        # CO2 should have some removal
        co2_exit = next(g for g in result["exit_gas"] if "dioxide" in g["name"].lower())
        assert co2_exit["removal_pct"] > 0
        # N2 should pass through
        n2_exit = next(g for g in result["exit_gas"] if "Nitrogen" in g["name"])
        assert n2_exit["removal_pct"] == 0.0
        # Column dimensions should be positive
        assert result["D_column_mm"] > 0
        assert result["Z_design_m"] > 0

    def test_natural_gas_mdea_selectivity(self):
        """MDEA should remove H2S faster than CO2 (selectivity)."""
        result = design_scrubber(
            gas_mixture=[
                {"name": "Methane", "mol_percent": 90},
                {"name": "Carbon dioxide", "mol_percent": 5},
                {"name": "Hydrogen sulfide", "mol_percent": 3},
                {"name": "Nitrogen", "mol_percent": 2},
            ],
            solvent_name="Methyldiethanolamine",
            packing_name="IMTP 50",
            removal_target_pct=95.0,
            G_mass_kgs=2.0, L_mass_kgs=10.0,
            T_celsius=35, P_bar=30.0,
            rho_L_kgm3=1038,
        )
        h2s_exit = next(g for g in result["exit_gas"] if "sulfide" in g["name"].lower())
        co2_exit = next(g for g in result["exit_gas"] if "dioxide" in g["name"].lower())
        # H2S should have higher removal than CO2 with MDEA
        assert h2s_exit["removal_pct"] >= co2_exit["removal_pct"]

    def test_water_physical_absorption(self):
        """SO2 scrubbing with water — physical absorption."""
        result = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 95},
                {"name": "Sulfur dioxide", "mol_percent": 5},
            ],
            solvent_name="Water",
            packing_name="Pall Ring 50mm",
            removal_target_pct=80.0,
            G_mass_kgs=0.5, L_mass_kgs=5.0,
            T_celsius=25, P_bar=1.01325,
        )
        assert result["Z_design_m"] > 0
        so2_exit = next(g for g in result["exit_gas"] if "Sulfur" in g["name"])
        assert so2_exit["removal_pct"] > 0

    def test_exit_gas_sums_to_100(self):
        """Exit gas mol percentages should sum to ~100%."""
        result = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            removal_target_pct=90.0,
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            T_celsius=40, P_bar=1.01325,
            rho_L_kgm3=1012,
        )
        total = sum(g["outlet_mol_pct"] for g in result["exit_gas"])
        assert abs(total - 100.0) < 0.1, f"Exit gas total = {total}%"

    def test_scrubber_api_endpoint(self):
        """Test the /api/column/scrubber-design endpoint."""
        from engine.api.server import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        r = client.post("/api/column/scrubber-design", json={
            "gas_mixture": [
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            "solvent_name": "Monoethanolamine",
            "packing_name": "Mellapak 250Y",
            "G_mass_kgs": 1.0,
            "L_mass_kgs": 20.0,
            "rho_L_kgm3": 1012,
        })
        assert r.status_code == 200
        data = r.json()
        assert "exit_gas" in data
        assert "Z_design_m" in data
        assert data["D_column_mm"] > 0

    # ── DOF solve mode tests ──

    def test_solve_for_Z_default_backward_compat(self):
        """Default solve_for='Z' should produce results with solve_mode='Z'."""
        result = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            removal_target_pct=90.0,
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            rho_L_kgm3=1012,
            solve_for="Z",
        )
        assert result["solve_mode"] == "Z"
        assert result["Z_design_m"] > 0
        assert result["D_column_mm"] > 0

    def test_solve_for_eta_mode(self):
        """Mode 2: Given L + Z, compute removal. Cross-validate with Mode 1."""
        # Run Mode 1 to get a reference Z
        result_mode1 = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            removal_target_pct=90.0,
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            rho_L_kgm3=1012,
        )
        Z_from_mode1 = result_mode1["Z_design_m"]

        # Run Mode 2 with the same L and the Z from Mode 1
        result_mode2 = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            rho_L_kgm3=1012,
            solve_for="eta",
            Z_packed_m=Z_from_mode1,
        )
        assert result_mode2["solve_mode"] == "eta"
        # Should recover ~90% removal for the dominant component
        co2_removal = next(g for g in result_mode2["exit_gas"] if "dioxide" in g["name"].lower())["removal_pct"]
        assert abs(co2_removal - 90.0) < 2.0, f"Expected ~90% removal, got {co2_removal}%"

    def test_solve_for_L_mode(self):
        """Mode 3: Given η + Z, compute L via bisection. Cross-validate with Mode 1."""
        # Run Mode 1 to get reference Z at L=20
        result_mode1 = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            removal_target_pct=90.0,
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            rho_L_kgm3=1012,
        )
        Z_ref = result_mode1["Z_design_m"]

        # Run Mode 3 with η=90% and Z from Mode 1
        result_mode3 = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            removal_target_pct=90.0,
            G_mass_kgs=1.0,
            rho_L_kgm3=1012,
            solve_for="L",
            Z_packed_m=Z_ref,
        )
        assert result_mode3["solve_mode"] == "L"
        assert result_mode3["bisection_converged"] is True
        # Should recover ~20 kg/s
        computed_L = result_mode3["computed_L_kgs"]
        assert abs(computed_L - 20.0) / 20.0 < 0.05, f"Expected ~20 kg/s, got {computed_L}"

    def test_solve_for_eta_with_shorter_column(self):
        """Mode 2: halving the column height should reduce removal."""
        # First get the reference Z for 90% removal
        ref = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            removal_target_pct=90.0,
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            rho_L_kgm3=1012,
        )
        Z_ref = ref["Z_design_m"]

        # Use half the height — should give less removal
        result = design_scrubber(
            gas_mixture=[
                {"name": "Nitrogen", "mol_percent": 85},
                {"name": "Carbon dioxide", "mol_percent": 15},
            ],
            solvent_name="Monoethanolamine",
            packing_name="Mellapak 250Y",
            G_mass_kgs=1.0, L_mass_kgs=20.0,
            rho_L_kgm3=1012,
            solve_for="eta",
            Z_packed_m=Z_ref * 0.5,
        )
        co2_removal = next(g for g in result["exit_gas"] if "dioxide" in g["name"].lower())["removal_pct"]
        assert co2_removal < 90.0, f"Halved column should give <90% removal, got {co2_removal}%"
        assert co2_removal > 0.0, "Some removal should still occur"
