import numpy as np

class Gate:
    def __init__(self, rate, threshold=0.1):
        self.rate = rate
        self.threshold = threshold
        self.bypass = False

    def apply(self, input_signal):
        if self.bypass:
            return input_signal
        output_signal = np.where(np.abs(input_signal) > self.threshold, input_signal, 0.0)
        return output_signal