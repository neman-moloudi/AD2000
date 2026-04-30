"""
Conical shell widget — AD-2000 Merkblatt B7.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QPushButton,
)
from PyQt6.QtCore import pyqtSignal

from ui.common import CommonInputs, fmt_error, fmt_warning, fmt_pass_fail
from calculations.cone import calc_cone, verify_cone


class ConeWidget(QWidget):
    result_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        hdr = QLabel("Conical Shell  —  AD-2000 Merkblatt B7")
        hdr.setStyleSheet("color:#4a9eff;font-size:16px;font-weight:bold;")
        root.addWidget(hdr)

        self.common = CommonInputs(show_v=True, show_material=True)
        root.addWidget(self.common)

        grp = QGroupBox("Cone Geometry")
        form = QFormLayout(grp)
        self.alpha_edit = QLineEdit("30.0")
        self.alpha_edit.setToolTip(
            "Half-apex angle α [degrees].  Valid range: 0° < α ≤ 70°.\n"
            "A warning is shown when α > 30° (reinforcement ring may be required)."
        )
        form.addRow("Half-apex angle  &alpha;  [°]:", self.alpha_edit)
        root.addWidget(grp)

        btn = QPushButton("Calculate")
        btn.clicked.connect(self._calculate)
        root.addWidget(btn)
        root.addStretch()

    # ------------------------------------------------------------------
    def _calculate(self):
        try:
            inp = self.common.get_values()
            p, Di   = inp["p"],  inp["Di"]
            K, S, v = inp["K"],  inp["S"], inp["v"]
            c1, c2  = inp["c1"], inp["c2"]
            s_ex    = inp.get("s_ex")
            alpha   = float(self.alpha_edit.text())

            r = verify_cone(p, Di, K, S, v, s_ex, c1, c2, alpha) if s_ex \
                else calc_cone(p, Di, K, S, v, c1, c2, alpha)

            K_S = r["K_S"]
            lines = [
                "<h3 style='color:#4a9eff;margin-bottom:4px'>Conical Shell</h3>",
                "<b>AD-2000 Merkblatt B7</b><br>",
                "<b>Formula:</b> s = p&middot;Di / "
                "(2&middot;cos&alpha;&middot;(K/S&middot;v &minus; p/2)) + c&#8321; + c&#8322;<br>",
                "<hr style='border-color:#2a2f3a'>",
                "<b>Intermediate Values</b><br>",
                f"&nbsp;&nbsp;p = {p:.3f} bar = {r['p_nmm2']:.4f} N/mm²<br>",
                f"&nbsp;&nbsp;&alpha; = {alpha:.2f}°,&nbsp; "
                f"cos&alpha; = {r['cos_alpha']:.6f}<br>",
                f"&nbsp;&nbsp;K/S = {K_S:.3f} N/mm²<br>",
                f"&nbsp;&nbsp;Denominator = 2&middot;cos&alpha;&middot;(K/S&middot;v &minus; p/2) "
                f"= {r['denom']:.6f}<br>",
                f"&nbsp;&nbsp;s_calc = {r['s_calc']:.4f} mm<br>",
                f"&nbsp;&nbsp;c&#8321; = {c1:.2f} mm,&nbsp; c&#8322; = {c2:.2f} mm<br>",
                "<br><b>Required wall thickness:</b><br>",
                f"<span style='color:#f0c040;font-size:18px'>"
                f"<b>s = {r['s_required']:.2f} mm</b></span>",
            ]

            if s_ex and "pass" in r:
                lines.append(fmt_pass_fail(r["pass"], s_ex, r["s_required"], r["p_max"]))
                lines.append(
                    f"<p>&nbsp;&nbsp;Effective s_eff = {r['s_eff']:.2f} mm</p>"
                )

            if r.get("warnings"):
                lines.extend(fmt_warning(w) for w in r["warnings"])

            self.result_ready.emit("".join(lines))

        except Exception as ex:
            self.result_ready.emit(fmt_error(str(ex)))
