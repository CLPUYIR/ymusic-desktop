"""
Vector Icon Generator for YMusic Desktop.
Draws crisp, high-DPI vector icons using QPainter and QPainterPath.
Ensures zero external asset dependencies and seamless cross-platform consistency.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF


class IconFactory:
    """Creates crisp QIcon instances on-the-fly with customizable color and size."""

    PRIMARY_COLOR = QColor("#FF0033")  # YouTube Music Red
    TEXT_COLOR = QColor("#FFFFFF")
    MUTED_COLOR = QColor("#AAAAAA")
    ACCENT_COLOR = QColor("#3EA6FF")
    SUCCESS_COLOR = QColor("#2BA640")

    @classmethod
    def create_icon(cls, name: str, color: QColor = TEXT_COLOR, size: int = 32) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        w = float(size)
        h = float(size)
        pad = w * 0.15

        if name == "play":
            path = QPainterPath()
            path.moveTo(pad * 1.3, pad)
            path.lineTo(w - pad * 0.9, h / 2.0)
            path.lineTo(pad * 1.3, h - pad)
            path.closeSubpath()
            painter.setBrush(QBrush(color))
            painter.drawPath(path)

        elif name == "pause":
            painter.setBrush(QBrush(color))
            bar_w = w * 0.18
            painter.drawRoundedRect(QRectF(pad * 1.2, pad, bar_w, h - 2 * pad), 2, 2)
            painter.drawRoundedRect(QRectF(w - pad * 1.2 - bar_w, pad, bar_w, h - 2 * pad), 2, 2)

        elif name == "next":
            path = QPainterPath()
            path.moveTo(pad, pad)
            path.lineTo(w * 0.55, h / 2.0)
            path.lineTo(pad, h - pad)
            path.closeSubpath()
            painter.setBrush(QBrush(color))
            painter.drawPath(path)
            painter.drawRoundedRect(QRectF(w * 0.65, pad, w * 0.12, h - 2 * pad), 1, 1)

        elif name == "prev":
            path = QPainterPath()
            path.moveTo(w - pad, pad)
            path.lineTo(w * 0.45, h / 2.0)
            path.lineTo(w - pad, h - pad)
            path.closeSubpath()
            painter.setBrush(QBrush(color))
            painter.drawPath(path)
            painter.drawRoundedRect(QRectF(pad * 0.9, pad, w * 0.12, h - 2 * pad), 1, 1)

        elif name == "download":
            # Downward arrow + tray
            painter.drawLine(QPointF(w / 2.0, pad), QPointF(w / 2.0, h - pad * 1.5))
            # Arrow head
            arrow = QPainterPath()
            arrow.moveTo(pad * 1.2, h / 2.0)
            arrow.lineTo(w / 2.0, h - pad * 1.5)
            arrow.lineTo(w - pad * 1.2, h / 2.0)
            painter.drawPath(arrow)
            # Bottom bar
            painter.drawLine(QPointF(pad, h - pad * 0.8), QPointF(w - pad, h - pad * 0.8))

        elif name == "music":
            # Music note icon
            path = QPainterPath()
            path.addEllipse(QRectF(pad, h - pad * 1.8, w * 0.28, h * 0.22))
            path.addEllipse(QRectF(w - pad * 2.0, h - pad * 2.2, w * 0.28, h * 0.22))
            painter.setBrush(QBrush(color))
            painter.drawPath(path)
            painter.drawLine(QPointF(pad + w * 0.25, h - pad * 1.2), QPointF(pad + w * 0.25, pad * 1.1))
            painter.drawLine(QPointF(w - pad * 0.8, h - pad * 1.6), QPointF(w - pad * 0.8, pad * 0.7))
            painter.drawLine(QPointF(pad + w * 0.25, pad * 1.1), QPointF(w - pad * 0.8, pad * 0.7))

        elif name == "youtube":
            # Play button inside rounded rectangle
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(QRectF(pad * 0.6, pad * 0.9, w - pad * 1.2, h - pad * 1.8), 6, 6)
            tri = QPainterPath()
            tri.moveTo(w * 0.42, h * 0.35)
            tri.lineTo(w * 0.65, h * 0.5)
            tri.lineTo(w * 0.42, h * 0.65)
            tri.closeSubpath()
            painter.setBrush(QBrush(QColor("#000000")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(tri)

        elif name == "back":
            path = QPainterPath()
            path.moveTo(w * 0.65, pad)
            path.lineTo(w * 0.3, h / 2.0)
            path.lineTo(w * 0.65, h - pad)
            painter.drawPath(path)

        elif name == "forward":
            path = QPainterPath()
            path.moveTo(w * 0.35, pad)
            path.lineTo(w * 0.7, h / 2.0)
            path.lineTo(w * 0.35, h - pad)
            painter.drawPath(path)

        elif name == "refresh":
            rect = QRectF(pad, pad, w - 2 * pad, h - 2 * pad)
            painter.drawArc(rect, 45 * 16, 270 * 16)
            # Arrow head
            arrow = QPainterPath()
            arrow.moveTo(w / 2.0, pad * 0.5)
            arrow.lineTo(w / 2.0 + pad * 0.8, pad * 1.2)
            arrow.lineTo(w / 2.0, pad * 1.9)
            painter.drawPath(arrow)

        elif name == "settings":
            # Gear icon
            painter.drawEllipse(QPointF(w / 2.0, h / 2.0), w * 0.22, h * 0.22)
            painter.drawEllipse(QPointF(w / 2.0, h / 2.0), w * 0.38, h * 0.38)

        elif name == "shield":
            # Ad-block shield icon
            path = QPainterPath()
            path.moveTo(w / 2.0, pad * 0.8)
            path.lineTo(w - pad, pad * 1.2)
            path.quadTo(w - pad, h - pad * 1.2, w / 2.0, h - pad * 0.5)
            path.quadTo(pad, h - pad * 1.2, pad, pad * 1.2)
            path.closeSubpath()
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 60)))
            painter.drawPath(path)

        elif name == "folder":
            path = QPainterPath()
            path.moveTo(pad, pad * 1.3)
            path.lineTo(w * 0.45, pad * 1.3)
            path.lineTo(w * 0.55, pad * 1.8)
            path.lineTo(w - pad, pad * 1.8)
            path.lineTo(w - pad, h - pad)
            path.lineTo(pad, h - pad)
            path.closeSubpath()
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 80)))
            painter.drawPath(path)

        elif name == "close":
            painter.drawLine(QPointF(pad * 1.2, pad * 1.2), QPointF(w - pad * 1.2, h - pad * 1.2))
            painter.drawLine(QPointF(w - pad * 1.2, pad * 1.2), QPointF(pad * 1.2, h - pad * 1.2))

        elif name in ("plus", "add"):
            # Clean '+' icon
            painter.drawLine(QPointF(w / 2.0, pad * 1.1), QPointF(w / 2.0, h - pad * 1.1))
            painter.drawLine(QPointF(pad * 1.1, h / 2.0), QPointF(w - pad * 1.1, h / 2.0))

        elif name == "app_logo":
            # Circular badge with play triangle in YouTube Red
            painter.setBrush(QBrush(cls.PRIMARY_COLOR))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(pad * 0.5, pad * 0.5, w - pad, h - pad))

            tri = QPainterPath()
            tri.moveTo(w * 0.4, h * 0.32)
            tri.lineTo(w * 0.7, h * 0.5)
            tri.lineTo(w * 0.4, h * 0.68)
            tri.closeSubpath()
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawPath(tri)

        else:
            # Fallback circle
            painter.drawEllipse(QRectF(pad, pad, w - 2 * pad, h - 2 * pad))

        painter.end()
        return QIcon(pixmap)
