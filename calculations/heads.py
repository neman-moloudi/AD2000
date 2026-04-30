"""
AD-2000 Merkblatt B2 / B3 / B5 — Head calculation functions.
Covers Hemispherical (B2), Ellipsoidal and Torispherical (B3), Flat end caps (B5).

All pressures are in bar externally; internally converted to N/mm² via factor 0.1.
"""
import math


# ---------------------------------------------------------------------------
# Hemispherical head — AD-2000 Merkblatt B2
# ---------------------------------------------------------------------------

def calc_hemispherical(p, Di, K, S, v, c1, c2):
    """
    AD-2000 B2: Required wall thickness for hemispherical head.

    s = (p * Di) / (4 * K/S * v - p) + c1 + c2
    """
    if p <= 0:
        raise ValueError("Design pressure p must be > 0")
    if Di <= 0:
        raise ValueError("Inner diameter Di must be > 0")

    p_nmm2 = p * 0.1
    K_S = K / S
    denom = 4 * K_S * v - p_nmm2

    if denom <= 0:
        raise ValueError(f"Denominator (4·K/S·v − p) = {denom:.4f} ≤ 0.")

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


def verify_hemispherical(p, Di, K, S, v, s_ex, c1, c2):
    """Verify existing hemispherical head; compute p_max."""
    K_S = K / S
    s_eff = s_ex - c1 - c2
    if s_eff <= 0:
        raise ValueError("Effective thickness (s_ex − c1 − c2) must be > 0")

    p_max_nmm2 = (4 * K_S * v * s_eff) / (Di + s_eff)
    p_max_bar = p_max_nmm2 * 10.0

    result = calc_hemispherical(p, Di, K, S, v, c1, c2)
    result.update({"s_ex": s_ex, "s_eff": s_eff, "p_max": p_max_bar,
                   "pass": s_ex >= result["s_required"]})
    return result


# ---------------------------------------------------------------------------
# Ellipsoidal head — AD-2000 Merkblatt B3
# ---------------------------------------------------------------------------

def calc_ellipsoidal(p, Di, K, S, v, c1, c2, beta=1.0):
    """
    AD-2000 B3: Ellipsoidal head (2:1 standard uses beta = 1.0).

    s = (p * Di * beta) / (2 * K/S * v - p * (beta - 0.5)) + c1 + c2

    Knuckle radius minimum check: r_knuckle >= 0.1 * Di
    """
    if p <= 0:
        raise ValueError("Design pressure p must be > 0")
    if Di <= 0:
        raise ValueError("Inner diameter Di must be > 0")

    p_nmm2 = p * 0.1
    K_S = K / S
    denom = 2 * K_S * v - p_nmm2 * (beta - 0.5)

    if denom <= 0:
        raise ValueError(f"Denominator = {denom:.4f} ≤ 0.")

    s_calc = (p_nmm2 * Di * beta) / denom
    s_required = s_calc + c1 + c2
    r_knuckle_min = 0.1 * Di

    return {
        "s_required": s_required,
        "s_calc": s_calc,
        "K_S": K_S,
        "p_nmm2": p_nmm2,
        "denom": denom,
        "beta": beta,
        "r_knuckle_min": r_knuckle_min,
        "c1": c1,
        "c2": c2,
        "warnings": [],
    }


def verify_ellipsoidal(p, Di, K, S, v, s_ex, c1, c2, beta=1.0):
    """Verify existing ellipsoidal head; compute p_max."""
    K_S = K / S
    s_eff = s_ex - c1 - c2
    if s_eff <= 0:
        raise ValueError("Effective thickness (s_ex − c1 − c2) must be > 0")

    # Rearranged: p_max = (2*K_S*v*s_eff) / (Di*beta + s_eff*(beta-0.5))  [N/mm2]
    p_max_nmm2 = (2 * K_S * v * s_eff) / (Di * beta + s_eff * (beta - 0.5))
    p_max_bar = p_max_nmm2 * 10.0

    result = calc_ellipsoidal(p, Di, K, S, v, c1, c2, beta)
    result.update({"s_ex": s_ex, "s_eff": s_eff, "p_max": p_max_bar,
                   "pass": s_ex >= result["s_required"]})
    return result


# ---------------------------------------------------------------------------
# Torispherical head — AD-2000 Merkblatt B3
# ---------------------------------------------------------------------------

def _beta_torispherical(Di, r):
    """
    AD-2000 B3: Shape factor for torispherical head.
    beta = 0.25 * (3 + sqrt(Di / r))
    """
    if r <= 0:
        raise ValueError("Knuckle radius r must be > 0")
    if Di <= 0:
        raise ValueError("Inner diameter Di must be > 0")
    return 0.25 * (3.0 + math.sqrt(Di / r))


def calc_torispherical(p, Di, K, S, v, c1, c2, head_type="klopper", R=None, r=None):
    """
    AD-2000 B3: Torispherical head under internal pressure.

    Klöpper:   R = Di,       r = 0.10 * Di
    Korbbogen: R = 0.8*Di,  r = 0.154 * Di
    Custom:    user-defined R and r

    beta = 0.25 * (3 + sqrt(Di / r))
    s = (p * Di * beta) / (2 * K/S * v) + c1 + c2
    """
    if p <= 0:
        raise ValueError("Design pressure p must be > 0")
    if Di <= 0:
        raise ValueError("Inner diameter Di must be > 0")

    if head_type == "klopper":
        R_used = Di
        r_used = 0.10 * Di
    elif head_type == "korbbogen":
        R_used = 0.8 * Di
        r_used = 0.154 * Di
    elif head_type == "custom":
        if R is None or r is None:
            raise ValueError("Custom head type requires both R and r values.")
        R_used = float(R)
        r_used = float(r)
    else:
        raise ValueError(f"Unknown head_type: '{head_type}'")

    beta = _beta_torispherical(Di, r_used)
    p_nmm2 = p * 0.1
    K_S = K / S
    denom = 2 * K_S * v

    s_calc = (p_nmm2 * Di * beta) / denom
    s_required = s_calc + c1 + c2

    warnings = []
    if r_used < 0.06 * Di:
        warnings.append(
            f"Knuckle radius r = {r_used:.1f} mm < 0.06·Di: risk of knuckle failure."
        )

    return {
        "s_required": s_required,
        "s_calc": s_calc,
        "K_S": K_S,
        "p_nmm2": p_nmm2,
        "beta": beta,
        "R_used": R_used,
        "r_used": r_used,
        "head_type": head_type,
        "c1": c1,
        "c2": c2,
        "warnings": warnings,
    }


def verify_torispherical(p, Di, K, S, v, s_ex, c1, c2, head_type="klopper", R=None, r=None):
    """Verify existing torispherical head; compute p_max."""
    K_S = K / S
    s_eff = s_ex - c1 - c2
    if s_eff <= 0:
        raise ValueError("Effective thickness (s_ex − c1 − c2) must be > 0")

    result = calc_torispherical(p, Di, K, S, v, c1, c2, head_type, R, r)
    beta = result["beta"]

    # Rearranged: p_max = s_eff * 2 * K_S * v / (Di * beta)  [N/mm2]
    p_max_nmm2 = (s_eff * 2 * K_S * v) / (Di * beta)
    p_max_bar = p_max_nmm2 * 10.0

    result.update({"s_ex": s_ex, "s_eff": s_eff, "p_max": p_max_bar,
                   "pass": s_ex >= result["s_required"]})
    return result


# ---------------------------------------------------------------------------
# Flat end cap — AD-2000 Merkblatt B5
# ---------------------------------------------------------------------------

def calc_flat_head(p, Di, K, S, c1, c2, edge_type="clamped"):
    """
    AD-2000 B5: Flat end cap / flat head under internal pressure.

    s = Di * C * sqrt(p / (K/S)) + c1 + c2

    Edge conditions:
      C = 0.36  clamped / welded (fixed edge)
      C = 0.41  simply supported
      C = 0.45  bolted flat cover (simplified)
    """
    if p <= 0:
        raise ValueError("Design pressure p must be > 0")
    if Di <= 0:
        raise ValueError("Inner diameter Di must be > 0")

    C_map = {"clamped": 0.36, "simply_supported": 0.41, "bolted": 0.45}
    if edge_type not in C_map:
        raise ValueError(f"edge_type must be one of {list(C_map.keys())}")

    C = C_map[edge_type]
    p_nmm2 = p * 0.1
    K_S = K / S

    s_calc = Di * C * math.sqrt(p_nmm2 / K_S)
    s_required = s_calc + c1 + c2

    return {
        "s_required": s_required,
        "s_calc": s_calc,
        "C": C,
        "K_S": K_S,
        "p_nmm2": p_nmm2,
        "edge_type": edge_type,
        "c1": c1,
        "c2": c2,
    }


def verify_flat_head(p, Di, K, S, s_ex, c1, c2, edge_type="clamped"):
    """Verify existing flat head; compute p_max."""
    K_S = K / S
    s_eff = s_ex - c1 - c2
    if s_eff <= 0:
        raise ValueError("Effective thickness (s_ex − c1 − c2) must be > 0")

    C_map = {"clamped": 0.36, "simply_supported": 0.41, "bolted": 0.45}
    C = C_map[edge_type]

    # Rearranged: p_max = K_S * (s_eff / (Di * C))^2  [N/mm2]
    p_max_nmm2 = K_S * (s_eff / (Di * C)) ** 2
    p_max_bar = p_max_nmm2 * 10.0

    result = calc_flat_head(p, Di, K, S, c1, c2, edge_type)
    result.update({"s_ex": s_ex, "s_eff": s_eff, "p_max": p_max_bar,
                   "pass": s_ex >= result["s_required"]})
    return result
