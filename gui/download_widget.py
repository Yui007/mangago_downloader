"""
Modern download widget for format selection and download configuration.
"""

import os
from typing import Dict, Any
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QRadioButton, QCheckBox, QSpinBox, QLabel,
                             QPushButton, QFrame, QFileDialog, QLineEdit,
                             QButtonGroup, QSlider, QComboBox)
from PyQt6.QtGui import QFont


class FormatSelectionWidget(QWidget):
    """Widget for selecting download format."""
    
    format_changed = pyqtSignal(str)  # format name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up format selection UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel("Output Format")
        title.setProperty("class", "subtitle")
        font = title.font()
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        layout.addWidget(title)
        
        # Format options
        formats_frame = QFrame()
        formats_frame.setProperty("class", "card")
        formats_layout = QVBoxLayout(formats_frame)
        formats_layout.setSpacing(12)
        
        # Button group for exclusive selection
        self.format_group = QButtonGroup()
        
        # Images only
        self.images_radio = QRadioButton("Images Only")
        self.images_radio.setChecked(True)  # Default
        self.images_desc = QLabel("Save as individual image files (JPG/PNG)")
        self.images_desc.setProperty("class", "caption")
        self.images_desc.setStyleSheet("color: #94A3B8; margin-left: 20px;")
        
        # PDF format
        self.pdf_radio = QRadioButton("PDF")
        self.pdf_desc = QLabel("Convert to PDF document for easy reading")
        self.pdf_desc.setProperty("class", "caption")
        self.pdf_desc.setStyleSheet("color: #94A3B8; margin-left: 20px;")
        
        # CBZ format
        self.cbz_radio = QRadioButton("CBZ")
        self.cbz_desc = QLabel("Comic Book ZIP format for comic readers")
        self.cbz_desc.setProperty("class", "caption")
        self.cbz_desc.setStyleSheet("color: #94A3B8; margin-left: 20px;")
        
        # Add to button group
        self.format_group.addButton(self.images_radio)
        self.format_group.addButton(self.pdf_radio)
        self.format_group.addButton(self.cbz_radio)
        
        # Add to layout
        formats_layout.addWidget(self.images_radio)
        formats_layout.addWidget(self.images_desc)
        formats_layout.addWidget(self.pdf_radio)
        formats_layout.addWidget(self.pdf_desc)
        formats_layout.addWidget(self.cbz_radio)
        formats_layout.addWidget(self.cbz_desc)
        
        layout.addWidget(formats_frame)
        
        # Format-specific options
        self._setup_format_options(layout)
        
        # Connect signals
        self.images_radio.toggled.connect(self._on_format_changed)
        self.pdf_radio.toggled.connect(self._on_format_changed)
        self.cbz_radio.toggled.connect(self._on_format_changed)
    
    def _setup_format_options(self, parent_layout):
        """Set up format-specific options."""
        # Delete images option (for PDF/CBZ)
        self.delete_images_frame = QFrame()
        self.delete_images_frame.setProperty("class", "card")
        delete_layout = QVBoxLayout(self.delete_images_frame)
        
        self.delete_images_checkbox = QCheckBox("Delete images after conversion")
        self.delete_images_checkbox.setChecked(False)
        
        delete_desc = QLabel("Remove original image files to save space")
        delete_desc.setProperty("class", "caption")
        delete_desc.setStyleSheet("color: #F59E0B; margin-left: 20px;")
        
        delete_layout.addWidget(self.delete_images_checkbox)
        delete_layout.addWidget(delete_desc)
        
        parent_layout.addWidget(self.delete_images_frame)
        
        # Initially hide delete option (only for PDF/CBZ)
        self.delete_images_frame.setVisible(False)
    
    def _on_format_changed(self):
        """Handle format selection change."""
        if self.images_radio.isChecked():
            format_name = "images"
            self.delete_images_frame.setVisible(False)
        elif self.pdf_radio.isChecked():
            format_name = "pdf"
            self.delete_images_frame.setVisible(True)
        else:  # CBZ
            format_name = "cbz"
            self.delete_images_frame.setVisible(True)
        
        self.format_changed.emit(format_name)
    
    def get_format(self) -> str:
        """Get selected format."""
        if self.pdf_radio.isChecked():
            return "pdf"
        elif self.cbz_radio.isChecked():
            return "cbz"
        else:
            return "images"
    
    def should_delete_images(self) -> bool:
        """Check if images should be deleted after conversion."""
        return (self.delete_images_checkbox.isChecked() and 
                self.delete_images_frame.isVisible())


class DownloadOptionsWidget(QWidget):
    """Widget for download options and settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up download options UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel("Download Options")
        title.setProperty("class", "subtitle")
        font = title.font()
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        layout.addWidget(title)
        
        # Download location
        location_frame = QFrame()
        location_frame.setProperty("class", "card")
        location_frame.setMinimumHeight(100)  # Set minimum height
        location_layout = QVBoxLayout(location_frame)
        location_layout.setSpacing(8)
        location_layout.setContentsMargins(16, 16, 16, 16)  # Add margins
        
        location_label = QLabel("Download Location")
        location_label.setProperty("class", "subtitle")
        location_layout.addWidget(location_label)
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Select download folder...")
        self.location_input.setText(os.path.abspath("downloads"))
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setProperty("class", "secondary")
        self.browse_button.clicked.connect(self._browse_location)

        location_input_layout = QHBoxLayout()
        location_input_layout.addWidget(self.location_input, 1)
        location_input_layout.addWidget(self.browse_button)
        location_layout.addLayout(location_input_layout)
        
        layout.addWidget(location_frame)
        
        # Performance options
        performance_frame = QFrame()
        performance_frame.setProperty("class", "card")
        performance_frame.setMinimumHeight(150)  # Set minimum height
        performance_layout = QVBoxLayout(performance_frame)
        performance_layout.setSpacing(12)
        performance_layout.setContentsMargins(16, 16, 16, 16)  # Add margins
        
        perf_label = QLabel("Performance Settings")
        perf_label.setProperty("class", "subtitle")
        performance_layout.addWidget(perf_label)
        
        # Concurrent downloads
        concurrent_layout = QHBoxLayout()
        concurrent_label = QLabel("Concurrent Downloads:")
        concurrent_label.setMinimumWidth(150)
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(20)
        self.concurrent_spin.setValue(5)
        self.concurrent_spin.setSuffix(" threads")
        self.concurrent_spin.setMinimumWidth(120)
        
        concurrent_layout.addWidget(concurrent_label)
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addStretch()
        
        performance_layout.addLayout(concurrent_layout)
        
        concurrent_desc = QLabel("Higher values = faster downloads but more system load")
        concurrent_desc.setProperty("class", "caption")
        concurrent_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        performance_layout.addWidget(concurrent_desc)
        
        # Download speed slider (visual only, for user feedback)
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Expected Speed:")
        speed_label.setMinimumWidth(150)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(5)
        self.speed_slider.setMinimumWidth(200)
        
        self.speed_value = QLabel("Normal")
        self.speed_value.setMinimumWidth(80)
        
        # Connect slider to update label
        self.speed_slider.valueChanged.connect(self._update_speed_label)
        self.concurrent_spin.valueChanged.connect(self._update_speed_from_threads)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider, 1)
        speed_layout.addWidget(self.speed_value)
        
        performance_layout.addLayout(speed_layout)
        
        layout.addWidget(performance_frame)
        
        # Advanced options
        self._setup_advanced_options(layout)

    def _setup_advanced_options(self, parent_layout):
        """Set up advanced download options."""
        advanced_frame = QFrame()
        advanced_frame.setProperty("class", "card")
        advanced_frame.setMinimumHeight(180)  # Set minimum height
        advanced_layout = QVBoxLayout(advanced_frame)
        advanced_layout.setSpacing(12)
        advanced_layout.setContentsMargins(16, 16, 16, 16)  # Add margins
        
        advanced_label = QLabel("Advanced Options")
        advanced_label.setProperty("class", "subtitle")
        advanced_layout.addWidget(advanced_label)

        # Retry options
        retry_layout = QHBoxLayout()
        retry_label = QLabel("Retry Failed Downloads:")
        retry_label.setMinimumWidth(150)
        
        self.retry_spin = QSpinBox()
        self.retry_spin.setMinimum(0)
        self.retry_spin.setMaximum(10)
        self.retry_spin.setValue(3)
        self.retry_spin.setSuffix(" times")
        self.retry_spin.setMinimumWidth(120)
        
        retry_layout.addWidget(retry_label)
        retry_layout.addWidget(self.retry_spin)
        retry_layout.addStretch()
        
        advanced_layout.addLayout(retry_layout)

        # Timeout settings
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Download Timeout:")
        timeout_label.setMinimumWidth(150)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setMinimum(10)
        self.timeout_spin.setMaximum(300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        self.timeout_spin.setMinimumWidth(120)
        
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        
        advanced_layout.addLayout(timeout_layout)
        
        # Overwrite existing files
        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        self.overwrite_checkbox.setChecked(False)
        advanced_layout.addWidget(self.overwrite_checkbox)
        
        parent_layout.addWidget(advanced_frame)
    
    def _browse_location(self):
        """Browse for download location."""
        current_path = self.location_input.text() or os.path.abspath("downloads")
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Download Folder", 
            current_path
        )
        if folder:
            self.location_input.setText(folder)
    
    def _update_speed_label(self, value):
        """Update speed label based on slider value."""
        labels = {
            1: "Very Slow", 2: "Slow", 3: "Below Normal", 4: "Below Normal",
            5: "Normal", 6: "Above Normal", 7: "Above Normal", 8: "Fast",
            9: "Very Fast", 10: "Maximum"
        }
        self.speed_value.setText(labels.get(value, "Normal"))
    
    def _update_speed_from_threads(self, threads):
        """Update speed slider based on thread count."""
        # Map thread count to speed slider value
        speed_value = min(10, max(1, threads // 2))
        self.speed_slider.setValue(speed_value)
    
    def get_options(self) -> Dict[str, Any]:
        """Get all download options."""
        return {
            "download_location": self.location_input.text(),
            "max_workers": self.concurrent_spin.value(),
            "retry_count": self.retry_spin.value(),
            "timeout": self.timeout_spin.value(),
            "overwrite_existing": self.overwrite_checkbox.isChecked()
        }


class DownloadWidget(QWidget):
    """Main download widget combining format selection and options."""
    
    download_requested = pyqtSignal(dict)  # download configuration
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the download widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Download Configuration")
        title.setProperty("class", "title")
        font = title.font()
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        
        # Download status
        self.status_label = QLabel("Ready to download")
        self.status_label.setProperty("class", "caption")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Format selection
        self.format_widget = FormatSelectionWidget()
        layout.addWidget(self.format_widget)
        
        # Download options
        self.options_widget = DownloadOptionsWidget()
        layout.addWidget(self.options_widget)
        
        # Action buttons
        self._setup_action_buttons(layout)
        
        layout.addStretch()
    
    def _setup_action_buttons(self, parent_layout):
        """Set up action buttons."""
        buttons_frame = QFrame()
        buttons_frame.setProperty("class", "card")
        buttons_layout = QHBoxLayout(buttons_frame)
        
        # Start download button
        self.start_button = QPushButton("Start Download")
        self.start_button.setMinimumHeight(48)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self._on_start_download)
        
        # Cancel/Reset button
        self.cancel_button = QPushButton("Reset Settings")
        self.cancel_button.setProperty("class", "secondary")
        self.cancel_button.setMinimumHeight(48)
        self.cancel_button.clicked.connect(self._on_reset_settings)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.start_button)
        
        parent_layout.addWidget(buttons_frame)
    
    def _on_start_download(self):
        """Handle start download button click."""
        config = self.get_download_config()
        self.download_requested.emit(config)
    
    def _on_reset_settings(self):
        """Reset all settings to defaults."""
        # Reset format to images
        self.format_widget.images_radio.setChecked(True)
        
        # Reset options
        self.options_widget.location_input.setText(os.path.abspath("downloads"))
        self.options_widget.concurrent_spin.setValue(5)
        self.options_widget.retry_spin.setValue(3)
        self.options_widget.timeout_spin.setValue(30)
        self.options_widget.overwrite_checkbox.setChecked(False)
        
        self.set_status("Settings reset to defaults", "info")
    
    def get_download_config(self) -> Dict[str, Any]:
        """Get complete download configuration."""
        config = self.options_widget.get_options()
        config.update({
            "format": self.format_widget.get_format(),
            "delete_images": self.format_widget.should_delete_images()
        })
        return config
    
    def enable_download(self, enabled: bool):
        """Enable or disable download functionality."""
        self.start_button.setEnabled(enabled)
        if enabled:
            self.set_status("Ready to download", "success")
        else:
            self.set_status("Select chapters to enable download", "info")
    
    def set_status(self, message: str, status_type: str = "info"):
        """Set status message."""
        self.status_label.setText(message)
        self.status_label.setProperty("class", f"status-{status_type}")
        style = self.status_label.style()
        if style:
            style.unpolish(self.status_label)
            style.polish(self.status_label)
    
    def set_downloading(self, downloading: bool):
        """Set downloading state."""
        if downloading:
            self.start_button.setText("Downloading...")
            self.start_button.setEnabled(False)
            self.set_status("Download in progress...", "info")
        else:
            self.start_button.setText("Start Download")
            self.start_button.setEnabled(True)
            self.set_status("Ready to download", "success")