"""
Modern progress widget for real-time download progress tracking.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, 
                             QLabel, QPushButton, QFrame, QScrollArea, QTableWidget,
                             QTableWidgetItem, QHeaderView, QGroupBox, QGridLayout)
from PyQt6.QtGui import QFont, QColor, QPalette

# Add src to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.models import DownloadResult, Chapter


class AnimatedProgressBar(QProgressBar):
    """Custom animated progress bar with smooth transitions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(True)
        self._target_value = 0
        self._animation = QPropertyAnimation(self, b"value")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def setAnimatedValue(self, value: int):
        """Set value with smooth animation."""
        self._target_value = value
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(value)
        self._animation.start()
    
    def setInstantValue(self, value: int):
        """Set value instantly without animation."""
        self._animation.stop()
        self.setValue(value)
        self._target_value = value


class DownloadItemWidget(QWidget):
    """Widget representing a single download item."""
    
    def __init__(self, chapter: Chapter, parent=None):
        super().__init__(parent)
        self.chapter = chapter
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the download item UI."""
        self.setProperty("class", "card")
        self.setMinimumHeight(80)
        
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Chapter info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Chapter title
        self.title_label = QLabel(f"Chapter {self.chapter.number}")
        self.title_label.setProperty("class", "subtitle")
        font = self.title_label.font()
        font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(font)
        
        # Chapter subtitle
        subtitle = self.chapter.title if self.chapter.title else "Downloading..."
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("class", "caption")
        self.subtitle_label.setStyleSheet("color: #94A3B8;")
        
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.subtitle_label)
        
        # Progress section
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)
        
        # Progress bar
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumHeight(8)
        
        # Status and details
        details_layout = QHBoxLayout()
        
        self.status_label = QLabel("Pending")
        self.status_label.setProperty("class", "caption")
        
        self.details_label = QLabel("")
        self.details_label.setProperty("class", "caption")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        details_layout.addWidget(self.status_label)
        details_layout.addStretch()
        details_layout.addWidget(self.details_label)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(details_layout)
        
        # Action button
        self.action_button = QPushButton("⏸")  # Pause symbol
        self.action_button.setProperty("class", "secondary")
        self.action_button.setMaximumSize(32, 32)
        self.action_button.setEnabled(False)
        
        # Layout assembly
        layout.addLayout(info_layout, 1)
        layout.addLayout(progress_layout, 2)
        layout.addWidget(self.action_button)
    
    def update_progress(self, current: int, total: int):
        """Update download progress."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setAnimatedValue(percentage)
            self.details_label.setText(f"{current}/{total} images")
        else:
            self.progress_bar.setAnimatedValue(0)
            self.details_label.setText("0/0 images")
    
    def set_status(self, status: str, status_type: str = "info"):
        """Set download status."""
        self.status_label.setText(status)
        
        # Apply status styling
        colors = {
            "pending": "#94A3B8",
            "downloading": "#3B82F6", 
            "success": "#10B981",
            "error": "#EF4444",
            "paused": "#F59E0B"
        }
        
        color = colors.get(status_type, "#94A3B8")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def set_completed(self, success: bool, message: str = ""):
        """Set download as completed."""
        if success:
            self.progress_bar.setAnimatedValue(100)
            self.set_status("Completed", "success")
            self.action_button.setText("✓")
            self.action_button.setStyleSheet("color: #10B981;")
        else:
            self.set_status("Failed", "error")
            self.action_button.setText("✗")
            self.action_button.setStyleSheet("color: #EF4444;")
        
        if message:
            self.subtitle_label.setText(message)
        
        self.action_button.setEnabled(False)


class OverallProgressWidget(QWidget):
    """Widget showing overall download progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.reset()
    
    def _setup_ui(self):
        """Set up overall progress UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Download Progress")
        title.setProperty("class", "title")
        font = title.font()
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        
        self.overall_status = QLabel("Ready")
        self.overall_status.setProperty("class", "caption")
        self.overall_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.overall_status)
        
        layout.addLayout(header_layout)
        
        # Overall progress bar
        self.overall_progress = AnimatedProgressBar()
        self.overall_progress.setMinimumHeight(16)
        layout.addWidget(self.overall_progress)
        
        # Statistics
        stats_frame = QFrame()
        stats_frame.setProperty("class", "card")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(16)
        
        # Total chapters
        self.total_label = QLabel("Total:")
        self.total_value = QLabel("0")
        self.total_value.setStyleSheet("color: #3B82F6; font-weight: bold; font-size: 16px;")
        
        # Completed chapters
        self.completed_label = QLabel("Completed:")
        self.completed_value = QLabel("0")
        self.completed_value.setStyleSheet("color: #10B981; font-weight: bold; font-size: 16px;")
        
        # Failed chapters
        self.failed_label = QLabel("Failed:")
        self.failed_value = QLabel("0")
        self.failed_value.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 16px;")
        
        # Download speed
        self.speed_label = QLabel("Speed:")
        self.speed_value = QLabel("0 KB/s")
        self.speed_value.setStyleSheet("color: #8B5CF6; font-weight: bold; font-size: 16px;")
        
        # ETA
        self.eta_label = QLabel("ETA:")
        self.eta_value = QLabel("--:--")
        self.eta_value.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 16px;")
        
        # Arrange in grid
        stats_layout.addWidget(self.total_label, 0, 0)
        stats_layout.addWidget(self.total_value, 0, 1)
        stats_layout.addWidget(self.completed_label, 0, 2)
        stats_layout.addWidget(self.completed_value, 0, 3)
        stats_layout.addWidget(self.failed_label, 0, 4)
        stats_layout.addWidget(self.failed_value, 0, 5)
        
        stats_layout.addWidget(self.speed_label, 1, 0)
        stats_layout.addWidget(self.speed_value, 1, 1)
        stats_layout.addWidget(self.eta_label, 1, 2)
        stats_layout.addWidget(self.eta_value, 1, 3)
        
        layout.addWidget(stats_frame)
    
    def reset(self):
        """Reset all progress indicators."""
        self.overall_progress.setInstantValue(0)
        self.overall_status.setText("Ready")
        self.total_value.setText("0")
        self.completed_value.setText("0")
        self.failed_value.setText("0")
        self.speed_value.setText("0 KB/s")
        self.eta_value.setText("--:--")
    
    def update_overall_progress(self, completed: int, total: int):
        """Update overall progress."""
        if total > 0:
            percentage = int((completed / total) * 100)
            self.overall_progress.setAnimatedValue(percentage)
            self.overall_status.setText(f"{completed}/{total} chapters")
        else:
            self.overall_progress.setAnimatedValue(0)
            self.overall_status.setText("No chapters")
    
    def update_stats(self, total: int, completed: int, failed: int):
        """Update download statistics."""
        self.total_value.setText(str(total))
        self.completed_value.setText(str(completed))
        self.failed_value.setText(str(failed))
    
    def update_speed_eta(self, speed_kbps: float, eta_seconds: int):
        """Update download speed and ETA."""
        # Format speed
        if speed_kbps < 1024:
            speed_text = f"{speed_kbps:.1f} KB/s"
        else:
            speed_text = f"{speed_kbps/1024:.1f} MB/s"
        
        self.speed_value.setText(speed_text)
        
        # Format ETA
        if eta_seconds > 0:
            hours = eta_seconds // 3600
            minutes = (eta_seconds % 3600) // 60
            if hours > 0:
                eta_text = f"{hours}h {minutes}m"
            else:
                eta_text = f"{minutes}m {eta_seconds % 60}s"
        else:
            eta_text = "--:--"
        
        self.eta_value.setText(eta_text)


class ProgressWidget(QWidget):
    """Main progress widget for download tracking."""
    
    download_paused = pyqtSignal()
    download_resumed = pyqtSignal()
    download_cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_items = {}  # chapter.number -> DownloadItemWidget
        self.start_time = None
        self.total_chapters = 0
        self.completed_chapters = 0
        self.failed_chapters = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the progress widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Overall progress
        self.overall_widget = OverallProgressWidget()
        layout.addWidget(self.overall_widget)
        
        # Control buttons
        self._setup_control_buttons(layout)
        
        # Individual chapters progress
        chapters_group = QGroupBox("Chapter Downloads")
        chapters_layout = QVBoxLayout(chapters_group)
        
        # Scroll area for individual downloads
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for download items
        self.downloads_container = QWidget()
        self.downloads_layout = QVBoxLayout(self.downloads_container)
        self.downloads_layout.setSpacing(8)
        self.downloads_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add stretch to push items to top
        self.downloads_layout.addStretch()
        
        self.scroll_area.setWidget(self.downloads_container)
        chapters_layout.addWidget(self.scroll_area)
        
        layout.addWidget(chapters_group, 1)
        
        # Setup update timer for speed/ETA calculations
        self._setup_update_timer()
    
    def _setup_control_buttons(self, parent_layout):
        """Set up download control buttons."""
        controls_frame = QFrame()
        controls_frame.setProperty("class", "card")
        controls_layout = QHBoxLayout(controls_frame)
        
        # Pause/Resume button
        self.pause_resume_button = QPushButton("Pause Download")
        self.pause_resume_button.setProperty("class", "secondary")
        self.pause_resume_button.setEnabled(False)
        self.pause_resume_button.clicked.connect(self._on_pause_resume_clicked)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel Download")
        self.cancel_button.setProperty("class", "danger")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        
        # Clear completed button
        self.clear_button = QPushButton("Clear Completed")
        self.clear_button.setProperty("class", "secondary")
        self.clear_button.clicked.connect(self._clear_completed)
        
        controls_layout.addWidget(self.clear_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.pause_resume_button)
        controls_layout.addWidget(self.cancel_button)
        
        parent_layout.addWidget(controls_frame)
    
    def _setup_update_timer(self):
        """Set up timer for updating speed and ETA."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_speed_eta)
        self.update_timer.setInterval(1000)  # Update every second
    
    def start_download(self, chapters: List[Chapter]):
        """Start download progress tracking."""
        import time
        self.start_time = time.time()
        self.total_chapters = len(chapters)
        self.completed_chapters = 0
        self.failed_chapters = 0
        
        # Clear existing items
        self._clear_all_items()
        
        # Create download items for each chapter
        for chapter in chapters:
            item_widget = DownloadItemWidget(chapter)
            self.download_items[chapter.number] = item_widget
            
            # Insert at the beginning (before stretch)
            self.downloads_layout.insertWidget(0, item_widget)
        
        # Update overall progress
        self.overall_widget.update_stats(self.total_chapters, 0, 0)
        self.overall_widget.update_overall_progress(0, self.total_chapters)
        
        # Enable controls
        self.pause_resume_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        # Start update timer
        self.update_timer.start()
    
    def update_chapter_progress(self, chapter: Chapter, current: int, total: int):
        """Update progress for a specific chapter."""
        if chapter.number in self.download_items:
            item = self.download_items[chapter.number]
            item.update_progress(current, total)
            item.set_status("Downloading", "downloading")
    
    def chapter_completed(self, result: DownloadResult):
        """Mark chapter as completed."""
        chapter = result.chapter
        if chapter.number in self.download_items:
            item = self.download_items[chapter.number]
            
            if result.success:
                self.completed_chapters += 1
                item.set_completed(True, f"Downloaded {result.images_downloaded} images")
            else:
                self.failed_chapters += 1
                item.set_completed(False, result.error_message or "Download failed")
            
            # Update overall progress
            self._update_overall_progress()
    
    def download_finished(self):
        """Mark entire download as finished."""
        self.update_timer.stop()
        
        # Disable controls
        self.pause_resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # Update status
        if self.failed_chapters == 0:
            self.overall_widget.overall_status.setText("All downloads completed successfully!")
            self.overall_widget.overall_status.setStyleSheet("color: #10B981; font-weight: bold;")
        else:
            self.overall_widget.overall_status.setText(f"Download completed with {self.failed_chapters} failures")
            self.overall_widget.overall_status.setStyleSheet("color: #F59E0B; font-weight: bold;")
    
    def _update_overall_progress(self):
        """Update overall progress display."""
        total_completed = self.completed_chapters + self.failed_chapters
        self.overall_widget.update_overall_progress(total_completed, self.total_chapters)
        self.overall_widget.update_stats(self.total_chapters, self.completed_chapters, self.failed_chapters)
    
    def _update_speed_eta(self):
        """Update download speed and ETA."""
        if not self.start_time:
            return
        
        import time
        elapsed = time.time() - self.start_time
        
        if elapsed > 0:
            # Calculate speed (chapters per second, converted to "KB/s" for display)
            chapters_per_second = (self.completed_chapters + self.failed_chapters) / elapsed
            # Mock speed calculation - in a real implementation, track bytes
            mock_speed_kbps = chapters_per_second * 50  # Assume ~50KB per chapter for display
            
            # Calculate ETA
            remaining_chapters = self.total_chapters - (self.completed_chapters + self.failed_chapters)
            if chapters_per_second > 0 and remaining_chapters > 0:
                eta_seconds = int(remaining_chapters / chapters_per_second)
            else:
                eta_seconds = 0
            
            self.overall_widget.update_speed_eta(mock_speed_kbps, eta_seconds)
    
    def _on_pause_resume_clicked(self):
        """Handle pause/resume button click."""
        if self.pause_resume_button.text() == "Pause Download":
            self.pause_resume_button.setText("Resume Download")
            self.download_paused.emit()
            self.update_timer.stop()
        else:
            self.pause_resume_button.setText("Pause Download")
            self.download_resumed.emit()
            self.update_timer.start()
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.download_cancelled.emit()
        self.download_finished()
    
    def _clear_completed(self):
        """Clear completed download items."""
        items_to_remove = []
        for chapter_num, item in self.download_items.items():
            if (item.status_label.text() in ["Completed", "Failed"]):
                items_to_remove.append(chapter_num)
        
        for chapter_num in items_to_remove:
            item = self.download_items.pop(chapter_num)
            self.downloads_layout.removeWidget(item)
            item.deleteLater()
    
    def _clear_all_items(self):
        """Clear all download items."""
        for item in self.download_items.values():
            self.downloads_layout.removeWidget(item)
            item.deleteLater()
        
        self.download_items.clear()
    
    def reset(self):
        """Reset the progress widget."""
        self.update_timer.stop()
        self._clear_all_items()
        self.overall_widget.reset()
        self.start_time = None
        self.total_chapters = 0
        self.completed_chapters = 0
        self.failed_chapters = 0
        
        # Reset button states
        self.pause_resume_button.setText("Pause Download")
        self.pause_resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)