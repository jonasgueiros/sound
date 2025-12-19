"""
Configuration window for audio enhancement software
"""
import json
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QCheckBox, QPushButton, QGroupBox,
                             QGridLayout, QMessageBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QColor

class ConfigWindow(QDialog):
    """Configuration window for application settings"""
    
    # Signals
    theme_changed = pyqtSignal(str)
    unified_device_changed = pyqtSignal(bool, object, object)
    
    def __init__(self, routing_system, parent=None):
        super().__init__(parent)
        self.routing_system = routing_system
        self.config_file = "config.json"
        self.config = self.load_config()
        
        self.setWindowTitle("Audio Enhancement Configuration")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Device Configuration Tab
        device_tab = self.create_device_tab()
        tab_widget.addTab(device_tab, "Device Settings")
        
        # Theme Configuration Tab
        theme_tab = self.create_theme_tab()
        tab_widget.addTab(theme_tab, "Appearance")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_settings)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_settings)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_device_tab(self):
        """Create the device configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Device Configuration Group
        unified_group = QGroupBox("Device Configuration")
        unified_layout = QGridLayout()
        
        # Output Device Selection
        unified_layout.addWidget(QLabel("Output Device:"), 0, 0)
        self.output_device_combo = QComboBox()
        self.populate_output_devices()
        unified_layout.addWidget(self.output_device_combo, 0, 1)
        
        # Input Device Selection
        unified_layout.addWidget(QLabel("Input Device:"), 1, 0)
        self.input_device_combo = QComboBox()
        self.populate_input_devices()
        unified_layout.addWidget(self.input_device_combo, 1, 1)
        
        # Refresh Devices Button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        unified_layout.addWidget(refresh_btn, 2, 0, 1, 2)
        
        unified_group.setLayout(unified_layout)
        layout.addWidget(unified_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_theme_tab(self):
        """Create the theme configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Theme Group
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QGridLayout()
        
        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        # Preview area
        preview_label = QLabel("Theme Preview")
        preview_label.setStyleSheet("padding: 20px; border: 1px solid gray; background-color: palette(base);")
        theme_layout.addWidget(preview_label, 1, 0, 1, 2)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def populate_output_devices(self):
        """Populate the output device combo box"""
        self.output_device_combo.clear()
        devices = self.routing_system.get_output_devices()
        # devices is a list of dicts: {'index': int, 'name': str, 'type': 'output', ...}
        for device in devices:
            self.output_device_combo.addItem(device['name'], device['index'])
            
    def populate_input_devices(self):
        """Populate the input device combo box"""
        self.input_device_combo.clear()
        devices = self.routing_system.get_input_devices()
        # devices is a list of dicts: {'index': int, 'name': str, 'type': 'input', ...}
        for device in devices:
            self.input_device_combo.addItem(device['name'], device['index'])
            
    def refresh_devices(self):
        """Refresh the device lists"""
        self.routing_system.refresh_devices()
        self.populate_output_devices()
        self.populate_input_devices()
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "theme": "Light",
            "unified_device_mode": False,
            "unified_output_device": None,
            "unified_input_device": None
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_config.update(config)
                    return default_config
            except Exception as e:
                print(f"Error loading config: {e}")
                
        return default_config
        
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {e}")
            
    def load_settings(self):
        """Load settings into the UI"""
        # Theme settings
        theme_index = self.theme_combo.findText(self.config.get("theme", "Light"))
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
            
        # Device settings (always unified mode)
        
        # Set device selections if they exist
        output_device = self.config.get("unified_output_device")
        if output_device is not None:
            output_index = self.output_device_combo.findData(output_device)
            if output_index >= 0:
                self.output_device_combo.setCurrentIndex(output_index)
                
        input_device = self.config.get("unified_input_device")
        if input_device is not None:
            input_index = self.input_device_combo.findData(input_device)
            if input_index >= 0:
                self.input_device_combo.setCurrentIndex(input_index)
                
    def apply_settings(self):
        """Apply the current settings"""
        # Update config
        self.config["theme"] = self.theme_combo.currentText()
        self.config["unified_device_mode"] = True  # Always use unified mode
        
        # Always save device selections
        self.config["unified_output_device"] = self.output_device_combo.currentData()
        self.config["unified_input_device"] = self.input_device_combo.currentData()
            
        # Apply to routing system
        self.routing_system.set_unified_device_mode(
            self.config["unified_device_mode"],
            self.config["unified_output_device"],
            self.config["unified_input_device"]
        )
        
        # Emit signals
        self.theme_changed.emit(self.config["theme"])
        self.unified_device_changed.emit(
            self.config["unified_device_mode"],
            self.config["unified_output_device"],
            self.config["unified_input_device"]
        )
        
        # Save config
        self.save_config()
        
    def accept_settings(self):
        """Apply settings and close the dialog"""
        self.apply_settings()
        self.accept()
        
    def get_theme_stylesheet(self, theme_name):
        """Get stylesheet for the specified theme"""
        if theme_name == "Dark":
            return """
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QComboBox {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 3px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 1px solid #555555;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
            }
            QTabBar::tab {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                border-bottom: 1px solid #2b2b2b;
            }
            """
        else:  # Light theme
            return """
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 3px;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            """