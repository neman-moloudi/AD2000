"""
Shared input widget and HTML result-formatting helpers used by all component widgets.
"""
from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QHBoxLayout, QWidget, QCheckBox,
)
from PyQt6.QtCore import Qt
from data.materials import get_material_names, get_K


class CommonInputs(QGroupBox):
    """
    Reusable QGroupBox containing the standard AD-2000 design parameters:
    p, T, Di, c1, c2, optional s_ex, material / K, weld efficiency v, safety factor S.
    """

    def __init__(self, show_v=True, show_material=True, parent=None):
        super().__init__("Design Parameters", parent)
        self.show_v = show_v
        self.show_material = show_material
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        form = QFormLayout(self)
        form.setSpacing(8)
        form.setContentsMargins(10, 12, 10, 10)

        self.p_edit = QLineEdit("10.0")
        form.addRow("Design pressure  p  [bar]:", self.p_edit)

        self.T_edit = QLineEdit("200")
        form.addRow("Design temperature  T  [°C]:", self.T_edit)

        self.Di_edit = QLineEdit("500")
        form.addRow("Inner diameter  Di  [mm]:", self.Di_edit)

        self.c1_edit = QLineEdit("2.0")
        form.addRow("Corrosion allowance  c₁  [mm]:", self.c1_edit)

        self.c2_edit = QLineEdit("0.0")
        form.addRow("Mill tolerance  c₂  [mm]:", self.c2_edit)

        # Optional verification thickness
        sex_row = QWidget()
        sex_layout = QHBoxLayout(sex_row)
        sex_layout.setContentsMargins(0, 0, 0, 0)
        sex_layout.setSpacing(6)
        self.sex_check = QCheckBox("Verify existing")
        self.s_ex_edit = QLineEdit()
        self.s_ex_edit.setPlaceholderText("e.g. 16.0")
        self.s_ex_edit.setEnabled(False)
        self.sex_check.stateChanged.connect(self._toggle_sex)
        self.s_ex_edit.textChanged.connect(self._auto_c2)
        sex_layout.addWidget(self.sex_check)
        sex_layout.addWidget(self.s_ex_edit)
        form.addRow("Nom. thickness  s_ex  [mm]:", sex_row)

        if self.show_material:
            self.mat_combo = QComboBox()
            self.mat_combo.addItems(get_material_names())
            self.mat_combo.addItem("— Custom K —")
            self.mat_combo.currentTextChanged.connect(self._on_material_changed)
            form.addRow("Material:", self.mat_combo)

            self.K_edit = QLineEdit()
            self.K_edit.setPlaceholderText("auto-filled")
            form.addRow("Allow. stress  K  [N/mm²]:", self.K_edit)

            self.T_edit.textChanged.connect(self._on_temp_changed)
            self._on_material_changed(self.mat_combo.currentText())

        if self.show_v:
            self.v_combo = QComboBox()
            self.v_combo.addItems(["1.0", "0.85", "0.7"])
            form.addRow("Weld efficiency  v:", self.v_combo)

        self.S_edit = QLineEdit("1.5")
        form.addRow("Safety factor  S:", self.S_edit)

    # ------------------------------------------------------------------
    def _toggle_sex(self, state):
        self.s_ex_edit.setEnabled(state == Qt.CheckState.Checked.value)

    def _auto_c2(self, text):
        """Auto-set c2 = 12.5 % of s_ex (mill tolerance) when s_ex changes."""
        try:
            self.c2_edit.setText(f"{float(text) * 0.125:.3f}")
        except ValueError:
            pass

    def _on_material_changed(self, name):
        if name == "— Custom K —":
            self.K_edit.setReadOnly(False)
            self.K_edit.setStyleSheet("")
        else:
            try:
                T = float(self.T_edit.text())
            except ValueError:
                T = 20.0
            self.K_edit.setText(str(get_K(name, T)))
            self.K_edit.setReadOnly(True)
            self.K_edit.setStyleSheet("color:#80c080;")

    def _on_temp_changed(self):
        if hasattr(self, "mat_combo") and self.mat_combo.currentText() != "— Custom K —":
            self._on_material_changed(self.mat_combo.currentText())

    # ------------------------------------------------------------------
    def get_values(self) -> dict:
        """
        Parse and validate all inputs. Returns a dict with keys:
          p, T, Di, c1, c2, S  (always present)
          K                    (if show_material)
          v                    (if show_v)
          s_ex                 (only if verification checkbox is checked)
        Raises ValueError with a descriptive message on any bad input.
        """
        def _f(edit, label):
            try:
                return float(edit.text())
            except ValueError:
                raise ValueError(f"Invalid value for {label}: '{edit.text()}'")

        p  = _f(self.p_edit,  "p")
        T  = _f(self.T_edit,  "T")
        Di = _f(self.Di_edit, "Di")
        c1 = _f(self.c1_edit, "c1")
        c2 = _f(self.c2_edit, "c2")
        S  = _f(self.S_edit,  "S")

        if p  <= 0: raise ValueError("Design pressure p must be > 0 bar")
        if Di <= 0: raise ValueError("Inner diameter Di must be > 0 mm")
        if S  <= 0: raise ValueError("Safety factor S must be > 0")
        if c1 < 0:  raise ValueError("Corrosion allowance c1 must be ≥ 0")
        if c2 < 0:  raise ValueError("Mill tolerance c2 must be ≥ 0")

        out = {"p": p, "T": T, "Di": Di, "c1": c1, "c2": c2, "S": S}

        if self.show_material:
            K = _f(self.K_edit, "K")
            if K <= 0: raise ValueError("Allowable stress K must be > 0 N/mm²")
            out["K"] = K

        if self.show_v:
            out["v"] = float(self.v_combo.currentText())

        if self.sex_check.isChecked():
            s_ex = _f(self.s_ex_edit, "s_ex")
            if s_ex <= 0: raise ValueError("Existing thickness s_ex must be > 0 mm")
            out["s_ex"] = s_ex

        return out


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def fmt_error(msg: str) -> str:
    return f"<p style='color:#f44336'><b>⚠ Input Error:</b><br>{msg}</p>"


def fmt_warning(msg: str) -> str:
    return f"<p style='color:#ff9800'>⚠ {msg}</p>"


def fmt_pass_fail(passed: bool, s_ex: float, s_req: float, p_max: float) -> str:
    color  = "#4caf50" if passed else "#f44336"
    symbol = "PASS ✓" if passed else "FAIL ✗"
    op     = "≥"  if passed else "&lt;"
    return (
        f"<p style='margin-top:8px'>"
        f"<span style='font-size:16px;color:{color}'><b>{symbol}</b></span><br>"
        f"<span style='color:{color}'>"
        f"s_ex = {s_ex:.2f} mm {op} s_req = {s_req:.2f} mm</span></p>"
        f"<p>Max allowable pressure: <b>p<sub>max</sub> = {p_max:.3f} bar</b></p>"
    )
