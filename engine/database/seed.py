"""
Seed the SIMCO chemical database with baseline data.

Run: python -m engine.database.seed
"""

from .db import ChemicalDatabase

COMPOUNDS = [
    dict(name="Water", formula="H2O", cas_number="7732-18-5", mw=18.015, tc=647.1, pc=22064000, omega=0.344, tb=373.15, category="solvent"),
    dict(name="Methanol", formula="CH3OH", cas_number="67-56-1", mw=32.042, tc=512.6, pc=8084000, omega=0.565, tb=337.7, category="solvent"),
    dict(name="Ethanol", formula="C2H5OH", cas_number="64-17-5", mw=46.069, tc=513.9, pc=6148000, omega=0.649, tb=351.4, category="solvent"),
    dict(name="Benzene", formula="C6H6", cas_number="71-43-2", mw=78.114, tc=562.2, pc=4895000, omega=0.210, tb=353.2, category="solvent"),
    dict(name="Toluene", formula="C7H8", cas_number="108-88-3", mw=92.141, tc=591.7, pc=4108000, omega=0.264, tb=383.8, category="solvent"),
    dict(name="Acetone", formula="C3H6O", cas_number="67-64-1", mw=58.08, tc=508.1, pc=4700000, omega=0.307, tb=329.2, category="solvent"),
    dict(name="n-Hexane", formula="C6H14", cas_number="110-54-3", mw=86.178, tc=507.4, pc=3025000, omega=0.299, tb=341.9, category="solvent"),
    dict(name="n-Heptane", formula="C7H16", cas_number="142-82-5", mw=100.205, tc=540.1, pc=2740000, omega=0.349, tb=371.6, category="solvent"),
    dict(name="Chloroform", formula="CHCl3", cas_number="67-66-3", mw=119.377, tc=536.4, pc=5472000, omega=0.222, tb=334.3, category="solvent"),
    dict(name="MEA", formula="C2H7NO", cas_number="141-43-5", mw=61.083, tc=678.0, pc=7120000, omega=0.446, tb=443.5, category="solvent"),
    dict(name="DEA", formula="C4H11NO2", cas_number="111-42-2", mw=105.14, tc=736.6, pc=4270000, omega=0.953, tb=542.0, category="solvent"),
    dict(name="MDEA", formula="C5H13NO2", cas_number="105-59-9", mw=119.16, tc=741.9, pc=3880000, omega=0.588, tb=520.0, category="solvent"),
    dict(name="Carbon dioxide", formula="CO2", cas_number="124-38-9", mw=44.01, tc=304.1, pc=7383000, omega=0.225, tb=194.7, category="gas"),
    dict(name="Hydrogen sulfide", formula="H2S", cas_number="7783-06-4", mw=34.08, tc=373.2, pc=8937000, omega=0.090, tb=212.8, category="gas"),
    dict(name="Sulfur dioxide", formula="SO2", cas_number="7446-09-5", mw=64.066, tc=430.8, pc=7884000, omega=0.245, tb=263.1, category="gas"),
    dict(name="Ammonia", formula="NH3", cas_number="7664-41-7", mw=17.031, tc=405.4, pc=11353000, omega=0.257, tb=239.8, category="gas"),
    dict(name="Nitrogen", formula="N2", cas_number="7727-37-9", mw=28.014, tc=126.2, pc=3394000, omega=0.040, tb=77.4, category="gas"),
    dict(name="Oxygen", formula="O2", cas_number="7782-44-7", mw=31.999, tc=154.6, pc=5043000, omega=0.022, tb=90.2, category="gas"),
    dict(name="Methane", formula="CH4", cas_number="74-82-8", mw=16.043, tc=190.6, pc=4599000, omega=0.011, tb=111.7, category="gas"),
    dict(name="Chlorine", formula="Cl2", cas_number="7782-50-5", mw=70.906, tc=417.2, pc=7711000, omega=0.069, tb=239.1, category="gas"),
]

ANTOINE_DATA = [
    dict(compound_name="Water", A=8.07131, B=1730.63, C=233.426, T_min=1, T_max=100, source="NIST"),
    dict(compound_name="Methanol", A=8.08097, B=1582.27, C=239.726, T_min=15, T_max=84, source="NIST"),
    dict(compound_name="Ethanol", A=8.20417, B=1642.89, C=230.300, T_min=20, T_max=93, source="NIST"),
    dict(compound_name="Benzene", A=6.90565, B=1211.033, C=220.790, T_min=8, T_max=80, source="NIST"),
    dict(compound_name="Toluene", A=6.95464, B=1344.800, C=219.482, T_min=6, T_max=137, source="NIST"),
    dict(compound_name="Acetone", A=7.02447, B=1161.0, C=224.0, T_min=-20, T_max=77, source="NIST"),
    dict(compound_name="n-Hexane", A=6.87776, B=1171.530, C=224.366, T_min=-25, T_max=92, source="NIST"),
    dict(compound_name="n-Heptane", A=6.89385, B=1264.370, C=216.636, T_min=-2, T_max=127, source="NIST"),
    dict(compound_name="Chloroform", A=6.95465, B=1170.966, C=226.232, T_min=-10, T_max=60, source="NIST"),
]

NRTL_DATA = [
    dict(comp1="Benzene", comp2="Toluene", dg12=228.46, dg21=-228.46, alpha12=0.30, source="DECHEMA"),
    dict(comp1="Methanol", comp2="Water", dg12=-253.88, dg21=845.21, alpha12=0.30, source="DECHEMA"),
    dict(comp1="Ethanol", comp2="Water", dg12=1300.52, dg21=975.49, alpha12=0.30, source="DECHEMA"),
    dict(comp1="Acetone", comp2="Water", dg12=631.05, dg21=1197.41, alpha12=0.30, source="DECHEMA"),
    dict(comp1="Acetone", comp2="Methanol", dg12=184.70, dg21=222.64, alpha12=0.30, source="DECHEMA"),
    dict(comp1="Methanol", comp2="Benzene", dg12=4148.36, dg21=2377.51, alpha12=0.47, source="DECHEMA"),
    dict(comp1="Ethanol", comp2="Benzene", dg12=4104.44, dg21=2386.41, alpha12=0.47, source="DECHEMA"),
    dict(comp1="Chloroform", comp2="Methanol", dg12=-1579.59, dg21=4824.98, alpha12=0.30, source="DECHEMA"),
]

HENRY_DATA = [
    dict(gas="CO2", solvent="water", H_pa=1.61e8, dH_sol=-19400, source="Sander 2015"),
    dict(gas="O2", solvent="water", H_pa=4.26e9, dH_sol=-14200, source="Sander 2015"),
    dict(gas="N2", solvent="water", H_pa=8.65e9, dH_sol=-10400, source="Sander 2015"),
    dict(gas="H2S", solvent="water", H_pa=5.53e7, dH_sol=-18000, source="Sander 2015"),
    dict(gas="SO2", solvent="water", H_pa=7.88e5, dH_sol=-24800, source="Sander 2015"),
    dict(gas="NH3", solvent="water", H_pa=5.69e4, dH_sol=-34200, source="Sander 2015"),
    dict(gas="Cl2", solvent="water", H_pa=6.25e6, dH_sol=-18900, source="Sander 2015"),
    dict(gas="CH4", solvent="water", H_pa=4.13e9, dH_sol=-14500, source="Sander 2015"),
    dict(gas="CO", solvent="water", H_pa=5.80e9, dH_sol=-11000, source="Sander 2015"),
    dict(gas="CO2", solvent="MEA 30wt%", H_pa=2.41e6, dH_sol=-84000, source="Austgen 1989"),
]

PACKING_DATA = [
    dict(name="Raschig Ring 25mm", type="random", material="ceramic", nominal_size_mm=25, specific_area=190, void_fraction=0.68, packing_factor=580, hetp=0.60, source="Perry's"),
    dict(name="Raschig Ring 50mm", type="random", material="ceramic", nominal_size_mm=50, specific_area=95, void_fraction=0.74, packing_factor=155, hetp=0.90, source="Perry's"),
    dict(name="Pall Ring 25mm", type="random", material="metal", nominal_size_mm=25, specific_area=205, void_fraction=0.94, packing_factor=157, hetp=0.45, source="Perry's"),
    dict(name="Pall Ring 50mm", type="random", material="metal", nominal_size_mm=50, specific_area=105, void_fraction=0.96, packing_factor=66, hetp=0.65, source="Perry's"),
    dict(name="IMTP 25", type="random", material="metal", nominal_size_mm=25, specific_area=230, void_fraction=0.97, packing_factor=135, hetp=0.40, source="Koch-Glitsch"),
    dict(name="IMTP 50", type="random", material="metal", nominal_size_mm=50, specific_area=108, void_fraction=0.98, packing_factor=57, hetp=0.60, source="Koch-Glitsch"),
    dict(name="Mellapak 250Y", type="structured", material="metal", nominal_size_mm=None, specific_area=250, void_fraction=0.98, packing_factor=66, hetp=0.35, source="Sulzer"),
    dict(name="Mellapak 500Y", type="structured", material="metal", nominal_size_mm=None, specific_area=500, void_fraction=0.98, packing_factor=112, hetp=0.20, source="Sulzer"),
    dict(name="Flexipac 1Y", type="structured", material="metal", nominal_size_mm=None, specific_area=410, void_fraction=0.97, packing_factor=98, hetp=0.25, source="Koch-Glitsch"),
    dict(name="Flexipac 2Y", type="structured", material="metal", nominal_size_mm=None, specific_area=225, void_fraction=0.98, packing_factor=59, hetp=0.40, source="Koch-Glitsch"),
    dict(name="Berl Saddle 25mm", type="random", material="ceramic", nominal_size_mm=25, specific_area=250, void_fraction=0.68, packing_factor=360, hetp=0.55, source="Perry's"),
    dict(name="Intalox Saddle 25mm", type="random", material="ceramic", nominal_size_mm=25, specific_area=256, void_fraction=0.73, packing_factor=302, hetp=0.50, source="Perry's"),
]


def seed_database(db_path: str = None):
    """Populate the database with baseline chemical data."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        print("Seeding compounds...")
        for c in COMPOUNDS:
            db.add_compound(**c)
        print(f"  → {len(COMPOUNDS)} compounds")

        print("Seeding Antoine coefficients...")
        for a in ANTOINE_DATA:
            db.add_antoine(**a)
        print(f"  → {len(ANTOINE_DATA)} sets")

        print("Seeding NRTL binary parameters...")
        for n in NRTL_DATA:
            db.add_nrtl(**n)
        print(f"  → {len(NRTL_DATA)} pairs")

        print("Seeding Henry's law constants...")
        for h in HENRY_DATA:
            db.add_henry(**h)
        print(f"  → {len(HENRY_DATA)} constants")

        print("Seeding packing data...")
        for p in PACKING_DATA:
            db.add_packing(**p)
        print(f"  → {len(PACKING_DATA)} packings")

        print("\nDatabase seeded successfully.")


if __name__ == "__main__":
    seed_database()
