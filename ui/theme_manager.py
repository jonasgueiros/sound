"""
Theme manager for the audio enhancement application
"""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    """Manages application themes and styling"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "Light"
        
    def set_theme(self, theme_name):
        """Set the application theme"""
        self.current_theme = theme_name
        stylesheet = self.get_theme_stylesheet(theme_name)
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
            
        self.theme_changed.emit(theme_name)
        
    def get_current_theme(self):
        """Get the current theme name"""
        return self.current_theme
        
    def get_theme_stylesheet(self, theme_name):
        """Get the complete stylesheet for a theme"""
        if theme_name == "Dark":
            return self.get_dark_theme()
        elif theme_name == "Green Matrix":
            return self.get_green_matrix_theme()
        elif theme_name == "System":
            return self.get_system_theme()
        else:
            return self.get_light_theme()
            
    def get_light_theme(self):
        """Light theme stylesheet"""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        
        QWidget {
            background-color: #ffffff;
            color: #000000;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 9pt;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 15px;
            background-color: #f8f9fa;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            background-color: #ffffff;
        }
        
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #e0e0e0;
            border-color: #999999;
        }
        
        QPushButton:pressed {
            background-color: #d0d0d0;
            border-color: #666666;
        }
        
        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #999999;
            border-color: #e0e0e0;
        }
        
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 6px 12px;
            border-radius: 4px;
            min-width: 120px;
        }
        
        QComboBox:hover {
            border-color: #999999;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #cccccc;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #666666;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #cccccc;
            height: 6px;
            background: #f0f0f0;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #0078d4;
            border: 1px solid #005a9e;
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #106ebe;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        
        QCheckBox::indicator:unchecked {
            background-color: #ffffff;
            border: 2px solid #cccccc;
            border-radius: 3px;
        }
        
        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border: 2px solid #0078d4;
            border-radius: 3px;
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 1px solid #ffffff;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #e8e8e8;
        }
        
        QLabel {
            color: #333333;
            background-color: transparent;
        }
        
        QScrollArea {
            border: 1px solid #cccccc;
            border-radius: 4px;
            background-color: #ffffff;
        }
        
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #cccccc;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #999999;
        }
        """
        
    def get_dark_theme(self):
        """Dark theme stylesheet"""
        return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 9pt;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #404040;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 15px;
            background-color: #2d2d30;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            padding: 8px 16px;
            border-radius: 4px;
            color: #ffffff;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #505050;
            border-color: #666666;
        }
        
        QPushButton:pressed {
            background-color: #353535;
            border-color: #777777;
        }
        
        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #666666;
            border-color: #333333;
        }
        
        QComboBox {
            background-color: #404040;
            border: 1px solid #555555;
            padding: 6px 12px;
            border-radius: 4px;
            color: #ffffff;
            min-width: 120px;
        }
        
        QComboBox:hover {
            border-color: #666666;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #555555;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #ffffff;
        }
        
        QComboBox QAbstractItemView {
            background-color: #404040;
            border: 1px solid #555555;
            selection-background-color: #0078d4;
            color: #ffffff;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #555555;
            height: 6px;
            background: #404040;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #0078d4;
            border: 1px solid #005a9e;
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #106ebe;
        }
        
        QCheckBox {
            color: #ffffff;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        
        QCheckBox::indicator:unchecked {
            background-color: #404040;
            border: 2px solid #555555;
            border-radius: 3px;
        }
        
        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border: 2px solid #0078d4;
            border-radius: 3px;
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2d2d30;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #404040;
            border: 1px solid #555555;
            padding: 8px 16px;
            margin-right: 2px;
            color: #ffffff;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #2d2d30;
            border-bottom: 1px solid #2d2d30;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #505050;
        }
        
        QLabel {
            color: #ffffff;
            background-color: transparent;
        }
        
        QScrollArea {
            border: 1px solid #555555;
            border-radius: 4px;
            background-color: #2d2d30;
        }
        
        QScrollBar:vertical {
            background-color: #404040;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #666666;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #777777;
        }
        
        QDialog {
            background-color: #1e1e1e;
        }
        """
        
    def get_green_matrix_theme(self):
        """Green Matrix theme - dark grey backgrounds with green accents"""
        return """
        QMainWindow {
            background-color: #1a1a1a;
            color: #00ff41;
        }
        
        QWidget {
            background-color: #1a1a1a;
            color: #00ff41;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 9pt;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #00cc33;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 15px;
            background-color: #2a2a2a;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            background-color: #1a1a1a;
            color: #00ff41;
        }
        
        QPushButton {
            background-color: #333333;
            border: 1px solid #00cc33;
            padding: 8px 16px;
            border-radius: 4px;
            color: #00ff41;
            font-weight: 500;
        }
        
        QPushButton:hover {
            background-color: #404040;
            border-color: #00ff41;
            color: #ffffff;
        }
        
        QPushButton:pressed {
            background-color: #00cc33;
            border-color: #00ff41;
            color: #000000;
        }
        
        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #666666;
            border-color: #444444;
        }
        
        QComboBox {
            background-color: #333333;
            border: 1px solid #00cc33;
            padding: 6px 12px;
            border-radius: 4px;
            color: #00ff41;
            min-width: 120px;
        }
        
        QComboBox:hover {
            border-color: #00ff41;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #00cc33;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #00ff41;
        }
        
        QComboBox QAbstractItemView {
            background-color: #333333;
            border: 1px solid #00cc33;
            selection-background-color: #00cc33;
            selection-color: #000000;
            color: #00ff41;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #00cc33;
            height: 6px;
            background: #333333;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #00ff41;
            border: 1px solid #00cc33;
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #33ff66;
        }
        
        QCheckBox {
            color: #00ff41;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        
        QCheckBox::indicator:unchecked {
            background-color: #333333;
            border: 2px solid #00cc33;
            border-radius: 3px;
        }
        
        QCheckBox::indicator:checked {
            background-color: #00cc33;
            border: 2px solid #00ff41;
            border-radius: 3px;
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
        }
        
        QTabWidget::pane {
            border: 1px solid #00cc33;
            background-color: #2a2a2a;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #333333;
            border: 1px solid #00cc33;
            padding: 8px 16px;
            margin-right: 2px;
            color: #00ff41;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #2a2a2a;
            border-bottom: 1px solid #2a2a2a;
            color: #00ff41;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #404040;
            color: #ffffff;
        }
        
        QLabel {
            color: #00ff41;
            background-color: transparent;
        }
        
        QScrollArea {
            border: 1px solid #00cc33;
            border-radius: 4px;
            background-color: #2a2a2a;
        }
        
        QScrollBar:vertical {
            background-color: #333333;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #00cc33;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #00ff41;
        }
        
        QListWidget {
            background-color: #2a2a2a;
            border: 1px solid #00cc33;
            border-radius: 4px;
            color: #00ff41;
            selection-background-color: #00cc33;
            selection-color: #000000;
        }
        
        QListWidget::item {
            padding: 4px;
            border-bottom: 1px solid #333333;
        }
        
        QListWidget::item:hover {
            background-color: #404040;
            color: #ffffff;
        }
        
        QListWidget::item:selected {
            background-color: #00cc33;
            color: #000000;
        }
        
        QDialog {
            background-color: #1a1a1a;
        }
        
        QMessageBox {
            background-color: #1a1a1a;
            color: #00ff41;
        }
        
        QMessageBox QPushButton {
            min-width: 80px;
        }
        """
        
    def get_system_theme(self):
        """System theme - uses OS default"""
        return ""  # Empty stylesheet uses system default