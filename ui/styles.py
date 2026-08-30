"""
Modern Dark Theme Stylesheets for YMusic Desktop.
Designed to seamlessly match YouTube Music's sleek aesthetic.
"""

DARK_THEME_QSS = """
/* Global Window & Widget Style */
QWidget {
    background-color: #0d0d0d;
    color: #f1f1f1;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #070707;
}

/* ToolBar & Navigation Header */
QToolBar {
    background-color: #121212;
    border-bottom: 1px solid #242424;
    padding: 6px 12px;
    spacing: 8px;
}

QToolButton {
    background-color: transparent;
    color: #e0e0e0;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #262626;
    color: #ffffff;
    border: 1px solid #383838;
}

QToolButton:pressed {
    background-color: #333333;
}

QToolButton:checked {
    background-color: #ff0033;
    color: #ffffff;
    border: 1px solid #ff2244;
}

/* Push Buttons */
QPushButton {
    background-color: #212121;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2f2f2f;
    border: 1px solid #4a4a4a;
}

QPushButton:pressed {
    background-color: #1a1a1a;
}

QPushButton.primary {
    background-color: #ff0033;
    border: 1px solid #ff2255;
    color: #ffffff;
}

QPushButton.primary:hover {
    background-color: #e6002e;
    border: 1px solid #ff3b65;
}

QPushButton.primary:pressed {
    background-color: #b80024;
}

QPushButton.secondary {
    background-color: #272727;
    border: 1px solid #3d3d3d;
}

/* URL / Search Input */
QLineEdit {
    background-color: #181818;
    color: #ffffff;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    padding: 6px 12px;
    selection-background-color: #ff0033;
}

QLineEdit:focus {
    border: 1px solid #3ea6ff;
    background-color: #1f1f1f;
}

/* Status Bar & Mini Player Bar */
QStatusBar {
    background-color: #121212;
    color: #aaaaaa;
    border-top: 1px solid #222222;
    padding: 4px 8px;
}

/* Progress Bars */
QProgressBar {
    background-color: #1c1c1c;
    border: 1px solid #2b2b2b;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    font-weight: bold;
    height: 16px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #ff0033, stop:1 #ff4b4b);
    border-radius: 4px;
}

/* Sliders (Volume / Seek) */
QSlider::groove:horizontal {
    height: 6px;
    background: #2b2b2b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #ff0033;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #ff4d6d;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #262626;
    background-color: #111111;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #181818;
    color: #aaaaaa;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #242424;
    color: #ffffff;
    font-weight: bold;
    border-bottom: 2px solid #ff0033;
}

QTabBar::tab:hover {
    background-color: #1e1e1e;
    color: #f1f1f1;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0f0f0f;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2a2a2a;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #444444;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Menus & Context Menus */
QMenu {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 7px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2b2b2b;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #333333;
    margin: 4px 6px;
}

/* Combo Box */
QComboBox {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 100px;
}

QComboBox:hover {
    border: 1px solid #4a4a4a;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #333333;
    selection-background-color: #2b2b2b;
    selection-color: #ffffff;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #444444;
    background-color: #181818;
}

QCheckBox::indicator:checked {
    background-color: #ff0033;
    border: 1px solid #ff2255;
}

/* Dialogs & Cards */
QDialog {
    background-color: #121212;
    border-radius: 8px;
}

QGroupBox {
    border: 1px solid #292929;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: bold;
    color: #e0e0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: #aaaaaa;
}
"""
