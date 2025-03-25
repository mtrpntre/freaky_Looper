import numpy as np
from scipy.signal import resample_poly
import warnings

class PitchShiftEffect:
    """More robust pitch shifting implementation"""
    def __init__(self, rate, semitones=0, quality='medium'):
        self.rate = rate
        self.semitones = semitones
        self.quality = quality
        self.set_quality(quality)
        
    def set_quality(self, quality):
        """Set resampling quality"""
        self.quality = quality
        # Larger window sizes give better quality but are more CPU intensive
        self.window_size = {
            'low': 64,
            'medium': 128,
            'high': 256
        }.get(quality.lower(), 128)
        
    def apply(self, input_signal):
        """Apply pitch shift to the input signal"""
        if self.semitones == 0 or len(input_signal) == 0:
            return input_signal.copy()
            
        try:
            # Changed sign here to correct direction
            ratio = 2 ** (-self.semitones / 12.0)  # Negative sign fixes direction
            
            # For downsampling (pitch down), we need to prevent aliasing
            if ratio < 1.0:
                input_signal = self._anti_alias_filter(input_signal, ratio)
            
            # Calculate resampling factors
            up = int(100 * ratio)
            down = 100
            
            # Suppress scipy's warning about perfect reconstruction
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                output_signal = resample_poly(
                    input_signal, 
                    up, 
                    down, 
                    window=('kaiser', self.window_size))
            
            # Maintain original length
            if len(output_signal) > len(input_signal):
                return output_signal[:len(input_signal)]
            else:
                return np.pad(output_signal, (0, max(0, len(input_signal) - len(output_signal))), 
                            mode='constant')
        except Exception as e:
            print(f"Pitch shift error: {e}")
            return input_signal.copy()
    
    def _anti_alias_filter(self, signal, ratio):
        """Simple anti-aliasing filter for pitch reduction"""
        # This is a basic low-pass filter - could be improved
        b = [0.05, 0.1, 0.2, 0.3, 0.2, 0.1, 0.05]
        a = 1
        return np.convolve(signal, b, mode='same')