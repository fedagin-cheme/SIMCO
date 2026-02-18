with open('engine/thermo/antoine.py', 'w') as f:
    f.write("""from typing import Optional

ANTOINE_COEFFICIENTS = {
    "water":      (8.07131, 1730.630, 233.426,   1.0,  100.0),
    "water_high": (8.14019, 1810.940, 244.485,  60.0,  150.0),
    "methanol":   (8.08097, 1582.271, 239.726, -10.0,   84.0),
    "ethanol":    (8.11220, 1592.864, 226.184,  20.0,   93.0),
    "benzene":    (6.90565, 1211.033, 220.790,   8.0,   80.0),
    "toluene":    (6.95087, 1342.310, 219.187,   6.0,  137.0),
    "acetone":    (7.11714, 1210.595, 229.664, -13.0,   55.0),
    "n_hexane":   (6.87776, 1171.530, 224.366, -25.0,   92.0),
    "n_heptane":  (6.89385, 1264.370, 216.636,  -2.0,  127.0),
    "chloroform": (6.95465, 1170.966, 226.232, -10.0,   60.0),
    "co2":        (6.81228, 1301.679,  -3.494, -56.6,   31.0),
    "h2s":        (7.07354, 1044.849,  -3.994, -85.5,  100.0),
    "mea":        (8.41085, 2492.659,   3.456,  10.0,  170.0),
    "mdea":       (7.97354, 2530.000,   0.000,  20.0,  200.0),
    "nitrogen":   (6.49457,  255.680,  -6.600,-210.0, -147.0),
    "oxygen":     (6.69144,  340.024,  -4.144,-218.0, -119.0),
    "methane":    (6.61184,  389.930,  -7.197,-182.0,  -82.0),
    "so2":        (7.28228, 1301.679,  -3.494, -72.7,  157.5),
}

def get_antoine_coefficients(compound: str) -> Optional[tuple]:
    key = compound.lower().replace(" ", "_").replace("-", "_")
    return ANTOINE_COEFFICIENTS.get(key)

def antoine_pressure(T_celsius: float, A: float, B: float, C: float) -> float:
    return 133.322 * (10 ** (A - B / (C + T_celsius)))

def antoine_temperature(P_pa: float, A: float, B: float, C: float) -> float:
    import math
    P_mmhg = P_pa / 133.322
    return B / (A - math.log10(P_mmhg)) - C
""")
print('Done')
