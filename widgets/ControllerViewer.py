"""
ControllerViewer — Renders the custom B&W SNES SVG with pixel-perfect
highlights using transformForElement() for accurate positioning.

Face buttons: SNES colours (X=blue, A=green, B=red, Y=yellow)
D-pad:        black directional triangles
Start/Select: black pill overlays
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QPainterPath, QPolygonF
)
from PySide6.QtSvg import QSvgRenderer
import os


class ControllerViewer(QWidget):

    # Face buttons → SVG element IDs (Matches NPG SNES layout)
    _FACE_BUTTONS = {
        "Y": "circle6",   # left
        "X": "circle7",   # top
        "A": "circle8",   # right
        "B": "circle9",   # bottom
    }

    # Shoulder buttons
    _SHOULDER_BUTTONS = {
        "R": "path1",
        "L": "path2",
    }

    # Bright, pleasant SNES colours for face button highlights
    _BUTTON_COLORS = {
        "X": QColor("#5b9eff"),   # top    — soft vivid blue
        "Y": QColor("#50d890"),   # left   — fresh green
        "A": QColor("#ff6b6b"),   # right  — warm coral red
        "B": QColor("#ffd55a"),   # bottom — sunny yellow
    }

    _DPAD_CROSS_ID = "path4"
    _DPAD_CENTER_ID = "circle5"

    _START_ID = "path26"
    _SELECT_ID = "path9"

    _PILL_ANGLE_DEG = -math.degrees(math.atan2(3.89828, 5.3155))

    _ALL_KEYS = ["A", "B", "X", "Y", "Dpad Up", "Dpad Down",
                 "Dpad Left", "Dpad Right", "L", "R", "Start"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(540, 250)

        from gamepad import resource_path
        svg_path = resource_path("icons/NPG SNES with Logo.svg")
        self._renderer = QSvgRenderer(svg_path)
        self.button_states: dict[str, float] = {k: 0.0 for k in self._ALL_KEYS}

        # Pre-compute mapped element rects (viewBox coords)
        self._vb_rects: dict[str, QRectF] = {}
        all_ids = list(self._FACE_BUTTONS.values()) + list(self._SHOULDER_BUTTONS.values()) + [
            self._DPAD_CROSS_ID, self._DPAD_CENTER_ID,
            self._START_ID, self._SELECT_ID, "path3"
        ]
        for eid in all_ids:
            if self._renderer.elementExists(eid):
                b = self._renderer.boundsOnElement(eid)
                t = self._renderer.transformForElement(eid)
                self._vb_rects[eid] = t.mapRect(b)

    # Public API 

    def update_button(self, name: str, value):
        if name in self.button_states:
            self.button_states[name] = float(value)
            self.update()

    def update_stick(self, name, x, y):
        pass

    def reset_all(self):
        for k in self.button_states:
            self.button_states[k] = 0.0
        self.update()

    def _pressed(self, name: str) -> bool:
        return self.button_states.get(name, 0.0) > 0.5

    # Coordinate mapping 

    def _vb_to_widget(self, rect: QRectF) -> QRectF:
        vw = self._renderer.viewBoxF().width()
        vh = self._renderer.viewBoxF().height()
        r = self._render_rect
        sx, sy = r.width() / vw, r.height() / vh
        return QRectF(
            r.x() + rect.x() * sx,
            r.y() + rect.y() * sy,
            rect.width() * sx,
            rect.height() * sy,
        )

    def _widget_rect(self, elem_id: str) -> QRectF | None:
        vb = self._vb_rects.get(elem_id)
        if vb is None:
            return None
        return self._vb_to_widget(vb)

    # Paint 

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, QColor("#0a0a0a"))

        vw = self._renderer.viewBoxF().width()
        vh = self._renderer.viewBoxF().height()
        aspect = vw / vh
        pad = 20
        avail_w, avail_h = W - 2 * pad, H - 2 * pad
        if avail_w / avail_h > aspect:
            rh = avail_h; rw = rh * aspect
        else:
            rw = avail_w; rh = rw / aspect
        self._render_rect = QRectF((W - rw) / 2, (H - rh) / 2, rw, rh)

        self._renderer.render(p, self._render_rect)

        self._draw_shoulder_highlights(p)
        self._draw_face_highlights(p)
        self._draw_dpad_highlights(p)
        self._draw_start_highlight(p)

        p.end()

    # Shoulder buttons: rendered accurately to silhouette 

    def _draw_shoulder_highlights(self, p: QPainter):
        from PySide6.QtGui import QImage
        
        active_names = [name for name in self._SHOULDER_BUTTONS if self._pressed(name)]
        if not active_names:
            return

        size = self._render_rect.size().toSize()
        if size.width() <= 0 or size.height() <= 0:
            return
            
        # Draw onto exactly the geometry of the main render rect
        img = QImage(size * 2, QImage.Format_ARGB32_Premultiplied)
        img.setDevicePixelRatio(2.0)
        img.fill(Qt.transparent)
        
        tmp_p = QPainter(img)
        tmp_p.setRenderHint(QPainter.Antialiasing)
        tmp_p.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 1. Render precisely the pressed shoulder button paths
        for name in active_names:
            eid = self._SHOULDER_BUTTONS[name]
            wr = self._widget_rect(eid)
            if wr is not None:
                # Target bounding rect translated to local img coordinates coordinates (0,0)
                target_rect = wr.translated(-self._render_rect.topLeft())
                self._renderer.render(tmp_p, eid, target_rect)
        
        # 2. Fill the drawn shape with the native SVG Dark Grey (#808080)
        tmp_p.setCompositionMode(QPainter.CompositionMode_SourceIn)
        tmp_p.fillRect(img.rect(), QColor("#808080"))
        
        # 3. Cut out the main controller body (path3) to reveal ONLY the perfect outer curve
        tmp_p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
        body_wr = self._widget_rect("path3")
        if body_wr is not None:
            mask_rect = body_wr.translated(-self._render_rect.topLeft())
            self._renderer.render(tmp_p, "path3", mask_rect)
            
        tmp_p.end()
        
        # Draw the neatly masked perfectly curved highlight flawlessly atop the main view!
        p.drawImage(self._render_rect.topLeft(), img)

    # Face buttons: SNES colour fills 

    def _draw_face_highlights(self, p: QPainter):
        for name, eid in self._FACE_BUTTONS.items():
            if not self._pressed(name):
                continue
            wr = self._widget_rect(eid)
            if wr is None:
                continue

            color = self._BUTTON_COLORS[name]
            cx, cy = wr.center().x(), wr.center().y()
            rx, ry = wr.width() / 2, wr.height() / 2

            # Coloured fill perfectly bordering the black SVG outline
            fill = QColor(color)
            fill.setAlpha(255)
            p.setPen(Qt.NoPen)
            p.setBrush(fill)
            
            # Draw slightly inset to fit perfectly inside the SVG's black stroke
            p.drawEllipse(QPointF(cx, cy), rx - 0.8, ry - 0.8)

    # D-pad: directional triangles 

    def _draw_dpad_highlights(self, p: QPainter):
        cross = self._widget_rect(self._DPAD_CROSS_ID)
        if cross is None:
            return

        cross_size = cross.width()
        arm_w = cross_size * 0.39

        cx = cross.center().x()
        cy = cross.center().y()

        # Engraved 3D triangle sizing
        tri_w = arm_w * 0.45   # base width of triangle
        tri_h = arm_w * 0.40   # height (tip to base)
        offset = arm_w * 0.65  # distance from center to base

        dirs = [("Dpad Up", 0, -1), ("Dpad Down", 0, 1),
                ("Dpad Left", -1, 0), ("Dpad Right", 1, 0)]

        # Pen settings to heavily round the triangle corners
        pen_width = arm_w * 0.15

        for name, dx, dy in dirs:
            if not self._pressed(name):
                continue

            # Build triangle pointing in the direction
            if dy < 0:  # Up
                tip = QPointF(cx, cy - offset - tri_h)
                bl  = QPointF(cx - tri_w / 2, cy - offset)
                br  = QPointF(cx + tri_w / 2, cy - offset)
            elif dy > 0:  # Down
                tip = QPointF(cx, cy + offset + tri_h)
                bl  = QPointF(cx - tri_w / 2, cy + offset)
                br  = QPointF(cx + tri_w / 2, cy + offset)
            elif dx < 0:  # Left
                tip = QPointF(cx - offset - tri_h, cy)
                bl  = QPointF(cx - offset, cy - tri_w / 2)
                br  = QPointF(cx - offset, cy + tri_w / 2)
            else:  # Right
                tip = QPointF(cx + offset + tri_h, cy)
                bl  = QPointF(cx + offset, cy - tri_w / 2)
                br  = QPointF(cx + offset, cy + tri_w / 2)

            tri_path = QPainterPath()
            tri_path.moveTo(tip)
            tri_path.lineTo(bl)
            tri_path.lineTo(br)
            tri_path.closeSubpath()
            
            p.save()
            # 1. Subtle white highlight shifted down-right for 3D embossed/engraved look
            shift = pen_width * 0.35
            p.translate(shift, shift)
            p.setPen(QPen(QColor(255, 255, 255, 80), pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(QColor(255, 255, 255, 80))
            p.drawPath(tri_path)
            p.restore()

            # 2. Main solid black rounded triangle
            p.setPen(QPen(QColor("#000000"), pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(QColor("#000000"))
            p.drawPath(tri_path)

    # Start button: black angled pill 

    def _draw_start_highlight(self, p: QPainter):
        if not self._pressed("Start"):
            return
        wr = self._widget_rect(self._START_ID)
        if wr is None:
            return

        cx, cy = wr.center().x(), wr.center().y()

        vw = self._renderer.viewBoxF().width()
        scale = self._render_rect.width() / vw
        # TUNING: adjust these two values to resize the pill highlight 
        pill_half_len = 6.2 * scale
        pill_half_w = 2.85 * scale

        p.save()
        p.translate(cx, cy)
        p.rotate(self._PILL_ANGLE_DEG)

        pill_rect = QRectF(-pill_half_len, -pill_half_w,
                           pill_half_len * 2, pill_half_w * 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#000000"))
        p.drawRoundedRect(pill_rect, pill_half_w, pill_half_w)

        p.restore()
