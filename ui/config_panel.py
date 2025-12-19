"""
Embedded settings panel for the Audio Enhancement Software
"""
import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QCheckBox, QPushButton, QGroupBox,
    QGridLayout, QMessageBox, QListWidget, QListWidgetItem,
    QAbstractItemView, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtCore import QTimer
from ui.device_notification_dialog import DeviceNotificationDialog

class ConfigPanel(QWidget):
    """Embedded configuration panel (used as a tab)"""

    # Signals
    theme_changed = pyqtSignal(str)
    profile_changed = pyqtSignal(str)
    unified_device_changed = pyqtSignal(bool, object, object)
    save_profile_requested = pyqtSignal()

    def __init__(self, routing_system, parent=None):
        super().__init__(parent)
        self.routing_system = routing_system
        self.config_file = "config.json"
        self.config = self.load_config()
        self.session_overrides = self.config.get("session_overrides_by_name", {})

        self.init_ui()
        self.load_settings()
        # Program categorization UI is now in Mixer; no session list here
        # Initialize device tracking sets and start polling for changes
        try:
            out_devs = self.routing_system.get_output_devices() or []
            in_devs = self.routing_system.get_input_devices() or []
        except Exception:
            out_devs, in_devs = [], []
        self._last_output_ids = {d.get('index') for d in out_devs}
        self._last_input_ids = {d.get('index') for d in in_devs}
        self._device_timer = QTimer(self)
        self._device_timer.setInterval(2000)  # 2 seconds
        self._device_timer.timeout.connect(self.check_device_changes)
        self._device_timer.start()

    def init_ui(self):
        layout = QVBoxLayout()

        # Device Configuration Group
        device_group = QGroupBox("Device Configuration")
        device_layout = QGridLayout()

        # Output Device Selection
        device_layout.addWidget(QLabel("Output Device:"), 0, 0)
        self.output_device_combo = QComboBox()
        self.populate_output_devices()
        device_layout.addWidget(self.output_device_combo, 0, 1)

        # Input Device Selection
        device_layout.addWidget(QLabel("Input Device:"), 1, 0)
        self.input_device_combo = QComboBox()
        self.populate_input_devices()
        device_layout.addWidget(self.input_device_combo, 1, 1)

        # Refresh Devices Button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(refresh_btn, 2, 0, 1, 2)

        device_group.setLayout(device_layout)
        layout.addWidget(device_group)

        # Equalizer Profile Management Group
        equalizer_group = QGroupBox("Equalizer Profile Management")
        equalizer_layout = QVBoxLayout()
        
        # Profile selection
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Active Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(self.profile_combo)
        
        # Profile management buttons
        new_profile_btn = QPushButton("New Profile")
        new_profile_btn.clicked.connect(self.create_new_profile)
        save_profile_btn = QPushButton("Save Profile")
        save_profile_btn.clicked.connect(self.save_current_profile)
        delete_profile_btn = QPushButton("Delete Profile")
        delete_profile_btn.clicked.connect(self.delete_current_profile)
        
        profile_layout.addWidget(new_profile_btn)
        profile_layout.addWidget(save_profile_btn)
        profile_layout.addWidget(delete_profile_btn)
        equalizer_layout.addLayout(profile_layout)
        
        # Band selection moved to Equalizer tab
        equalizer_group.setLayout(equalizer_layout)
        layout.addWidget(equalizer_group)

        # Theme Group
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QGridLayout()

        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Green Matrix", "System"])
        theme_layout.addWidget(self.theme_combo, 0, 1)

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Program Categorization moved to Mixer tab

        controls_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self.on_apply_clicked)
        controls_layout.addWidget(apply_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        layout.addStretch()
        self.setLayout(layout)

        # Connect immediate-apply behaviors
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.output_device_combo.currentIndexChanged.connect(self.on_devices_changed)
        self.input_device_combo.currentIndexChanged.connect(self.on_devices_changed)

    def _make_drop_handler(self, category):
        def handler(event):
            try:
                mime = event.mimeData()
                text = mime.text()
                # Expect format: pid:<pid>|name:<name>
                if text.startswith("pid:"):
                    parts = text.split("|")
                    pid_part = parts[0].split(":")[1]
                    name_part = parts[1].split(":")[1] if len(parts) > 1 else "Unknown"
                    pid = int(pid_part) if pid_part.isdigit() else -1
                    self.on_session_dropped(pid, name_part, category)
            except Exception:
                pass
            event.accept()
        return handler

    def _add_item(self, lst: QListWidget, name: str, pid: int):
        # Encode PID|NAME in the visible text so drops can parse reliably
        item = QListWidgetItem(f"pid:{pid}|name:{name}")
        item.setData(Qt.UserRole, {"pid": pid, "name": name})
        item.setFlags(item.flags() | Qt.ItemIsEnabled)
        lst.addItem(item)

    def refresh_sessions_ui(self):
        # Clear lists
        for lst in self.session_lists.values():
            lst.clear()
        sessions = []
        try:
            sessions = self.routing_system.list_active_sessions() or []
        except Exception:
            sessions = []
        # Populate All and categories with auto-categorization
        for sess in sessions:
            name = sess.get("name") or sess.get("display_name") or "Unknown"
            pid = sess.get("pid") or sess.get("process_id") or -1
            self._add_item(self.session_lists["all"], name, pid)
            cat = self._determine_category(name, pid)
            if cat in self.session_lists and cat != "all":
                self._add_item(self.session_lists[cat], name, pid)
                try:
                    self.routing_system.set_session_category(pid, cat)
                except Exception:
                    pass

    def _determine_category(self, name: str, pid: int) -> str:
        lname = (name or "").lower()
        # Overrides by name take precedence
        if hasattr(self, "session_overrides") and lname in self.session_overrides:
            return self.session_overrides[lname]
        # Auto rules
        if pid == -1 or "system" in lname:
            return "system"
        if any(x in lname for x in ["discord", "whatsapp", "telegram", "skype", "zoom"]):
            return "chat"
        # Default bucket
        return "others"

    def on_session_dropped(self, pid: int, name: str, category: str):
        lname = (name or "").lower()
        # Persist override by name
        if not hasattr(self, "session_overrides"):
            self.session_overrides = {}
        self.session_overrides[lname] = category
        self.config["session_overrides_by_name"] = self.session_overrides
        self.save_config()
        # Route session
        try:
            self.routing_system.set_session_category(pid, category)
        except Exception:
            pass
        # Rebuild lists to reflect change
        self.refresh_sessions_ui()

    def on_session_item_clicked(self, item: QListWidgetItem):
        try:
            text = item.text()
            pid = -1
            name = "Unknown"
            if text.startswith("pid:"):
                parts = text.split("|")
                pid_part = parts[0].split(":")[1]
                name_part = parts[1].split(":")[1] if len(parts) > 1 else "Unknown"
                pid = int(pid_part) if pid_part.isdigit() else -1
                name = name_part
            # Prompt for category selection
            display_options = ["Game", "Others", "System", "Chat"]
            key_map = {"Game": "game", "Others": "others", "System": "system", "Chat": "chat"}
            choice, ok = QInputDialog.getItem(self, "Set Category", f"Choose category for {name}", display_options, 0, False)
            if ok and choice in key_map:
                self.on_session_dropped(pid, name, key_map[choice])
        except Exception:
            pass

    def populate_output_devices(self):
        """Populate the output device combo box"""
        self.output_device_combo.clear()
        devices = self.routing_system.get_output_devices()
        for device in devices:
            self.output_device_combo.addItem(device['name'], device['index'])

    def populate_input_devices(self):
        """Populate the input device combo box"""
        self.input_device_combo.clear()
        devices = self.routing_system.get_input_devices()
        for device in devices:
            self.input_device_combo.addItem(device['name'], device['index'])

    def refresh_devices(self):
        """Refresh the device lists and reapply current selections"""
        self.routing_system.refresh_devices()
        self.populate_output_devices()
        self.populate_input_devices()
        # Reapply selection from config
        self.load_settings()
        # Apply unified configuration after refresh to keep routing in sync
        self.apply_device_configuration()

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "theme": "Light",
            "unified_device_mode": False,
            "unified_output_device": None,
            "unified_input_device": None,
            "session_overrides_by_name": {},
            "equalizer": {
                "enabled": True,
                "preset": "Flat",
                "bands": 10,
                "gains": [0] * 10
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
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

        # Device settings - always use unified mode now
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

        # Equalizer settings - refresh profiles
        try:
            self.refresh_profiles()
        except Exception:
            pass

    def on_theme_changed(self, theme_name):
        """Apply theme immediately when changed"""
        self.config["theme"] = theme_name
        self.save_config()
        self.theme_changed.emit(theme_name)

    def on_devices_changed(self):
        """Apply device routing when device selections change"""
        self.apply_device_configuration()

    def apply_device_configuration(self):
        """Apply and emit device routing configuration - always unified mode"""
        self.config["unified_device_mode"] = True  # Always enabled now
        self.config["unified_output_device"] = self.output_device_combo.currentData()
        self.config["unified_input_device"] = self.input_device_combo.currentData()

        # Apply to routing system
        self.routing_system.set_unified_device_mode(
            True,  # Always unified
            self.config["unified_output_device"],
            self.config["unified_input_device"]
        )

        # Save and emit signals
        self.save_config()
        self.unified_device_changed.emit(
            True,  # Always unified
            self.config["unified_output_device"],
            self.config["unified_input_device"]
        )

    def on_apply_clicked(self):
        # Persist and apply device configuration
        self.apply_device_configuration()
        # Ensure session overrides are saved and applied to active sessions
        self.config["session_overrides_by_name"] = getattr(self, "session_overrides", {})
        self.save_config()
        try:
            sessions = self.routing_system.list_active_sessions() or []
        except Exception:
            sessions = []
        overrides = getattr(self, "session_overrides", {}) or {}
        for sess in sessions:
            name = (sess.get("name") or sess.get("display_name") or "Unknown").lower()
            pid = sess.get("pid") or sess.get("process_id") or -1
            if name in overrides:
                try:
                    self.routing_system.set_session_category(pid, overrides[name])
                except Exception:
                    pass
        # Mixer tab hosts program/category UI; no session list refresh here
        QMessageBox.information(self, "Settings Applied", "Configuration and routing have been applied.")


    def on_profile_changed(self, profile_name):
        """Handle profile selection change"""
        try:
            self.config["equalizer_settings"] = self.config.get("equalizer_settings", {})
            self.config["equalizer_settings"]["active_profile"] = profile_name
            self.save_config()
            
            # Notify all audio type widgets to reload their equalizer settings
            self.profile_changed.emit(profile_name)
            
        except Exception as e:
            print(f"Error changing profile: {e}")
    
    def on_bands_changed(self, bands_str):
        """Deprecated: bands are controlled directly in Equalizer tab"""
        try:
            bands = int(bands_str)
            self.config["equalizer_settings"] = self.config.get("equalizer_settings", {})
            self.config["equalizer_settings"]["bands"] = bands
            self.save_config()
        except Exception as e:
            print(f"Error changing bands: {e}")
    
    def create_new_profile(self):
        """Create a new equalizer profile"""
        from PyQt5.QtWidgets import QInputDialog
        
        profile_name, ok = QInputDialog.getText(self, "New Profile", "Enter profile name:")
        if ok and profile_name.strip():
            try:
                self.config["equalizer_settings"] = self.config.get("equalizer_settings", {})
                self.config["equalizer_settings"]["profiles"] = self.config["equalizer_settings"].get("profiles", {})
                
                # Create new profile with default settings
                bands = self.config["equalizer_settings"].get("bands", 10)
                new_profile = {}
                for category in ["game", "others", "system", "chat", "microphone"]:
                    new_profile[category] = {
                        "enabled": False,
                        "preset": "Flat",
                        "gains": [0.0] * bands
                    }
                
                self.config["equalizer_settings"]["profiles"][profile_name] = new_profile
                self.config["equalizer_settings"]["active_profile"] = profile_name
                self.save_config()
                
                self.refresh_profiles()
                self.profile_combo.setCurrentText(profile_name)
                
            except Exception as e:
                print(f"Error creating profile: {e}")
    
    def save_current_profile(self):
        """Request saving current equalizer settings to active profile"""
        try:
            # Emit signal so MainWindow can coordinate saving from all category tabs
            self.save_profile_requested.emit()
            QMessageBox.information(self, "Profile Saved", 
                                  "Current equalizer settings have been saved to the active profile.")
            
        except Exception as e:
            print(f"Error saving profile: {e}")
    
    def delete_current_profile(self):
        """Delete the current profile"""
        current_profile = self.profile_combo.currentText()
        if current_profile == "Default":
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the Default profile.")
            return
        
        reply = QMessageBox.question(self, "Delete Profile", 
                                   f"Are you sure you want to delete the '{current_profile}' profile?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.config["equalizer_settings"] = self.config.get("equalizer_settings", {})
                self.config["equalizer_settings"]["profiles"] = self.config["equalizer_settings"].get("profiles", {})
                
                if current_profile in self.config["equalizer_settings"]["profiles"]:
                    del self.config["equalizer_settings"]["profiles"][current_profile]
                
                self.config["equalizer_settings"]["active_profile"] = "Default"
                self.save_config()
                
                self.refresh_profiles()
                self.profile_combo.setCurrentText("Default")
                
            except Exception as e:
                print(f"Error deleting profile: {e}")
    
    def refresh_profiles(self):
        """Refresh the profile combo box"""
        try:
            self.profile_combo.clear()
            profiles = self.config.get("equalizer_settings", {}).get("profiles", {"Default": {}})
            for profile_name in profiles.keys():
                self.profile_combo.addItem(profile_name)
            
            # Set current profile
            active_profile = self.config.get("equalizer_settings", {}).get("active_profile", "Default")
            index = self.profile_combo.findText(active_profile)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
                
        except Exception as e:
            print(f"Error refreshing profiles: {e}")

    def check_device_changes(self):
        """Detect newly connected/disconnected audio devices and offer to switch."""
        try:
            out_devs = self.routing_system.get_output_devices() or []
            in_devs = self.routing_system.get_input_devices() or []
        except Exception:
            return
        current_out_ids = {d.get('index') for d in out_devs}
        current_in_ids = {d.get('index') for d in in_devs}

        # Detect new output devices
        new_out_ids = current_out_ids - getattr(self, '_last_output_ids', set())
        if new_out_ids:
            self.populate_output_devices()
            new_out_id = next(iter(new_out_ids))
            device_name = "Unknown Device"
            for device in out_devs:
                if device.get('index') == new_out_id:
                    device_name = device.get('name', 'Unknown Device')
                    break
            current_device_name = self.output_device_combo.currentText() or "No device selected"
            dialog = DeviceNotificationDialog(device_name, "output", current_device_name, self)
            if dialog.exec_() == dialog.Accepted:
                for i in range(self.output_device_combo.count()):
                    if self.output_device_combo.itemData(i) == new_out_id:
                        self.output_device_combo.setCurrentIndex(i)
                        break
                self.apply_device_configuration()

        # Detect new input devices (microphones)
        new_in_ids = current_in_ids - getattr(self, '_last_input_ids', set())
        if new_in_ids:
            self.populate_input_devices()
            new_in_id = next(iter(new_in_ids))
            device_name = "Unknown Device"
            for device in in_devs:
                if device.get('index') == new_in_id:
                    device_name = device.get('name', 'Unknown Device')
                    break
            current_device_name = self.input_device_combo.currentText() or "No device selected"
            dialog = DeviceNotificationDialog(device_name, "input", current_device_name, self)
            if dialog.exec_() == dialog.Accepted:
                for i in range(self.input_device_combo.count()):
                    if self.input_device_combo.itemData(i) == new_in_id:
                        self.input_device_combo.setCurrentIndex(i)
                        break
                self.apply_device_configuration()

        # Detect removed output devices; prompt if current selection disappeared
        removed_out_ids = getattr(self, '_last_output_ids', set()) - current_out_ids
        if removed_out_ids:
            current_sel_id = self.output_device_combo.currentData()
            if current_sel_id in removed_out_ids:
                self.populate_output_devices()
                if self.output_device_combo.count() > 0:
                    fallback_name = self.output_device_combo.itemText(0)
                    current_device_name = self.output_device_combo.currentText() or "No device selected"
                    dialog = DeviceNotificationDialog(fallback_name, "output", current_device_name, self)
                    if dialog.exec_() == dialog.Accepted:
                        self.output_device_combo.setCurrentIndex(0)
                        self.apply_device_configuration()

        # Detect removed input devices; prompt if current selection disappeared
        removed_in_ids = getattr(self, '_last_input_ids', set()) - current_in_ids
        if removed_in_ids:
            current_sel_id = self.input_device_combo.currentData()
            if current_sel_id in removed_in_ids:
                self.populate_input_devices()
                if self.input_device_combo.count() > 0:
                    fallback_name = self.input_device_combo.itemText(0)
                    current_device_name = self.input_device_combo.currentText() or "No device selected"
                    dialog = DeviceNotificationDialog(fallback_name, "input", current_device_name, self)
                    if dialog.exec_() == dialog.Accepted:
                        self.input_device_combo.setCurrentIndex(0)
                        self.apply_device_configuration()

        # Update last seen sets
        self._last_output_ids = current_out_ids
        self._last_input_ids = current_in_ids