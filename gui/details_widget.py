"""
Modern details widget for displaying manga information and interactive chapter selection.
"""

import sys
import os
from typing import List, Optional, Set
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QCheckBox, QSpinBox, QGroupBox, QGridLayout,
                             QSplitter, QTextEdit, QButtonGroup)
from PyQt6.QtGui import QPixmap, QFont

# Add src to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.models import Manga, Chapter


class MangaInfoWidget(QWidget):
    """Widget for displaying manga information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the manga info UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Cover image section
        cover_layout = QVBoxLayout()
        
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 280)
        self.cover_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 2px dashed rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        """)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setText("📚\nManga\nCover")
        self.cover_label.setWordWrap(True)
        
        cover_layout.addWidget(self.cover_label)
        cover_layout.addStretch()
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(16)
        
        # Title
        self.title_label = QLabel("Select a manga to view details")
        self.title_label.setProperty("class", "title")
        font = self.title_label.font()
        font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        
        # Author
        self.author_label = QLabel("")
        self.author_label.setProperty("class", "subtitle")
        self.author_label.setStyleSheet("color: #8B5CF6; font-weight: bold;")
        
        # Metadata row
        metadata_frame = QFrame()
        metadata_frame.setProperty("class", "card")
        metadata_layout = QGridLayout(metadata_frame)
        metadata_layout.setSpacing(16)
        
        # Chapters count
        self.chapters_count_label = QLabel("Chapters:")
        self.chapters_count_value = QLabel("0")
        self.chapters_count_value.setStyleSheet("color: #10B981; font-weight: bold; font-size: 16px;")
        
        # Genres
        self.genres_label = QLabel("Genres:")
        self.genres_value = QLabel("N/A")
        self.genres_value.setWordWrap(True)
        self.genres_value.setStyleSheet("color: #3B82F6;")
        
        # Status
        self.status_label = QLabel("Status:")
        self.status_value = QLabel("Unknown")
        self.status_value.setStyleSheet("color: #F59E0B; font-weight: bold;")
        
        metadata_layout.addWidget(self.chapters_count_label, 0, 0)
        metadata_layout.addWidget(self.chapters_count_value, 0, 1)
        metadata_layout.addWidget(self.genres_label, 1, 0)
        metadata_layout.addWidget(self.genres_value, 1, 1)
        metadata_layout.addWidget(self.status_label, 2, 0)
        metadata_layout.addWidget(self.status_value, 2, 1)
        
        # Description/Summary (for future enhancement)
        self.summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout(self.summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(120)
        self.summary_text.setPlainText("Summary will be available in future updates.")
        self.summary_text.setReadOnly(True)
        
        summary_layout.addWidget(self.summary_text)
        
        # Assemble info layout
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.author_label)
        info_layout.addWidget(metadata_frame)
        info_layout.addWidget(self.summary_group)
        info_layout.addStretch()
        
        # Add to main layout
        layout.addLayout(cover_layout)
        layout.addLayout(info_layout, 1)
    
    def update_manga_info(self, manga: Manga):
        """Update displayed manga information."""
        self.title_label.setText(manga.title)
        
        if manga.author:
            self.author_label.setText(f"by {manga.author}")
        else:
            self.author_label.setText("by Unknown Author")
        
        # Update chapters count
        if manga.total_chapters:
            self.chapters_count_value.setText(str(manga.total_chapters))
        else:
            self.chapters_count_value.setText("Unknown")
        
        # Update genres
        if manga.genres:
            self.genres_value.setText(", ".join(manga.genres))
        else:
            self.genres_value.setText("N/A")
        
        # Update status (placeholder for now)
        self.status_value.setText("Ongoing")  # This could be enhanced with actual status data
    
    def clear(self):
        """Clear manga information."""
        self.title_label.setText("Select a manga to view details")
        self.author_label.setText("")
        self.chapters_count_value.setText("0")
        self.genres_value.setText("N/A")
        self.status_value.setText("Unknown")


class ChapterSelectionWidget(QWidget):
    """Widget for interactive chapter selection."""
    
    selection_changed = pyqtSignal()  # Emitted when selection changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chapters = []
        self.selected_chapters = set()
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the chapter selection UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header with selection tools
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Chapter Selection")
        title_label.setProperty("class", "subtitle")
        font = title_label.font()
        font.setWeight(QFont.Weight.Bold)
        title_label.setFont(font)
        
        # Selection count
        self.selection_count_label = QLabel("0 selected")
        self.selection_count_label.setProperty("class", "caption")
        self.selection_count_label.setStyleSheet("color: #8B5CF6; font-weight: bold;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.selection_count_label)
        
        layout.addLayout(header_layout)
        
        # Selection tools
        tools_frame = QFrame()
        tools_frame.setProperty("class", "card")
        tools_layout = QHBoxLayout(tools_frame)
        tools_layout.setSpacing(12)
        
        # Quick selection buttons
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setProperty("class", "secondary")
        self.select_all_btn.clicked.connect(self._select_all)
        
        self.select_none_btn = QPushButton("Select None")
        self.select_none_btn.setProperty("class", "secondary")
        self.select_none_btn.clicked.connect(self._select_none)
        
        self.invert_selection_btn = QPushButton("Invert Selection")
        self.invert_selection_btn.setProperty("class", "secondary")
        self.invert_selection_btn.clicked.connect(self._invert_selection)
        
        # Range selection
        range_label = QLabel("Range:")
        self.range_from_spin = QSpinBox()
        self.range_from_spin.setMinimum(1)
        range_to_label = QLabel("to")
        self.range_to_spin = QSpinBox()
        self.range_to_spin.setMinimum(1)
        
        self.select_range_btn = QPushButton("Select Range")
        self.select_range_btn.setProperty("class", "secondary")
        self.select_range_btn.clicked.connect(self._select_range)
        
        tools_layout.addWidget(self.select_all_btn)
        tools_layout.addWidget(self.select_none_btn)
        tools_layout.addWidget(self.invert_selection_btn)
        tools_layout.addWidget(QFrame())  # Separator
        tools_layout.addWidget(range_label)
        tools_layout.addWidget(self.range_from_spin)
        tools_layout.addWidget(range_to_label)
        tools_layout.addWidget(self.range_to_spin)
        tools_layout.addWidget(self.select_range_btn)
        tools_layout.addStretch()
        
        layout.addWidget(tools_frame)
        
        # Chapters table
        self.chapters_table = QTableWidget()
        self.chapters_table.setColumnCount(3)
        self.chapters_table.setHorizontalHeaderLabels(["Select", "Chapter", "Title"])
        
        # Table styling
        header = self.chapters_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.chapters_table.setColumnWidth(0, 80)
        self.chapters_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.chapters_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.chapters_table, 1)
        
        # Empty state
        self._setup_empty_state()
    
    def _setup_empty_state(self):
        """Set up empty state for chapter selection."""
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(16)
        
        empty_icon = QLabel("📖")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("font-size: 48px;")
        
        empty_title = QLabel("No chapters loaded")
        empty_title.setProperty("class", "subtitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_desc = QLabel("Select a manga to view and choose chapters for download")
        empty_desc.setProperty("class", "caption")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setWordWrap(True)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_desc)
        
        # Initially hide the table and show empty state
        self.chapters_table.setVisible(False)
        layout = self.layout()
        layout.addWidget(self.empty_widget)
    
    def update_chapters(self, chapters: List[Chapter]):
        """Update the chapters list."""
        self.chapters = chapters
        self.selected_chapters.clear()
        
        if not chapters:
            self._show_empty_state()
            return
        
        # Hide empty state and show table
        if hasattr(self, 'empty_widget'):
            self.empty_widget.setVisible(False)
        self.chapters_table.setVisible(True)
        
        # Update spinbox ranges
        self.range_from_spin.setMaximum(len(chapters))
        self.range_to_spin.setMaximum(len(chapters))
        self.range_to_spin.setValue(len(chapters))
        
        # Populate table
        self.chapters_table.setRowCount(len(chapters))
        
        for i, chapter in enumerate(chapters):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, idx=i: self._on_checkbox_changed(idx, state))
            self.chapters_table.setCellWidget(i, 0, checkbox)
            
            # Chapter number
            chapter_item = QTableWidgetItem(f"Ch. {chapter.number}")
            chapter_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chapters_table.setItem(i, 1, chapter_item)
            
            # Chapter title
            title_item = QTableWidgetItem(chapter.title or "Untitled")
            self.chapters_table.setItem(i, 2, title_item)
        
        self._update_selection_count()
    
    def _show_empty_state(self):
        """Show empty state."""
        self.chapters_table.setVisible(False)
        if hasattr(self, 'empty_widget'):
            self.empty_widget.setVisible(True)
        self._update_selection_count()
    
    def _on_checkbox_changed(self, chapter_index: int, state: int):
        """Handle checkbox state change."""
        if state == Qt.CheckState.Checked.value:
            self.selected_chapters.add(chapter_index)
        else:
            self.selected_chapters.discard(chapter_index)
        
        self._update_selection_count()
        self.selection_changed.emit()
    
    def _select_all(self):
        """Select all chapters."""
        for i in range(len(self.chapters)):
            checkbox = self.chapters_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def _select_none(self):
        """Deselect all chapters."""
        for i in range(len(self.chapters)):
            checkbox = self.chapters_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def _invert_selection(self):
        """Invert current selection."""
        for i in range(len(self.chapters)):
            checkbox = self.chapters_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(not checkbox.isChecked())
    
    def _select_range(self):
        """Select range of chapters."""
        start = self.range_from_spin.value() - 1  # Convert to 0-based
        end = self.range_to_spin.value()  # End is exclusive
        
        for i in range(len(self.chapters)):
            checkbox = self.chapters_table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(start <= i < end)
    
    def _update_selection_count(self):
        """Update selection count display."""
        count = len(self.selected_chapters)
        total = len(self.chapters)
        self.selection_count_label.setText(f"{count} of {total} selected")
    
    def get_selected_chapters(self) -> List[Chapter]:
        """Get list of selected chapters."""
        return [self.chapters[i] for i in sorted(self.selected_chapters)]
    
    def has_selection(self) -> bool:
        """Check if any chapters are selected."""
        return len(self.selected_chapters) > 0
    
    def clear(self):
        """Clear chapters and selection."""
        self.chapters = []
        self.selected_chapters.clear()
        self.chapters_table.setRowCount(0)
        self._show_empty_state()


class DetailsWidget(QWidget):
    """Main details widget containing manga info and chapter selection."""
    
    chapters_selected = pyqtSignal(object, list)  # manga, selected_chapters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_manga = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the details UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Manga info section
        self.manga_info = MangaInfoWidget()
        info_frame = QFrame()
        info_frame.setProperty("class", "card")
        info_layout = QVBoxLayout(info_frame)
        info_layout.addWidget(self.manga_info)
        
        # Chapter selection section
        self.chapter_selection = ChapterSelectionWidget()
        self.chapter_selection.selection_changed.connect(self._on_selection_changed)
        selection_frame = QFrame()
        selection_frame.setProperty("class", "card")
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.addWidget(self.chapter_selection)
        
        # Add to splitter
        splitter.addWidget(info_frame)
        splitter.addWidget(selection_frame)
        splitter.setSizes([300, 400])  # Initial sizes
        
        layout.addWidget(splitter)
        
        # Action buttons
        self._setup_action_buttons(layout)
    
    def _setup_action_buttons(self, parent_layout):
        """Set up action buttons."""
        buttons_frame = QFrame()
        buttons_frame.setProperty("class", "card")
        buttons_layout = QHBoxLayout(buttons_frame)
        
        # Download button
        self.download_button = QPushButton("Download Selected Chapters")
        self.download_button.setMinimumHeight(44)
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self._on_download_clicked)
        
        # Quick download options
        self.download_all_button = QPushButton("Download All")
        self.download_all_button.setProperty("class", "secondary")
        self.download_all_button.setMinimumHeight(44)
        self.download_all_button.setEnabled(False)
        self.download_all_button.clicked.connect(self._on_download_all_clicked)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.download_all_button)
        buttons_layout.addWidget(self.download_button)
        
        parent_layout.addWidget(buttons_frame)
    
    def update_manga(self, manga: Manga):
        """Update displayed manga."""
        self.current_manga = manga
        self.manga_info.update_manga_info(manga)
        self.download_all_button.setEnabled(True)
    
    def update_chapters(self, chapters: List[Chapter]):
        """Update chapters list."""
        self.chapter_selection.update_chapters(chapters)
        self._on_selection_changed()  # Update button states
    
    def _on_selection_changed(self):
        """Handle chapter selection change."""
        has_selection = self.chapter_selection.has_selection()
        self.download_button.setEnabled(has_selection)
    
    def _on_download_clicked(self):
        """Handle download selected chapters."""
        if self.current_manga and self.chapter_selection.has_selection():
            selected_chapters = self.chapter_selection.get_selected_chapters()
            self.chapters_selected.emit(self.current_manga, selected_chapters)
    
    def _on_download_all_clicked(self):
        """Handle download all chapters."""
        if self.current_manga:
            all_chapters = self.chapter_selection.chapters
            if all_chapters:
                self.chapters_selected.emit(self.current_manga, all_chapters)
    
    def show_loading(self, message: str = "Loading chapters..."):
        """Show loading state."""
        # Could add a loading overlay here
        pass
    
    def hide_loading(self):
        """Hide loading state."""
        pass
    
    def clear(self):
        """Clear all data."""
        self.current_manga = None
        self.manga_info.clear()
        self.chapter_selection.clear()
        self.download_button.setEnabled(False)
        self.download_all_button.setEnabled(False)