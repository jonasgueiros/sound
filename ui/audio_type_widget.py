"""
Widget for controlling a specific audio type (game, movie, music, chat, microphone)
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QSlider, QGroupBox, QPushButton, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.equalizer_widget import EqualizerWidget
import json
import os

class AudioTypeWidget(QWidget):
    """Widget for controlling a specific audio type"""
    
    # Signal emitted when equalizer settings change
    equalizer_changed = pyqtSignal(str, dict)  # audio_type, settings
    
    def __init__(self, audio_type, routing_system):
        super().__init__()
        self.audio_type = audio_type
        self.routing_system = routing_system
        self.processors = {}
        self.active_processors = []
        self.equalizer_widget = None
        
        # Set up UI
        self.init_ui()
        
        # Load settings
        self.load_settings()

    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Category title
        title_label = QLabel(f"{self.get_category_display_name()} Audio")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        main_layout.addWidget(title_label)
        
        # Equalizer section
        eq_group = QGroupBox("Equalizer")
        eq_layout = QVBoxLayout(eq_group)
        
        # Create equalizer widget for this category
        self.equalizer_widget = EqualizerWidget()
        self.equalizer_widget.settings_changed.connect(self.on_equalizer_changed)
        eq_layout.addWidget(self.equalizer_widget)
        
        main_layout.addWidget(eq_group)
        
        # Add stretch to push content to top
        main_layout.addStretch()

    def get_category_display_name(self):
        """Get display name for the audio category"""
        display_names = {
            'game': 'Game',
            'others': 'Others',
            'system': 'System', 
            'chat': 'Chat',
            'microphone': 'Microphone'
        }
        return display_names.get(self.audio_type, self.audio_type.title())

    def set_processors(self, processors):
        """Set available audio processors"""
        self.processors = processors
        
        # Set equalizer processor for this widget
        if self.equalizer_widget and 'equalizer' in processors:
            self.equalizer_widget.set_equalizer(processors['equalizer'])

    def load_settings(self):
        """Load equalizer settings for this category from config"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                eq_settings = config.get('equalizer_settings', {})
                active_profile = eq_settings.get('active_profile', 'Default')
                profiles = eq_settings.get('profiles', {})
                
                if active_profile in profiles and self.audio_type in profiles[active_profile]:
                    category_settings = profiles[active_profile][self.audio_type]
                    if self.equalizer_widget:
                        self.equalizer_widget.load_settings(category_settings)
        except Exception as e:
            print(f"Error loading settings for {self.audio_type}: {e}")

    def on_equalizer_changed(self):
        """Handle equalizer settings change"""
        if not self.equalizer_widget:
            return
            
        settings = self.equalizer_widget.get_settings()
        
        # Save to config
        self.save_settings(settings)
        
        # Apply to audio processing
        self.apply_equalizer_processing(settings)
        
        # Emit signal
        self.equalizer_changed.emit(self.audio_type, settings)

    def save_settings(self, settings):
        """Save equalizer settings to config file"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            
            # Load current config
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            # Ensure structure exists
            if 'equalizer_settings' not in config:
                config['equalizer_settings'] = {'bands': 10, 'profiles': {}, 'active_profile': 'Default'}
            
            eq_settings = config['equalizer_settings']
            active_profile = eq_settings.get('active_profile', 'Default')
            
            if 'profiles' not in eq_settings:
                eq_settings['profiles'] = {}
            
            if active_profile not in eq_settings['profiles']:
                eq_settings['profiles'][active_profile] = {}
            
            # Save category settings
            eq_settings['profiles'][active_profile][self.audio_type] = settings
            
            # Write back to file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Error saving settings for {self.audio_type}: {e}")

    def apply_equalizer_processing(self, settings):
        """Apply or remove equalizer processing based on settings"""
        if not self.routing_system or 'equalizer' not in self.processors:
            return
            
        equalizer = self.processors['equalizer']
        
        if settings.get('enabled', False):
            # Configure equalizer with current settings using per-band API
            gains = settings.get('gains', [0.0] * getattr(equalizer, 'bands', 10))
            band_count = min(getattr(equalizer, 'bands', 10), len(gains))
            for i in range(band_count):
                equalizer.set_gain(i, gains[i])
            
            # Apply to this audio type
            self.routing_system.apply_audio_processing(self.audio_type, equalizer)
        else:
            # Remove equalizer processing
            self.routing_system.remove_audio_processing(self.audio_type, equalizer)

    def update_device_list(self):
        """Device selection is managed in Settings; no-op here"""
        pass
        
    def on_device_changed(self, index):
        """Device selection removed from this tab"""
        pass
        
    def on_volume_changed(self, value):
        """Volume control removed from this tab"""
        pass
    
    def load_equalizer_settings(self):
        """Reload equalizer settings from config (called when profile changes)"""
        self.load_settings()
    
    def update_equalizer_bands(self, bands):
        """Update equalizer band count (called when bands setting changes)"""
        # Update processor bands so frequencies/gains reflect change
        equalizer = self.processors.get('equalizer') if hasattr(self, 'processors') else None
        if equalizer:
            try:
                equalizer.set_bands(bands)
            except Exception:
                pass
        if self.equalizer_widget:
            # Update the equalizer widget with new band count
            self.equalizer_widget.rebuild_bands_ui(bands)
            # Reload settings to apply to new bands
            self.load_settings()
    
    def save_current_profile(self):
        """Save the current equalizer settings for this category to config"""
        if self.equalizer_widget:
            settings = self.equalizer_widget.get_settings()
            self.save_settings(settings)