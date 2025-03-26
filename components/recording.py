import numpy as np
from scipy.io.wavfile import write

class RecordingSession:
    def __init__(self, rate):
        self.rate = rate
        self.is_active = False
        self.recorded_data = []
        
    def start(self):
        self.is_active = True
        self.recorded_data = []
        
    def stop(self):
        self.is_active = False
        
    def add_data(self, audio_data):
        if self.is_active:
            # Ensure proper shape (mono)
            chunk = np.asarray(audio_data, dtype=np.float32).flatten()
            self.recorded_data.append(chunk)
            
    def save(self, filename):
        if not self.recorded_data:
            raise ValueError("No recorded data to save")
            
        audio_data = np.concatenate(self.recorded_data)
        audio_data = np.clip(audio_data, -1.0, 1.0)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        write(filename, self.rate, audio_data)