"""
Audio device management module for handling multiple audio sources
"""
import pyaudio
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
from comtypes import CLSCTX_ALL, cast, POINTER
import numpy as np
import threading
import time

class AudioDeviceManager:
    """
    Manages audio devices, providing functionality to enumerate, select,
    and route audio between different devices
    """
    def __init__(self):
        self.pyaudio = pyaudio.PyAudio()
        self.devices = self._enumerate_devices()
        self.active_devices = {}  # Maps audio type to device
        self.device_volumes = {}  # Maps device index to volume level (0-100)
        self.device_settings = {}  # Maps device index to settings dict
        self.audio_types = ["game", "others", "system", "chat", "microphone"]
        self.monitoring = False
        self.monitor_thread = None
        
    def _enumerate_devices(self):
        """Get all available audio devices"""
        devices = []
        
        # Get output devices
        output_devices = AudioUtilities.GetSpeakers()
        for i in range(self.pyaudio.get_device_count()):
            device_info = self.pyaudio.get_device_info_by_index(i)
            if device_info['maxOutputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxOutputChannels'],
                    'type': 'output',
                    'sample_rate': int(device_info['defaultSampleRate'])
                })
                
        # Get input devices (microphones)
        for i in range(self.pyaudio.get_device_count()):
            device_info = self.pyaudio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'],
                    'type': 'input',
                    'sample_rate': int(device_info['defaultSampleRate'])
                })
                
        return devices
    
    def get_output_devices(self):
        """Return list of output devices only"""
        return [d for d in self.devices if d['type'] == 'output']
    
    def get_input_devices(self):
        """Return list of input devices only"""
        return [d for d in self.devices if d['type'] == 'input']
    
    def set_device_for_audio_type(self, audio_type, device_index):
        """Assign a device to a specific audio type"""
        if audio_type not in self.audio_types:
            raise ValueError(f"Unknown audio type: {audio_type}")
            
        # Find the device with the given index
        device = next((d for d in self.devices if d['index'] == device_index), None)
        if not device:
            raise ValueError(f"No device found with index {device_index}")
            
        # Check if device type matches audio type requirements
        if audio_type == "microphone" and device['type'] != 'input':
            raise ValueError("Microphone audio type requires an input device")
        elif audio_type != "microphone" and device['type'] != 'output':
            raise ValueError(f"{audio_type} audio type requires an output device")
            
        self.active_devices[audio_type] = device
        return True
    
    def get_device_for_audio_type(self, audio_type):
        """Get the currently assigned device for an audio type"""
        if audio_type not in self.audio_types:
            raise ValueError(f"Unknown audio type: {audio_type}")
            
        return self.active_devices.get(audio_type)
    
    def refresh_devices(self):
        """Refresh the list of available devices"""
        self.devices = self._enumerate_devices()
        
        # Remove any active devices that are no longer available
        device_indices = [d['index'] for d in self.devices]
        for audio_type in list(self.active_devices.keys()):
            if self.active_devices[audio_type]['index'] not in device_indices:
                del self.active_devices[audio_type]
                
    def get_device_volume(self, device_index):
        """Get the current volume level for a device (0-100)"""
        # Check if we have the volume cached
        if device_index in self.device_volumes:
            return self.device_volumes[device_index]
            
        # Otherwise get it from Windows
        try:
            device = next((d for d in self.devices if d['index'] == device_index), None)
            if not device:
                return 0
                
            if device['type'] == 'output':
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    level = volume.GetMasterVolume() * 100
                    self.device_volumes[device_index] = level
                    return level
            else:
                # For input devices
                devices = AudioUtilities.GetMicrophone()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                level = volume.GetMasterVolumeLevelScalar() * 100
                self.device_volumes[device_index] = level
                return level
        except Exception as e:
            print(f"Error getting volume: {e}")
            return 0
    
    def set_device_volume(self, device_index, volume_level):
        """Set the volume level for a device (0-100)"""
        if volume_level < 0 or volume_level > 100:
            raise ValueError("Volume level must be between 0 and 100")
        try:
            device = next((d for d in self.devices if d['index'] == device_index), None)
            if not device:
                return False
            if device['type'] == 'output':
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    volume.SetMasterVolume(volume_level / 100, None)
            else:
                devices = AudioUtilities.GetMicrophone()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(volume_level / 100, None)
            self.device_volumes[device_index] = volume_level
            return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False
    
    def get_device_setting(self, device_index, setting_name, default=None):
        """Get a device-specific setting"""
        if device_index not in self.device_settings:
            return default
            
        return self.device_settings.get(device_index, {}).get(setting_name, default)
    
    def set_device_setting(self, device_index, setting_name, value):
        """Set a device-specific setting"""
        if device_index not in self.device_settings:
            self.device_settings[device_index] = {}
            
        self.device_settings[device_index][setting_name] = value
    
    def start_device_monitoring(self):
        """Start monitoring audio devices for changes"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_devices)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_device_monitoring(self):
        """Stop monitoring audio devices"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _monitor_devices(self):
        """Monitor thread that checks for device changes"""
        last_device_count = self.pyaudio.get_device_count()
        
        while self.monitoring:
            current_count = self.pyaudio.get_device_count()
            if current_count != last_device_count:
                self.refresh_devices()
                last_device_count = current_count
                
            # Check every 2 seconds
            time.sleep(2)
    
    def __del__(self):
        """Clean up PyAudio resources"""
        self.stop_device_monitoring()
        if hasattr(self, 'pyaudio'):
            self.pyaudio.terminate()

    def get_active_audio_sessions(self):
        """List active audio sessions (programs producing sound)"""
        sessions_info = []
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                try:
                    proc = session.Process
                    pid = proc.pid if proc else -1
                    # Prefer process name; fallback to display name or identifier for apps like browsers
                    name = None
                    if proc:
                        try:
                            name = proc.name()
                        except Exception:
                            name = None
                    if not name:
                        try:
                            # Some sessions expose a display name via IAudioSessionControl
                            name = session._ctl.GetDisplayName()
                        except Exception:
                            name = None
                    if not name:
                        try:
                            ident = session._ctl.GetSessionIdentifier()
                            # Derive a sensible short name from identifier
                            name = ident.split("\\")[-1]
                        except Exception:
                            name = None
                    if not name:
                        name = "System" if pid == -1 else "Unknown"
                except Exception:
                    name = "Unknown"
                    pid = -1
                try:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume).GetMasterVolume()
                    volume_level = int(volume * 100)
                except Exception:
                    volume_level = None
                sessions_info.append({
                    'pid': pid,
                    'name': name,
                    'volume': volume_level
                })
        except Exception as e:
            print(f"Error listing sessions: {e}")
        return sessions_info

    def set_session_volume(self, pid, volume_level):
        """Set volume for a specific audio session by process id"""
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                proc = session.Process
                spid = proc.pid if proc else -1
                if spid == pid:
                    vol = session._ctl.QueryInterface(ISimpleAudioVolume)
                    vol.SetMasterVolume(volume_level / 100, None)
                    return True
        except Exception as e:
            print(f"Error setting session volume: {e}")
        return False

    def route_session_to_device(self, pid, device_index):
        """Placeholder to track routing a session to a specific device"""
        if not hasattr(self, 'session_routes'):
            self.session_routes = {}
        self.session_routes[pid] = device_index
        return True
