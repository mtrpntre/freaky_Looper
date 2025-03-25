import numpy as np

class ReverbEffect:
    """Enhanced reverb effect with configurable parameters"""
    def __init__(self, rate, decay=0.5, wet=0.5, delay_ms=100):
        self.rate = rate
        self.decay = decay
        self.wet = wet
        self.delay_ms = delay_ms
        self.delay_samples = int(rate * delay_ms / 1000)
        self.buffer = np.zeros(self.delay_samples)
        
    def apply(self, input_signal):
        output_signal = np.zeros_like(input_signal)
        for i in range(len(input_signal)):
            # Get the delayed sample
            delayed_sample = self.buffer[-1] * self.decay
            
            # Mix with input
            output_signal[i] = input_signal[i] + delayed_sample
            
            # Update buffer
            self.buffer = np.roll(self.buffer, 1)
            self.buffer[0] = output_signal[i]
            
        # Apply wet/dry mix
        return (1 - self.wet) * input_signal + self.wet * output_signal