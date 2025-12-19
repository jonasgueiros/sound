"""
Virtual audio device management for routing audio between different applications
"""
import numpy as np
import sounddevice as sd

class VirtualAudioDevice:
    """
    Creates a virtual audio device for routing audio between applications
    """
    def __init__(self, name, channels=2, sample_rate=48000, buffer_size=1024):
        self.name = name
        self.channels = channels
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.buffer = np.zeros((buffer_size, channels), dtype=np.float32)
        self.is_active = False
        self.stream = None
        self.processing_chain = []
        
    def start(self):
        """Start the virtual audio device"""
        if self.is_active:
            return
            
        def callback(indata, outdata, frames, time, status):
            """Audio callback for processing audio data"""
            if status:
                print(f"Status: {status}")
                
            # Copy input data to our buffer
            self.buffer[:frames] = indata[:frames]
            
            # Apply processing chain
            processed_data = self.buffer[:frames].copy()
            for processor in self.processing_chain:
                processed_data = processor.process(processed_data)
                
            # Copy processed data to output
            outdata[:frames] = processed_data
        
        # Inform processors of format prior to stream start
        try:
            for processor in self.processing_chain:
                try:
                    processor.set_format(sample_rate=self.sample_rate,
                                          channels=self.channels,
                                          blocksize=self.buffer_size)
                except Exception:
                    pass
        except Exception:
            pass

        self.stream = sd.Stream(
            channels=self.channels,
            samplerate=self.sample_rate,
            blocksize=self.buffer_size,
            callback=callback
        )
        self.stream.start()
        self.is_active = True
        
    def stop(self):
        """Stop the virtual audio device"""
        if not self.is_active:
            return
            
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        self.is_active = False
        
    def add_processor(self, processor):
        """Add an audio processor to the processing chain"""
        self.processing_chain.append(processor)
        # Configure processor with current device format
        try:
            processor.set_format(sample_rate=self.sample_rate,
                                 channels=self.channels,
                                 blocksize=self.buffer_size)
        except Exception:
            pass
        
    def remove_processor(self, processor):
        """Remove an audio processor from the processing chain"""
        if processor in self.processing_chain:
            self.processing_chain.remove(processor)
            
    def clear_processors(self):
        """Clear all processors from the processing chain"""
        self.processing_chain = []
        
    def __del__(self):
        """Clean up resources"""
        self.stop()


class VirtualAudioRouter:
    """
    Manages multiple virtual audio devices and routes audio between them
    """
    def __init__(self):
        self.virtual_devices = {}
        self.routing_table = {}  # Maps source to destination
        
    def create_virtual_device(self, name, channels=2, sample_rate=48000, buffer_size=1024):
        """Create a new virtual audio device"""
        if name in self.virtual_devices:
            raise ValueError(f"Virtual device '{name}' already exists")
            
        device = VirtualAudioDevice(name, channels, sample_rate, buffer_size)
        self.virtual_devices[name] = device
        return device
        
    def remove_virtual_device(self, name):
        """Remove a virtual audio device"""
        if name not in self.virtual_devices:
            return False
            
        # Stop the device and remove it
        device = self.virtual_devices[name]
        device.stop()
        
        # Remove any routes involving this device
        for source in list(self.routing_table.keys()):
            if source == name or self.routing_table[source] == name:
                del self.routing_table[source]
                
        # Remove the device
        del self.virtual_devices[name]
        return True
        
    def get_virtual_device(self, name):
        """Get a virtual audio device by name"""
        return self.virtual_devices.get(name)
        
    def route_audio(self, source_name, destination_name):
        """Route audio from one virtual device to another"""
        if source_name not in self.virtual_devices:
            raise ValueError(f"Source device '{source_name}' does not exist")
            
        if destination_name not in self.virtual_devices:
            raise ValueError(f"Destination device '{destination_name}' does not exist")
            
        # Add the route
        self.routing_table[source_name] = destination_name
        
        # Make sure both devices are active
        self.virtual_devices[source_name].start()
        self.virtual_devices[destination_name].start()
        
        return True
        
    def remove_route(self, source_name):
        """Remove an audio route"""
        if source_name in self.routing_table:
            del self.routing_table[source_name]
            return True
        return False
        
    def get_route(self, source_name):
        """Get the destination for a source device"""
        return self.routing_table.get(source_name)
        
    def get_all_routes(self):
        """Get all audio routes"""
        return self.routing_table.copy()
        
    def start_all_devices(self):
        """Start all virtual audio devices"""
        for device in self.virtual_devices.values():
            device.start()
            
    def stop_all_devices(self):
        """Stop all virtual audio devices"""
        for device in self.virtual_devices.values():
            device.stop()
            
    def __del__(self):
        """Clean up resources"""
        self.stop_all_devices()
