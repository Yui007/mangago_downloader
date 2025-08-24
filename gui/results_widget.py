"""
Modern results widget for displaying search results in beautiful card layout.
"""

import sys
import os
from typing import List, Optional
from PyQt6.QtCore import (Qt, pyqtSignal, QPropertyAnimation, QEasingCurve,
                          QRect, QTimer, QSize, QEvent, QRunnable,
                          QObject, pyqtSlot, QThreadPool)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QStackedWidget,
                             QLabel, QPushButton, QFrame, QGridLayout, QSizePolicy,
                             QSpacerItem, QButtonGroup)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QBrush, QColor, QFont, QMouseEvent, QEnterEvent
import httpx

# Add src to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.models import SearchResult, Manga
from src.utils import get_headers


class WorkerSignals(QObject):
    """Defines signals available from a running worker thread."""
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class ImageDownloader(QRunnable):
    """Worker thread for downloading images."""
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            with httpx.Client(headers=get_headers()) as client:
                response = client.get(self.url, timeout=20)
                response.raise_for_status()
                self.signals.result.emit(response.content)
        except Exception as e:
            self.signals.error.emit((e,))
        finally:
            self.signals.finished.emit()


class MangaCard(QFrame):
    """Individual manga card with hover effects and modern styling."""
    
    clicked = pyqtSignal(object)  # SearchResult
    
    def __init__(self, search_result: SearchResult, parent=None):
        super().__init__(parent)
        self.search_result = search_result
        self.manga = search_result.manga
        self._is_hovered = False
        self.threadpool = QThreadPool()
        self._setup_ui()
        self._setup_animations()
        self._load_cover_image()
    
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
    
    def _load_cover_image(self):
        """Load cover image from URL in a background thread."""
        if self.manga.cover_image_url:
            downloader = ImageDownloader(self.manga.cover_image_url)
            downloader.signals.result.connect(self._set_cover_image)
            self.threadpool.start(downloader)

    def _set_cover_image(self, image_data: bytes):
        """Set the cover image from downloaded data."""
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.cover_label.setPixmap(pixmap.scaled(
            self.cover_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        self.cover_label.setStyleSheet("border: 1px solid #4A5568; border-radius: 8px;")

    def _setup_animations(self):
        """Set up hover animations."""
        self.shadow_animation = QPropertyAnimation(self, b"geometry")
        self.shadow_animation.setDuration(200)
        self.shadow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def enterEvent(self, event: QEnterEvent | None) -> None:
        """Handle mouse enter for hover effect."""
        super().enterEvent(event)
        self.setProperty("class", "card-hover")
        style = self.style()
        if style:
            style.polish(self)

    def leaveEvent(self, a0: QEvent | None) -> None:
        """Handle mouse leave for hover effect."""
        super().leaveEvent(a0)
        self.setProperty("class", "card")
        style = self.style()
        if style:
            style.polish(self)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        """Handle mouse press for click effect."""
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.search_result)
        super().mousePressEvent(a0)


class PaginationWidget(QWidget):
    """Pagination controls for search results."""
    
    page_changed = pyqtSignal(int)  # new page number
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.has_more_pages = True
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
        self.page_label = QLabel("Page 1")
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
    
    def set_page(self, page: int, has_more: bool):
        """Set the current page and whether more pages are available."""
        self.current_page = page
        self.has_more_pages = has_more
        self.page_label.setText(f"Page {self.current_page}")
        self._update_buttons()

    def reset(self):
        """Reset to the first page."""
        self.set_page(1, True)

    def _update_buttons(self):
        """Update button states."""
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.has_more_pages)
    
    def _go_previous(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.page_changed.emit(self.current_page - 1)
    
    def _go_next(self):
        """Go to next page."""
        if self.has_more_pages:
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
        
        # Use a stacked widget to manage different states (results, empty, loading)
        self.view_stack = QStackedWidget()

        # 1. Results container
        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setSpacing(16)
        self.results_layout.setContentsMargins(8, 8, 8, 8)
        self.view_stack.addWidget(self.results_container)

        # 2. Empty state widget
        self._setup_empty_state()
        self.view_stack.addWidget(self.empty_widget)

        # 3. Loading state widget
        self._setup_loading_state()
        self.view_stack.addWidget(self.loading_widget)
        
        self.scroll_area.setWidget(self.view_stack)
        layout.addWidget(self.scroll_area, 1)
        
        # Pagination
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.page_changed.emit)
        layout.addWidget(self.pagination)
        
        # Set initial view to empty
        self.view_stack.setCurrentWidget(self.empty_widget)

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
        self.empty_title = QLabel("No results yet")
        self.empty_title.setProperty("class", "subtitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Empty description
        self.empty_desc = QLabel("Search for manga titles or paste a direct URL to get started")
        self.empty_desc.setProperty("class", "caption")
        self.empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_desc.setWordWrap(True)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_desc)
        
    
    def display_results(self, results: List[SearchResult], page: int):
        """Display search results."""
        self.hide_loading()
        self.current_results = results
        self.current_page = page
        
        has_more = bool(results)
        if not has_more and page == 1:
            self.show_error("No manga found", "Try different search terms or check your spelling.")
            return
        
        # Update header
        self.results_count.setText(f"{len(results)} results found")
        
        # Clear previous results before adding new ones
        self._clear_results()
        
        # Add result cards to the existing layout
        columns = 3
        for i, result in enumerate(results):
            card = MangaCard(result)
            card.clicked.connect(self.manga_selected.emit)
            row, col = divmod(i, columns)
            self.results_layout.addWidget(card, row, col)
            
        # Add stretch to fill remaining space
        self.results_layout.setRowStretch(self.results_layout.rowCount(), 1)
        
        # Switch to the results view
        self.view_stack.setCurrentWidget(self.results_container)
        
        # Update pagination
        self.pagination.set_page(page, has_more)
    
    def _show_empty_state(self, title: str, description: str):
        """Show empty state with custom message."""
        # Update the text of the existing empty_widget
        self.empty_title.setText(title)
        self.empty_desc.setText(description)
        self.view_stack.setCurrentWidget(self.empty_widget)
        self.results_count.setText("")
    
    def _clear_results(self):
        """Clear current results from the layout safely."""
        if self.results_layout is None:
            return
        while (item := self.results_layout.takeAt(0)) is not None:
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout is not None:
                    self._clear_layout(layout)

    def _clear_layout(self, layout):
        """Recursively clear a layout."""
        while (item := layout.takeAt(0)) is not None:
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                nested_layout = item.layout()
                if nested_layout is not None:
                    self._clear_layout(nested_layout)
    
    def _update_view(self):
        """Update view mode (grid/list)."""
        # For now, we only support grid view
        # List view can be implemented later
        pass
    
    def _setup_loading_state(self):
        """Set up the loading state widget."""
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(16)
        
        # Loading icon (spinning)
        self.loading_icon = QLabel("⟳")
        self.loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_icon.setStyleSheet("font-size: 48px; color: #8B5CF6;")
        
        # Loading text
        loading_text = QLabel("Searching for manga...")
        loading_text.setProperty("class", "subtitle")
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_layout.addWidget(self.loading_icon)
        loading_layout.addWidget(loading_text)

    def show_loading(self):
        """Show loading state."""
        self.pagination.reset() # Reset pagination on new search
        self.view_stack.setCurrentWidget(self.loading_widget)
        self.results_count.setText("Searching...")
        
        # Simple rotation animation for loading icon
        if not hasattr(self, 'loading_timer'):
            self.loading_timer = QTimer()
            self.loading_timer.timeout.connect(
                lambda: self.loading_icon.setText("⟲" if self.loading_icon.text() == "⟳" else "⟳")
            )
        self.loading_timer.start(500)
    
    def hide_loading(self):
        """Hide loading state."""
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
    
    def show_error(self, title: str, message: str):
        """Show error state."""
        self.hide_loading()
        self._show_empty_state(title, message)
    
    def clear(self):
        """Clear all results."""
        self.current_results = []
        self._clear_results()
        self._show_empty_state("No results yet", "Search for manga titles or paste a direct URL to get started")
        self.pagination.reset()