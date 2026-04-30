"""
Head widgets — AD-2000 Merkblatt B2 / B3 / B5.
A single HeadsWidget class is parameterised by head_type and instantiated
once per head type in MainWindow.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
)
from PyQt6.QtCore import pyqtSignal

from ui.common import CommonInputs, fmt_error, fmt_warning, fmt_pass_fail
from calculations.heads import (
    calc_hemispherical,  verify_hemispherical,
    calc_ellipsoidal,    verify_ellipsoidal,
    calc_torispherical,  verify_torispherical,
    calc_flat_head,      verify_flat_head,
)

_TITLES = {
    "hemispherical": "Hemispherical Head  —  AD-2000 Merkblatt B2",
    "ellipsoidal":   "Ellipsoidal Head (2:1)  —  AD-2000 Merkblatt B3",
    "torispherical": "Torispherical Head  —  AD-2000 Merkblatt B3",
    "flat":          "Flat End Cap  —  AD-2000 Merkblatt B5",
}
_FORMULAS = {
    "hemispherical": "s = p&middot;Di / (4&middot;K/S&middot;v &minus; p) + c&#8321; + c&#8322;",
    "ellipsoidal":   "s = p&middot;Di&middot;&beta; / (2&middot;K/S&middot;v &minus; p&middot;(&beta;&minus;0.5)) + c&#8321; + c&#8322;",
    "torispherical": "&beta; = 0.25&middot;(3 + &radic;(Di/r));&nbsp; s = p&middot;Di&middot;&beta; / (2&middot;K/S&middot;v) + c&#8321; + c&#8322;",
    "flat":          "s = Di&middot;C&middot;&radic;(p / (K/S)) + c&#8321; + c&#8322;",
}


class HeadsWidget(QWidget):
    result_ready = pyqtSignal(str)

    def __init__(self, head_type: str):
        super().__init__()
        self.head_type = head_type
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        hdr = QLabel(_TITLES.get(self.head_type, "Head"))
        hdr.setStyleSheet("color:#4a9eff;font-size:16px;font-weight:bold;")
        root.addWidget(hdr)

        # Flat head formula has no explicit v term; pass show_v=False
        self.common = CommonInputs(show_v=(self.head_type != "flat"))
        root.addWidget(self.common)

        if self.head_type == "ellipsoidal":
            self._add_ellipsoidal_extras(root)
        elif self.head_type == "torispherical":
            self._add_torispherical_extras(root)
        elif self.head_type == "flat":
            self._add_flat_extras(root)

        btn = QPushButton("Calculate")
        btn.clicked.connect(self._calculate)
        root.addWidget(btn)
        root.addStretch()

    # ------------------------------------------------------------------
    def _add_ellipsoidal_extras(self, layout):
        grp = QGroupBox("Ellipsoidal Shape Factor")
        form = QFormLayout(grp)
        self.beta_edit = QLineEdit("1.0")
        self.beta_edit.setToolTip("1.0 for the standard 2:1 ellipsoid")
        form.addRow("Shape factor  &beta;:", self.beta_edit)
        layout.addWidget(grp)

    def _add_torispherical_extras(self, layout):
        grp = QGroupBox("Torispherical Geometry")
        form = QFormLayout(grp)

        self.tori_combo = QComboBox()
        self.tori_combo.addItems([
            "Klöpper  (R = Di,  r = 0.1·Di)",
            "Korbbogen  (R = 0.8·Di,  r = 0.154·Di)",
            "Custom",
        ])
        self.tori_combo.currentIndexChanged.connect(self._toggle_tori_custom)
        form.addRow("Head geometry:", self.tori_combo)

        self.R_edit = QLineEdit()
        self.R_edit.setPlaceholderText("Crown radius R [mm]")
        self.R_edit.setEnabled(False)
        form.addRow("Crown radius  R  [mm]:", self.R_edit)

        self.r_edit = QLineEdit()
        self.r_edit.setPlaceholderText("Knuckle radius r [mm]")
        self.r_edit.setEnabled(False)
        form.addRow("Knuckle radius  r  [mm]:", self.r_edit)

        layout.addWidget(grp)

    def _toggle_tori_custom(self, idx):
        custom = (idx == 2)
        self.R_edit.setEnabled(custom)
        self.r_edit.setEnabled(custom)

    def _add_flat_extras(self, layout):
        grp = QGroupBox("Edge / Attachment Condition")
        form = QFormLayout(grp)
        self.edge_combo = QComboBox()
        self.edge_combo.addItems([
            "Clamped / welded  (C = 0.36)",
            "Simply supported  (C = 0.41)",
            "Bolted cover  (C = 0.45)",
        ])
        form.addRow("Edge condition:", self.edge_combo)
        layout.addWidget(grp)

    # ------------------------------------------------------------------
    def _calculate(self):
        try:
            inp = self.common.get_values()
            p, Di   = inp["p"],  inp["Di"]
            K, S    = inp["K"],  inp["S"]
            v       = inp.get("v", 1.0)
            c1, c2  = inp["c1"], inp["c2"]
            s_ex    = inp.get("s_ex")

            dispatch = {
                "hemispherical": self._hemi,
                "ellipsoidal":   self._ellipsoidal,
                "torispherical": self._torispherical,
                "flat":          self._flat,
            }
            html = dispatch[self.head_type](p, Di, K, S, v, c1, c2, s_ex)
            self.result_ready.emit(html)
        except Exception as ex:
            self.result_ready.emit(fmt_error(str(ex)))

    # ------------------------------------------------------------------
    def _hemi(self, p, Di, K, S, v, c1, c2, s_ex):
        r = verify_hemispherical(p, Di, K, S, v, s_ex, c1, c2) if s_ex \
            else calc_hemispherical(p, Di, K, S, v, c1, c2)
        extra = f"Denominator = 4&middot;K/S&middot;v &minus; p = {r['denom']:.5f} N/mm²"
        return self._render(r, p, s_ex, "Hemispherical Head", "B2", extra)

    def _ellipsoidal(self, p, Di, K, S, v, c1, c2, s_ex):
        beta = float(self.beta_edit.text())
        if beta <= 0:
            raise ValueError("Shape factor β must be > 0")
        r = verify_ellipsoidal(p, Di, K, S, v, s_ex, c1, c2, beta) if s_ex \
            else calc_ellipsoidal(p, Di, K, S, v, c1, c2, beta)
        extra = (
            f"Shape factor &beta; = {r['beta']:.4f}<br>"
            f"&nbsp;&nbsp;Denominator = {r['denom']:.5f} N/mm²<br>"
            f"&nbsp;&nbsp;Min. knuckle radius r ≥ 0.1&middot;Di = {r['r_knuckle_min']:.1f} mm"
        )
        html = self._render(r, p, s_ex, "Ellipsoidal Head (2:1)", "B3", extra)
        if r.get("warnings"):
            html += "".join(fmt_warning(w) for w in r["warnings"])
        return html

    def _torispherical(self, p, Di, K, S, v, c1, c2, s_ex):
        idx = self.tori_combo.currentIndex()
        ht  = ["klopper", "korbbogen", "custom"][idx]
        R   = float(self.R_edit.text()) if (ht == "custom" and self.R_edit.text()) else None
        r_v = float(self.r_edit.text()) if (ht == "custom" and self.r_edit.text()) else None
        r   = verify_torispherical(p, Di, K, S, v, s_ex, c1, c2, ht, R, r_v) if s_ex \
              else calc_torispherical(p, Di, K, S, v, c1, c2, ht, R, r_v)
        extra = (
            f"Crown radius R = {r['R_used']:.1f} mm,&nbsp; "
            f"Knuckle radius r = {r['r_used']:.1f} mm<br>"
            f"&nbsp;&nbsp;Shape factor &beta; = {r['beta']:.5f}"
        )
        html = self._render(r, p, s_ex, "Torispherical Head", "B3", extra)
        if r.get("warnings"):
            html += "".join(fmt_warning(w) for w in r["warnings"])
        return html

    def _flat(self, p, Di, K, S, v, c1, c2, s_ex):
        edge_map = {0: "clamped", 1: "simply_supported", 2: "bolted"}
        edge = edge_map[self.edge_combo.currentIndex()]
        r = verify_flat_head(p, Di, K, S, s_ex, c1, c2, edge) if s_ex \
            else calc_flat_head(p, Di, K, S, c1, c2, edge)
        return self._render(r, p, s_ex, "Flat End Cap", "B5",
                            extra=f"Edge factor C = {r['C']:.2f}")

    # ------------------------------------------------------------------
    def _render(self, r, p, s_ex, title, ref, extra="") -> str:
        K_S     = r["K_S"]
        formula = _FORMULAS.get(self.head_type, "")
        lines = [
            f"<h3 style='color:#4a9eff;margin-bottom:4px'>{title}</h3>",
            f"<b>AD-2000 Merkblatt {ref}</b><br>",
            f"<b>Formula:</b> {formula}<br>",
            "<hr style='border-color:#2a2f3a'>",
            "<b>Intermediate Values</b><br>",
            f"&nbsp;&nbsp;p = {p:.3f} bar = {r['p_nmm2']:.4f} N/mm²<br>",
            f"&nbsp;&nbsp;K/S = {K_S:.3f} N/mm²<br>",
        ]
        if extra:
            lines.append(f"&nbsp;&nbsp;{extra}<br>")
        lines += [
            f"&nbsp;&nbsp;s_calc = {r['s_calc']:.4f} mm<br>",
            f"&nbsp;&nbsp;c&#8321; = {r['c1']:.2f} mm,&nbsp; c&#8322; = {r['c2']:.2f} mm<br>",
            "<br><b>Required wall thickness:</b><br>",
            f"<span style='color:#f0c040;font-size:18px'><b>s = {r['s_required']:.2f} mm</b></span>",
        ]
        if s_ex and "pass" in r:
            lines.append(fmt_pass_fail(r["pass"], s_ex, r["s_required"], r["p_max"]))
            lines.append(f"<p>&nbsp;&nbsp;Effective s_eff = {r['s_eff']:.2f} mm</p>")
        return "".join(lines)
