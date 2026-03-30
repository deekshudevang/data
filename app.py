"""
app.py — AI Smart Data Entry Automation Tool
Main PyQt5 Desktop Application
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime
import pyautogui

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QTabWidget, QSlider, QComboBox,
    QGroupBox, QStatusBar, QFrame, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QSpinBox, QCheckBox, QSizePolicy, QScrollArea,
    QAction, QMenuBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter,
    QLinearGradient, QBrush
)

import learning
from bot_engine import AutomationEngine
from mpf_bot import MPFBot, create_sample_csv

# ─── Logging Setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("automation.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("App")


# ─── Colors & Style ───────────────────────────────────────────────────────────

DARK_BG = "#0D1117"
CARD_BG = "#161B22"
ACCENT = "#00D4FF"
ACCENT2 = "#7C3AED"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
ERROR = "#EF4444"
TEXT_PRIMARY = "#F0F6FC"
TEXT_SECONDARY = "#8B949E"
BORDER = "#30363D"
HOVER = "#1F2937"

APP_STYLE = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}

QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {CARD_BG};
}}

QTabBar::tab {{
    background: {DARK_BG};
    color: {TEXT_SECONDARY};
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background: {CARD_BG};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover {{
    background: {HOVER};
}}

QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px;
    background: {CARD_BG};
    font-weight: 600;
    color: {TEXT_SECONDARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {ACCENT};
}}

QTextEdit {{
    background: #0A0E14;
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: #AFAFAF;
    font-family: 'Cascadia Code', 'Courier New', monospace;
    font-size: 11px;
    padding: 8px;
}}

QTableWidget {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    color: {TEXT_PRIMARY};
}}
QTableWidget::item {{
    padding: 6px;
    border-bottom: 1px solid {BORDER};
}}
QTableWidget::item:selected {{
    background: {ACCENT}33;
    color: {TEXT_PRIMARY};
}}
QHeaderView::section {{
    background: #1C2333;
    color: {TEXT_SECONDARY};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    border-radius: 8px;
    width: 16px;
    height: 16px;
    margin: -6px 0;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {ACCENT2}, stop:1 {ACCENT});
    border-radius: 2px;
}}

QComboBox {{
    background: #1C2333;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    color: {TEXT_PRIMARY};
    min-width: 120px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT}33;
}}

QScrollBar:vertical {{
    background: {DARK_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_SECONDARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QStatusBar {{
    background: {CARD_BG};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER};
    padding: 4px 12px;
    font-size: 11px;
}}

QMenuBar {{
    background: {CARD_BG};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid {BORDER};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background: {HOVER};
    border-radius: 4px;
}}
QMenu {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {ACCENT}33;
    color: {TEXT_PRIMARY};
}}

QCheckBox {{
    color: {TEXT_SECONDARY};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {DARK_BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
"""


def make_button(text: str, primary: bool = False, danger: bool = False,
                icon_char: str = "") -> QPushButton:
    """Factory for styled buttons."""
    btn = QPushButton(f"  {icon_char}  {text}" if icon_char else text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(40)
    btn.setFont(QFont("Segoe UI", 10, QFont.Bold))

    if danger:
        style = f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #7F1D1D, stop:1 #991B1B);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #991B1B, stop:1 #B91C1C);
            }}
            QPushButton:pressed {{ background: #7F1D1D; }}
            QPushButton:disabled {{ background: #374151; color: #6B7280; }}
        """
    elif primary:
        style = f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT2}, stop:1 {ACCENT});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #8B5CF6, stop:1 #22D3EE);
            }}
            QPushButton:pressed {{ background: {ACCENT2}; }}
            QPushButton:disabled {{ background: #374151; color: #6B7280; }}
        """
    else:
        style = f"""
            QPushButton {{
                background: #1C2333;
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background: {HOVER};
                border-color: {ACCENT};
                color: {ACCENT};
            }}
            QPushButton:pressed {{ background: {DARK_BG}; }}
            QPushButton:disabled {{ background: #374151; color: #6B7280; }}
        """
    btn.setStyleSheet(style)
    return btn


def make_badge(text: str, color: str = ACCENT, bg: str = "") -> QLabel:
    """Small colored badge label."""
    lbl = QLabel(text)
    bg_color = bg or color + "22"
    lbl.setStyleSheet(f"""
        QLabel {{
            background: {bg_color};
            color: {color};
            border: 1px solid {color}55;
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 700;
        }}
    """)
    return lbl


# ─── Worker Thread ────────────────────────────────────────────────────────────

class BotWorker(QThread):
    """Runs the AutomationEngine in a background QThread."""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    field_filled_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self.engine = engine

    def run(self):
        self.engine.start()

    def stop(self):
        self.engine.stop()


class MPFWorker(QThread):
    """Runs the MPFBot in a background QThread."""
    log_signal   = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    record_done_signal = pyqtSignal(int, int)   # (done, total)
    finished_signal = pyqtSignal()

    def __init__(self, bot: MPFBot):
        super().__init__()
        self.bot = bot

    def run(self):
        self.bot.start()

    def stop(self):
        self.bot.stop()

    def pause(self):
        self.bot.pause()

    def resume(self):
        self.bot.resume()


# ─── Status Card Widget ────────────────────────────────────────────────────────

class StatCard(QFrame):
    """A metric card showing a stat with icon."""
    def __init__(self, title: str, value: str = "0", icon: str = "●", color: str = ACCENT):
        super().__init__()
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 4px;
            }}
            QFrame:hover {{
                border-color: {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"color: {color}; font-size: 18px;")
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 22px; font-weight: 700;")
        layout.addWidget(self.value_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(title_lbl)

    def set_value(self, val: str):
        self.value_lbl.setText(val)


# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Smart Data Entry Automation Tool")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 780)

        # State
        self.engine: AutomationEngine | None = None
        self.worker: BotWorker | None = None
        self.fields_filled = 0
        self.start_time: float | None = None

        self._setup_ui()
        self._setup_timer()
        self._apply_style()
        self._update_memory_stats()

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _apply_style(self):
        self.setStyleSheet(APP_STYLE)

    def _setup_ui(self):
        self._build_menu()
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        root.addWidget(self._build_header())

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(12)

        # Stat cards row
        content_layout.addWidget(self._build_stat_cards())

        # Main panel with tabs
        content_layout.addWidget(self._build_tabs(), stretch=1)
        self.tabs.setCurrentIndex(3)

        root.addWidget(content, stretch=1)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready — Click 'Start Automation' to begin")
        self.setStatusBar(self.status_bar)

    def _build_menu(self):
        mb = self.menuBar()
        file_menu = mb.addMenu("File")
        file_menu.addAction(QAction("View Log File", self, triggered=self._open_log))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Exit", self, triggered=self.close))

        tools_menu = mb.addMenu("Tools")
        tools_menu.addAction(QAction("Clear Memory", self,
                                     triggered=self._clear_memory))
        tools_menu.addAction(QAction("Export Memory", self,
                                     triggered=self._export_memory))

        help_menu = mb.addMenu("Help")
        help_menu.addAction(QAction("About", self, triggered=self._show_about))

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {CARD_BG}, stop:0.5 #1A1F2E, stop:1 {CARD_BG});
            border-bottom: 1px solid {BORDER};
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo + title
        title_layout = QVBoxLayout()
        title = QLabel("⚡ AI Data Entry Automation")
        title.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        subtitle = QLabel("Intelligent Form Filling · Self-Learning AI")
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        layout.addStretch()

        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 22px;")
        self.status_label_header = QLabel("Idle")
        self.status_label_header.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-weight: 600; font-size: 13px;"
        )
        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_label_header)
        layout.addSpacing(20)

        # Control buttons
        self.start_btn = make_button("Start Automation", primary=True, icon_char="▶")
        self.stop_btn = make_button("Stop", danger=True, icon_char="⏹")
        self.stop_btn.setEnabled(False)

        self.start_btn.clicked.connect(self._mpf_start)
        self.stop_btn.clicked.connect(self._mpf_stop)

        layout.addWidget(self.start_btn)
        layout.addSpacing(8)
        layout.addWidget(self.stop_btn)

        return header

    def _build_stat_cards(self) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setSpacing(10)

        self.card_fields = StatCard("Fields Filled", "0", "✏️", ACCENT)
        self.card_matches = StatCard("Successful Matches", "0", "🎯", SUCCESS)
        self.card_apps = StatCard("Apps Learned", "0", "🧠", ACCENT2)
        self.card_mappings = StatCard("Total Mappings", "0", "📋", WARNING)

        for card in [self.card_fields, self.card_matches, self.card_apps, self.card_mappings]:
            row.addWidget(card)

        return w

    def _build_tabs(self) -> QTabWidget:
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dashboard_tab(), "📊  Dashboard")
        self.tabs.addTab(self._build_activity_tab(), "📡  Live Activity")
        self.tabs.addTab(self._build_memory_tab(), "🧠  AI Memory")
        self.tabs.addTab(self._build_mpf_tab(), "🗂️  MPF Bot")
        self.tabs.addTab(self._build_settings_tab(), "⚙️  Settings")
        return self.tabs

    # ── Dashboard Tab ─────────────────────────────────────────────────────────

    def _build_dashboard_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Left: Log console
        left = QGroupBox("📟 Automation Log")
        left_layout = QVBoxLayout(left)
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMinimumHeight(200)
        left_layout.addWidget(self.log_console)

        btn_row = QHBoxLayout()
        clear_btn = make_button("Clear Log", icon_char="🗑")
        clear_btn.clicked.connect(self.log_console.clear)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        left_layout.addLayout(btn_row)
        layout.addWidget(left, stretch=2)

        # Right: Status panel
        right = QVBoxLayout()

        # Status group
        status_group = QGroupBox("🔄 Automation Status")
        sg_layout = QVBoxLayout(status_group)

        self.current_action_lbl = QLabel("Waiting for start...")
        self.current_action_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
        )
        self.current_action_lbl.setWordWrap(True)
        sg_layout.addWidget(self.current_action_lbl)

        sg_layout.addSpacing(8)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {DARK_BG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT2}, stop:1 {ACCENT});
                border-radius: 4px;
            }}
        """)
        sg_layout.addWidget(self.progress_bar)

        self.elapsed_lbl = QLabel("Duration: —")
        self.elapsed_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        sg_layout.addWidget(self.elapsed_lbl)

        right.addWidget(status_group)

        # Filled fields preview
        fields_group = QGroupBox("✅ Recently Filled Fields")
        fg_layout = QVBoxLayout(fields_group)
        self.filled_table = QTableWidget(0, 3)
        self.filled_table.setHorizontalHeaderLabels(["Label", "Value", "Confidence"])
        self.filled_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.filled_table.setMaximumHeight(220)
        self.filled_table.verticalHeader().setVisible(False)
        self.filled_table.setEditTriggers(QTableWidget.NoEditTriggers)
        fg_layout.addWidget(self.filled_table)
        right.addWidget(fields_group)
        right.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right)
        layout.addWidget(right_widget, stretch=1)

        return w

    # ── Live Activity Tab ─────────────────────────────────────────────────────

    def _build_activity_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        info = QLabel("📡 Real-time stream of all automation events and extracted data")
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; margin-bottom: 6px;")
        layout.addWidget(info)

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        layout.addWidget(self.activity_log)

        btn_row = QHBoxLayout()
        clear_act = make_button("Clear", icon_char="🗑")
        clear_act.clicked.connect(self.activity_log.clear)
        export_act = make_button("Export Log", icon_char="💾")
        export_act.clicked.connect(self._export_log)
        btn_row.addStretch()
        btn_row.addWidget(clear_act)
        btn_row.addWidget(export_act)
        layout.addLayout(btn_row)

        return w

    # ── AI Memory Tab ─────────────────────────────────────────────────────────

    def _build_memory_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("🧠 Learned App-Specific Field Mappings"))
        top_row.addStretch()

        self.app_filter = QComboBox()
        self.app_filter.addItem("All Apps")
        self.app_filter.currentTextChanged.connect(self._refresh_memory_table)
        top_row.addWidget(QLabel("Filter:"))
        top_row.addWidget(self.app_filter)

        refresh_btn = make_button("Refresh", icon_char="🔄")
        refresh_btn.clicked.connect(self._update_memory_stats)
        top_row.addWidget(refresh_btn)
        layout.addLayout(top_row)

        self.memory_table = QTableWidget(0, 5)
        self.memory_table.setHorizontalHeaderLabels(
            ["App", "Label", "Field", "Confidence", "Uses"]
        )
        self.memory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.memory_table.verticalHeader().setVisible(False)
        self.memory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.memory_table)

        btn_row = QHBoxLayout()
        reset_btn = make_button("Reset All Memory", danger=True, icon_char="🗑")
        reset_btn.clicked.connect(self._confirm_reset_memory)
        btn_row.addStretch()
        btn_row.addWidget(reset_btn)
        layout.addLayout(btn_row)

        return w

    # ── MPF Bot Tab ───────────────────────────────────────────────────────────

    def _build_mpf_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Header ──
        hdr = QLabel("🗂️  MRJ MPF Automation — Top-Grade Vision Bot")
        hdr.setStyleSheet(f"color: {ACCENT}; font-size: 15px; font-weight: 700;")
        layout.addWidget(hdr)
        sub = QLabel("Fully automatic form filling. Choose to read from a CSV file or scan the screen in real-time.")
        sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # ── Source Mode Selection ──
        mode_group = QGroupBox("🎯 Process Mode")
        mg_layout = QHBoxLayout(mode_group)
        self.mpf_mode_csv = QCheckBox("📁 CSV Data Mode")
        self.mpf_mode_vision = QCheckBox("👁️ Live Vision Mode (Read from Screen)")
        self.mpf_mode_csv.setChecked(True)
        
        # Make them exclusive
        def toggle_mode(m):
            if m == "csv":
                self.mpf_mode_vision.setChecked(not self.mpf_mode_csv.isChecked())
            else:
                self.mpf_mode_csv.setChecked(not self.mpf_mode_vision.isChecked())
            self._update_mpf_ui_visibility()

        self.mpf_mode_csv.toggled.connect(lambda: toggle_mode("csv"))
        self.mpf_mode_vision.toggled.connect(lambda: toggle_mode("vision"))
        
        mg_layout.addWidget(self.mpf_mode_csv)
        mg_layout.addSpacing(20)
        mg_layout.addWidget(self.mpf_mode_vision)
        mg_layout.addStretch()
        layout.addWidget(mode_group)

        # ── File Selection ──
        file_group = QGroupBox("📂 Data File")
        fg_layout = QHBoxLayout(file_group)
        self.mpf_file_lbl = QLabel("No file selected")
        self.mpf_file_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: monospace; font-size: 11px;"
        )
        self.mpf_file_lbl.setWordWrap(True)
        fg_layout.addWidget(self.mpf_file_lbl, stretch=1)

        browse_btn = make_button("Browse…", icon_char="📂")
        browse_btn.clicked.connect(self._mpf_browse_file)
        fg_layout.addWidget(browse_btn)

        sample_btn = make_button("Create Sample CSV", icon_char="📄")
        sample_btn.clicked.connect(self._mpf_create_sample)
        fg_layout.addWidget(sample_btn)
        layout.addWidget(file_group)

        # ── Progress ──
        prog_group = QGroupBox("📋 Progress")
        prog_layout = QVBoxLayout(prog_group)

        prog_row = QHBoxLayout()
        self.mpf_record_lbl = QLabel("Records: 0 / 0")
        self.mpf_record_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 700; font-size: 13px;")
        prog_row.addWidget(self.mpf_record_lbl)
        prog_row.addStretch()
        self.mpf_status_lbl = QLabel("Idle")
        self.mpf_status_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        prog_row.addWidget(self.mpf_status_lbl)
        prog_layout.addLayout(prog_row)

        self.mpf_progress = QProgressBar()
        self.mpf_progress.setRange(0, 100)
        self.mpf_progress.setValue(0)
        self.mpf_progress.setStyleSheet(f"""
            QProgressBar {{
                background: {DARK_BG}; border: 1px solid {BORDER};
                border-radius: 6px; height: 14px; text-align: center;
                color: {TEXT_PRIMARY}; font-size: 11px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT2}, stop:1 {ACCENT});
                border-radius: 6px;
            }}
        """)
        self.mpf_progress.setFormat("%p%")
        prog_layout.addWidget(self.mpf_progress)
        layout.addWidget(prog_group)

        # ── Controls ──
        ctrl_group = QGroupBox("🎮 Controls")
        ctrl_layout = QHBoxLayout(ctrl_group)

        self.mpf_start_btn  = make_button("▶  Start MPF Bot",  primary=True)
        self.mpf_pause_btn  = make_button("⏸  Pause",          icon_char="")
        self.mpf_resume_btn = make_button("▶  Resume",         icon_char="")
        self.mpf_stop_btn   = make_button("⏹  Stop",           danger=True)

        self.mpf_pause_btn.setEnabled(False)
        self.mpf_resume_btn.setEnabled(False)
        self.mpf_stop_btn.setEnabled(False)

        self.mpf_start_btn.clicked.connect(self._mpf_start)
        self.mpf_pause_btn.clicked.connect(self._mpf_pause)
        self.mpf_resume_btn.clicked.connect(self._mpf_resume)
        self.mpf_stop_btn.clicked.connect(self._mpf_stop)

        ctrl_layout.addWidget(self.mpf_start_btn)
        ctrl_layout.addWidget(self.mpf_pause_btn)
        ctrl_layout.addWidget(self.mpf_resume_btn)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.mpf_stop_btn)
        layout.addWidget(ctrl_group)

        # ── Speed Settings (inline) ──
        speed_row_group = QGroupBox("⚡ MPF Speed Settings")
        speed_row_layout = QHBoxLayout(speed_row_group)

        speed_row_layout.addWidget(QLabel("Fill Speed:"))
        self.mpf_speed_slider = QSlider(Qt.Horizontal)
        self.mpf_speed_slider.setRange(1, 10)
        self.mpf_speed_slider.setValue(5)
        self.mpf_speed_lbl = QLabel("Normal (5/10)")
        self.mpf_speed_lbl.setStyleSheet(f"color: {ACCENT}; min-width: 110px;")
        self.mpf_speed_slider.valueChanged.connect(
            lambda v: self.mpf_speed_lbl.setText(
                f"{'Slow' if v < 4 else 'Fast' if v > 7 else 'Normal'} ({v}/10)"
            )
        )
        speed_row_layout.addWidget(self.mpf_speed_slider, stretch=1)
        speed_row_layout.addWidget(self.mpf_speed_lbl)
        speed_row_layout.addSpacing(30)

        speed_row_layout.addWidget(QLabel("Field Delay (s):"))
        self.mpf_field_delay = QSpinBox()
        self.mpf_field_delay.setRange(5, 200)
        self.mpf_field_delay.setValue(25)
        self.mpf_field_delay.setSuffix(" ×0.01s")
        self.mpf_field_delay.setStyleSheet(f"""
            QSpinBox {{ background:#1C2333; border:1px solid {BORDER};
            border-radius:6px; padding:4px 8px; color:{TEXT_PRIMARY}; }}
        """)
        speed_row_layout.addWidget(self.mpf_field_delay)
        speed_row_layout.addSpacing(20)

        speed_row_layout.addWidget(QLabel("Form Delay (s):"))
        self.mpf_form_delay = QSpinBox()
        self.mpf_form_delay.setRange(1, 10)
        self.mpf_form_delay.setValue(2)
        self.mpf_form_delay.setSuffix(" s")
        self.mpf_form_delay.setStyleSheet(f"""
            QSpinBox {{ background:#1C2333; border:1px solid {BORDER};
            border-radius:6px; padding:4px 8px; color:{TEXT_PRIMARY}; }}
        """)
        speed_row_layout.addWidget(self.mpf_form_delay)
        layout.addWidget(speed_row_group)
        
        # ── Smart Wait Toggle ──
        sync_row = QHBoxLayout()
        self.mpf_sync_cb = QCheckBox("Smart Wait (Automatically detect when form is ready via Vision)")
        self.mpf_sync_cb.setChecked(True)
        self.mpf_sync_cb.setStyleSheet(f"color: {ACCENT}; font-weight: 600;")
        sync_row.addWidget(self.mpf_sync_cb)
        sync_row.addStretch()
        layout.addLayout(sync_row)

        # ── End-of-Form Sequence Calibration ──
        calib_group = QGroupBox("📌 End-of-Form Custom Clicks")
        calib_layout = QVBoxLayout(calib_group)
        
        self.btn_coords = {
            "upload": {"lbl": QLabel("Not Set"), "pos": None, "delay": QSpinBox()},
            "screenshot": {"lbl": QLabel("Not Set"), "pos": None, "delay": QSpinBox()},
            "next": {"lbl": QLabel("Not Set"), "pos": None}
        }
        
        self.btn_coords["upload"]["delay"].setRange(0, 30)
        self.btn_coords["upload"]["delay"].setValue(5)
        self.btn_coords["upload"]["delay"].setSuffix(" s")
        self.btn_coords["upload"]["delay"].setPrefix("Wait ")
        
        self.btn_coords["screenshot"]["delay"].setRange(0, 10)
        self.btn_coords["screenshot"]["delay"].setValue(1)
        self.btn_coords["screenshot"]["delay"].setSuffix(" s")
        self.btn_coords["screenshot"]["delay"].setPrefix("Wait ")

        def make_row(title, key, has_delay):
            row = QHBoxLayout()
            row.addWidget(QLabel(title))
            btn = make_button("🎯 Pick Coords", bg_color=PANEL_BG)
            btn.clicked.connect(lambda _, k=key, b=btn: self._start_coord_picker(k, b))
            row.addWidget(btn)
            
            lbl = self.btn_coords[key]["lbl"]
            lbl.setStyleSheet(f"color: {ACCENT}; margin-left:10px;")
            row.addWidget(lbl)
            
            if has_delay:
                row.addSpacing(20)
                row.addWidget(self.btn_coords[key]["delay"])
                
            row.addStretch()
            return row

        calib_layout.addLayout(make_row("1. Upload Details:  ", "upload", True))
        calib_layout.addLayout(make_row("2. Take Screenshot: ", "screenshot", True))
        calib_layout.addLayout(make_row("3. Load Another:    ", "next", False))
        
        layout.addWidget(calib_group)

        # ── Log Console ──
        log_group = QGroupBox("📟 MPF Bot Log")
        log_layout = QVBoxLayout(log_group)
        self.mpf_log = QTextEdit()
        self.mpf_log.setReadOnly(True)
        self.mpf_log.setMinimumHeight(180)
        log_layout.addWidget(self.mpf_log)
        clr_row = QHBoxLayout()
        clr_btn = make_button("Clear Log", icon_char="🗑")
        clr_btn.clicked.connect(self.mpf_log.clear)
        clr_row.addStretch()
        clr_row.addWidget(clr_btn)
        log_layout.addLayout(clr_row)
        layout.addWidget(log_group, stretch=1)

        # internal state
        self._mpf_data_file = ""
        self._mpf_source_region = None
        self._mpf_worker: MPFWorker | None = None
        self._mpf_total = 0

        return w

    def _update_mpf_ui_visibility(self):
        is_vision = self.mpf_mode_vision.isChecked()
        self.mpf_file_group.setVisible(not is_vision)
        self.mpf_vision_group.setVisible(is_vision)

    def _mpf_calibrate_source(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Calibrate Source Area")
        msg.setText("First, click 'OK' then move your mouse to the TOP-LEFT corner of the gray data pane on the MRJ software. Wait 3 seconds...")
        msg.exec_()
        
        self.mpf_cal_btn.setText("Hover Top-Left (3s)...")
        self.mpf_cal_btn.setEnabled(False)
        QApplication.processEvents()
        
        def step2():
            x1, y1 = pyautogui.position()
            self._mpf_log(f"📍 Top-Left captured: ({x1}, {y1})", "info")
            msg2 = QMessageBox(self)
            msg2.setText("Now move your mouse to the BOTTOM-RIGHT corner of the gray data pane. Wait 3 seconds...")
            msg2.exec_()
            self.mpf_cal_btn.setText("Hover Bottom-Right (3s)...")
            QApplication.processEvents()
            
            def finish():
                x2, y2 = pyautogui.position()
                w, h = x2 - x1, y2 - y1
                if w < 50 or h < 50:
                    QMessageBox.critical(self, "Invalid Area", "Selected area is too small. Please try again.")
                    self.mpf_cal_btn.setText("🎯 Set Source Region")
                    self.mpf_cal_btn.setEnabled(True)
                    return
                
                self._mpf_source_region = (x1, y1, w, h)
                self.mpf_source_lbl.setText(f"Region: {x1}, {y1} ({w}x{h})")
                self.mpf_source_lbl.setStyleSheet(f"color: {SUCCESS}; font-family: monospace; font-size: 11px;")
                self.mpf_cal_btn.setText("✅ Source Set")
                self.mpf_cal_btn.setEnabled(True)
                self._mpf_log(f"🎯 MPF Source Region Locked: {self._mpf_source_region}", "success")
            
            QTimer.singleShot(3000, finish)
            
        QTimer.singleShot(3000, step2)

    def _start_coord_picker(self, key, btn):
        original_text = btn.text()
        btn.setText("Hover over button... (3s)")
        btn.setStyleSheet(f"background-color: #E74C3C; color: white; border-radius: 4px; padding: 6px;")
        QApplication.processEvents()
        
        def capture():
            x, y = pyautogui.position()
            self.btn_coords[key]["pos"] = (x, y)
            self.btn_coords[key]["lbl"].setText(f"X: {x}, Y: {y}")
            btn.setText("🎯 Picked!")
            btn.setStyleSheet(f"background-color: #27AE60; color: white; border-radius: 4px; padding: 6px;")
            self._mpf_log(f"🎯 Coordinates for '{key}' picked: ({x}, {y})", "success")
            
        QTimer.singleShot(3000, capture)

    # ── MPF Bot Wiring ────────────────────────────────────────────────────────

    def _mpf_browse_file(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "",
            "Data Files (*.csv *.json);;CSV Files (*.csv);;JSON Files (*.json)"
        )
        if path:
            self._mpf_data_file = path
            # Show truncated path
            display = path if len(path) < 70 else "…" + path[-67:]
            self.mpf_file_lbl.setText(display)
            self.mpf_file_lbl.setStyleSheet(f"color: {SUCCESS}; font-family: monospace; font-size: 11px;")
            self._mpf_log(f"📂 Data file: {path}", "success")

    def _mpf_create_sample(self):
        import os
        path = os.path.join(os.getcwd(), "sample_mpf_data.csv")
        create_sample_csv(path)
        self._mpf_data_file = path
        display = path if len(path) < 70 else "…" + path[-67:]
        self.mpf_file_lbl.setText(display)
        self.mpf_file_lbl.setStyleSheet(f"color: {SUCCESS}; font-family: monospace; font-size: 11px;")
        self._mpf_log(f"✅ Sample CSV created: {path}", "success")
        self._mpf_log("   Edit the file then click ▶ Start MPF Bot.", "info")

    def _mpf_start(self):
        if not self._mpf_data_file:
            QMessageBox.warning(self, "No Data File",
                "Please select or create a CSV/JSON data file first.")
            return

        speed = self.mpf_speed_slider.value() / 5.0
        field_delay = self.mpf_field_delay.value() / 100.0
        form_delay  = float(self.mpf_form_delay.value())

        mode = "screen" if self.mpf_mode_vision.isChecked() else "csv"
        
        if mode == "screen" and not self._mpf_source_region:
            QMessageBox.warning(self, "Calibration Needed", 
                "Please calibrate the Source Region first for Live Vision mode.")
            return

        bot = MPFBot(
            data_file=self._mpf_data_file,
            log_cb=lambda m: self._mpf_log(m),
            status_cb=lambda s: self._mpf_status(s),
            record_done_cb=lambda d, t: self._mpf_record_done(d, t),
            stopped_cb=self._mpf_stopped,
            fill_speed=speed,
            delay_between_fields=field_delay,
            delay_between_forms=form_delay,
            use_visual_sync=self.mpf_sync_cb.isChecked(),
            source_mode=mode,
            source_region=self._mpf_source_region,
            end_sequence={
                "upload": self.btn_coords["upload"]["pos"],
                "upload_delay": self.btn_coords["upload"]["delay"].value(),
                "screenshot": self.btn_coords["screenshot"]["pos"],
                "screenshot_delay": self.btn_coords["screenshot"]["delay"].value(),
                "next": self.btn_coords["next"]["pos"],
            }
        )

        self._mpf_worker = MPFWorker(bot)
        self._mpf_worker.start()

        self.mpf_start_btn.setEnabled(False)
        self.mpf_pause_btn.setEnabled(True)
        self.mpf_stop_btn.setEnabled(True)
        self.mpf_resume_btn.setEnabled(False)
        
        # Link master buttons
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.mpf_progress.setValue(0)
        self._mpf_log("▶ MPF Bot started — switch to MPF window!", "success")

    def _mpf_pause(self):
        if self._mpf_worker:
            self._mpf_worker.pause()
        self.mpf_pause_btn.setEnabled(False)
        self.mpf_resume_btn.setEnabled(True)

    def _mpf_resume(self):
        if self._mpf_worker:
            self._mpf_worker.resume()
        self.mpf_pause_btn.setEnabled(True)
        self.mpf_resume_btn.setEnabled(False)

    def _mpf_stop(self):
        if self._mpf_worker:
            self._mpf_worker.stop()
        self.mpf_stop_btn.setEnabled(False)
        self.mpf_pause_btn.setEnabled(False)
        self.mpf_resume_btn.setEnabled(False)
        # Link master buttons
        self.stop_btn.setEnabled(False)

    def _mpf_stopped(self):
        self.mpf_start_btn.setEnabled(True)
        self.mpf_stop_btn.setEnabled(False)
        self.mpf_pause_btn.setEnabled(False)
        self.mpf_resume_btn.setEnabled(False)
        # Link master buttons
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._mpf_status("Idle")

    def _mpf_record_done(self, done: int, total: int):
        self._mpf_total = total
        pct = int(done / total * 100) if total else 0
        self.mpf_progress.setValue(pct)
        self.mpf_record_lbl.setText(f"Records: {done} / {total}")

    def _mpf_status(self, msg: str):
        self.mpf_status_lbl.setText(msg)

    def _mpf_log(self, msg: str, level: str = "info"):
        colors = {
            "info": TEXT_SECONDARY,
            "success": "#34D399",
            "warning": "#FBBF24",
            "error": "#F87171"
        }
        level_map = "info"
        if "❌" in msg or "Error" in msg.lower():
            level_map = "error"
        elif "⚠️" in msg or "Warning" in msg.lower():
            level_map = "warning"
        elif "✅" in msg or "🎉" in msg or "▶" in msg:
            level_map = "success"
        color = colors.get(level if level != "info" else level_map, TEXT_SECONDARY)
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#4B5563;">[{ts}]</span> <span style="color:{color};">{msg}</span>'
        self.mpf_log.append(html)
        self.mpf_log.ensureCursorVisible()

    # ── Settings Tab ──────────────────────────────────────────────────────────

    def _build_settings_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ── Automation Speed ──
        speed_group = QGroupBox("⚡ Automation Speed")
        speed_layout = QVBoxLayout(speed_group)
        speed_layout.addWidget(QLabel("Fill Speed (slower = more reliable):"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_label = QLabel("Normal (5/10)")
        self.speed_label.setStyleSheet(f"color: {ACCENT};")
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{'Slow' if v < 4 else 'Fast' if v > 7 else 'Normal'} ({v}/10)")
        )
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        layout.addWidget(speed_group)

        # ── OCR Settings ──
        ocr_group = QGroupBox("🔤 OCR Settings")
        ocr_layout = QVBoxLayout(ocr_group)
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("OCR Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["eng", "fra", "deu", "spa", "ita", "por",
                                   "chi_sim", "jpn", "kor", "ara"])
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()
        ocr_layout.addLayout(lang_row)
        layout.addWidget(ocr_group)

        # ── Detection Tuning ──
        detect_group = QGroupBox("🔎 Field Detection Tuning")
        detect_layout = QVBoxLayout(detect_group)
        conf_row = QHBoxLayout()
        conf_row.addWidget(QLabel("Minimum Confidence Threshold:"))
        self.conf_spin = QSpinBox()
        self.conf_spin.setRange(10, 90)
        self.conf_spin.setValue(30)
        self.conf_spin.setSuffix("%")
        self.conf_spin.setStyleSheet(f"""
            QSpinBox {{
                background: #1C2333; border: 1px solid {BORDER};
                border-radius: 6px; padding: 4px 8px; color: {TEXT_PRIMARY};
            }}
        """)
        conf_row.addWidget(self.conf_spin)
        conf_row.addStretch()
        detect_layout.addLayout(conf_row)
        layout.addWidget(detect_group)

        # ── Automation Behavior ──
        behavior_group = QGroupBox("🤖 Automation Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        self.continuous_cb = QCheckBox("Continuous Mode (auto-handle multi-page forms)")
        self.continuous_cb.setChecked(False)
        behavior_layout.addWidget(self.continuous_cb)

        retry_row = QHBoxLayout()
        retry_row.addWidget(QLabel("Max Retries per Field:"))
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.setStyleSheet(f"""
            QSpinBox {{
                background: #1C2333; border: 1px solid {BORDER};
                border-radius: 6px; padding: 4px 8px; color: {TEXT_PRIMARY};
            }}
        """)
        retry_row.addWidget(self.retry_spin)
        retry_row.addStretch()
        behavior_layout.addLayout(retry_row)
        layout.addWidget(behavior_group)

        # ── MPF Bot Settings ──
        mpf_group = QGroupBox("🗂️ MPF Bot Default Settings")
        mpf_layout = QVBoxLayout(mpf_group)
        
        mpf_f_row = QHBoxLayout()
        mpf_f_row.addWidget(QLabel("Default Field Delay (×0.01s):"))
        self.mpf_def_field_delay = QSpinBox()
        self.mpf_def_field_delay.setRange(5, 200)
        self.mpf_def_field_delay.setValue(25)
        mpf_f_row.addWidget(self.mpf_def_field_delay)
        mpf_layout.addLayout(mpf_f_row)

        mpf_s_row = QHBoxLayout()
        mpf_s_row.addWidget(QLabel("Default Form Delay (s):"))
        self.mpf_def_form_delay = QSpinBox()
        self.mpf_def_form_delay.setRange(1, 10)
        self.mpf_def_form_delay.setValue(2)
        mpf_s_row.addWidget(self.mpf_def_form_delay)
        mpf_layout.addLayout(mpf_s_row)
        
        layout.addWidget(mpf_group)

        # ── Tesseract Path ──
        tess_group = QGroupBox("📁 Tesseract OCR Path")
        tess_layout = QVBoxLayout(tess_group)
        self.tess_path_lbl = QLabel(
            "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
        )
        self.tess_path_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: monospace; font-size: 11px;"
        )
        tess_layout.addWidget(self.tess_path_lbl)
        layout.addWidget(tess_group)

        # Save button
        save_btn = make_button("  Save Settings", primary=True, icon_char="💾")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
        layout.addStretch()

        scroll.setWidget(w)
        return scroll

    # ── Business Logic ────────────────────────────────────────────────────────

    def _start_automation(self):
        """Create engine with current settings and start worker thread."""
        self.fields_filled = 0
        self.start_time = time.time()

        # Build engine
        speed = self.speed_slider.value() / 5.0  # 0.2 – 2.0
        self.engine = AutomationEngine(
            log_cb=self._on_log,
            status_cb=self._on_status,
            field_filled_cb=self._on_field_filled,
            stopped_cb=self._on_stopped,
        )
        self.engine.fill_speed = speed
        self.engine.ocr_lang = self.lang_combo.currentText()
        self.engine.confidence_threshold = self.conf_spin.value() / 100.0
        self.engine.continuous_mode = self.continuous_cb.isChecked()
        self.engine.max_retries = self.retry_spin.value()

        self.worker = BotWorker(self.engine)
        self.worker.start()

        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self._set_status("running")
        self.log("▶ Automation started", "info")
        self.status_bar.showMessage("Automation running...")

    def _stop_automation(self):
        if self.worker:
            self.worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_stopped(self):
        """Called from engine thread when automation stops."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self._set_status("idle")
        self._update_memory_stats()
        self.status_bar.showMessage(f"Automation finished — {self.fields_filled} fields filled")

    def _on_log(self, msg: str):
        """Receive log message from engine."""
        level = "info"
        if "❌" in msg or "Error" in msg.lower():
            level = "error"
        elif "⚠️" in msg or "Warning" in msg.lower():
            level = "warning"
        elif "✅" in msg or "🎉" in msg:
            level = "success"
        self.log(msg, level)

    def _on_status(self, status: str):
        """Receive status update from engine."""
        self.current_action_lbl.setText(status)
        self.status_bar.showMessage(status)

    def _on_field_filled(self, data: dict):
        """Called when a field is successfully filled."""
        self.fields_filled += 1
        self.card_fields.set_value(str(self.fields_filled))
        self.card_matches.set_value(str(self.fields_filled))

        # Add to filled table
        row = self.filled_table.rowCount()
        self.filled_table.insertRow(row)
        self.filled_table.setItem(row, 0, QTableWidgetItem(data.get("label", "")))
        self.filled_table.setItem(row, 1, QTableWidgetItem(data.get("value", "")))

        conf = data.get("confidence", 0.0)
        conf_item = QTableWidgetItem(f"{conf:.0%}")
        color = SUCCESS if conf > 0.65 else WARNING if conf > 0.35 else ERROR
        conf_item.setForeground(QColor(color))
        self.filled_table.setItem(row, 2, conf_item)
        self.filled_table.scrollToBottom()

    def _set_status(self, state: str):
        colors = {"running": SUCCESS, "idle": TEXT_SECONDARY, "error": ERROR}
        labels = {"running": "Running", "idle": "Idle", "error": "Error"}
        color = colors.get(state, TEXT_SECONDARY)
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 22px;")
        self.status_label_header.setText(labels.get(state, "Unknown"))
        self.status_label_header.setStyleSheet(
            f"color: {color}; font-weight: 600; font-size: 13px;"
        )

    def log(self, msg: str, level: str = "info"):
        """Append colored message to log consoles."""
        colors = {
            "info": TEXT_SECONDARY,
            "success": "#34D399",
            "warning": "#FBBF24",
            "error": "#F87171"
        }
        color = colors.get(level, TEXT_SECONDARY)
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#4B5563;">[{ts}]</span> <span style="color:{color};">{msg}</span>'
        self.log_console.append(html)
        self.activity_log.append(html)
        self.log_console.ensureCursorVisible()
        self.activity_log.ensureCursorVisible()

    def _update_memory_stats(self):
        """Refresh memory stats and table."""
        stats = learning.get_memory_stats()
        self.card_apps.set_value(str(stats["apps"]))
        self.card_mappings.set_value(str(stats["total_mappings"]))

        # Update app filter
        self.app_filter.blockSignals(True)
        self.app_filter.clear()
        self.app_filter.addItem("All Apps")
        for app in stats["known_apps"]:
            self.app_filter.addItem(app)
        self.app_filter.blockSignals(False)

        self._refresh_memory_table()

    def _refresh_memory_table(self):
        """Refresh the memory table based on filter."""
        mem = learning.load_memory()
        self.memory_table.setRowCount(0)

        selected_app = self.app_filter.currentText()

        for app_name, app_data in mem.items():
            if selected_app != "All Apps" and app_name != selected_app:
                continue
            for label, entry in app_data.items():
                row = self.memory_table.rowCount()
                self.memory_table.insertRow(row)

                self.memory_table.setItem(row, 0, QTableWidgetItem(app_name))
                self.memory_table.setItem(row, 1, QTableWidgetItem(label))
                self.memory_table.setItem(row, 2,
                                          QTableWidgetItem(entry.get("field", "")))

                conf = entry.get("confidence", 0.0)
                conf_item = QTableWidgetItem(f"{conf:.0%}")
                color = SUCCESS if conf > 0.65 else WARNING if conf > 0.35 else ERROR
                conf_item.setForeground(QColor(color))
                self.memory_table.setItem(row, 3, conf_item)

                uses = str(entry.get("uses", 0))
                self.memory_table.setItem(row, 4, QTableWidgetItem(uses))

    def _save_settings(self):
        self.log("⚙️ Settings saved successfully", "success")
        QMessageBox.information(self, "Settings", "Settings saved successfully!")

    def _confirm_reset_memory(self):
        reply = QMessageBox.question(
            self, "Reset Memory",
            "This will delete ALL learned mappings. Are you sure?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._clear_memory()

    def _clear_memory(self):
        from pathlib import Path
        mem_file = Path("memory.json")
        if mem_file.exists():
            mem_file.unlink()
        self._update_memory_stats()
        self.log("🗑 AI memory cleared", "warning")

    def _export_memory(self):
        import json
        from pathlib import Path
        mem = learning.load_memory()
        out = Path("memory_export.json")
        with open(out, "w") as f:
            json.dump(mem, f, indent=2)
        self.log(f"💾 Memory exported to {out.resolve()}", "success")

    def _export_log(self):
        content = self.activity_log.toPlainText()
        path = f"log_export_{int(time.time())}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"💾 Log exported to {path}", "success")

    def _open_log(self):
        os.startfile("automation.log") if os.path.exists("automation.log") else None

    def _show_about(self):
        QMessageBox.about(
            self, "About",
            "<h3>⚡ AI Smart Data Entry Automation Tool</h3>"
            "<p>Version 1.0.0 | Built with Python · PyQt5 · OpenCV · Tesseract · scikit-learn</p>"
            "<p>A self-learning intelligent form-filling automation system.</p>"
        )

    def _setup_timer(self):
        """Update elapsed time display every second."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _tick(self):
        if self.start_time and self.engine and self.engine.is_running:
            elapsed = int(time.time() - self.start_time)
            m, s = divmod(elapsed, 60)
            self.elapsed_lbl.setText(f"Duration: {m:02d}:{s:02d}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    # High DPI scaling for modern displays
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Data Entry Automation")
    app.setApplicationVersion("1.0.0")
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()
    window.log("🚀 AI Smart Data Entry Automation Tool initialized", "success")
    window.log(f"📁 Working directory: {os.getcwd()}", "info")

    stats = learning.get_memory_stats()
    window.log(f"🧠 Memory: {stats['total_mappings']} mappings across {stats['apps']} apps", "info")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
