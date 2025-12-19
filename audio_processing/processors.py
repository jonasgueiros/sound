"""
Audio processors for enhancing audio quality
"""
import numpy as np
from scipy import signal

# Try to import native DSP backend (Rust via pyo3)
try:
    import native_dsp
except Exception:
    native_dsp = None

class AudioProcessor:
    """Base class for all audio processors"""
    def __init__(self):
        self.enabled = True
        # Processing format (optional; set by host)
        self.sample_rate = None
        self.channels = None
        self.blocksize = None
        
    def process(self, data):
        """Process audio data"""
        if not self.enabled:
            return data
        return self._process_impl(data)
        
    def _process_impl(self, data):
        """Implementation of the processing algorithm"""
        # Base class does nothing
        return data
        
    def enable(self):
        """Enable the processor"""
        self.enabled = True
        
    def disable(self):
        """Disable the processor"""
        self.enabled = False
        
    def toggle(self):
        """Toggle the processor state"""
        self.enabled = not self.enabled

    def set_format(self, sample_rate=None, channels=None, blocksize=None):
        """Configure processing format (sample rate, channels, blocksize)."""
        # Base implementation stores values; subclasses may override.
        if sample_rate is not None:
            self.sample_rate = int(sample_rate)
        if channels is not None:
            self.channels = int(channels)
        if blocksize is not None:
            self.blocksize = int(blocksize)


class Equalizer(AudioProcessor):
    """
    Multi-band equalizer for audio processing.

    Attributes:
        sample_rate (float): The sample rate of the audio data.
        bands (int): The number of frequency bands in the equalizer.
        _native (Optional[EqualizerEngine]): Native DSP backend for processing.
    """

    def __init__(self, sample_rate=48000, bands=10):
        """
        Initialize the Equalizer.

        Args:
            sample_rate (float): The sample rate of the audio data.
            bands (int): The number of frequency bands in the equalizer.
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.bands = bands
        self._native = None

        # Initialize native backend with error handling
        if native_dsp is not None:
            try:
                self._native = native_dsp.EqualizerEngine(float(self.sample_rate), int(self.bands), 2)
            except Exception as e:
                print(f"Failed to initialize native DSP backend: {e}")
                self._native = None

        # Ensure _native is always defined
        self._native = None

        # Initialize band frequencies (logarithmically spaced)
        self.min_freq = 20
        self.max_freq = 20000
        self.frequencies = np.logspace(
            np.log10(self.min_freq),
            np.log10(self.max_freq),
            bands
        )

        # Initialize gains (in dB)
        # Target gains set by UI
        self.gains = np.zeros(bands)
        # Smoothed gains used for filter design to avoid clicks
        self._smoothed_gains = np.zeros(bands)
        # Smoothing parameters
        self._smoothing_tau_sec = 0.03  # ~30ms smoothing
        self._alpha = 0.2               # fallback alpha if format unknown
        self._epsilon_db = 0.05         # threshold for filter update
        self._needs_update = True

        # Output gain (master volume boost in dB)
        self.output_gain_db = 0.0

        # Initialize filters
        self.update_filters()

    def set_format(self, sample_rate=None, channels=None, blocksize=None):
        """Update processing format and recompute filters when sample rate changes."""
        super().set_format(sample_rate, channels, blocksize)
        if sample_rate is not None:
            # Recompute filters for new sample rate
            try:
                self.update_filters()
            except Exception:
                pass
        # Propagate to native backend
        if self._native is not None:
            try:
                fs = float(self.sample_rate or sample_rate or 48000)
                ch = int(self.channels or channels or 2)
                self._native.set_format(fs, ch)
            except Exception:
                pass
        
    def update_filters(self, gains=None):
        """Update filter coefficients based on provided gains (in dB)."""
        self.filters = []
        if gains is None:
            gains = self.gains
        
        for i, freq in enumerate(self.frequencies):
            if abs(gains[i]) < 0.1:  # Skip if gain is close to 0 dB
                continue
                
            # Convert from dB to linear gain
            gain = 10 ** (gains[i] / 20)
            
            # Create a peaking EQ filter
            Q = 1.0  # Filter quality factor
            
            if i == 0:  # Lowest band - use low shelf
                b, a = signal.butter(2, freq / (self.sample_rate/2), 'low')
                if gains[i] > 0:
                    b = b * gain
                else:
                    a = a * gain
            elif i == self.bands - 1:  # Highest band - use high shelf
                b, a = signal.butter(2, freq / (self.sample_rate/2), 'high')
                if gains[i] > 0:
                    b = b * gain
                else:
                    a = a * gain
            else:  # Mid bands - use peaking EQ
                bandwidth = freq / Q
                b, a = signal.butter(2, [
                    (freq - bandwidth/2) / (self.sample_rate/2),
                    (freq + bandwidth/2) / (self.sample_rate/2)
                ], 'band')
                if gains[i] > 0:
                    b = b * gain
                else:
                    a = a * gain
                
            self.filters.append((b, a))
        # Propagate to native backend
        if self._native is not None:
            try:
                self._native.set_gains([float(g) for g in gains])
            except Exception:
                pass
        
    def set_gain(self, band, gain_db):
        """Set the gain for a specific frequency band"""
        if band < 0 or band >= self.bands:
            raise ValueError(f"Band index {band} out of range")
            
        # Update target gain; defer filter recompute to process for smoothing
        self.gains[band] = gain_db
        self._needs_update = True
        # Propagate to native backend using full gains vector (smoothed applied in process)
        if self._native is not None:
            try:
                self._native.set_gains([float(g) for g in self.gains])
            except Exception:
                pass

    def set_bands(self, bands):
        """Change the number of bands and rebuild filters"""
        bands = int(max(1, bands))
        # Preserve existing gains up to new size
        old_gains = np.array(self.gains) if hasattr(self, 'gains') else np.zeros(0)
        self.bands = bands
        self.frequencies = np.logspace(
            np.log10(self.min_freq),
            np.log10(self.max_freq),
            bands
        )
        new_gains = np.zeros(bands)
        copy_count = min(len(old_gains), bands)
        if copy_count > 0:
            new_gains[:copy_count] = old_gains[:copy_count]
        self.gains = new_gains
        self._smoothed_gains = np.array(new_gains)
        self.update_filters(self._smoothed_gains)
        if self._native is not None:
            try:
                self._native.set_bands(int(self.bands))
                self._native.set_gains([float(g) for g in self._smoothed_gains])
            except Exception:
                pass

    def set_output_gain(self, gain_db):
        """Set master output gain in dB (applied post EQ)"""
        try:
            self.output_gain_db = float(gain_db)
        except Exception:
            self.output_gain_db = 0.0
        # Native backend output gain
        if self._native is not None:
            try:
                self._native.set_output_gain(float(self.output_gain_db))
            except Exception:
                pass

    def set_smoothing_time(self, tau_seconds):
        """Set smoothing time constant for parameter changes (in seconds)."""
        try:
            self._smoothing_tau_sec = max(0.0, float(tau_seconds))
        except Exception:
            pass
        
    def process(self, data):
        """
        Process audio data.

        Args:
            data (np.ndarray): The audio data to process.

        Returns:
            np.ndarray: The processed audio data.
        """
        if not self.enabled:
            return data

        try:
            if self._native:
                return self._native.process(data)
            else:
                return self._process_impl(data)
        except Exception as e:
            print(f"Error during processing: {e}")
            return data

    def _process_impl(self, data):
        """
        Optimized processing implementation.

        Args:
            data (np.ndarray): The audio data to process.

        Returns:
            np.ndarray: The processed audio data.
        """
        # Use NumPy for efficient batch processing
        if self.bands == 0 or data.size == 0:
            return data

        try:
            # Apply each band filter in sequence
            for band in range(self.bands):
                # Example: Apply a simple gain adjustment per band
                data *= self.gains[band]
        except Exception as e:
            print(f"Error in processing chain: {e}")

        return data


class BassBoost(AudioProcessor):
    """Bass boost processor"""
    def __init__(self, sample_rate=48000, cutoff=200, gain_db=6):
        super().__init__()
        self.sample_rate = sample_rate
        self.cutoff = cutoff
        self.gain_db = gain_db
        self.update_filter()

    def set_format(self, sample_rate=None, channels=None, blocksize=None):
        """Update processing format and recompute filter when sample rate changes."""
        super().set_format(sample_rate, channels, blocksize)
        if sample_rate is not None:
            try:
                self.update_filter()
            except Exception:
                pass
        
    def update_filter(self):
        """Update filter coefficients"""
        # Create a low-shelf filter
        self.b, self.a = signal.butter(
            2, 
            self.cutoff / (self.sample_rate/2),
            'low'
        )
        
        # Apply gain
        gain = 10 ** (self.gain_db / 20)
        self.b = self.b * gain
        
    def set_gain(self, gain_db):
        """Set the bass boost gain"""
        self.gain_db = gain_db
        self.update_filter()
        
    def set_cutoff(self, cutoff):
        """Set the cutoff frequency"""
        self.cutoff = cutoff
        self.update_filter()
        
    def _process_impl(self, data):
        """Apply bass boost to audio data"""
        return signal.lfilter(self.b, self.a, data, axis=0)


class SpatialEnhancer(AudioProcessor):
    """Spatial audio enhancer for 3D/surround effect"""
    def __init__(self, width = 0.5):
        super().__init__()
        self.width = max(0, min(1, width))
        
    def set_width(self, width):
        """Set the stereo width"""
        self.width = max(0, min(1, width))

    def set_format(self, sample_rate=None, channels=None, blocksize=None):
        """Store format; can be used to validate stereo channel count."""
        super().set_format(sample_rate, channels, blocksize)
        
    def _process_impl(self, data):
        """Apply spatial enhancement to audio data"""
        if data.shape[1] != 2:  # Only works with stereo
            return data
            
        # Simple stereo widening
        mid = (data[:, 0] + data[:, 1]) / 2
        side = (data[:, 0] - data[:, 1]) / 2
        
        # Enhance the side signal
        side = side * (1 + self.width)
        
        # Recombine
        left = mid + side
        right = mid - side
        
        result = np.column_stack((left, right))
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(result))
        if max_val > 1.0:
            result = result / max_val
            
        return result


class NoiseReducer(AudioProcessor):
    """Simple noise reduction processor"""
    def __init__(self, threshold=0.1):
        super().__init__()
        self.threshold = threshold
        
    def set_threshold(self, threshold):
        """Set the noise threshold"""
        self.threshold = max(0, min(1, threshold))
        
    def _process_impl(self, data):
        """Apply noise reduction to audio data"""
        # Simple noise gate
        magnitude = np.abs(data)
        mask = magnitude > self.threshold
        
        # Apply soft mask
        soft_mask = np.clip((magnitude - self.threshold) / self.threshold, 0, 1)
        
        # Apply the mask
        result = data * soft_mask[:, np.newaxis] if len(data.shape) > 1 else data * soft_mask
        
        return result
