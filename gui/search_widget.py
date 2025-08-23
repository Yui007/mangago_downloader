"""
Modern search widget with dual mode support for title search and direct URL input.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QStringListModel
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QButtonGroup, QRadioButton,
                             QFrame, QCompleter)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen
import json
import os


class AnimatedToggle(QWidget):
    """Custom animated toggle switch."""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 32)
        self._checked = False
        self._animation = QPropertyAnimation(self, b"position")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._position = 2
    
    @property
    def position(self):
        return self._position
    
    @position.setter
    def position(self, value):
        self._position = value
        self.update()
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animation.setStartValue(self._position)
            self._animation.setEndValue(30 if checked else 2)
            self._animation.start()
            self.toggled.emit(checked)
    
    def isChecked(self):
        return self._checked
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw track
        track_color = "#8B5CF6" if self._checked else "#374151"
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(Qt.GlobalColor.transparent))
        
        track_rect = QRect(0, 8, 60, 16)
        painter.fillRect(track_rect, Qt.GlobalColor.transparent)
        
        # Draw background track
        painter.setBrush(Qt.GlobalColor.transparent)
        pen = QPen()
        pen.setColor(Qt.GlobalColor.transparent)
        painter.setPen(pen)
        painter.drawRoundedRect(track_rect, 8, 8)
        
        # Draw handle
        handle_color = "#FFFFFF"
        handle_rect = QRect(int(self._position), 2, 28, 28)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(QPen(Qt.GlobalColor.transparent))
        painter.drawEllipse(handle_rect)


class SearchWidget(QWidget):
    """Modern search widget with dual mode support."""
    
    search_requested = pyqtSignal(str, str)  # query, mode ("title" or "url")
    mode_changed = pyqtSignal(str)  # mode
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mode = "title"
        self._search_history = []
        self._setup_ui()
        self._load_search_history()
        self._setup_connections()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header with mode toggle
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Search Manga")
        self.title_label.setObjectName("title")
        self.title_label.setProperty("class", "title")
        
        # Mode toggle section
        mode_layout = QHBoxLayout()
        mode_layout.addStretch()
        
        self.title_radio = QRadioButton("Search by Title")
        self.url_radio = QRadioButton("Direct URL")
        self.title_radio.setChecked(True)
        
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.title_radio)
        mode_layout.addWidget(self.url_radio)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addLayout(mode_layout)
        
        layout.addLayout(header_layout)
        
        # Search input section
        search_layout = QVBoxLayout()
        
        # Search input with button
        input_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter manga title to search...")
        self.search_input.setMinimumHeight(48)
        
        self.search_button = QPushButton("Search")
        self.search_button.setMinimumSize(100, 48)
        self.search_button.setDefault(True)
        
        input_layout.addWidget(self.search_input, 1)
        input_layout.addWidget(self.search_button)
        
        search_layout.addLayout(input_layout)
        
        # Search suggestions/history
        self.suggestions_label = QLabel("Recent searches will appear here")
        self.suggestions_label.setProperty("class", "caption")
        self.suggestions_label.setStyleSheet("color: #94A3B8; font-style: italic;")
        
        search_layout.addWidget(self.suggestions_label)
        
        layout.addLayout(search_layout)
        
        # Advanced options (collapsed by default)
        self._setup_advanced_options(layout)
        
        # Status section
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "caption")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _setup_advanced_options(self, parent_layout):
        """Set up advanced search options."""
        # Advanced options frame (hidden by default)
        self.advanced_frame = QFrame()
        self.advanced_frame.setVisible(False)
        self.advanced_frame.setFrameStyle(QFrame.Shape.Box)
        self.advanced_frame.setProperty("class", "card")
        
        advanced_layout = QVBoxLayout(self.advanced_frame)
        
        advanced_header = QHBoxLayout()
        advanced_title = QLabel("Advanced Options")
        advanced_title.setProperty("class", "subtitle")
        advanced_header.addWidget(advanced_title)
        advanced_header.addStretch()
        
        advanced_layout.addLayout(advanced_header)
        
        # Page selection for search results
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Results per page:"))
        
        # Add more advanced options here as needed
        
        advanced_layout.addLayout(page_layout)
        
        # Toggle button for advanced options
        self.advanced_toggle = QPushButton("Show Advanced Options")
        self.advanced_toggle.setProperty("class", "secondary")
        self.advanced_toggle.clicked.connect(self._toggle_advanced_options)
        
        parent_layout.addWidget(self.advanced_toggle)
        parent_layout.addWidget(self.advanced_frame)
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.search_button.clicked.connect(self._on_search_clicked)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.title_radio.toggled.connect(self._on_mode_changed)
        self.url_radio.toggled.connect(self._on_mode_changed)
    
    def _toggle_advanced_options(self):
        """Toggle advanced options visibility."""
        is_visible = self.advanced_frame.isVisible()
        self.advanced_frame.setVisible(not is_visible)
        self.advanced_toggle.setText(
            "Hide Advanced Options" if not is_visible else "Show Advanced Options"
        )
    
    def _on_mode_changed(self):
        """Handle mode change between title search and URL input."""
        if self.title_radio.isChecked():
            self._current_mode = "title"
            self.search_input.setPlaceholderText("Enter manga title to search...")
            self.title_label.setText("Search Manga")
            self.suggestions_label.setText("Recent searches will appear here")
        else:
            self._current_mode = "url"
            self.search_input.setPlaceholderText("Enter manga URL directly...")
            self.title_label.setText("Direct URL")
            self.suggestions_label.setText("Paste the full URL of the manga page")
        
        self.mode_changed.emit(self._current_mode)
        self._update_search_suggestions()
    
    def _on_search_clicked(self):
        """Handle search button click."""
        query = self.search_input.text().strip()
        if not query:
            self.set_status("Please enter a search term or URL", "warning")
            return
        
        # Add to search history
        if query not in self._search_history:
            self._search_history.insert(0, query)
            self._search_history = self._search_history[:10]  # Keep only last 10
            self._save_search_history()
            self._update_search_suggestions()
        
        self.search_requested.emit(query, self._current_mode)
    
    def _update_search_suggestions(self):
        """Update search suggestions based on history."""
        if self._search_history:
            # Set up auto-completion
            completer = QCompleter(self._search_history)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.search_input.setCompleter(completer)
            
            # Update suggestions label
            recent_items = self._search_history[:3]
            if self._current_mode == "title":
                self.suggestions_label.setText(f"Recent: {', '.join(recent_items)}")
            else:
                self.suggestions_label.setText("Paste the full URL of the manga page")
    
    def _load_search_history(self):
        """Load search history from file."""
        try:
            history_file = os.path.join("downloads", "search_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._search_history = data.get('history', [])
        except Exception:
            self._search_history = []
    
    def _save_search_history(self):
        """Save search history to file."""
        try:
            os.makedirs("downloads", exist_ok=True)
            history_file = os.path.join("downloads", "search_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({'history': self._search_history}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Ignore save errors
    
    def set_status(self, message: str, status_type: str = "info"):
        """Set status message with appropriate styling."""
        self.status_label.setText(message)
        self.status_label.setProperty("class", f"status-{status_type}")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def clear_status(self):
        """Clear status message."""
        self.status_label.setText("")
    
    def set_loading(self, loading: bool):
        """Set loading state."""
        self.search_button.setEnabled(not loading)
        self.search_input.setEnabled(not loading)
        
        if loading:
            self.search_button.setText("Searching...")
            self.set_status("Searching for manga...", "info")
        else:
            self.search_button.setText("Search")
            self.clear_status()
    
    def get_current_mode(self) -> str:
        """Get current search mode."""
        return self._current_mode
    
    def get_search_query(self) -> str:
        """Get current search query."""
        return self.search_input.text().strip()
    
    def clear_search(self):
        """Clear search input."""
        self.search_input.clear()
        self.clear_status()