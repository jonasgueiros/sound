"""
Main window for the Audio Enhancement Software
"""
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                            QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, QSize
from ui.audio_type_widget import AudioTypeWidget
from ui.mixer_widget import MixerWidget
from ui.config_panel import ConfigPanel
from ui.theme_manager import ThemeManager
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont

class MainWindow(QMainWindow):
    """Main application window with tabs for different audio types"""
    def __init__(self, routing_system):
        super().__init__()
        
        # Initialize audio routing system
        self.routing_system = routing_system
        self.processors = {}
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Set up UI
        self.setWindowTitle("Audio Enhancement Software")
        self.setMinimumSize(800, 600)
        # Prefer maximizing to fit screen on startup
        try:
            from PyQt5.QtWidgets import QApplication
            screen_geom = QApplication.primaryScreen().availableGeometry()
            self.resize(int(screen_geom.width() * 0.9), int(screen_geom.height() * 0.9))
        except Exception:
            pass
        
        # Remove top menu bar
        self.menuBar().setVisible(False)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create tab widget (left-side tabs)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.West)
        self.tab_widget.setIconSize(QSize(24, 24))
        self.main_layout.addWidget(self.tab_widget)
        
        # Helper to create emoji icons, flipped when tabs are on the left
        def make_emoji_icon(emoji: str) -> QIcon:
            pix = QPixmap(48, 48)
            pix.fill(Qt.transparent)
            painter = QPainter(pix)
            font = QFont()
            font.setPointSize(28)
            painter.setFont(font)
            painter.drawText(pix.rect(), Qt.AlignCenter, emoji)
            painter.end()
            # Flip horizontally for West-positioned tabs so icons face inward
            if self.tab_widget.tabPosition() == QTabWidget.West:
                from PyQt5.QtGui import QTransform
                t = QTransform()
                t.scale(-1, 1)
                pix = pix.transformed(t)
            return QIcon(pix)
        
        # Add Mixer tab first (emoji icon as tab icon)
        self.mixer_widget = MixerWidget(self.routing_system)
        mixer_index = self.tab_widget.addTab(self.mixer_widget, "")
        self.tab_widget.setTabIcon(mixer_index, make_emoji_icon("🎛️"))
        self.tab_widget.setTabToolTip(mixer_index, "Mixer")
        
        # Add audio type tabs with emoji icons
        self.audio_tabs = {}
        icon_map = {
            'game': ("🎮", "Game"),
            'others': ("📦", "Others"),
            'system': ("🖥️", "System"),
            'chat': ("💬", "Chat"),
            'microphone': ("🎙️", "Mic"),
        }
        for audio_type in ['game', 'others', 'system', 'chat', 'microphone']:
            widget = AudioTypeWidget(audio_type, self.routing_system)
            icon_text, tooltip = icon_map.get(audio_type, (audio_type.title(), audio_type.title()))
            idx = self.tab_widget.addTab(widget, "")
            self.tab_widget.setTabIcon(idx, make_emoji_icon(icon_text))
            self.tab_widget.setTabToolTip(idx, tooltip)
            self.audio_tabs[audio_type] = widget
            # Volume/device controls are removed from these tabs; no signals to connect
            
        # Add Settings tab using embedded ConfigPanel (emoji icon)
        self.settings_panel = ConfigPanel(self.routing_system)
        settings_index = self.tab_widget.addTab(self.settings_panel, "")
        self.tab_widget.setTabIcon(settings_index, make_emoji_icon("⚙️"))
        self.tab_widget.setTabToolTip(settings_index, "Settings")
        # Wire settings signals to apply immediately
        self.settings_panel.theme_changed.connect(self.set_theme)
        self.settings_panel.unified_device_changed.connect(self.on_unified_device_changed)
        # Connect equalizer profile signals
        self.settings_panel.profile_changed.connect(self.on_profile_changed)
        self.settings_panel.save_profile_requested.connect(self.on_save_profile_requested)
            
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Create control buttons
        self.create_control_buttons()

        # System tray setup
        from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
        self.tray_icon = QSystemTrayIcon(make_emoji_icon("🎧"), self)
        self.tray_icon.setToolTip("Audio Enhancement — running")
        self._tray_menu = QMenu()
        self.tray_icon.setContextMenu(self._tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self._build_tray_menu()
        self.tray_icon.show()

    def register_processors(self, processors):
        """Register audio processors with the UI"""
        self.processors = processors
        # Make equalizer available to Settings panel
        try:
            self.settings_panel.equalizer_widget.set_equalizer(processors.get('equalizer'))
        except Exception:
            pass
        
        # Make processors available to all tabs
        for tab in self.audio_tabs.values():
            tab.set_processors(processors)
            
    def set_theme(self, theme_name):
        """Set the application theme"""
        self.theme_manager.set_theme(theme_name)

    def on_unified_device_changed(self, enabled, output_device, input_device):
        """Handle unified device configuration changes"""
        # Update mixer labels to reflect new device routing
        self.mixer_widget.refresh_category_devices()
        # Rebuild tray menu to reflect new device selections
        try:
            self._build_tray_menu()
        except Exception:
            pass
    
    def on_profile_changed(self, profile_name):
        """Handle equalizer profile change"""
        # Notify all audio type widgets to reload their equalizer settings
        for widget in self.audio_tabs.values():
            if hasattr(widget, 'load_equalizer_settings'):
                widget.load_equalizer_settings()
        # Update tray menu checkmark
        try:
            self._build_tray_menu()
        except Exception:
            pass
    
    def on_bands_changed(self, bands):
        """Update all audio tabs when bands setting changes"""
        for audio_type, widget in self.audio_tabs.items():
            widget.update_equalizer_bands(bands)
    
    def on_save_profile_requested(self):
        """Persist current equalizer settings from all category tabs to config"""
        for audio_type, widget in self.audio_tabs.items():
            if hasattr(widget, 'save_current_profile'):
                widget.save_current_profile()

    def create_control_buttons(self):
        """Create control buttons for starting/stopping processing and refreshing devices"""
        # Add start/stop and refresh buttons to status bar as simple actions
        start_stop = QPushButton("Start Processing")
        start_stop.setCheckable(True)
        start_stop.toggled.connect(self.toggle_processing)
        refresh = QPushButton("Refresh Devices")
        refresh.clicked.connect(self.refresh_devices)
        self.statusBar().addPermanentWidget(refresh)
        self.statusBar().addPermanentWidget(start_stop)
        self.start_stop_button = start_stop

    def refresh_devices(self):
        """Refresh the list of audio devices"""
        self.routing_system.refresh_devices()
        # Mixer needs to reflect device routing and sessions list
        self.mixer_widget.refresh_category_devices()
        try:
            self.mixer_widget.refresh_sessions()
        except Exception:
            pass
        self.statusBar().showMessage("Devices refreshed", 3000)

    def toggle_processing(self, checked):
        """Start or stop audio processing"""
        if checked:
            # Start audio routing
            self.routing_system.start_routing()
            self.start_stop_button.setText("Stop Processing")
            self.statusBar().showMessage("Audio processing started")
        else:
            # Stop audio routing
            self.routing_system.stop_routing()
            self.start_stop_button.setText("Start Processing")
            self.statusBar().showMessage("Audio processing stopped")
            
    def closeEvent(self, event):
         """Handle window close event"""
         # Hide to tray and keep routing running
         self.hide()
         from PyQt5.QtWidgets import QSystemTrayIcon
         if getattr(self, 'tray_icon', None):
             try:
                 self.tray_icon.showMessage(
                     "Audio Enhancement",
                     "Still running in tray. Right-click tray icon for controls.",
                     QSystemTrayIcon.Information,
                     3000
                 )
             except Exception:
                 pass
         event.ignore()

    def _on_tray_activated(self, reason):
        from PyQt5.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def _build_tray_menu(self):
        from PyQt5.QtWidgets import QAction, QMenu
        self._tray_menu.clear()
        # Open
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: (self.showNormal(), self.raise_(), self.activateWindow()))
        self._tray_menu.addAction(open_action)
        # Switch Profile submenu
        profiles_menu = QMenu("Switch Profile", self)
        eq_settings = (self.settings_panel.config.get("equalizer_settings") or {})
        profiles = list((eq_settings.get("profiles") or {}).keys()) or ["Default"]
        active = eq_settings.get("active_profile", "Default")
        for name in profiles:
            act = QAction(name, self, checkable=True, checked=(name == active))
            act.triggered.connect(lambda chk, n=name: self._switch_profile(n))
            profiles_menu.addAction(act)
        self._tray_menu.addMenu(profiles_menu)
        # Output devices submenu
        out_menu = QMenu("Output Device", self)
        try:
            out_devs = self.routing_system.get_output_devices() or []
        except Exception:
            out_devs = []
        current_out_id = self.settings_panel.output_device_combo.currentData()
        for dev in out_devs:
            name = dev.get("name") or f"Device {dev.get('index')}"
            idx = dev.get("index")
            act = QAction(name, self, checkable=True, checked=(idx == current_out_id))
            act.triggered.connect(lambda chk, did=idx: self._switch_output_device(did))
            out_menu.addAction(act)
        self._tray_menu.addMenu(out_menu)
        # Input devices submenu
        in_menu = QMenu("Input Device", self)
        try:
            in_devs = self.routing_system.get_input_devices() or []
        except Exception:
            in_devs = []
        current_in_id = self.settings_panel.input_device_combo.currentData()
        for dev in in_devs:
            name = dev.get("name") or f"Device {dev.get('index')}"
            idx = dev.get("index")
            act = QAction(name, self, checkable=True, checked=(idx == current_in_id))
            act.triggered.connect(lambda chk, did=idx: self._switch_input_device(did))
            in_menu.addAction(act)
        self._tray_menu.addMenu(in_menu)
        # Exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_app)
        self._tray_menu.addAction(exit_action)

    def _switch_profile(self, profile_name: str):
        try:
            idx = self.settings_panel.profile_combo.findText(profile_name)
            if idx >= 0:
                self.settings_panel.profile_combo.setCurrentIndex(idx)
            else:
                self.settings_panel.on_profile_changed(profile_name)
            self._build_tray_menu()
        except Exception:
            pass

    def _switch_output_device(self, device_id: int | None):
        try:
            combo = self.settings_panel.output_device_combo
            for i in range(combo.count()):
                if combo.itemData(i) == device_id:
                    combo.setCurrentIndex(i)
                    break
            self.settings_panel.apply_device_configuration()
            self._build_tray_menu()
        except Exception:
            pass

    def _switch_input_device(self, device_id: int | None):
        try:
            combo = self.settings_panel.input_device_combo
            for i in range(combo.count()):
                if combo.itemData(i) == device_id:
                    combo.setCurrentIndex(i)
                    break
            self.settings_panel.apply_device_configuration()
            self._build_tray_menu()
        except Exception:
            pass

    def _exit_app(self):
        try:
            self.routing_system.stop_routing()
        except Exception:
            pass
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().quit()
