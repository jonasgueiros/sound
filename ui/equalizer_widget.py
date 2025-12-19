"""
Equalizer widget for audio enhancement with real-time frequency response visualization
"""
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QSlider, QGroupBox, QPushButton, QComboBox,
                            QCheckBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor

class FrequencyResponseView(QFrame):
    """Widget for displaying the frequency response curve"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.gains = [0] * 10
        self.frequencies = []
        
    def update_response(self, gains, frequencies=None):
        """Update the frequency response curve"""
        self.gains = gains
        if frequencies:
            self.frequencies = frequencies
        self.update()
        
    def paintEvent(self, event):
        """Draw the frequency response curve"""
        super().paintEvent(event)
        if not self.gains:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw frame
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        # Draw grid
        pen = QPen(QColor(100, 100, 100, 50))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        # Horizontal grid lines (gain levels)
        h_steps = 6
        for i in range(1, h_steps):
            y = int(self.height() * i / h_steps)
            painter.drawLine(0, y, self.width(), y)
            
        # Vertical grid lines (frequency decades)
        v_steps = 4
        for i in range(1, v_steps):
            x = int(self.width() * i / v_steps)
            painter.drawLine(x, 0, x, self.height())
            
        # Draw frequency response curve
        pen = QPen(QColor(0, 120, 255))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Calculate points
        points = []
        width = self.width() - 1
        height = self.height() - 1
        mid_height = height / 2
        scale = height / 24  # Scale for ±12 dB range
        
        for i, gain in enumerate(self.gains):
            x = int(width * i / (len(self.gains) - 1))
            y = int(mid_height - (gain * scale))
            points.append((x, y))
            
        # Draw curve
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            painter.drawLine(x1, y1, x2, y2)

class EqualizerWidget(QWidget):
    """Widget for controlling the equalizer with frequency response visualization"""
    
    # Signal emitted when equalizer settings change 
    settings_changed = pyqtSignal()
    
    def __init__(self, equalizer_processor=None):
        super().__init__()
        self.equalizer = equalizer_processor
        
        # Initialize state
        self.current_bands = 10
        self.sample_rate = 48000
        
        # Define logarithmically spaced frequency bands
        self.frequencies = self._calculate_frequencies()
        self.frequency_labels = []  # Added missing attribute
        self.band_labels = []
        self.band_sliders = []
        self.freq_response_curve = None
        self.freq_sliders = []  # Added missing attribute
        self.gain_labels = []   # Added missing attribute
        
        # Define presets with reasonable gain values (-12 to +12 dB range)
        # Enhanced presets with additional controls
        self.presets = {
            "Flat": [0] * 10,
            "Bass Boost": [12, 9, 6, 3, 0, 0, 0, 0, 0, 0],
            "Bass Cut": [-12, -9, -6, -3, 0, 0, 0, 0, 0, 0],
            "Treble Boost": [0, 0, 0, 0, 0, 0, 3, 6, 9, 12],
            "Treble Cut": [0, 0, 0, 0, 0, 0, -3, -6, -9, -12],
            "Voice Enhance": [-6, -3, 0, 6, 9, 9, 6, 0, -3, -6],
            "Voice Cut": [6, 3, 0, -6, -9, -9, -6, 0, 3, 6],
            "Rock": [6, 4, 2, 0, -2, -2, 0, 2, 4, 6],
            "Pop": [-3, 0, 3, 6, 3, -3, -3, 0, 3, 6],
            "Classical": [4, 4, 0, 0, 0, 0, -2, -2, -2, -4],
            "Jazz": [2, 4, 3, 2, -1, -2, 0, 1, 2, 3],
            "Electronic": [4, 6, 3, 0, -2, 0, 2, 4, 6, 6],
            "Sub Bass": [15, 9, 3, 0, 0, 0, 0, 0, 0, 0],
            "Acoustic": [3, 2, 0, 0, 0, 2, 4, 5, 5, 3],
            "Vocal Clarity": [-3, -2, 0, 4, 6, 6, 4, 2, -2, -3]
        }
        
        # Initialize the Rust-based equalizer
        self.eq_processor = None
        try:
            from native_dsp import Equalizer
            self.eq_processor = Equalizer(float(self.sample_rate))
        except ImportError:
            print("Warning: native_dsp module not available, falling back to Python implementation")
        except Exception as e:
            print(f"Error initializing native_dsp equalizer: {e}, falling back to Python implementation")

        self.init_ui()
        
    def _calculate_frequencies(self):
        """Calculate logarithmically spaced frequency bands"""
        # Standard frequencies for 10-band EQ
        return [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    
    def _format_frequency(self, freq):
        """Format frequency value for display"""
        if freq >= 1000:
            if freq >= 10000:
                return f"{freq/1000:.0f}k"  # No decimal for 10k+
            return f"{freq/1000:.1f}k"  # One decimal under 10k
        return f"{int(freq)}"
        
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 5)  # Reduced bottom margin
        layout.setSpacing(5)  # Reduced spacing between elements
        
        # Equalizer controls group
        eq_group = QGroupBox(f"{self.current_bands}-Band Equalizer")
        eq_layout = QVBoxLayout()
        
        # Top controls layout with enable, presets, and reset
        top_controls = QHBoxLayout()
        
        # Enable/Disable checkbox
        self.enable_checkbox = QCheckBox("Enable Equalizer")
        self.enable_checkbox.setChecked(True)
        self.enable_checkbox.toggled.connect(self.on_enable_toggled)
        self.enable_checkbox.setToolTip("Enable or disable the equalizer effect")
        top_controls.addWidget(self.enable_checkbox)
        
        top_controls.addStretch()
        
        # Preset selection with label
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(sorted(self.presets.keys()))
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        self.preset_combo.setMinimumWidth(120)
        preset_layout.addWidget(self.preset_combo)
        top_controls.addLayout(preset_layout)
        
        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_equalizer)
        reset_btn.setToolTip("Reset all bands to 0 dB")
        top_controls.addWidget(reset_btn)
        
        eq_layout.addLayout(top_controls)
        
        # Quick control buttons
        quick_controls = QHBoxLayout()
        
        # Bass controls
        bass_group = QGroupBox("Bass")
        bass_layout = QHBoxLayout()
        bass_boost = QPushButton("+")
        bass_boost.setToolTip("Boost bass frequencies")
        bass_boost.clicked.connect(lambda: self.quick_adjust("bass", +3))
        bass_cut = QPushButton("-")
        bass_cut.setToolTip("Cut bass frequencies")
        bass_cut.clicked.connect(lambda: self.quick_adjust("bass", -3))
        bass_layout.addWidget(bass_cut)
        bass_layout.addWidget(bass_boost)
        bass_group.setLayout(bass_layout)
        quick_controls.addWidget(bass_group)
        
        # Voice controls
        voice_group = QGroupBox("Voice")
        voice_layout = QHBoxLayout()
        voice_boost = QPushButton("+")
        voice_boost.setToolTip("Enhance vocal frequencies")
        voice_boost.clicked.connect(lambda: self.quick_adjust("voice", +3))
        voice_cut = QPushButton("-")
        voice_cut.setToolTip("Reduce vocal frequencies")
        voice_cut.clicked.connect(lambda: self.quick_adjust("voice", -3))
        voice_layout.addWidget(voice_cut)
        voice_layout.addWidget(voice_boost)
        voice_group.setLayout(voice_layout)
        quick_controls.addWidget(voice_group)
        
        # Treble controls
        treble_group = QGroupBox("Treble")
        treble_layout = QHBoxLayout()
        treble_boost = QPushButton("+")
        treble_boost.setToolTip("Boost high frequencies")
        treble_boost.clicked.connect(lambda: self.quick_adjust("treble", +3))
        treble_cut = QPushButton("-")
        treble_cut.setToolTip("Cut high frequencies")
        treble_cut.clicked.connect(lambda: self.quick_adjust("treble", -3))
        treble_layout.addWidget(treble_cut)
        treble_layout.addWidget(treble_boost)
        treble_group.setLayout(treble_layout)
        quick_controls.addWidget(treble_group)
        
        eq_layout.addLayout(quick_controls)
        
        # Add frequency response visualization
        self.response_view = FrequencyResponseView(self)
        self.response_view.setMinimumHeight(100)
        eq_layout.addWidget(self.response_view)
        
        # Frequency bands grid
        bands_grid = QGridLayout()
        bands_grid.setSpacing(5)
        # Set smaller margins to prevent cutoff
        bands_grid.setContentsMargins(5, 5, 5, 15)  # Added bottom margin
        
        self.freq_sliders = []
        self.gain_labels = []
        
        # Add +12dB label at the top
        top_db_label = QLabel("+12 dB")
        top_db_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bands_grid.addWidget(top_db_label, 0, 0)
        
        # Add frequency labels with proper spacing
        for i, freq in enumerate(self.frequencies):
            freq_label = QLabel(self._format_frequency(freq))
            freq_label.setAlignment(Qt.AlignCenter)
            freq_label.setMinimumHeight(25)  # Ensure enough height for the label
            freq_label.setContentsMargins(0, 5, 0, 5)  # Add vertical padding
            bands_grid.addWidget(freq_label, 3, i)  # Moved to bottom
            
        # Add -12dB label at the bottom
        bottom_db_label = QLabel("-12 dB")
        bottom_db_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bands_grid.addWidget(bottom_db_label, 2, 0)
        
        # Add sliders
        for i in range(len(self.frequencies)):
            slider = QSlider(Qt.Vertical)  # Changed to Vertical
            slider.setRange(-12, 12)
            slider.setValue(0)
            slider.setFixedHeight(130)  # Reduced height from 150 to 130
            slider.valueChanged.connect(lambda val, idx=i: self._on_single_slider_change(idx, val))
            slider.setToolTip("0 dB")  # Initial tooltip
            self.freq_sliders.append(slider)
            bands_grid.addWidget(slider, 1, i)
            
            # Gain value label
            gain_label = QLabel("0 dB")
            gain_label.setAlignment(Qt.AlignCenter)
            self.gain_labels.append(gain_label)
            bands_grid.addWidget(gain_label, 2, i)
        
        eq_layout.addLayout(bands_grid)
        eq_group.setLayout(eq_layout)
        layout.addWidget(eq_group)
        
        # Advanced settings group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QGridLayout()
        
        # Sample rate display
        advanced_layout.addWidget(QLabel("Sample Rate:"), 0, 0)
        self.sample_rate_label = QLabel(f"{self.sample_rate} Hz")
        advanced_layout.addWidget(self.sample_rate_label, 0, 1)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Set minimum width for the widget
        self.setMinimumWidth(max(600, len(self.frequencies) * 60))  # Scale with number of bands
        
    def on_enable_toggled(self, enabled):
        """Handle enable/disable checkbox toggle"""
        if self.equalizer:
            self.equalizer.set_enabled(enabled)
        self.settings_changed.emit()
            
    def on_preset_changed(self, preset):
        """Handle preset selection"""
        gains = self.presets.get(preset, [0] * 10)
        for i, (slider, gain, label) in enumerate(zip(self.freq_sliders, gains, self.gain_labels)):
            slider.setValue(gain)
            label.setText(f"{gain:+d} dB")
            
        if self.equalizer:
            # Update each band individually
            for i, gain in enumerate(gains):
                self.equalizer.set_gain(i, gain)
        elif hasattr(self, 'eq_processor') and self.eq_processor is not None:
            self.eq_processor.set_gains([float(g) for g in gains])
            
        # Update visualization
        if self.response_view:
            self.response_view.update_response(gains)
            
        self.settings_changed.emit()
            
    def _on_single_slider_change(self, slider_idx, value):
        """Handle individual slider value change
        
        Args:
            slider_idx (int): Index of the slider that changed
            value (int): New value of the slider
        """
        # Update gain label
        gain_text = f"{value:+d} dB"
        self.gain_labels[slider_idx].setText(gain_text)
        
        # Update tooltip
        freq = self.frequencies[slider_idx]
        freq_text = f"{freq}Hz" if freq < 1000 else f"{freq/1000:.1f}kHz"
        self.freq_sliders[slider_idx].setToolTip(f"{freq_text}: {gain_text}")
        
        # Update gains and process
        self._update_equalizer()
        
    def _update_equalizer(self):
        """Update equalizer with current gain values"""
        gains = [slider.value() for slider in self.freq_sliders]
        
        # Update the equalizer
        if self.eq_processor is not None:
            self.eq_processor.set_gains([float(g) for g in gains])
        elif self.equalizer:
            # Update each band individually if using the Python equalizer
            for i, gain in enumerate(gains):
                self.equalizer.set_gain(i, gain)
            
        # Update frequency response visualization
        if self.response_view:
            self.response_view.update_response(gains)
            
        self.settings_changed.emit()
        if self.eq_processor is not None:
            self.eq_processor.set_gains([float(g) for g in gains])
            
        # Update frequency response visualization
        if self.response_view:
            self.response_view.update_response(gains)
            
        self.settings_changed.emit()
            
    def reset_equalizer(self):
        """Reset all sliders to 0"""
        for slider, label in zip(self.freq_sliders, self.gain_labels):
            slider.setValue(0)
            label.setText("0 dB")
            
        if hasattr(self, 'eq_processor') and self.eq_processor is not None:
            self.eq_processor.reset()
        elif self.equalizer:
            # Reset each band individually
            for i in range(len(self.freq_sliders)):
                self.equalizer.set_gain(i, 0)
        self.settings_changed.emit()
        
    def quick_adjust(self, band_type, amount):
        """Quick adjustment for bass, voice, or treble frequencies
        
        Args:
            band_type (str): 'bass', 'voice', or 'treble'
            amount (int): Amount to adjust by (-3 or +3 typically)
        """
        if band_type == "bass":
            # Adjust the first 3 bands (low frequencies)
            for i in range(3):
                current = self.freq_sliders[i].value()
                self.freq_sliders[i].setValue(max(-12, min(12, current + amount)))
        elif band_type == "voice":
            # Adjust the middle 4 bands (mid frequencies)
            for i in range(3, 7):
                current = self.freq_sliders[i].value()
                self.freq_sliders[i].setValue(max(-12, min(12, current + amount)))
        elif band_type == "treble":
            # Adjust the last 3 bands (high frequencies)
            for i in range(7, 10):
                current = self.freq_sliders[i].value()
                self.freq_sliders[i].setValue(max(-12, min(12, current + amount)))
        
    def clear_layout(self, layout):
        """Recursively clear a QLayout of all child widgets and layouts"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
        
    def set_equalizer(self, equalizer_processor):
        """Set the equalizer processor"""
        self.equalizer = equalizer_processor
        if self.equalizer:
            self.sample_rate_label.setText(f"{self.equalizer.sample_rate} Hz")
            self.current_bands = self.equalizer.bands
            # Update UI to match current equalizer state
            self.update_ui_from_equalizer()
    
    def update_ui_from_equalizer(self):
        """Update UI sliders to match equalizer gains"""
        if not self.equalizer:
            return
            
        for i, gain in enumerate(self.equalizer.gains):
            if i < len(self.band_sliders):
                self.band_sliders[i].setValue(int(gain * 10))  # Convert to slider scale
                self.band_labels[i].setText(f"{gain:.1f} dB")
    
    def on_enable_toggled(self, enabled):
        """Handle equalizer enable/disable"""
        if self.equalizer:
            if enabled:
                self.equalizer.enable()
            else:
                self.equalizer.disable()
        
        # Enable/disable all controls
        for slider in self.band_sliders:
            slider.setEnabled(enabled)
        self.preset_combo.setEnabled(enabled)
        # Bands selection is managed in Settings panel
        
        self.settings_changed.emit()
    
    def on_preset_changed(self, preset_name):
        """Handle preset selection"""
        if preset_name in self.presets:
            gains = self.presets[preset_name]
            for i, gain in enumerate(gains):
                if i < len(self.band_sliders):
                    self.band_sliders[i].setValue(int(gain * 10))
                    self.on_band_changed(i, int(gain * 10))
    
    def on_bands_selector_changed(self, bands_str):
        """Handle changes to the number of bands."""
        bands = int(bands_str)
        self.current_bands = bands
        self.eq_group.setTitle(f"{bands}-Band Equalizer")
        self.rebuild_bands_ui(bands)
        self.settings_changed.emit()

    def rebuild_bands_ui(self, bands):
        """Rebuild the UI sliders for the specified number of bands."""
        # Clear existing sliders and labels
        for slider in self.band_sliders:
            slider.deleteLater()
        for label in self.band_labels:
            label.deleteLater()
        for freq_label in self.frequency_labels:
            freq_label.deleteLater()
        self.band_sliders.clear()
        self.band_labels.clear()
        self.frequency_labels.clear()

        # Create new sliders and labels
        for i in range(bands):
            freq_label = QLabel(f"Band {i + 1}")
            self.frequency_labels.append(freq_label)
            self.eq_group.layout().addWidget(freq_label)

            slider = QSlider(Qt.Vertical)
            slider.setRange(-120, 120)
            slider.setValue(0)
            slider.valueChanged.connect(self.on_band_gain_changed)
            self.band_sliders.append(slider)
            self.eq_group.layout().addWidget(slider)

            gain_label = QLabel("0.0 dB")
            self.band_labels.append(gain_label)
            self.eq_group.layout().addWidget(gain_label)

    def create_band_controls(self):
        """Create sliders and labels for each frequency band."""
        # Clear existing controls
        for slider in self.band_sliders:
            slider.deleteLater()
        for label in self.band_labels:
            label.deleteLater()
        for freq_label in self.frequency_labels:
            freq_label.deleteLater()

        self.band_sliders.clear()
        self.band_labels.clear()
        self.frequency_labels.clear()

        # Define frequency ranges for the bands
        frequencies = np.logspace(np.log10(20), np.log10(20000), self.current_bands, dtype=int)

        for i, freq in enumerate(frequencies):
            # Create a vertical layout for each band
            band_layout = QVBoxLayout()

            # Frequency label
            freq_label = QLabel(f"{freq} Hz")
            freq_label.setAlignment(Qt.AlignCenter)
            self.frequency_labels.append(freq_label)
            band_layout.addWidget(freq_label)

            # Slider
            slider = QSlider(Qt.Vertical)
            slider.setRange(-10, 10)  # Gain range in dB
            slider.setValue(0)  # Default to 0 dB
            slider.valueChanged.connect(self.on_slider_change)
            self.band_sliders.append(slider)
            band_layout.addWidget(slider)

            # Gain label
            gain_label = QLabel("0 dB")
            gain_label.setAlignment(Qt.AlignCenter)
            self.band_labels.append(gain_label)
            band_layout.addWidget(gain_label)

            # Add the band layout to the bands container
            self.bands_layout.addLayout(band_layout)

    def on_slider_change(self):
        """Update gain labels and notify processor when sliders change."""
        for slider, label in zip(self.band_sliders, self.band_labels):
            gain = slider.value()
            label.setText(f"{gain} dB")
        self.settings_changed.emit()
    
    def on_band_gain_changed(self):
        """Update gain labels when a band slider is adjusted."""
        for i, slider in enumerate(self.band_sliders):
            gain = slider.value() / 10.0
            self.band_labels[i].setText(f"{gain:.1f} dB")
        self.settings_changed.emit()
    
    def reset_equalizer(self):
        """Reset all bands to 0 dB"""
        for slider in self.band_sliders:
            slider.setValue(0)
        self.preset_combo.setCurrentText("Flat")
    
    def get_settings(self):
        """Get current equalizer settings"""
        settings = {
            'enabled': self.enable_checkbox.isChecked(),
            'preset': self.preset_combo.currentText(),
            'bands': getattr(self, 'current_bands', 10),
            'gains': []
        }
        
        for slider in self.band_sliders:
            settings['gains'].append(slider.value() / 10.0)
        
        return settings
    
    def load_settings(self, settings):
        """Load equalizer settings"""
        if 'enabled' in settings:
            self.enable_checkbox.setChecked(settings['enabled'])
        
        if 'preset' in settings:
            self.preset_combo.setCurrentText(settings['preset'])
        
        if 'bands' in settings:
            self.rebuild_bands_ui(settings['bands'])
        
        if 'gains' in settings:
            for i, gain in enumerate(settings['gains']):
                if i < len(self.band_sliders):
                    self.band_sliders[i].setValue(int(gain * 10))
                    self.on_band_changed(i, int(gain * 10))
    
    def on_band_changed(self, band_index, value):
        """Update processor gain and UI when a band slider changes."""
        try:
            gain_db = value / 10.0
            # Update processor if available
            if self.equalizer:
                try:
                    self.equalizer.set_gain(band_index, gain_db)
                except Exception:
                    pass
            # Update optional dB label if present
            if band_index < len(self.band_labels) and self.band_labels[band_index] is not None:
                try:
                    self.band_labels[band_index].setText(f"{gain_db:.1f} dB")
                except Exception:
                    pass
        finally:
            self.settings_changed.emit()
    
    def on_bass_changed(self, value):
        bass_db = value / 10.0
        self.bass_value.setText(f"{bass_db:.1f} dB")
        self._apply_tone_to_range(bass_db, low_cut=0, high_cut=200)
        self.settings_changed.emit()
    
    def on_voice_changed(self, value):
        voice_db = value / 10.0
        self.voice_value.setText(f"{voice_db:.1f} dB")
        self._apply_tone_to_range(voice_db, low_cut=300, high_cut=3000)
        self.settings_changed.emit()
    
    def on_treble_changed(self, value):
        treble_db = value / 10.0
        self.treble_value.setText(f"{treble_db:.1f} dB")
        self._apply_tone_to_range(treble_db, low_cut=6000, high_cut=99999)
        self.settings_changed.emit()
    
    def on_boost_changed(self, value):
        boost_db = value / 10.0
        self.boost_value.setText(f"{boost_db:.1f} dB")
        if self.equalizer:
            try:
                self.equalizer.set_output_gain(boost_db)
            except Exception:
                pass
        self.settings_changed.emit()
    
    def _apply_tone_to_range(self, db_change, low_cut=0, high_cut=20000):
        # Adjust the band sliders that fall into the frequency range
        if self.equalizer and hasattr(self.equalizer, 'frequencies'):
            freqs = self.equalizer.frequencies
        else:
            freqs = np.logspace(np.log10(20), np.log10(20000), getattr(self, 'current_bands', 10))
        # compute delta in slider units (+/-)
        delta = int(db_change * 10)
        for i, f in enumerate(freqs[:len(self.band_sliders)]):
            if low_cut <= f <= high_cut:
                new_val = max(-120, min(120, self.band_sliders[i].value() + delta))
                # setValue triggers on_band_changed
                self.band_sliders[i].setValue(new_val)
