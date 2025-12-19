"""
Audio routing system for connecting physical and virtual audio devices
"""
from .audio_devices import AudioDeviceManager
from .virtual_devices import VirtualAudioRouter

class AudioRoutingSystem:
    """
    Manages routing between physical audio devices and virtual audio devices
    """
    def __init__(self):
        self.device_manager = AudioDeviceManager()
        self.virtual_router = VirtualAudioRouter()
        self.routes = {}  # Maps audio_type to (source, destination) tuples
        self.unified_device_mode = False
        self.unified_output_device = None
        self.unified_input_device = None
        self.session_categories = {}
        
    def set_unified_device_mode(self, enabled, output_device_id=None, input_device_id=None):
        """
        Enable or disable unified device mode where all audio types use the same device
        
        Args:
            enabled: Whether to enable unified device mode
            output_device_id: ID of the output device to use for all audio types
            input_device_id: ID of the input device to use for microphone
        """
        self.unified_device_mode = enabled
        if enabled:
            self.unified_output_device = output_device_id
            self.unified_input_device = input_device_id
            # Apply unified device to all audio types
            if output_device_id:
                for audio_type in ['game', 'others', 'system', 'chat']:
                    self.device_manager.set_device_for_audio_type(audio_type, output_device_id)
            if input_device_id:
                self.device_manager.set_device_for_audio_type('microphone', input_device_id)
    
    def get_unified_device_config(self):
        """Get the current unified device configuration"""
        return {
            'enabled': self.unified_device_mode,
            'output_device': self.unified_output_device,
            'input_device': self.unified_input_device
        }

    def create_route(self, audio_type, physical_device_id, virtual_device_name):
        """
        Create a route from a physical device to a virtual device
        
        Args:
            audio_type: Type of audio (game, movie, music, chat, microphone)
            physical_device_id: ID of the physical device
            virtual_device_name: Name of the virtual device
        """
        # If unified mode is enabled, use the unified device instead
        if self.unified_device_mode:
            if audio_type == 'microphone' and self.unified_input_device:
                physical_device_id = self.unified_input_device
            elif audio_type != 'microphone' and self.unified_output_device:
                physical_device_id = self.unified_output_device
        
        # Set the physical device for this audio type
        self.device_manager.set_device_for_audio_type(audio_type, physical_device_id)
        
        # Create a virtual device if it doesn't exist
        if not self.virtual_router.get_virtual_device(virtual_device_name):
            self.virtual_router.create_virtual_device(virtual_device_name)
            
        # Store the route
        self.routes[audio_type] = (physical_device_id, virtual_device_name)
        
        return True
        
    def remove_route(self, audio_type):
        """Remove a route for an audio type"""
        if audio_type in self.routes:
            del self.routes[audio_type]
            return True
        return False
        
    def get_route(self, audio_type):
        """Get the route for an audio type"""
        return self.routes.get(audio_type)
        
    def get_all_routes(self):
        """Get all audio routes"""
        return self.routes.copy()
        
    def apply_audio_processing(self, audio_type, processor):
        """
        Apply an audio processor to a specific audio type
        
        Args:
            audio_type: Type of audio (game, movie, music, chat, microphone)
            processor: Audio processor instance
        """
        if audio_type not in self.routes:
            return False
            
        _, virtual_device_name = self.routes[audio_type]
        virtual_device = self.virtual_router.get_virtual_device(virtual_device_name)
        
        if virtual_device:
            virtual_device.add_processor(processor)
            return True
            
        return False
        
    def remove_audio_processing(self, audio_type, processor):
        """Remove an audio processor from a specific audio type"""
        if audio_type not in self.routes:
            return False
            
        _, virtual_device_name = self.routes[audio_type]
        virtual_device = self.virtual_router.get_virtual_device(virtual_device_name)
        
        if virtual_device:
            virtual_device.remove_processor(processor)
            return True
            
        return False
        
    def start_routing(self):
        """Start all audio routing"""
        self.virtual_router.start_all_devices()
        
    def stop_routing(self):
        """Stop all audio routing"""
        self.virtual_router.stop_all_devices()
        
    def refresh_devices(self):
        """Refresh the list of physical audio devices"""
        self.device_manager.refresh_devices()
        
    def get_input_devices(self):
        """Get all input devices"""
        return self.device_manager.get_input_devices()
        
    def get_output_devices(self):
        """Get all output devices"""
        return self.device_manager.get_output_devices()
        
    def get_device_for_audio_type(self, audio_type):
        """Get the currently assigned device dict for an audio type"""
        try:
            return self.device_manager.get_device_for_audio_type(audio_type)
        except Exception:
            return None
        
    def set_device_volume(self, device_index, volume_level):
        """Delegate to device manager to set device volume"""
        return self.device_manager.set_device_volume(device_index, volume_level)

    def list_active_sessions(self):
        """List active audio sessions (programs producing sound)"""
        return self.device_manager.get_active_audio_sessions()

    def set_session_volume(self, pid, volume_level):
        """Set volume for a specific audio session by process id"""
        return self.device_manager.set_session_volume(pid, volume_level)

    def route_session_to_device(self, pid, device_index):
        """Assign a session to a target device (placeholder)"""
        return self.device_manager.route_session_to_device(pid, device_index)

    def __del__(self):
        """Clean up resources"""
        self.stop_routing()

    def set_session_category(self, pid, category):
        """Assign a session to a logical category (game, others, system, chat)."""
        if category not in ['game', 'others', 'system', 'chat']:
            return False
        self.session_categories[pid] = category
        # Immediately route to the device for this category if available
        return self.route_session_to_category(pid, category)

    def get_session_category(self, pid):
        """Return the assigned category for a session PID."""
        return self.session_categories.get(pid)

    def route_session_to_category(self, pid, category):
        """Route the session to the device assigned to the given category."""
        try:
            dev = self.device_manager.get_device_for_audio_type(category)
            if dev and dev.get('index') is not None:
                return self.device_manager.route_session_to_device(pid, dev.get('index'))
        except Exception:
            return False
        return False

    def set_category_volume(self, category, volume_level):
        """Set volume for all sessions assigned to a category.
        Output categories ('game','others','system','chat') adjust per-session volumes.
        For 'microphone', adjust input device endpoint volume if available.
        """
        try:
            if category == 'microphone':
                dev = self.device_manager.get_device_for_audio_type('microphone')
                if dev and dev.get('index') is not None:
                    return self.device_manager.set_device_volume(dev.get('index'), volume_level)
                return False
            # For output categories, change session volumes only
            changed = False
            sessions = self.device_manager.get_active_audio_sessions() or []
            for sess in sessions:
                pid = sess.get('pid') or sess.get('process_id')
                if pid is None:
                    continue
                if self.session_categories.get(pid) == category:
                    ok = self.device_manager.set_session_volume(pid, volume_level)
                    if ok:
                        changed = True
            return changed
        except Exception:
            return False