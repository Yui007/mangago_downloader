"""
Main window for the Mangago Downloader GUI application.
Modern PyQt6 interface integrating all components.
"""

import sys
import os
from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QPushButton, QLabel, QFrame, 
                             QSplitter, QMenuBar, QMenu, QStatusBar, QMessageBox,
                             QTabWidget, QApplication)
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap, QCloseEvent

# Import our custom widgets
from .search_widget import SearchWidget
from .results_widget import ResultsWidget
from .details_widget import DetailsWidget
from .download_widget import DownloadWidget
from .progress_widget import ProgressWidget
from .styles import style_manager
from .controllers import SearchController, MangaController, DownloadController, ConversionController

# Add src to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.models import Manga, Chapter, SearchResult


class HeaderWidget(QWidget):
    """Modern header widget with branding and theme controls."""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up header UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        
        # Logo and branding
        branding_layout = QVBoxLayout()
        
        # App title
        self.app_title = QLabel("Mangago Downloader")
        self.app_title.setProperty("class", "title")
        font = self.app_title.font()
        font.setWeight(QFont.Weight.Bold)
        font.setPointSize(20)
        self.app_title.setFont(font)
        
        # App subtitle
        self.app_subtitle = QLabel("Download your favorite manga with style")
        self.app_subtitle.setProperty("class", "caption")
        self.app_subtitle.setStyleSheet("color: #8B5CF6; font-style: italic;")
        
        branding_layout.addWidget(self.app_title)
        branding_layout.addWidget(self.app_subtitle)
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # Theme toggle
        self.theme_button = QPushButton("🌙 Dark")
        self.theme_button.setProperty("class", "secondary")
        self.theme_button.setMinimumSize(100, 36)
        self.theme_button.clicked.connect(self._toggle_theme)
        
        # Settings button (for future)
        self.settings_button = QPushButton("⚙ Settings")
        self.settings_button.setProperty("class", "secondary")
        self.settings_button.setMinimumSize(100, 36)
        self.settings_button.setEnabled(False)  # Placeholder
        
        # About button
        self.about_button = QPushButton("ℹ About")
        self.about_button.setProperty("class", "secondary")
        self.about_button.setMinimumSize(80, 36)
        self.about_button.clicked.connect(self._show_about)
        
        controls_layout.addWidget(self.theme_button)
        controls_layout.addWidget(self.settings_button)
        controls_layout.addWidget(self.about_button)
        
        # Assembly
        layout.addLayout(branding_layout)
        layout.addStretch()
        layout.addLayout(controls_layout)
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        current_theme = style_manager.get_current_theme()
        new_theme = "light" if current_theme == "dark" else "dark"
        
        style_manager.set_theme(new_theme)
        
        # Update button text
        if new_theme == "dark":
            self.theme_button.setText("🌙 Dark")
        else:
            self.theme_button.setText("☀ Light")
        
        self.theme_changed.emit(new_theme)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
        <h2>Mangago Downloader</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>A modern manga downloading tool</b></p>
        
        <p>Features:</p>
        <ul>
        <li>🔍 Search manga by title</li>
        <li>📁 Direct URL support</li>
        <li>📊 Real-time progress tracking</li>
        <li>📚 Multiple output formats (PDF, CBZ)</li>
        <li>🎨 Beautiful modern interface</li>
        <li>🌙 Dark/Light theme support</li>
        </ul>
        
        <p><b>Built with:</b> Python, PyQt6, and lots of ❤️</p>
        
        <p><i>Respect the content creators and use responsibly!</i></p>
        """
        
        QMessageBox.about(self, "About Mangago Downloader", about_text)


class NavigationWidget(QWidget):
    """Navigation sidebar for switching between different views."""
    
    view_changed = pyqtSignal(str)  # view name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_view = "search"
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up navigation UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 24, 16, 24)
        
        # Navigation title
        nav_title = QLabel("Navigation")
        nav_title.setProperty("class", "subtitle")
        font = nav_title.font()
        font.setWeight(QFont.Weight.Bold)
        nav_title.setFont(font)
        layout.addWidget(nav_title)
        
        layout.addWidget(QFrame())  # Separator
        
        # Navigation buttons
        self.nav_buttons = {}
        
        # Search view
        self.search_btn = self._create_nav_button("🔍 Search", "search", True)
        layout.addWidget(self.search_btn)
        
        # Results view
        self.results_btn = self._create_nav_button("📋 Results", "results", False)
        layout.addWidget(self.results_btn)
        
        # Details view
        self.details_btn = self._create_nav_button("📖 Details", "details", False)
        layout.addWidget(self.details_btn)
        
        # Download view
        self.download_btn = self._create_nav_button("⚙ Configure", "download", False)
        layout.addWidget(self.download_btn)
        
        # Progress view
        self.progress_btn = self._create_nav_button("📊 Progress", "progress", False)
        layout.addWidget(self.progress_btn)
        
        layout.addStretch()
        
        # Connection status
        self._setup_status_section(layout)
    
    def _create_nav_button(self, text: str, view_name: str, active: bool = False) -> QPushButton:
        """Create a navigation button."""
        button = QPushButton(text)
        button.setProperty("class", "secondary")
        button.setMinimumHeight(44)
        button.setCheckable(True)
        button.setChecked(active)
        
        if active:
            button.setStyleSheet("""
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #8B5CF6, stop:1 #3B82F6);
                    color: white;
                }
            """)
        
        button.clicked.connect(lambda: self._on_nav_clicked(view_name))
        self.nav_buttons[view_name] = button
        
        return button
    
    def _setup_status_section(self, parent_layout):
        """Set up status section at bottom of navigation."""
        status_frame = QFrame()
        status_frame.setProperty("class", "card")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(8)
        
        # Connection status
        status_title = QLabel("Status")
        status_title.setProperty("class", "caption")
        status_title.setStyleSheet("font-weight: bold;")
        
        self.connection_status = QLabel("🟢 Ready")
        self.connection_status.setProperty("class", "caption")
        
        # Download stats
        self.download_stats = QLabel("Downloads: 0")
        self.download_stats.setProperty("class", "caption")
        
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.connection_status)
        status_layout.addWidget(self.download_stats)
        
        parent_layout.addWidget(status_frame)
    
    def _on_nav_clicked(self, view_name: str):
        """Handle navigation button click."""
        # Update button states
        for name, button in self.nav_buttons.items():
            button.setChecked(name == view_name)
            
            if name == view_name:
                button.setStyleSheet("""
                    QPushButton:checked {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #8B5CF6, stop:1 #3B82F6);
                        color: white;
                    }
                """)
            else:
                button.setStyleSheet("")
        
        self.current_view = view_name
        self.view_changed.emit(view_name)
    
    def enable_view(self, view_name: str, enabled: bool = True):
        """Enable or disable a view."""
        if view_name in self.nav_buttons:
            self.nav_buttons[view_name].setEnabled(enabled)
    
    def update_connection_status(self, status: str, connected: bool = True):
        """Update connection status."""
        icon = "🟢" if connected else "🔴"
        self.connection_status.setText(f"{icon} {status}")
    
    def update_download_stats(self, count: int):
        """Update download statistics."""
        self.download_stats.setText(f"Downloads: {count}")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_manga = None
        self.current_chapters = []
        self.download_config = {}
        self.current_search_page = 1
        self._setup_controllers()
        self._setup_ui()
        self._setup_connections()
        self._apply_initial_theme()
    
    def _setup_controllers(self):
        """Set up controller instances."""
        self.search_controller = SearchController()
        self.manga_controller = MangaController()
        self.download_controller = DownloadController()
        self.conversion_controller = ConversionController()
    
    def _setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle("Mangago Downloader - Modern Manga Downloading")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation sidebar
        self.navigation = NavigationWidget()
        self.navigation.setFixedWidth(200)
        
        # Content area with stacked widgets
        self.content_stack = QStackedWidget()
        
        # Create and add view widgets
        self._setup_view_widgets()
        
        # Splitter for resizable layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.navigation)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([200, 1200])
        splitter.setCollapsible(0, False)  # Don't allow navigation to collapse
        
        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)
        
        # Status bar
        # Status bar
        self.status_bar = self.statusBar()
        if self.status_bar:
            self.status_bar.showMessage("Ready to search for manga")
        
        # Set initial view
        self.content_stack.setCurrentWidget(self.search_widget)
    
    def _setup_view_widgets(self):
        """Set up all view widgets."""
        # Search widget
        self.search_widget = SearchWidget()
        self.content_stack.addWidget(self.search_widget)
        
        # Results widget
        self.results_widget = ResultsWidget()
        self.content_stack.addWidget(self.results_widget)
        
        # Details widget
        self.details_widget = DetailsWidget()
        self.content_stack.addWidget(self.details_widget)
        
        # Download widget
        self.download_widget = DownloadWidget()
        self.content_stack.addWidget(self.download_widget)
        
        # Progress widget
        self.progress_widget = ProgressWidget()
        self.content_stack.addWidget(self.progress_widget)
    
    def _setup_connections(self):
        """Set up signal/slot connections."""
        # Header connections
        self.header.theme_changed.connect(self._on_theme_changed)
        
        # Navigation connections
        self.navigation.view_changed.connect(self._on_view_changed)
        
        # Search widget connections
        self.search_widget.search_requested.connect(self._on_search_requested)
        
        # Results widget connections
        self.results_widget.manga_selected.connect(self._on_manga_selected)
        self.results_widget.page_changed.connect(self._on_search_page_changed)
        
        # Details widget connections
        self.details_widget.chapters_selected.connect(self._on_chapters_selected)
        
        # Download widget connections
        self.download_widget.download_requested.connect(self._on_download_requested)
        
        # Progress widget connections
        self.progress_widget.download_paused.connect(self._on_download_paused)
        self.progress_widget.download_resumed.connect(self._on_download_resumed)
        self.progress_widget.download_cancelled.connect(self._on_download_cancelled)
        
        # Controller connections
        self._setup_controller_connections()
    
    def _setup_controller_connections(self):
        """Set up controller signal connections."""
        # Search controller
        self.search_controller.search_started.connect(
            lambda: self.results_widget.show_loading()
        )
        self.search_controller.search_completed.connect(self._on_search_completed)
        self.search_controller.search_failed.connect(self._on_search_failed)
        
        # Manga controller
        self.manga_controller.details_started.connect(
            lambda: self.status_bar.showMessage("Loading manga details...") if self.status_bar else None
        )
        self.manga_controller.details_completed.connect(self._on_manga_details_completed)
        self.manga_controller.chapters_completed.connect(self._on_chapters_completed)
        self.manga_controller.operation_failed.connect(self._on_operation_failed)
        
        # Download controller
        self.download_controller.download_started.connect(self._on_download_started)
        self.download_controller.urls_progress.connect(self._on_urls_progress)
        self.download_controller.urls_completed.connect(self._on_urls_completed)
        self.download_controller.download_progress.connect(self._on_download_progress)
        self.download_controller.chapter_downloaded.connect(self._on_chapter_downloaded)
        self.download_controller.download_completed.connect(self._on_download_completed)
        self.download_controller.status_updated.connect(self._on_download_status_updated)
        self.download_controller.operation_failed.connect(self._on_operation_failed)
        
        # Conversion controller
        self.conversion_controller.conversion_started.connect(
            lambda: self.status_bar.showMessage("Converting chapters...") if self.status_bar else None
        )
        self.conversion_controller.conversion_completed.connect(self._on_conversion_completed)
        self.conversion_controller.conversion_failed.connect(self._on_operation_failed)
        self.conversion_controller.status_updated.connect(self._on_download_status_updated)
    
    def _apply_initial_theme(self):
        """Apply initial theme."""
        style_manager.apply_theme()
    
    # Event handlers
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        if self.status_bar:
            self.status_bar.showMessage(f"Switched to {theme} theme", 2000)
    
    def _on_view_changed(self, view_name: str):
        """Handle view change."""
        view_widgets = {
            "search": self.search_widget,
            "results": self.results_widget,
            "details": self.details_widget,
            "download": self.download_widget,
            "progress": self.progress_widget
        }
        
        if view_name in view_widgets:
            self.content_stack.setCurrentWidget(view_widgets[view_name])
            
            # Update status bar
            view_names = {
                "search": "Search for manga",
                "results": "Browse search results",
                "details": "View manga details and select chapters",
                "download": "Configure download settings",
                "progress": "Monitor download progress"
            }
            if self.status_bar:
                self.status_bar.showMessage(view_names.get(view_name, "Ready"))
    
    def _on_search_requested(self, query: str, mode: str):
        """Handle search request."""
        if mode == "title":
            self.current_search_page = 1
            self.search_controller.search_manga(query, self.current_search_page)
        else:  # URL mode
            self.manga_controller.get_manga_details(query)
            # Switch to details view for URL mode
            self.navigation._on_nav_clicked("details")
        
        if self.status_bar:
            self.status_bar.showMessage(f"Searching: {query}")
    
    def _on_search_page_changed(self, page: int):
        """Handle search page change."""
        self.current_search_page = page
        query = self.search_widget.get_search_query()
        if query:
            self.search_controller.search_manga(query, self.current_search_page)
    
    def _on_search_completed(self, results: List[SearchResult]):
        """Handle search completion."""
        self.results_widget.hide_loading()
        self.results_widget.display_results(results, self.current_search_page)
        
        # Switch to results view
        self.navigation._on_nav_clicked("results")
        self.navigation.enable_view("results", True)
        
        if self.status_bar:
            self.status_bar.showMessage(f"Found {len(results)} manga")
    
    def _on_search_failed(self, error: str):
        """Handle search failure."""
        self.results_widget.hide_loading()
        self.results_widget.show_error("Search Failed", error)
        if self.status_bar:
            self.status_bar.showMessage(f"Search failed: {error}")
    
    def _on_manga_selected(self, result: SearchResult):
        """Handle manga selection."""
        self.manga_controller.get_manga_details(result.manga.url)
        self.navigation._on_nav_clicked("details")
        self.navigation.enable_view("details", True)
    
    def _on_manga_details_completed(self, manga: Manga):
        """Handle manga details completion."""
        self.current_manga = manga
        self.details_widget.update_manga(manga)
        if self.status_bar:
            self.status_bar.showMessage(f"Loaded details for: {manga.title}")
    
    def _on_chapters_completed(self, chapters: List[Chapter]):
        """Handle chapters list completion."""
        self.current_chapters = chapters
        self.details_widget.update_chapters(chapters)
        if self.status_bar:
            self.status_bar.showMessage(f"Found {len(chapters)} chapters")
    
    def _on_chapters_selected(self, manga: Manga, selected_chapters: List[Chapter]):
        """Handle chapters selection for download."""
        self.current_manga = manga
        self.current_chapters = selected_chapters
        
        # Enable download configuration
        self.navigation._on_nav_clicked("download")
        self.navigation.enable_view("download", True)
        self.download_widget.enable_download(True)
        
        if self.status_bar:
            self.status_bar.showMessage(f"Selected {len(selected_chapters)} chapters for download")
    
    def _on_download_requested(self, config: dict):
        """Handle download request."""
        if not self.current_manga or not self.current_chapters:
            QMessageBox.warning(self, "No Selection", "Please select manga and chapters first.")
            return
        
        self.download_config = config
        
        # Switch to progress view
        self.navigation._on_nav_clicked("progress")
        self.navigation.enable_view("progress", True)
        
        # Start download
        max_workers = config.get("max_workers", 5)
        self.download_controller.download_chapters(
            self.current_manga, 
            self.current_chapters, 
            max_workers
        )
    
    def _on_download_started(self):
        """Handle download start."""
        self.progress_widget.start_download(self.current_chapters)
        if self.status_bar:
            self.status_bar.showMessage("Download started")
    
    def _on_urls_progress(self, current: int, total: int):
        """Handle URL fetching progress."""
        if self.status_bar:
            self.status_bar.showMessage(f"Fetching URLs: {current}/{total}")
    
    def _on_urls_completed(self):
        """Handle URL fetching completion."""
        if self.status_bar:
            self.status_bar.showMessage("Starting chapter downloads...")
    
    def _on_download_progress(self, current: int, total: int):
        """Handle download progress."""
        if self.status_bar:
            self.status_bar.showMessage(f"Downloading: {current}/{total} chapters")
    
    def _on_chapter_downloaded(self, result):
        """Handle individual chapter download completion."""
        self.progress_widget.chapter_completed(result)
    
    def _on_download_completed(self, results: List):
        """Handle download completion."""
        self.progress_widget.download_finished()
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if self.status_bar:
            self.status_bar.showMessage(
                f"Download completed: {len(successful)} successful, {len(failed)} failed"
            )
        
        # Start conversion if needed
        format_type = self.download_config.get("format", "images")
        if format_type != "images" and successful and self.current_manga:
            delete_images = self.download_config.get("delete_images", False)
            self.conversion_controller.convert_chapters(
                self.current_manga,
                format_type,
                delete_images
            )
    
    def _on_download_status_updated(self, status: str):
        """Handle download status updates."""
        if self.status_bar:
            self.status_bar.showMessage(status)
    
    def _on_conversion_completed(self, created_files: List[str]):
        """Handle conversion completion."""
        if self.status_bar:
            self.status_bar.showMessage(f"Converted {len(created_files)} chapters successfully")
        
        # Show completion message
        QMessageBox.information(
            self, 
            "Download Complete", 
            f"Successfully downloaded and converted {len(created_files)} chapters!\n\n"
            f"Files saved to: {self.download_config.get('download_location', 'downloads')}"
        )
    
    def _on_operation_failed(self, error: str):
        """Handle operation failure."""
        if self.status_bar:
            self.status_bar.showMessage(f"Error: {error}")
        QMessageBox.critical(self, "Operation Failed", f"An error occurred:\n\n{error}")
    
    def _on_download_paused(self):
        """Handle download pause."""
        if self.status_bar:
            self.status_bar.showMessage("Download paused")
    
    def _on_download_resumed(self):
        """Handle download resume."""
        if self.status_bar:
            self.status_bar.showMessage("Download resumed")
    
    def _on_download_cancelled(self):
        """Handle download cancellation."""
        if self.status_bar:
            self.status_bar.showMessage("Download cancelled")
    
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Handle window close event."""
        # Clean up any running operations
        if hasattr(self, 'download_controller'):
            # Note: In a full implementation, you'd want to properly stop downloads
            pass
        
        if a0:
            a0.accept()