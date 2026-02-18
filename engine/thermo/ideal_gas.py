"""
Ideal Gas Law: PV = nRT

Utility functions for quick ideal gas calculations.
All functions use SI units (Pa, m³, K, mol).
"""

# Universal gas constant [J/(mol·K)]
R = 8.314


def ideal_gas_pressure(n: float, T_kelvin: float, V_m3: float) -> float:
    """
    Calculate pressure from P = nRT/V.

    Parameters
    ----------
    n : float
        Amount of substance [mol].
    T_kelvin : float
        Temperature [K].
    V_m3 : float
        Volume [m³].

    Returns
    -------
    float
        Pressure [Pa].
    """
    if V_m3 <= 0:
        raise ValueError(f"Volume must be positive, got {V_m3} m³")
    if T_kelvin <= 0:
        raise ValueError(f"Temperature must be positive, got {T_kelvin} K")
    if n < 0:
        raise ValueError(f"Moles must be non-negative, got {n}")

    return n * R * T_kelvin / V_m3


def ideal_gas_volume(n: float, T_kelvin: float, P_pa: float) -> float:
    """
    Calculate volume from V = nRT/P.

    Returns
    -------
    float
        Volume [m³].
    """
    if P_pa <= 0:
        raise ValueError(f"Pressure must be positive, got {P_pa} Pa")
    if T_kelvin <= 0:
        raise ValueError(f"Temperature must be positive, got {T_kelvin} K")
    if n < 0:
        raise ValueError(f"Moles must be non-negative, got {n}")

    return n * R * T_kelvin / P_pa


def ideal_gas_temperature(n: float, P_pa: float, V_m3: float) -> float:
    """
    Calculate temperature from T = PV/(nR).

    Returns
    -------
    float
        Temperature [K].
    """
    if P_pa <= 0:
        raise ValueError(f"Pressure must be positive, got {P_pa} Pa")
    if V_m3 <= 0:
        raise ValueError(f"Volume must be positive, got {V_m3} m³")
    if n <= 0:
        raise ValueError(f"Moles must be positive, got {n}")

    return P_pa * V_m3 / (n * R)


def ideal_gas_moles(P_pa: float, V_m3: float, T_kelvin: float) -> float:
    """
    Calculate moles from n = PV/(RT).

    Returns
    -------
    float
        Amount of substance [mol].
    """
    if P_pa <= 0:
        raise ValueError(f"Pressure must be positive, got {P_pa} Pa")
    if V_m3 <= 0:
        raise ValueError(f"Volume must be positive, got {V_m3} m³")
    if T_kelvin <= 0:
        raise ValueError(f"Temperature must be positive, got {T_kelvin} K")

    return P_pa * V_m3 / (R * T_kelvin)


def ideal_gas_density(M_kg_mol: float, P_pa: float, T_kelvin: float) -> float:
    """
    Calculate ideal gas density: ρ = PM/(RT).

    Parameters
    ----------
    M_kg_mol : float
        Molar mass [kg/mol].
    P_pa : float
        Pressure [Pa].
    T_kelvin : float
        Temperature [K].

    Returns
    -------
    float
        Density [kg/m³].
    """
    if P_pa <= 0:
        raise ValueError(f"Pressure must be positive, got {P_pa} Pa")
    if T_kelvin <= 0:
        raise ValueError(f"Temperature must be positive, got {T_kelvin} K")
    if M_kg_mol <= 0:
        raise ValueError(f"Molar mass must be positive, got {M_kg_mol} kg/mol")

    return P_pa * M_kg_mol / (R * T_kelvin)
