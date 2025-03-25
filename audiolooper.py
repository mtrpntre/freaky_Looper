import sounddevice as sd
import numpy as np
import threading
from effects.reverb import ReverbEffect
from effects.gate import GateEffect
from components.recording import RecordingSession
from components.loop_controls import LoopControls

class AudioLooper:
    def __init__(self, rate=44100, chunk=512, format='float32', initial_loop_lengths=[2.0, 4.0, 8.0]):
        self.rate = rate
        self.chunk = chunk
        self.format = format

        self.loop_controls = LoopControls(rate, chunk, format, initial_loop_lengths)

        self.input_device = sd.default.device[0]
        self.output_device = sd.default.device[1]

        # Initialize components
        self.recording_session = RecordingSession(rate)
        self.loop_controls = LoopControls(rate, chunk, format, initial_loop_lengths)
        
        # Effects
        self.reverb = ReverbEffect(rate)
        self.reverb_input_loop = 0
        self.reverb_output_loop = 0
        self.reverb_bypass = True
        self.reverb_overdub = False

        self.gate = GateEffect(rate)
        self.gate_input_loop = 0
        self.gate_output_loop = 0
        self.gate_bypass = True
        self.gate_overdub = False

        self.is_running = True
        self.lock = threading.Lock()

    def __del__(self):
        self.stop()

    def start_recording_session(self):
        self.recording_session.start()

    def stop_recording_session(self):
        self.recording_session.stop()

    def save_recording(self, filename):
        self.recording_session.save(filename)

    def start(self):
        try:
            # Reset PortAudio to clean state
            sd._terminate()
            sd._initialize()
            
            # Configure with higher latency for stability
            self.output_stream = sd.OutputStream(
                device=self.output_device,
                samplerate=self.rate,
                channels=1,
                dtype=self.format,
                blocksize=self.chunk,
                latency='high'
            )
            self.output_stream.start()

            self.input_stream = sd.InputStream(
                device=self.input_device,
                samplerate=self.rate,
                channels=1,
                dtype=self.format,
                blocksize=self.chunk,
                latency='high',
                callback=self.callback
            )
            self.input_stream.start()

            self.playback_thread = threading.Thread(target=self.playback, daemon=True)
            self.playback_thread.start()

        except Exception as e:
            print(f"Audio initialization error: {e}")
            self.stop()
            raise

    def stop(self):
        self.is_running = False
        
        # Stop playback thread first
        if hasattr(self, 'playback_thread'):
            self.playback_thread.join(timeout=0.5)
        
        # Stop and close streams in correct order
        if hasattr(self, 'input_stream'):
            try:
                self.input_stream.stop()
                self.input_stream.close()
                del self.input_stream
            except Exception as e:
                print(f"Error closing input stream: {e}")
        
        if hasattr(self, 'output_stream'):
            try:
                self.output_stream.stop()
                self.output_stream.close()
                del self.output_stream
            except Exception as e:
                print(f"Error closing output stream: {e}")
        
        # Add slight delay to ensure resources are released
        import time
        time.sleep(0.1)
        
        # Force PortAudio cleanup
        try:
            sd._terminate()
        except:
            pass
        
        # Reinitialize for future use
        try:
            sd._initialize()
        except:
            pass

    def playback(self):
        while self.is_running:
            try:
                if not hasattr(self, 'output_stream') or not self.output_stream.active:
                    break
                    
                mixed_buffer = self.mix_loops()
                self.output_stream.write(mixed_buffer)
            except Exception as e:
                if self.is_running:  # Only print errors if we're supposed to be running
                    print(f"Playback error: {e}")
                break

   

    def callback(self, indata, frames, time, status):
        if status:
            print(f"Input stream status: {status}")
        with self.lock:
            if (self.loop_controls.is_recording and 
                self.loop_controls.current_loop < len(self.loop_controls.loops)):
                current_pos = self.loop_controls.loop_positions[self.loop_controls.current_loop]
                if current_pos < self.loop_controls.loop_sizes[self.loop_controls.current_loop]:
                    if self.loop_controls.is_overdubbing:
                        self.loop_controls.loops[self.loop_controls.current_loop][current_pos] = np.clip(
                            self.loop_controls.loops[self.loop_controls.current_loop][current_pos] + indata[:, 0],
                            -1.0, 1.0
                        )
                    else:
                        self.loop_controls.loops[self.loop_controls.current_loop][current_pos] = indata[:, 0]

  

    def mix_loops(self):
        with self.lock:
            mixed_buffer = np.zeros(self.chunk, dtype=self.format)

            any_soloed = any(self.loop_controls.soloed_loops)

            for i in range(len(self.loop_controls.loops)):
                if self.loop_controls.loop_positions[i] < self.loop_controls.loop_sizes[i]:
                    if self.loop_controls.muted_loops[i] or (any_soloed and not self.loop_controls.soloed_loops[i]):
                        continue

                    loop_buffer = self.loop_controls.loops[i][self.loop_controls.loop_positions[i]]

                    # Apply reverb
                    if i == self.reverb_input_loop and not self.reverb_bypass:
                        reverb_output = self.reverb.apply(loop_buffer)
                        if self.reverb_output_loop < len(self.loop_controls.loops):
                            if self.reverb_overdub:
                                self.loop_controls.loops[self.reverb_output_loop][self.loop_controls.loop_positions[self.reverb_output_loop]] += reverb_output
                            else:
                                self.loop_controls.loops[self.reverb_output_loop][self.loop_controls.loop_positions[self.reverb_output_loop]] = reverb_output

                    # Apply gate
                    if i == self.gate_input_loop and not self.gate_bypass:
                        gate_output = self.gate.apply(loop_buffer)
                        if self.gate_output_loop < len(self.loop_controls.loops):
                            if self.gate_overdub:
                                self.loop_controls.loops[self.gate_output_loop][self.loop_controls.loop_positions[self.gate_output_loop]] += gate_output
                            else:
                                self.loop_controls.loops[self.gate_output_loop][self.loop_controls.loop_positions[self.gate_output_loop]] = gate_output

                    mixed_buffer += loop_buffer
                    self.loop_controls.loop_positions[i] = (self.loop_controls.loop_positions[i] + 1) % self.loop_controls.loop_sizes[i]

            if self.recording_session.is_active:
                self.recording_session.add_data(mixed_buffer)

            return np.clip(mixed_buffer, -1.0, 1.0)

    def update_loop_length(self, loop_index, length):
        self.loop_controls.update_loop_length(loop_index, length)