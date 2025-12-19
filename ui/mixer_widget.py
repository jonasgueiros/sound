from PyQt5 import QtWidgets, QtCore, QtGui

class MixerWidget(QtWidgets.QWidget):
    session_reroute_requested = QtCore.pyqtSignal(int, int)  # pid, device_index

    def __init__(self, routing_system, parent=None):
        super().__init__(parent)
        self.routing_system = routing_system
        self.output_devices = []
        self._build_ui()
        self._connect_signals()
        # Remove master device selection; Active Programs moved to Settings
        self.refresh_category_devices()
        # Populate active programs initially
        self.refresh_sessions()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Category volumes only (no master device selection)
        cat_group = QtWidgets.QGroupBox("Category Volumes")
        cg_layout = QtWidgets.QGridLayout(cat_group)
        self.category_controls = {}
        # Reordered volumes: system, others, game, chat, microphone
        categories = [
            ("system", "🖥️"),
            ("others", "📦"),
            ("game", "🎮"),
            ("chat", "💬"),
            ("microphone", "🎙️"),
        ]
        for row, (key, icon_text) in enumerate(categories):
            name_label = QtWidgets.QLabel(icon_text)
            font = name_label.font()
            font.setPointSize(24)
            name_label.setFont(font)
            name_label.setAlignment(QtCore.Qt.AlignCenter)
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50)
            value_label = QtWidgets.QLabel("50%")
            cg_layout.addWidget(name_label, row, 0)
            cg_layout.addWidget(slider, row, 1)
            cg_layout.addWidget(value_label, row, 2)
            self.category_controls[key] = {
                "slider": slider,
                "value_label": value_label,
            }
        layout.addWidget(cat_group)

        # Active Programs and Categories (compact square-ish layout)
        prog_group = QtWidgets.QGroupBox("Active Programs and Categories")
        grid = QtWidgets.QGridLayout(prog_group)
        prog_group.setMaximumHeight(230)

        class DraggableListWidget(QtWidgets.QListWidget):
            def startDrag(self, supportedActions):
                item = self.currentItem()
                if not item:
                    return
                # Build MIME from stored UserRole data so visible text can be just name
                data = item.data(QtCore.Qt.UserRole) or {}
                pid = data.get("pid")
                name = data.get("name") or item.text()
                if pid is None:
                    return
                drag = QtGui.QDrag(self)
                mime = QtCore.QMimeData()
                mime.setText(f"pid:{pid}|name:{name}")
                drag.setMimeData(mime)
                drag.exec_(supportedActions)

        def make_list(title, draggable=True):
            box = QtWidgets.QGroupBox(title)
            v = QtWidgets.QVBoxLayout(box)
            lst = DraggableListWidget() if draggable else QtWidgets.QListWidget()
            lst.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            lst.setFixedSize(120, 120)
            lst.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            lst.setDragEnabled(True)
            lst.setDropIndicatorShown(True)
            v.addWidget(lst)
            return box, lst

        # 1x5 layout: All + System + Others + Game + Chat (equal height/width)
        all_box, all_list = make_list("All Sounds", draggable=True)
        system_box, system_list = make_list("System", draggable=True)
        others_box, others_list = make_list("Others", draggable=True)
        game_box, game_list = make_list("Game", draggable=True)
        chat_box, chat_list = make_list("Chat", draggable=True)

        # Arrange in a single row with five squares
        grid.addWidget(all_box,    0, 0)
        grid.addWidget(system_box, 0, 1)
        grid.addWidget(others_box, 0, 2)
        grid.addWidget(game_box,   0, 3)
        grid.addWidget(chat_box,   0, 4)

        # Small refresh button in top-right
        refresh_sessions_btn = QtWidgets.QPushButton("↻")
        refresh_sessions_btn.setToolTip("Refresh Active Programs")
        refresh_sessions_btn.setFixedSize(28, 28)
        refresh_sessions_btn.clicked.connect(self.refresh_sessions_ui)
        grid.addWidget(refresh_sessions_btn, 0, 5, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)

        layout.addWidget(prog_group)

        self.session_lists = {
            "all": all_list,
            "system": system_list,
            "others": others_list,
            "game": game_list,
            "chat": chat_list,
        }

        # Enable drag-and-drop to categorize sessions (not for All as target)
        for category, lst in self.session_lists.items():
            if category != "all":
                lst.setAcceptDrops(True)
                lst.dragEnterEvent = self._make_drop_handler(category)
                lst.dropEvent = self._make_drop_handler(category)

    def _connect_signals(self):
        # Category sliders
        for key, controls in self.category_controls.items():
            controls["slider"].valueChanged.connect(lambda v, k=key: self._on_category_volume_changed(k, v))
        # Connect clicks for session lists to choose category
        for lst in getattr(self, "session_lists", {}).values():
            lst.itemClicked.connect(self.on_session_item_clicked)
            lst.itemDoubleClicked.connect(self.on_session_item_clicked)

    def refresh_category_devices(self):
        # Device name is no longer shown in Mixer category rows
        pass

    # Wrapper to match existing expectations
    def refresh_sessions(self):
        self.refresh_sessions_ui()

    # Build drag/drop handlers copied from Settings implementation
    def _make_drop_handler(self, category):
        def handler(event):
            try:
                md = event.mimeData()
                text = md.text() if md and md.hasText() else ""
                pid = -1
                name = "Unknown"
                if text.startswith("pid:"):
                    parts = text.split("|")
                    pid_part = parts[0].split(":")[1]
                    name_part = parts[1].split(":")[1] if len(parts) > 1 else "Unknown"
                    pid = int(pid_part) if pid_part.isdigit() else -1
                    name = name_part
                if event.type() == QtCore.QEvent.DragEnter:
                    event.acceptProposedAction()
                    return
                # Drop
                if pid != -1:
                    self.on_session_dropped(pid, name, category)
                event.acceptProposedAction()
            except Exception:
                event.ignore()
        return handler

    def _add_item(self, lst: QtWidgets.QListWidget, name: str, pid: int):
        # Show only program name in list; encode pid/name in UserRole and tooltip
        item = QtWidgets.QListWidgetItem(name)
        item.setToolTip(f"PID: {pid}\n{name}")
        item.setData(QtCore.Qt.UserRole, {"pid": pid, "name": name})
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEnabled)
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
            # Always list in All Sounds
            self._add_item(self.session_lists["all"], name, pid)
            # Use existing assignment if present; otherwise auto-categorize
            assigned = None
            try:
                assigned = self.routing_system.get_session_category(pid)
            except Exception:
                assigned = None
            cat = assigned if assigned in self.session_lists and assigned != "all" else self._determine_category(name, pid)
            if cat in self.session_lists and cat != "all":
                self._add_item(self.session_lists[cat], name, pid)
                # Record inferred auto-assignment the first time only
                if not assigned:
                    try:
                        self.routing_system.set_session_category(pid, cat)
                    except Exception:
                        pass

    def _determine_category(self, name: str, pid: int) -> str:
        lname = (name or "").lower()
        # Auto rules and potential overrides
        if pid == -1 or "system" in lname:
            return "system"
        if any(x in lname for x in ["discord", "whatsapp", "telegram", "skype", "zoom"]):
            return "chat"
        return "others"

    def on_session_dropped(self, pid: int, name: str, category: str):
        try:
            self.routing_system.set_session_category(pid, category)
        except Exception:
            pass
        self.refresh_sessions_ui()

    def on_session_item_clicked(self, item: QtWidgets.QListWidgetItem):
        try:
            data = item.data(QtCore.Qt.UserRole) or {}
            pid = int(data.get("pid") or -1)
            name = data.get("name") or item.text() or "Unknown"
            # Menu order: System, Others, Game, Chat
            display_options = ["System", "Others", "Game", "Chat"]
            key_map = {"System": "system", "Others": "others", "Game": "game", "Chat": "chat"}
            choice, ok = QtWidgets.QInputDialog.getItem(self, "Set Category", f"Choose category for {name}", display_options, 0, False)
            if ok and choice in key_map:
                self.on_session_dropped(pid, name, key_map[choice])
        except Exception:
            pass

    def _on_category_volume_changed(self, audio_type, value):
        controls = self.category_controls.get(audio_type)
        if controls:
            controls["value_label"].setText(f"{value}%")
        try:
            # Output categories: adjust per-session volume; microphone adjusts endpoint
            self.routing_system.set_category_volume(audio_type, value)
        except Exception:
            pass
