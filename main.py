"""
Audio Enhancement Software - Main Application
"""
import sys
import json
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.audio_router import AudioRoutingSystem
from audio_processing.processors import Equalizer, BassBoost, SpatialEnhancer, NoiseReducer

def load_config():
    """Load application configuration"""
    config_file = "config.json"
    default_config = {
        "theme": "Light",
        "unified_device_mode": False,
        "unified_output_device": None,
        "unified_input_device": None
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        except Exception as e:
            print(f"Error loading config: {e}")
            
    return default_config

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Load configuration
    config = load_config()
    
    # Initialize audio routing system
    routing_system = AudioRoutingSystem()
    
    # Always apply unified device configuration (no longer optional)
    # Validate configured device IDs against current enumeration
    try:
        output_devices = routing_system.get_output_devices() or []
        input_devices = routing_system.get_input_devices() or []
    except Exception:
        output_devices, input_devices = [], []
    valid_output_ids = {d.get('index') for d in output_devices}
    valid_input_ids = {d.get('index') for d in input_devices}
    out_id = config.get("unified_output_device")
    in_id = config.get("unified_input_device")
    # If invalid, null out to avoid crashes
    if out_id not in valid_output_ids:
        out_id = None
    if in_id not in valid_input_ids:
        in_id = None
    # Always enable unified mode
    routing_system.set_unified_device_mode(True, out_id, in_id)
    
    # Create main window
    window = MainWindow(routing_system)
    
    # Apply saved theme
    window.set_theme(config.get("theme", "Light"))
    
    # Register audio processors
    processors = {
        'equalizer': Equalizer(),
        'bass_boost': BassBoost(),
        'spatial': SpatialEnhancer(),
        'noise_reducer': NoiseReducer()
    }
    
    window.register_processors(processors)
    
    # Show the window (resized to fit screen by MainWindow)
    window.show()
    
    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    sys.exit(main())
