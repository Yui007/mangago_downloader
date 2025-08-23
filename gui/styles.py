"""
Modern styling system for the Mangago Downloader GUI.
Provides dark/light theme support with beautiful modern design elements.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from typing import Dict, Any


class StyleManager(QObject):
    """Manages application styling and theming."""
    
    theme_changed = pyqtSignal(str)  # Emitted when theme changes
    
    def __init__(self):
        super().__init__()
        self._current_theme = "dark"
        self._themes = {
            "dark": self._get_dark_theme(),
            "light": self._get_light_theme()
        }
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self._current_theme
    
    def set_theme(self, theme_name: str):
        """Set the application theme."""
        if theme_name in self._themes:
            self._current_theme = theme_name
            self.apply_theme()
            self.theme_changed.emit(theme_name)
    
    def apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self._themes[self._current_theme])
    
    def _get_dark_theme(self) -> str:
        """Get the dark theme stylesheet."""
        return """
        /* Main Application Styling */
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #0F172A, stop:1 #1E293B);
            color: #F8FAFC;
            font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
        }
        
        /* Widget Base Styling */
        QWidget {
            background-color: transparent;
            color: #F8FAFC;
            font-size: 14px;
        }
        
        /* Card-style containers */
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 16px;
            margin: 8px;
        }
        
        /* Modern Buttons */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #8B5CF6, stop:1 #3B82F6);
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            padding: 12px 24px;
            font-size: 14px;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #9333EA, stop:1 #2563EB);
            transform: translateY(-1px);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #7C3AED, stop:1 #1D4ED8);
        }
        
        QPushButton:disabled {
            background: #374151;
            color: #6B7280;
        }
        
        /* Secondary Buttons */
        QPushButton.secondary {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #F8FAFC;
        }
        
        QPushButton.secondary:hover {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        /* Danger Buttons */
        QPushButton.danger {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #EF4444, stop:1 #DC2626);
        }
        
        QPushButton.danger:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #F87171, stop:1 #EF4444);
        }
        
        /* Modern Input Fields */
        QLineEdit, QTextEdit, QSpinBox, QComboBox {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            color: #F8FAFC;
            selection-background-color: #8B5CF6;
        }
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
            border-color: #8B5CF6;
            background: rgba(139, 92, 246, 0.1);
        }
        
        QLineEdit::placeholder {
            color: #94A3B8;
        }
        
        /* ComboBox Dropdown */
        QComboBox::drop-down {
            border: none;
            width: 30px;
        }
        
        QComboBox::down-arrow {
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDYiIHN0cm9rZT0iIzk0QTNCOCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
        }
        
        QComboBox QAbstractItemView {
            background: #1E293B;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            selection-background-color: #8B5CF6;
            outline: none;
        }
        
        /* Progress Bars */
        QProgressBar {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 8px;
            height: 8px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #8B5CF6, stop:1 #3B82F6);
            border-radius: 8px;
        }
        
        /* Scroll Areas */
        QScrollArea {
            border: none;
            background: transparent;
        }
        
        QScrollBar:vertical {
            background: rgba(255, 255, 255, 0.05);
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* Tables and Lists */
        QTableWidget, QListWidget {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            alternate-background-color: rgba(255, 255, 255, 0.03);
            selection-background-color: rgba(139, 92, 246, 0.3);
            gridline-color: rgba(255, 255, 255, 0.05);
        }
        
        QTableWidget::item, QListWidget::item {
            padding: 12px;
            border: none;
        }
        
        QTableWidget::item:hover, QListWidget::item:hover {
            background: rgba(255, 255, 255, 0.08);
        }
        
        QHeaderView::section {
            background: rgba(255, 255, 255, 0.05);
            color: #CBD5E1;
            border: none;
            padding: 12px;
            font-weight: 600;
        }
        
        /* Checkboxes */
        QCheckBox {
            spacing: 8px;
            color: #F8FAFC;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 4px;
            background: transparent;
        }
        
        QCheckBox::indicator:checked {
            background: #8B5CF6;
            border-color: #8B5CF6;
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzIDRMNiAxMUwzIDgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
        }
        
        QCheckBox::indicator:hover {
            border-color: #8B5CF6;
        }
        
        /* Radio Buttons */
        QRadioButton {
            spacing: 8px;
            color: #F8FAFC;
        }
        
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 9px;
            background: transparent;
        }
        
        QRadioButton::indicator:checked {
            background: #8B5CF6;
            border-color: #8B5CF6;
        }
        
        QRadioButton::indicator:checked:after {
            content: "";
            width: 6px;
            height: 6px;
            border-radius: 3px;
            background: white;
            margin: 3px;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.02);
        }
        
        QTabBar::tab {
            background: rgba(255, 255, 255, 0.05);
            border: none;
            padding: 12px 24px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        
        QTabBar::tab:selected {
            background: #8B5CF6;
            color: white;
        }
        
        QTabBar::tab:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        /* Labels */
        QLabel {
            color: #F8FAFC;
        }
        
        QLabel.title {
            font-size: 24px;
            font-weight: 700;
            color: #F8FAFC;
        }
        
        QLabel.subtitle {
            font-size: 18px;
            font-weight: 600;
            color: #CBD5E1;
        }
        
        QLabel.caption {
            font-size: 12px;
            color: #94A3B8;
        }
        
        /* Status indicators */
        .status-success {
            color: #10B981;
            font-weight: 600;
        }
        
        .status-warning {
            color: #F59E0B;
            font-weight: 600;
        }
        
        .status-error {
            color: #EF4444;
            font-weight: 600;
        }
        
        .status-info {
            color: #3B82F6;
            font-weight: 600;
        }
        """
    
    def _get_light_theme(self) -> str:
        """Get the light theme stylesheet."""
        return """
        /* Main Application Styling */
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #FFFFFF, stop:1 #F8FAFC);
            color: #0F172A;
            font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
        }
        
        /* Widget Base Styling */
        QWidget {
            background-color: transparent;
            color: #0F172A;
            font-size: 14px;
        }
        
        /* Card-style containers */
        .card {
            background: rgba(0, 0, 0, 0.02);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 12px;
            padding: 16px;
            margin: 8px;
        }
        
        /* Modern Buttons */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #8B5CF6, stop:1 #3B82F6);
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            padding: 12px 24px;
            font-size: 14px;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #9333EA, stop:1 #2563EB);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #7C3AED, stop:1 #1D4ED8);
        }
        
        QPushButton:disabled {
            background: #E5E7EB;
            color: #9CA3AF;
        }
        
        /* Secondary Buttons */
        QPushButton.secondary {
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
            color: #374151;
        }
        
        QPushButton.secondary:hover {
            background: rgba(0, 0, 0, 0.08);
            border-color: rgba(0, 0, 0, 0.15);
        }
        
        /* Danger Buttons */
        QPushButton.danger {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #EF4444, stop:1 #DC2626);
        }
        
        QPushButton.danger:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #F87171, stop:1 #EF4444);
        }
        
        /* Modern Input Fields */
        QLineEdit, QTextEdit, QSpinBox, QComboBox {
            background: rgba(0, 0, 0, 0.02);
            border: 2px solid rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            color: #0F172A;
            selection-background-color: #8B5CF6;
        }
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
            border-color: #8B5CF6;
            background: rgba(139, 92, 246, 0.05);
        }
        
        QLineEdit::placeholder {
            color: #64748B;
        }
        
        /* Progress Bars */
        QProgressBar {
            background: rgba(0, 0, 0, 0.1);
            border: none;
            border-radius: 8px;
            height: 8px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #8B5CF6, stop:1 #3B82F6);
            border-radius: 8px;
        }
        
        /* Tables and Lists */
        QTableWidget, QListWidget {
            background: rgba(0, 0, 0, 0.01);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 12px;
            alternate-background-color: rgba(0, 0, 0, 0.02);
            selection-background-color: rgba(139, 92, 246, 0.2);
            gridline-color: rgba(0, 0, 0, 0.05);
        }
        
        QTableWidget::item, QListWidget::item {
            padding: 12px;
            border: none;
        }
        
        QTableWidget::item:hover, QListWidget::item:hover {
            background: rgba(0, 0, 0, 0.05);
        }
        
        QHeaderView::section {
            background: rgba(0, 0, 0, 0.03);
            color: #475569;
            border: none;
            padding: 12px;
            font-weight: 600;
        }
        
        /* Labels */
        QLabel {
            color: #0F172A;
        }
        
        QLabel.title {
            font-size: 24px;
            font-weight: 700;
            color: #0F172A;
        }
        
        QLabel.subtitle {
            font-size: 18px;
            font-weight: 600;
            color: #475569;
        }
        
        QLabel.caption {
            font-size: 12px;
            color: #64748B;
        }
        
        /* Status indicators */
        .status-success {
            color: #059669;
            font-weight: 600;
        }
        
        .status-warning {
            color: #D97706;
            font-weight: 600;
        }
        
        .status-error {
            color: #DC2626;
            font-weight: 600;
        }
        
        .status-info {
            color: #2563EB;
            font-weight: 600;
        }
        """


# Global style manager instance
style_manager = StyleManager()