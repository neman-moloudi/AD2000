"""
AD-2000 / EN material library with allowable stress K [N/mm²] at standard temperatures.
Linear interpolation is used for intermediate temperatures.
"""

# Format: { material_name: { "standard": str, "temps": [T...], "K": [K...] } }
MATERIALS = {
    "P265GH": {
        "standard": "EN 10028-2",
        "temps": [20, 100, 200, 300],
        "K":     [177, 160, 147, 131],
    },
    "P295GH": {
        "standard": "EN 10028-2",
        "temps": [20, 100, 200, 300],
        "K":     [197, 180, 165, 150],
    },
    "16Mo3": {
        "standard": "EN 10028-2",
        "temps": [20, 100, 200, 300],
        "K":     [197, 180, 170, 160],
    },
    "X5CrNi18-10": {
        "standard": "EN 10028-7",
        "temps": [20, 100, 200, 300],
        "K":     [160, 138, 120, 108],
    },
    "X6CrNiMoTi316": {
        "standard": "EN 10028-7",
        "temps": [20, 100, 200, 300],
        "K":     [160, 138, 120, 108],
    },
}


def get_material_names():
    """Return list of available material names."""
    return list(MATERIALS.keys())


def get_K(material_name, temperature):
    """
    Return allowable stress K [N/mm²] for given material and temperature [°C].
    Uses linear interpolation between table values.
    Clamps to min/max temperature range.
    """
    if material_name not in MATERIALS:
        raise ValueError(f"Unknown material: {material_name}")

    data = MATERIALS[material_name]
    temps = data["temps"]
    K_vals = data["K"]

    if temperature <= temps[0]:
        return float(K_vals[0])
    if temperature >= temps[-1]:
        return float(K_vals[-1])

    for i in range(len(temps) - 1):
        if temps[i] <= temperature <= temps[i + 1]:
            t0, t1 = temps[i], temps[i + 1]
            K0, K1 = K_vals[i], K_vals[i + 1]
            K = K0 + (K1 - K0) * (temperature - t0) / (t1 - t0)
            return round(K, 2)

    return float(K_vals[-1])


def get_material_info(material_name):
    """Return full material record."""
    if material_name not in MATERIALS:
        raise ValueError(f"Unknown material: {material_name}")
    return MATERIALS[material_name]
