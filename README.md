# AD-2000 Pressure Vessel Calculator

A desktop engineering calculator for pressure vessel design according to the
**AD-2000 Regelwerk** (Arbeitsgemeinschaft Druckbehälter) German pressure vessel code.

Built with **Python 3** and **PyQt6**. Runs on Ubuntu 24.04 and any platform
supporting Python 3.11+.

---

## Features

| Component | AD-2000 Merkblatt | Modes |
|---|---|---|
| Cylindrical shell — internal pressure | B1 | Design + Verification |
| Cylindrical shell — external pressure (buckling) | B6 | Buckling check |
| Hemispherical head | B2 | Design + Verification |
| Ellipsoidal head (2:1, custom β) | B3 | Design + Verification |
| Torispherical head (Klöpper / Korbbogen / Custom) | B3 | Design + Verification |
| Flat end cap (clamped / simply-supported / bolted) | B5 | Design + Verification |
| Conical shell / transition piece | B7 | Design + Verification |

**Material library** (EN 10028-2/7) with linear temperature interpolation:
P265GH, P295GH, 16Mo3, X5CrNi18-10, X6CrNiMoTi316 — or enter a custom K value.

**Verification mode**: tick *Verify existing* and enter a nominal wall thickness
to get a PASS/FAIL verdict and maximum allowable pressure pₘₐˣ.

---

## Installation (Ubuntu 24.04)

```bash
# 1. Clone the repository
git clone https://github.com/neman-moloudi/ad2000.git
cd ad2000

# 2. Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the application
python main.py
```

> **Note:** PyQt6 requires Qt 6 libraries. On Ubuntu 24.04 these are bundled
> inside the `PyQt6` pip package — no separate system packages are needed.

---

## Project Structure

```
ad2000/
├── main.py                  # Entry point
├── requirements.txt
├── calculations/
│   ├── shell.py             # B1 / B6  cylindrical shell
│   ├── heads.py             # B2 / B3 / B5  heads and flat caps
│   └── cone.py              # B7  conical shell
├── data/
│   └── materials.py         # Material table + interpolation
└── ui/
    ├── main_window.py       # MainWindow (layout + stylesheet)
    ├── common.py            # CommonInputs widget + HTML helpers
    ├── shell_widget.py      # CylindricalShellWidget
    ├── head_widget.py       # HeadsWidget (all four head types)
    └── cone_widget.py       # ConeWidget
```

---

## Design Parameters (common to all components)

| Field | Symbol | Unit | Notes |
|---|---|---|---|
| Design pressure | p | bar | Internal or external |
| Design temperature | T | °C | Used for K interpolation |
| Inner diameter | Di | mm | |
| Corrosion allowance | c₁ | mm | |
| Mill tolerance | c₂ | mm | Auto-filled as 12.5 % of s_ex |
| Nominal thickness | s_ex | mm | Optional — enables verification |
| Allowable stress | K | N/mm² | From material table or custom |
| Weld efficiency | v | — | 1.0 / 0.85 / 0.7 |
| Safety factor | S | — | Default 1.5 |

---

## Unit Convention

- Pressures: **bar** (input/output); converted to N/mm² internally (1 bar = 0.1 N/mm²)
- Lengths / thicknesses: **mm**
- Stresses: **N/mm²**

---

## License

MIT — see [LICENSE](LICENSE).
