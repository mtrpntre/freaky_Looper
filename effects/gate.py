import numpy as np

class GateEffect:
    """Enhanced gate effect with attack/release controls"""
    def __init__(self, rate, threshold=0.1, attack_ms=10, release_ms=100):
        self.rate = rate
        self.threshold = threshold
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.attack_samples = int(rate * attack_ms / 1000)
        self.release_samples = int(rate * release_ms / 1000)
        self.gain = 0.0
        
    def apply(self, input_signal):
        output_signal = np.zeros_like(input_signal)
        
        for i in range(len(input_signal)):
            # Determine if signal is above threshold
            if abs(input_signal[i]) > self.threshold:
                # Attack phase
                self.gain = min(1.0, self.gain + 1.0/self.attack_samples)
            else:
                # Release phase
                self.gain = max(0.0, self.gain - 1.0/self.release_samples)
                
            output_signal[i] = input_signal[i] * self.gain
            
        return output_signal