import numpy as np
from scipy.io.wavfile import write

class RecordingSession:
    def __init__(self, rate):
        self.rate = rate
        self.is_active = False
        self.recorded_data = []
        
    def start(self):
        """Start a new recording session"""
        self.is_active = True
        self.recorded_data = []
        
    def stop(self):
        """Stop the current recording session"""
        self.is_active = False
        
    def add_data(self, audio_data):
        """Add audio data to the recording"""
        if self.is_active:
            self.recorded_data.append(audio_data)
            
    def save(self, filename):
        """Save the recorded audio to a file"""
        if not self.recorded_data:
            raise ValueError("No recorded data to save")
            
        audio_data = np.concatenate(self.recorded_data, axis=0)
        write(filename, self.rate, audio_data)