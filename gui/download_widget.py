"""
Modern download widget for format selection and download configuration.
"""

import os
from typing import Dict, Any
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QRadioButton, QCheckBox, QSpinBox, QLabel,
                             QPushButton, QFrame, QFileDialog, QLineEdit,
                             QButtonGroup, QSlider, QComboBox, QFormLayout, QScrollArea)
from PyQt6.QtGui import QFont

# Import ConfigManager
from .config import ConfigManager


class FormatSelectionWidget(QWidget):
    """Widget for selecting download format."""
    
    format_changed = pyqtSignal(str)  # format name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
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
        # Get default format from config
        default_format = self.config_manager.get("format", "images")
        self.images_radio.setChecked(default_format == "images")
        self.images_desc = QLabel("Save as individual image files (JPG/PNG)")
        self.images_desc.setProperty("class", "caption")
        self.images_desc.setStyleSheet("color: #94A3B8; margin-left: 20px;")
        
        # PDF format
        self.pdf_radio = QRadioButton("PDF")
        self.pdf_radio.setChecked(default_format == "pdf")
        self.pdf_desc = QLabel("Convert to PDF document for easy reading")
        self.pdf_desc.setProperty("class", "caption")
        self.pdf_desc.setStyleSheet("color: #94A3B8; margin-left: 20px;")
        
        # CBZ format
        self.cbz_radio = QRadioButton("CBZ")
        self.cbz_radio.setChecked(default_format == "cbz")
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
        self.images_radio.toggled.connect(self._save_config)
        self.pdf_radio.toggled.connect(self._on_format_changed)
        self.pdf_radio.toggled.connect(self._save_config)
        self.cbz_radio.toggled.connect(self._on_format_changed)
        self.cbz_radio.toggled.connect(self._save_config)
        self.delete_images_checkbox.stateChanged.connect(self._save_config)
    
    def _setup_format_options(self, parent_layout):
        """Set up format-specific options."""
        # Delete images option (for PDF/CBZ)
        self.delete_images_frame = QFrame()
        self.delete_images_frame.setProperty("class", "card")
        delete_layout = QVBoxLayout(self.delete_images_frame)
        
        self.delete_images_checkbox = QCheckBox("Delete images after conversion")
        # Get default delete images setting from config
        default_delete_images = self.config_manager.get("delete_images", False)
        self.delete_images_checkbox.setChecked(default_delete_images)
        
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
    
    def _save_config(self):
        """Save current configuration to ConfigManager."""
        config = {
            "format": self.get_format(),
            "delete_images": self.should_delete_images()
        }
        self.config_manager.set_all(config)
    
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
        self.config_manager = ConfigManager()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the download options UI from scratch."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # --- Title ---
        title = QLabel("Download Options")
        title.setProperty("class", "title")
        font = title.font()
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        main_layout.addWidget(title)

        # --- Download Location Group ---
        location_group = QGroupBox("Download Location")
        location_layout = QVBoxLayout(location_group)
        
        # Get default download location from config
        default_download_location = self.config_manager.get("download_location", os.path.abspath("downloads"))
        self.location_input = QLineEdit(default_download_location)
        self.location_input.setMinimumHeight(36)
        self.location_input.setPlaceholderText("Select download folder...")
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setProperty("class", "secondary")
        self.browse_button.clicked.connect(self._browse_location)

        location_input_layout = QHBoxLayout()
        location_input_layout.addWidget(self.location_input, 1)
        location_input_layout.addWidget(self.browse_button)
        location_layout.addLayout(location_input_layout)
        
        main_layout.addWidget(location_group)

        # --- Performance Group ---
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QFormLayout(performance_group)
        performance_layout.setSpacing(12)
        performance_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 20)
        # Get default max workers from config
        default_max_workers = self.config_manager.get("max_workers", 5)
        self.concurrent_spin.setValue(default_max_workers)
        self.concurrent_spin.setSuffix(" threads")
        self.concurrent_spin.setMinimumWidth(100) # Make the spinbox wider
        performance_layout.addRow("Concurrent Downloads:", self.concurrent_spin)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_slider.setMinimumWidth(200) # Make the slider wider
        self.speed_value = QLabel("Normal")
        self.speed_value.setMinimumWidth(80) # Ensure the speed label has enough space
        self.speed_slider.valueChanged.connect(self._update_speed_label)
        self.concurrent_spin.valueChanged.connect(self._update_speed_from_threads)
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_slider, 1) # Allow slider to expand
        speed_layout.addWidget(self.speed_value)
        performance_layout.addRow("Expected Speed:", speed_layout)
        
        main_layout.addWidget(performance_group)
        
       # --- Advanced Group ---
        advanced_group = QGroupBox("Advanced Options")
        advanced_group.setMinimumHeight(120)
        advanced_group.setMaximumHeight(150)  # Set a maximum height to trigger scrolling

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)  # Remove the frame border

        # Create the content widget that will be scrollable
        content_widget = QWidget()
        advanced_layout = QVBoxLayout(content_widget)
        advanced_layout.setSpacing(15)
        advanced_layout.setContentsMargins(15, 10, 15, 15)

        # Retry section
        retry_widget = QWidget()
        retry_layout = QHBoxLayout(retry_widget)
        retry_layout.setContentsMargins(0, 0, 0, 0)
        retry_label = QLabel("Retry Failed Downloads:")
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        # Get default retry count from config
        default_retry_count = self.config_manager.get("retry_count", 3)
        self.retry_spin.setValue(default_retry_count)
        self.retry_spin.setSuffix(" times")
        self.retry_spin.setFixedWidth(120)
        retry_layout.addWidget(retry_label)
        retry_layout.addStretch()
        retry_layout.addWidget(self.retry_spin)
        advanced_layout.addWidget(retry_widget)

        # Timeout section
        timeout_widget = QWidget()
        timeout_layout = QHBoxLayout(timeout_widget)
        timeout_layout.setContentsMargins(0, 0, 0, 0)
        timeout_label = QLabel("Download Timeout:")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        # Get default timeout from config
        default_timeout = self.config_manager.get("timeout", 30)
        self.timeout_spin.setValue(default_timeout)
        self.timeout_spin.setSuffix(" seconds")
        self.timeout_spin.setFixedWidth(120)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addStretch()
        timeout_layout.addWidget(self.timeout_spin)
        advanced_layout.addWidget(timeout_widget)

        # Checkbox section
        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        # Get default overwrite setting from config
        default_overwrite = self.config_manager.get("overwrite_existing", False)
        self.overwrite_checkbox.setChecked(default_overwrite)
        advanced_layout.addWidget(self.overwrite_checkbox)

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Add the scroll area to the group box
        group_layout = QVBoxLayout(advanced_group)
        group_layout.setContentsMargins(5, 15, 5, 5)
        group_layout.addWidget(scroll_area)

        main_layout.addWidget(advanced_group)
        main_layout.addStretch()

    def _browse_location(self):
        """Browse for download location."""
        current_path = self.location_input.text() or os.path.abspath("downloads")
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", current_path)
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
        self.config_manager = ConfigManager()
        self._setup_ui()
        self._load_config()
    
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
        self.format_widget.format_changed.connect(self._save_config)
        layout.addWidget(self.format_widget)
        
        # Download options
        self.options_widget = DownloadOptionsWidget()
        # Connect signals to save config when options change
        self.options_widget.location_input.textChanged.connect(self._save_config)
        self.options_widget.concurrent_spin.valueChanged.connect(self._save_config)
        self.options_widget.retry_spin.valueChanged.connect(self._save_config)
        self.options_widget.timeout_spin.valueChanged.connect(self._save_config)
        self.options_widget.overwrite_checkbox.stateChanged.connect(self._save_config)
        layout.addWidget(self.options_widget)
        
        # Action buttons
        self._setup_action_buttons(layout)
        
        layout.addStretch()
    
    def _load_config(self):
        """Load configuration from ConfigManager."""
        config = self.config_manager.get_all()
        
        # Set format
        format_type = config.get("format", "images")
        if format_type == "pdf":
            self.format_widget.pdf_radio.setChecked(True)
        elif format_type == "cbz":
            self.format_widget.cbz_radio.setChecked(True)
        else:
            self.format_widget.images_radio.setChecked(True)
        
        # Set download options
        self.options_widget.location_input.setText(config.get("download_location", os.path.abspath("downloads")))
        self.options_widget.concurrent_spin.setValue(config.get("max_workers", 5))
        self.options_widget.retry_spin.setValue(config.get("retry_count", 3))
        self.options_widget.timeout_spin.setValue(config.get("timeout", 30))
        self.options_widget.overwrite_checkbox.setChecked(config.get("overwrite_existing", False))
        
        # Set delete images option
        self.format_widget.delete_images_checkbox.setChecked(config.get("delete_images", False))
    
    def _save_config(self):
        """Save current configuration to ConfigManager."""
        config = self.get_download_config()
        self.config_manager.set_all(config)
    
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
        
        # Save the reset configuration
        self._save_config()
        
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