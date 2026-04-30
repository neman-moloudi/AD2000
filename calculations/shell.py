"""
AD-2000 Merkblatt B1 / B6 — Cylindrical shell calculations.
Internal pressure design (B1) and external pressure buckling check (B6).
"""
import math


def calc_shell_internal(p, Di, K, S, v, c1, c2):
    """
    AD-2000 B1: Required wall thickness for cylindrical shell under internal pressure.

    Formula: s = (p * Di) / (2 * K/S * v - p) + c1 + c2

    Parameters
    ----------
    p   : design pressure [bar] -- converted to N/mm² internally (1 bar = 0.1 N/mm²)
    Di  : inner diameter [mm]
    K   : allowable stress at design temp [N/mm²]
    S   : safety factor (typically 1.5)
    v   : weld joint efficiency (0.7 / 0.85 / 1.0)
    c1  : corrosion allowance [mm]
    c2  : mill tolerance [mm]
    """
    if p <= 0:
        raise ValueError("Design pressure p must be > 0")
    if Di <= 0:
        raise ValueError("Inner diameter Di must be > 0")

    # Convert bar -> N/mm²  (1 bar = 0.1 N/mm²)
    p_nmm2 = p * 0.1

    K_S = K / S  # allowable stress
    denom = 2 * K_S * v - p_nmm2

    if denom <= 0:
        raise ValueError(
            f"Denominator (2·K/S·v − p) = {denom:.4f} ≤ 0: "
            "pressure exceeds allowable. Increase wall thickness or material strength."
        )

    s_calc = (p_nmm2 * Di) / denom
    s_required = s_calc + c1 + c2

    return {
        "s_required": s_required,
        "s_calc": s_calc,
        "K_S": K_S,
        "p_nmm2": p_nmm2,
        "denom": denom,
        "c1": c1,
        "c2": c2,
    }


def verify_shell_internal(p, Di, K, S, v, s_ex, c1, c2):
    """
    AD-2000 B1: Verify existing wall thickness and compute max allowable pressure.

    p_max = (2 * K/S * v * s_eff) / (Di + s_eff)   [N/mm², then convert to bar]
    where s_eff = s_ex - c1 - c2
    """
    K_S = K / S
    s_eff = s_ex - c1 - c2

    if s_eff <= 0:
        raise ValueError("Effective thickness (s_ex − c1 − c2) must be > 0")

    p_max_nmm2 = (2 * K_S * v * s_eff) / (Di + s_eff)
    p_max_bar = p_max_nmm2 * 10.0  # convert N/mm² -> bar

    result = calc_shell_internal(p, Di, K, S, v, c1, c2)
    result["s_ex"] = s_ex
    result["s_eff"] = s_eff
    result["p_max"] = p_max_bar
    result["pass"] = s_ex >= result["s_required"]
    return result


def calc_shell_external(p, Di, s_ex, E, L, S_ext=3.0, nu=0.3):
    """
    AD-2000 B6 (simplified buckling): Critical pressure for cylindrical shell
    under external pressure.

    p_k = 2.42 * E * (s/Da)^2.5 / ((1 - nu^2)^0.75 * (L/Da - 0.45 * sqrt(s/Da)))

    Required: p_k / S_ext >= p  (S_ext = 3.0 per AD-2000 B6)

    Parameters
    ----------
    p     : external design pressure [bar]
    Di    : inner diameter [mm]
    s_ex  : nominal wall thickness [mm]
    E     : Young's modulus [N/mm²]
    L     : unsupported length [mm]
    S_ext : buckling safety factor (default 3.0)
    nu    : Poisson's ratio (default 0.3 for steel)
    """
    p_nmm2 = p * 0.1
    Da = Di + 2 * s_ex

    ratio_s_Da = s_ex / Da
    ratio_L_Da = L / Da

    factor_a = 2.42 * E * (ratio_s_Da ** 2.5)
    factor_b = ((1 - nu ** 2) ** 0.75) * (ratio_L_Da - 0.45 * math.sqrt(ratio_s_Da))

    if factor_b <= 0:
        raise ValueError(
            "Buckling formula denominator ≤ 0: L/Da ratio is too small. "
            "Increase unsupported length or wall thickness."
        )

    p_k_nmm2 = factor_a / factor_b
    p_k_bar = p_k_nmm2 * 10.0
    p_allow_bar = p_k_bar / S_ext

    return {
        "Da": Da,
        "p_k": p_k_bar,
        "p_allow": p_allow_bar,
        "S_ext": S_ext,
        "ratio_s_Da": ratio_s_Da,
        "ratio_L_Da": ratio_L_Da,
        "pass": p_allow_bar >= p,
    }
