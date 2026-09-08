"""
UI Styling & Theme for Fire and Smoke Detection Application.
Dark Industrial / Cyber-Safety Theme.
"""

DARK_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #0E1116;
    color: #E6EDF3;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

/* Group Boxes / Cards */
QGroupBox {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: 600;
    font-size: 12px;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    background-color: #21262D;
    border: 1px solid #30363D;
    border-radius: 4px;
    color: #58A6FF;
}

/* Push Buttons */
QPushButton {
    background-color: #21262D;
    color: #C9D1D9;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #30363D;
    border-color: #8B949E;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #161B22;
}

QPushButton:disabled {
    background-color: #111418;
    color: #484F58;
    border-color: #21262D;
}

/* Primary Action Buttons */
QPushButton#primaryBtn {
    background-color: #238636;
    color: #FFFFFF;
    border: 1px solid #2EA043;
    font-weight: 600;
}

QPushButton#primaryBtn:hover {
    background-color: #2EA043;
    border-color: #3FB950;
}

/* Danger Buttons */
QPushButton#dangerBtn {
    background-color: #DA3633;
    color: #FFFFFF;
    border: 1px solid #F85149;
    font-weight: 600;
}

QPushButton#dangerBtn:hover {
    background-color: #F85149;
}

/* Playback Control Buttons */
QPushButton#controlBtn {
    background-color: #21262D;
    border: 1px solid #363C46;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QPushButton#controlBtn:hover {
    background-color: #2F3642;
    border-color: #58A6FF;
    color: #58A6FF;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #21262D;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #1F6FEB;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #58A6FF;
    border: 1px solid #79C0FF;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #79C0FF;
    transform: scale(1.1);
}

/* Timeline Slider Specific */
QSlider#timelineSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1F6FEB, stop:1 #FF7B72);
}

/* List / Table Views */
QListWidget, QTableWidget {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 6px;
    color: #C9D1D9;
    gridline-color: #21262D;
    selection-background-color: #1F6FEB;
    selection-color: #FFFFFF;
}

QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #161B22;
    border-radius: 4px;
    margin: 2px 4px;
}

QListWidget::item:hover {
    background-color: #161B22;
    color: #58A6FF;
}

QListWidget::item:selected {
    background-color: #1F6FEB;
    color: #FFFFFF;
    font-weight: 600;
}

/* Table Headers */
QHeaderView::section {
    background-color: #161B22;
    color: #8B949E;
    padding: 6px;
    border: none;
    border-right: 1px solid #21262D;
    border-bottom: 1px solid #30363D;
    font-weight: 600;
    font-size: 11px;
}

/* Checkboxes */
QCheckBox {
    color: #C9D1D9;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #30363D;
    border-radius: 4px;
    background-color: #0D1117;
}

QCheckBox::indicator:checked {
    background-color: #238636;
    border-color: #3FB950;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0E1116;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #30363D;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #8B949E;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #161B22;
    border-top: 1px solid #30363D;
    color: #8B949E;
    font-size: 12px;
}

/* Combo Box */
QComboBox {
    background-color: #21262D;
    color: #C9D1D9;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 4px 10px;
    min-width: 60px;
}

QComboBox:hover {
    border-color: #58A6FF;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #161B22;
    color: #C9D1D9;
    selection-background-color: #1F6FEB;
    border: 1px solid #30363D;
}
"""
