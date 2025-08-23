"""
Modern results widget for displaying search results in beautiful card layout.
"""

import sys
import os
from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer, QSize
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QLabel, QPushButton, QFrame, QGridLayout, QSizePolicy,
                             QSpacerItem, QButtonGroup)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QBrush, QColor, QFont

# Add src to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.models import SearchResult, Manga


class MangaCard(QFrame):
    """Individual manga card with hover effects and modern styling."""
    
    clicked = pyqtSignal(object)  # SearchResult
    
    def __init__(self, search_result: SearchResult, parent=None):
        super().__init__(parent)
        self.search_result = search_result
        self.manga = search_result.manga
        self._is_hovered = False
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        """Set up the card UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setProperty("class", "card")
        self.setMinimumSize(280, 320)
        self.setMaximumSize(320, 360)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Cover image placeholder
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(240, 160)
        self.cover_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 2px dashed rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }
        """)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setText("📚\nCover")
        self.cover_label.setWordWrap(True)
        
        # Title
        self.title_label = QLabel(self.manga.title)
        self.title_label.setProperty("class", "subtitle")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(60)
        font = self.title_label.font()
        font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(font)
        
        # Author
        author_text = self.manga.author if self.manga.author else "Unknown Author"
        self.author_label = QLabel(f"by {author_text}")
        self.author_label.setProperty("class", "caption")
        self.author_label.setStyleSheet("color: #94A3B8;")
        
        # Metadata row
        metadata_layout = QHBoxLayout()
        
        # Chapters count
        chapters_text = f"{self.manga.total_chapters} chapters" if self.manga.total_chapters else "N/A"
        self.chapters_label = QLabel(chapters_text)
        self.chapters_label.setProperty("class", "caption")
        self.chapters_label.setStyleSheet("color: #10B981; font-weight: bold;")
        
        # Genres (first 2)
        if self.manga.genres:
            genres_text = ", ".join(self.manga.genres[:2])
            if len(self.manga.genres) > 2:
                genres_text += "..."
        else:
            genres_text = "Various"
        
        self.genres_label = QLabel(genres_text)
        self.genres_label.setProperty("class", "caption")
        self.genres_label.setStyleSheet("color: #8B5CF6;")
        
        metadata_layout.addWidget(self.chapters_label)
        metadata_layout.addStretch()
        metadata_layout.addWidget(self.genres_label)
        
        # Action button
        self.select_button = QPushButton("Select")
        self.select_button.setMinimumHeight(36)
        self.select_button.clicked.connect(lambda: self.clicked.emit(self.search_result))
        
        # Layout assembly
        layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addWidget(self.author_label)
        layout.addLayout(metadata_layout)
        layout.addStretch()
        layout.addWidget(self.select_button)
    
    def _setup_animations(self):
        """Set up hover animations."""
        self.shadow_animation = QPropertyAnimation(self, b"geometry")
        self.shadow_animation.setDuration(200)
        self.shadow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def enterEvent(self, event):
        """Handle mouse enter for hover effect."""
        self._is_hovered = True
        self.setStyleSheet("""
            MangaCard {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(139, 92, 246, 0.3);
                transform: translateY(-2px);
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave for hover effect."""
        self._is_hovered = False
        self.setStyleSheet("")
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press for click effect."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.search_result)
        super().mousePressEvent(event)


class PaginationWidget(QWidget):
    """Pagination controls for search results."""
    
    page_changed = pyqtSignal(int)  # new page number
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.total_pages = 1
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up pagination UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Previous button
        self.prev_button = QPushButton("‹ Previous")
        self.prev_button.setProperty("class", "secondary")
        self.prev_button.clicked.connect(self._go_previous)
        
        # Page info
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(120)
        
        # Next button
        self.next_button = QPushButton("Next ›")
        self.next_button.setProperty("class", "secondary")
        self.next_button.clicked.connect(self._go_next)
        
        layout.addStretch()
        layout.addWidget(self.prev_button)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_button)
        layout.addStretch()
        
        self._update_buttons()
    
    def set_page_info(self, current: int, total: int):
        """Set current page and total pages."""
        self.current_page = max(1, current)
        self.total_pages = max(1, total)
        self.page_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self._update_buttons()
    
    def _update_buttons(self):
        """Update button states."""
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
    
    def _go_previous(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.page_changed.emit(self.current_page - 1)
    
    def _go_next(self):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.page_changed.emit(self.current_page + 1)


class ResultsWidget(QWidget):
    """Modern results widget for displaying search results."""
    
    manga_selected = pyqtSignal(object)  # SearchResult
    page_changed = pyqtSignal(int)  # page number
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_results = []
        self.current_page = 1
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the results UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 16, 24, 24)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.results_title = QLabel("Search Results")
        self.results_title.setProperty("class", "title")
        
        self.results_count = QLabel("")
        self.results_count.setProperty("class", "caption")
        self.results_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(self.results_title)
        header_layout.addStretch()
        header_layout.addWidget(self.results_count)
        
        layout.addLayout(header_layout)
        
        # View toggle (grid/list) - for future enhancement
        view_layout = QHBoxLayout()
        view_layout.addStretch()
        
        # Grid view button (default)
        self.grid_button = QPushButton("⊞ Grid")
        self.grid_button.setProperty("class", "secondary")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(True)
        
        # List view button
        self.list_button = QPushButton("☰ List")
        self.list_button.setProperty("class", "secondary")
        self.list_button.setCheckable(True)
        
        # Button group for exclusive selection
        self.view_group = QButtonGroup()
        self.view_group.addButton(self.grid_button)
        self.view_group.addButton(self.list_button)
        
        view_layout.addWidget(self.grid_button)
        view_layout.addWidget(self.list_button)
        
        layout.addLayout(view_layout)
        
        # Results scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Results container
        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setSpacing(16)
        self.results_layout.setContentsMargins(8, 8, 8, 8)
        
        self.scroll_area.setWidget(self.results_container)
        layout.addWidget(self.scroll_area, 1)
        
        # Pagination
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.page_changed.emit)
        layout.addWidget(self.pagination)
        
        # Empty state
        self._setup_empty_state()
        
        # Connect view toggle
        self.grid_button.clicked.connect(self._update_view)
        self.list_button.clicked.connect(self._update_view)
    
    def _setup_empty_state(self):
        """Set up empty state display."""
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(16)
        
        # Empty icon
        empty_icon = QLabel("🔍")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("font-size: 48px;")
        
        # Empty title
        empty_title = QLabel("No results yet")
        empty_title.setProperty("class", "subtitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Empty description
        empty_desc = QLabel("Search for manga titles or paste a direct URL to get started")
        empty_desc.setProperty("class", "caption")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setWordWrap(True)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_desc)
        
        # Initially show empty state
        self.scroll_area.setWidget(self.empty_widget)
    
    def display_results(self, results: List[SearchResult], page: int = 1, total_pages: int = 1):
        """Display search results."""
        self.current_results = results
        self.current_page = page
        
        if not results:
            self._show_empty_state("No manga found", "Try different search terms or check your spelling")
            return
        
        # Update header
        self.results_count.setText(f"{len(results)} results found")
        
        # Clear existing results
        self._clear_results()
        
        # Create new results container
        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setSpacing(16)
        self.results_layout.setContentsMargins(8, 8, 8, 8)
        
        # Add result cards
        columns = 3  # 3 cards per row
        for i, result in enumerate(results):
            card = MangaCard(result)
            card.clicked.connect(self.manga_selected.emit)
            
            row = i // columns
            col = i % columns
            self.results_layout.addWidget(card, row, col)
        
        # Add stretch to remaining columns
        for col in range(len(results) % columns, columns):
            if len(results) % columns != 0:  # Only if we have incomplete last row
                spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                self.results_layout.addItem(spacer, (len(results) - 1) // columns, col)
        
        # Add vertical stretch
        self.results_layout.setRowStretch(self.results_layout.rowCount(), 1)
        
        self.scroll_area.setWidget(self.results_container)
        
        # Update pagination
        self.pagination.set_page_info(page, total_pages)
    
    def _show_empty_state(self, title: str, description: str):
        """Show empty state with custom message."""
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(16)
        
        # Empty icon
        empty_icon = QLabel("😔")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("font-size: 48px;")
        
        # Empty title
        empty_title = QLabel(title)
        empty_title.setProperty("class", "subtitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Empty description
        empty_desc = QLabel(description)
        empty_desc.setProperty("class", "caption")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setWordWrap(True)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_desc)
        
        self.scroll_area.setWidget(empty_widget)
        self.results_count.setText("")
    
    def _clear_results(self):
        """Clear current results."""
        # Clear the layout
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _update_view(self):
        """Update view mode (grid/list)."""
        # For now, we only support grid view
        # List view can be implemented later
        pass
    
    def show_loading(self):
        """Show loading state."""
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(16)
        
        # Loading icon (spinning)
        loading_icon = QLabel("⟳")
        loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_icon.setStyleSheet("font-size: 48px; color: #8B5CF6;")
        
        # Loading text
        loading_text = QLabel("Searching for manga...")
        loading_text.setProperty("class", "subtitle")
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_layout.addWidget(loading_icon)
        loading_layout.addWidget(loading_text)
        
        self.scroll_area.setWidget(loading_widget)
        self.results_count.setText("Searching...")
        
        # Simple rotation animation for loading icon
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(
            lambda: loading_icon.setText("⟲" if loading_icon.text() == "⟳" else "⟳")
        )
        self.loading_timer.start(500)
    
    def hide_loading(self):
        """Hide loading state."""
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
    
    def show_error(self, error_message: str):
        """Show error state."""
        self.hide_loading()
        self._show_empty_state("Search failed", f"Error: {error_message}")
    
    def clear(self):
        """Clear all results."""
        self.current_results = []
        self.scroll_area.setWidget(self.empty_widget)
        self.results_count.setText("")
        self.pagination.set_page_info(1, 1)