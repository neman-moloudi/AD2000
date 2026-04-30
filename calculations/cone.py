"""
AD-2000 Merkblatt B7 — Conical shell / transition piece calculations.

All pressures accepted in bar, converted internally to N/mm² (1 bar = 0.1 N/mm²).
"""
import math


def calc_cone(p, Di, K, S, v, c1, c2, alpha_deg):
    """
    AD-2000 B7: Required wall thickness for conical shell under internal pressure.

    s = (p * Di) / (2 * cos(alpha) * (K/S * v - p/2)) + c1 + c2

    Parameters
    ----------
    alpha_deg : half-apex angle [degrees]. Must be 0 < alpha <= 70.
                Warn if alpha > 30° (reinforcement ring likely needed per B7).
    """
    if p <= 0:
        raise ValueError("Design pressure p must be > 0")
    if Di <= 0:
        raise ValueError("Inner diameter Di must be > 0")
    if not (0 < alpha_deg <= 70):
        raise ValueError("Half-apex angle alpha must satisfy 0° < α ≤ 70°.")

    p_nmm2 = p * 0.1
    alpha_rad = math.radians(alpha_deg)
    K_S = K / S
    cos_a = math.cos(alpha_rad)

    denom = 2 * cos_a * (K_S * v - p_nmm2 / 2)

    if denom <= 0:
        raise ValueError(
            f"Denominator = {denom:.6f} ≤ 0. "
            "Check pressure vs allowable stress (K/S·v must exceed p/2)."
        )

    s_calc = (p_nmm2 * Di) / denom
    s_required = s_calc + c1 + c2

    warnings = []
    if alpha_deg > 30:
        warnings.append(
            f"α = {alpha_deg}° > 30°: a reinforcement ring at the cone-cylinder "
            "junction is likely required per AD-2000 B7."
        )

    return {
        "s_required": s_required,
        "s_calc": s_calc,
        "alpha_deg": alpha_deg,
        "alpha_rad": alpha_rad,
        "cos_alpha": cos_a,
        "K_S": K_S,
        "p_nmm2": p_nmm2,
        "denom": denom,
        "c1": c1,
        "c2": c2,
        "warnings": warnings,
    }


def verify_cone(p, Di, K, S, v, s_ex, c1, c2, alpha_deg):
    """
    Verify existing conical shell wall thickness against design pressure.
    Computes max allowable pressure p_max by inverting the B7 formula.

    Rearranged:
      p_max = 2*cos(alpha)*K_S*v*s_eff / (Di/10 + cos(alpha)*s_eff/10) * 10
    Compact form:
      p_max [bar] = 20 * cos(alpha) * K_S * v * s_eff / (Di + cos(alpha) * s_eff)
    """
    if not (0 < alpha_deg <= 70):
        raise ValueError("Half-apex angle alpha must satisfy 0° < α ≤ 70°.")

    alpha_rad = math.radians(alpha_deg)
    K_S = K / S
    cos_a = math.cos(alpha_rad)
    s_eff = s_ex - c1 - c2

    if s_eff <= 0:
        raise ValueError("Effective thickness (s_ex − c1 − c2) must be > 0")

    # Algebraic inversion of the cone formula (pressures cancel units via factor 10)
    p_max_bar = (20.0 * cos_a * K_S * v * s_eff) / (Di + cos_a * s_eff)

    result = calc_cone(p, Di, K, S, v, c1, c2, alpha_deg)
    result.update({"s_ex": s_ex, "s_eff": s_eff, "p_max": p_max_bar,
                   "pass": s_ex >= result["s_required"]})
    return result
