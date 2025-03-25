import numpy as np

class Reverb:
    def __init__(self, rate, decay=0.5, wet=0.5):
        self.rate = rate
        self.decay = decay
        self.wet = wet
        self.buffer = np.zeros(int(rate * 0.1))

    def apply(self, input_signal):
        output_signal = np.zeros_like(input_signal)
        for i in range(len(input_signal)):
            delayed_sample = self.buffer[-1] * self.decay
            output_signal[i] = input_signal[i] + delayed_sample
            self.buffer = np.roll(self.buffer, 1)
            self.buffer[0] = output_signal[i]
        return (1 - self.wet) * input_signal + self.wet * output_signal