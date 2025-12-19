from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon


class DeviceNotificationDialog(QDialog):
    def __init__(self, device_name, device_type, current_device, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.device_type = device_type  # "input" or "output"
        self.current_device = current_device
        self.user_choice = None  # Will be "switch" or "keep"
        
        self.setup_ui()
        self.setModal(True)
        
    def setup_ui(self):
        self.setWindowTitle("New Audio Device Detected")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("🔊 New Audio Device Connected")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Device info
        info_layout = QVBoxLayout()
        
        device_type_text = "Input Device (Microphone)" if self.device_type == "input" else "Output Device (Speaker/Headphones)"
        
        new_device_label = QLabel(f"<b>New {device_type_text}:</b><br>{self.device_name}")
        new_device_label.setWordWrap(True)
        info_layout.addWidget(new_device_label)
        
        current_device_label = QLabel(f"<b>Currently Using:</b><br>{self.current_device}")
        current_device_label.setWordWrap(True)
        info_layout.addWidget(current_device_label)
        
        question_label = QLabel("<b>Would you like to switch to the new device?</b>")
        question_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(question_label)
        
        layout.addLayout(info_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        switch_button = QPushButton("Switch to New Device")
        switch_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        switch_button.clicked.connect(self.switch_device)
        
        keep_button = QPushButton("Keep Current Device")
        keep_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        keep_button.clicked.connect(self.keep_current)
        
        button_layout.addWidget(switch_button)
        button_layout.addWidget(keep_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def switch_device(self):
        self.user_choice = "switch"
        self.accept()
        
    def keep_current(self):
        self.user_choice = "keep"
        self.reject()
        
    def get_user_choice(self):
        return self.user_choice