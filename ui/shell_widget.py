"""
Cylindrical shell widget — AD-2000 Merkblatt B1 (internal) / B6 (external buckling).
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget,
)
from PyQt6.QtCore import pyqtSignal

from ui.common import CommonInputs, fmt_error, fmt_pass_fail
from calculations.shell import (
    calc_shell_internal, verify_shell_internal, calc_shell_external,
)


class CylindricalShellWidget(QWidget):
    result_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        hdr = QLabel("Cylindrical Shell  —  AD-2000 Merkblatt B1 / B6")
        hdr.setStyleSheet("color:#4a9eff;font-size:16px;font-weight:bold;")
        root.addWidget(hdr)

        tabs = QTabWidget()
        root.addWidget(tabs)
        root.addStretch()

        # --- Internal pressure tab (B1) ---
        int_tab = QWidget()
        int_layout = QVBoxLayout(int_tab)
        int_layout.setContentsMargins(8, 8, 8, 8)
        int_layout.setSpacing(10)
        self.int_inputs = CommonInputs(show_v=True, show_material=True)
        int_layout.addWidget(self.int_inputs)
        btn_int = QPushButton("Calculate")
        btn_int.clicked.connect(self._calc_internal)
        int_layout.addWidget(btn_int)
        int_layout.addStretch()
        tabs.addTab(int_tab, "Internal Pressure  (B1)")

        # --- External pressure / buckling tab (B6) ---
        ext_tab = QWidget()
        ext_layout = QVBoxLayout(ext_tab)
        ext_layout.setContentsMargins(8, 8, 8, 8)
        ext_layout.setSpacing(10)
        self.ext_inputs = CommonInputs(show_v=False, show_material=False)
        ext_layout.addWidget(self.ext_inputs)

        ext_grp = QGroupBox("External Pressure / Buckling Parameters  (B6)")
        ext_form = QFormLayout(ext_grp)
        self.E_edit      = QLineEdit("200000")
        self.L_edit      = QLineEdit("1000")
        self.s_ex_e_edit = QLineEdit("10.0")
        self.nu_edit     = QLineEdit("0.3")
        self.S_ext_edit  = QLineEdit("3.0")
        ext_form.addRow("Young's modulus  E  [N/mm²]:", self.E_edit)
        ext_form.addRow("Unsupported length  L  [mm]:",  self.L_edit)
        ext_form.addRow("Wall thickness  s_ex  [mm]:",   self.s_ex_e_edit)
        ext_form.addRow("Poisson's ratio  ν:",           self.nu_edit)
        ext_form.addRow("Buckling safety factor  S_ext:", self.S_ext_edit)
        ext_layout.addWidget(ext_grp)

        btn_ext = QPushButton("Calculate Buckling Check")
        btn_ext.clicked.connect(self._calc_external)
        ext_layout.addWidget(btn_ext)
        ext_layout.addStretch()
        tabs.addTab(ext_tab, "External Pressure  (B6)")

    # ------------------------------------------------------------------
    def _calc_internal(self):
        try:
            inp = self.int_inputs.get_values()
            p, Di        = inp["p"],  inp["Di"]
            K, S, v      = inp["K"],  inp["S"], inp["v"]
            c1, c2       = inp["c1"], inp["c2"]
            s_ex         = inp.get("s_ex")

            if s_ex:
                r = verify_shell_internal(p, Di, K, S, v, s_ex, c1, c2)
            else:
                r = calc_shell_internal(p, Di, K, S, v, c1, c2)

            self.result_ready.emit(self._fmt_internal(r, p, v, c1, c2, s_ex))
        except Exception as ex:
            self.result_ready.emit(fmt_error(str(ex)))

    def _fmt_internal(self, r, p, v, c1, c2, s_ex):
        K_S = r["K_S"]
        lines = [
            "<h3 style='color:#4a9eff;margin-bottom:4px'>Cylindrical Shell</h3>",
            "<b>AD-2000 Merkblatt B1</b><br>",
            "<b>Formula:</b> s = p&middot;Di / (2&middot;K/S&middot;v &minus; p) + c&#8321; + c&#8322;<br>",
            "<hr style='border-color:#2a2f3a'>",
            "<b>Intermediate Values</b><br>",
            f"&nbsp;&nbsp;p = {p:.3f} bar = {r['p_nmm2']:.4f} N/mm²<br>",
            f"&nbsp;&nbsp;K/S = {K_S:.3f} N/mm²<br>",
            f"&nbsp;&nbsp;2&middot;K/S&middot;v = {2*K_S*v:.4f} N/mm²<br>",
            f"&nbsp;&nbsp;Denominator = {r['denom']:.5f} N/mm²<br>",
            f"&nbsp;&nbsp;s_calc = {r['s_calc']:.4f} mm<br>",
            f"&nbsp;&nbsp;c&#8321; = {c1:.2f} mm,&nbsp; c&#8322; = {c2:.2f} mm<br>",
            "<br><b>Required wall thickness:</b><br>",
            f"<span style='color:#f0c040;font-size:18px'><b>s = {r['s_required']:.2f} mm</b></span>",
        ]
        if s_ex:
            lines.append(fmt_pass_fail(r["pass"], s_ex, r["s_required"], r["p_max"]))
            lines.append(f"<p>&nbsp;&nbsp;Effective s_eff = {r['s_eff']:.2f} mm</p>")
        return "".join(lines)

    # ------------------------------------------------------------------
    def _calc_external(self):
        try:
            inp  = self.ext_inputs.get_values()
            p, Di = inp["p"], inp["Di"]
            E     = float(self.E_edit.text())
            L     = float(self.L_edit.text())
            s_ex  = float(self.s_ex_e_edit.text())
            nu    = float(self.nu_edit.text())
            S_ext = float(self.S_ext_edit.text())

            if s_ex <= 0: raise ValueError("Wall thickness s_ex must be > 0")
            if E    <= 0: raise ValueError("Young's modulus E must be > 0")
            if L    <= 0: raise ValueError("Unsupported length L must be > 0")

            r = calc_shell_external(p, Di, s_ex, E, L, S_ext, nu)
            self.result_ready.emit(self._fmt_external(r, p, s_ex, S_ext))
        except Exception as ex:
            self.result_ready.emit(fmt_error(str(ex)))

    def _fmt_external(self, r, p, s_ex, S_ext):
        passed = r["pass"]
        color  = "#4caf50" if passed else "#f44336"
        status = "PASS ✓"  if passed else "FAIL ✗"
        op     = "≥"       if passed else "&lt;"
        return "".join([
            "<h3 style='color:#4a9eff;margin-bottom:4px'>Cylindrical Shell — Buckling</h3>",
            "<b>AD-2000 Merkblatt B6</b><br>",
            "<b>Formula:</b><br>",
            "&nbsp;p<sub>k</sub> = 2.42&middot;E&middot;(s/D<sub>a</sub>)<sup>2.5</sup> / "
            "[(1&minus;ν²)<sup>0.75</sup>&middot;(L/D<sub>a</sub> &minus; 0.45&middot;&radic;(s/D<sub>a</sub>))]<br>",
            "<hr style='border-color:#2a2f3a'>",
            "<b>Intermediate Values</b><br>",
            f"&nbsp;&nbsp;D<sub>a</sub> = {r['Da']:.2f} mm<br>",
            f"&nbsp;&nbsp;s/D<sub>a</sub> = {r['ratio_s_Da']:.6f}<br>",
            f"&nbsp;&nbsp;L/D<sub>a</sub> = {r['ratio_L_Da']:.5f}<br>",
            f"&nbsp;&nbsp;p<sub>k</sub> = {r['p_k']:.4f} bar<br>",
            f"&nbsp;&nbsp;S<sub>ext</sub> = {S_ext:.1f}<br>",
            f"&nbsp;&nbsp;p<sub>allow</sub> = {r['p_allow']:.4f} bar<br>",
            "<br>",
            f"Design pressure p = {p:.3f} bar<br>",
            f"<p><span style='font-size:16px;color:{color}'><b>{status}</b></span><br>",
            f"<span style='color:{color}'>p<sub>allow</sub> = {r['p_allow']:.4f} bar "
            f"{op} p = {p:.3f} bar</span></p>",
        ])
