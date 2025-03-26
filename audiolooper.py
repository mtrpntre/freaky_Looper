import sounddevice as sd
import numpy as np
import threading
from effects.reverb import ReverbEffect
from effects.gate import GateEffect
from effects.pitch_shift import PitchShiftEffect
from components.recording import RecordingSession
from components.loop_controls import LoopControls


class AudioLooper:
    def __init__(self, rate=44100, chunk=1024, format='float32', initial_loop_lengths=[2.0, 4.0, 8.0]):
        self.rate = rate
        self.chunk = chunk
        self.format = format

    
        self.loops = {}
        self.loop_sizes = {}
        self.loop_positions = {}
        self.muted_loops = {}
        self.soloed_loops = {}
        self.next_loop_id = 0

        self.is_recording = False
        self.is_overdubbing = False

        for length in initial_loop_lengths:
            self.add_loop(length)


        self.current_loop_id = min(self.loops.keys()) if self.loops else None

        self.input_device = sd.default.device[0]
        self.output_device = sd.default.device[1]

        # Initialize components
        self.recording_session = RecordingSession(rate)
        self.is_session_recording = False
        self.loop_controls = LoopControls(rate, chunk, format, initial_loop_lengths)


        
        # Effects
        self.reverb = ReverbEffect(rate)
        self.reverb_input_id = None  # Will be set when loops exist
        self.reverb_output_id = None
        self.reverb_bypass = True
        self.reverb_overdub = False

        self.gate = GateEffect(rate)
        self.gate_input_id = None
        self.gate_output_id = None
        self.gate_bypass = True
        self.gate_overdub = False

        self.pitch_shift = PitchShiftEffect(rate)
        self.pitch_input_id = None
        self.pitch_output_id = None
        self.pitch_bypass = True
        self.pitch_overdub = False
        self.pitch_feedback = 0.0  # 0.0-1.0 range, start with 0 for no feedback

        if initial_loop_lengths:
            self.pitch_input_id = next(iter(self.loop_controls.loops.keys()), None)
            self.pitch_output_id = next(iter(self.loop_controls.loops.keys()), None)
        else:
            self.pitch_input_id = None
            self.pitch_output_id = None

        self.is_running = True
        self.lock = threading.Lock()

        
        if initial_loop_lengths:
            first_loop = next(iter(self.loop_controls.loops.keys()), None)
            self.pitch_input_id = first_loop
            self.pitch_output_id = first_loop
            self.reverb_input_id = first_loop 
            self.reverb_output_id = first_loop
            self.gate_input_id = first_loop
            self.gate_output_id = first_loop

    def __del__(self):
        self.stop()

    def start_recording_session(self):
        """Start recording the full mix to session"""
        self.recording_session.start()
        self.is_session_recording = True
        print("Session recording started - recording all audio output")

    def stop_recording_session(self):
        """Stop session recording"""
        if self.is_session_recording:
            self.recording_session.stop()
            self.is_session_recording = False
            print("Session recording stopped")
        else:
            print("No active session to stop")

    def save_recording(self, filename):
        """Save the session recording to file"""
        try:
            if not self.recording_session.is_active and len(self.recording_session.recorded_data) > 0:
                self.recording_session.save(filename)
                print(f"Session saved to {filename}")
                return True
            else:
                print("No recording data to save")
                return False
        except Exception as e:
            print(f"Error saving session: {str(e)}")
            raise

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
            current_loop_id = self.loop_controls.current_loop_id
            if (self.loop_controls.is_recording and 
                current_loop_id is not None and
                current_loop_id in self.loop_controls.loops):
                
                current_pos = self.loop_controls.loop_positions[current_loop_id]
                loop_size = self.loop_controls.loop_sizes[current_loop_id]
                
                if current_pos < loop_size:
                    if self.loop_controls.is_overdubbing:
                        self.loop_controls.loops[current_loop_id][current_pos] = np.clip(
                            self.loop_controls.loops[current_loop_id][current_pos] + indata[:, 0],
                            -1.0, 1.0
                        )
                    else:
                        self.loop_controls.loops[current_loop_id][current_pos] = indata[:, 0]


    def mix_loops(self):
        output = np.zeros(self.chunk, dtype=self.format)
        
        with self.lock:
            # Process live input (if recording)
            if self.loop_controls.is_recording and self.loop_controls.current_loop_id is not None:
                current_loop_id = self.loop_controls.current_loop_id
                pos = self.loop_controls.loop_positions[current_loop_id]
                audio_data = self.loop_controls.loops[current_loop_id][pos].copy()
                
                processed = self.process_effects(current_loop_id, audio_data)
                output += processed

                # Update loop buffer
                if self.loop_controls.is_overdubbing:
                    self.loop_controls.loops[current_loop_id][pos] = np.clip(
                        self.loop_controls.loops[current_loop_id][pos] + processed,
                        -1.0, 1.0
                    )
                else:
                    self.loop_controls.loops[current_loop_id][pos] = processed
                
                self.loop_controls.loop_positions[current_loop_id] = (pos + 1) % self.loop_controls.loop_sizes[current_loop_id]
            
            # Process all other loops
            for loop_id in self.loop_controls.loops:
                if self.loop_controls.is_recording and loop_id == self.loop_controls.current_loop_id:
                    continue
                    
                pos = self.loop_controls.loop_positions[loop_id]
                audio_data = self.loop_controls.loops[loop_id][pos].copy()
                
                # Skip muted/soloed loops
                if ((self.loop_controls.muted_loops.get(loop_id, False) and 
                    not any(self.loop_controls.soloed_loops.values())) or
                    (any(self.loop_controls.soloed_loops.values()) and 
                    not self.loop_controls.soloed_loops.get(loop_id, False))):
                    continue
                
                processed = self.process_effects(loop_id, audio_data)
                
                if not self._is_effect_input_routed(loop_id):
                    output += processed
                
                self.loop_controls.loop_positions[loop_id] = (pos + 1) % self.loop_controls.loop_sizes[loop_id]
            
            # Record the final mixed output (ONCE per buffer)
            if self.is_session_recording:
                self.recording_session.add_data(output.copy())
        
        return np.clip(output, -1.0, 1.0)

    def process_effects(self, loop_id, audio_data):
        """Process audio through all active effects"""
        processed = audio_data.copy()
        
        # Gate first
        if not self.gate_bypass and loop_id == self.gate_input_id:
            processed = self.gate.apply(processed)
        
        # Then pitch shift
        if not self.pitch_bypass and loop_id == self.pitch_input_id:
            processed = self.pitch_shift.apply(processed)
            
            # Handle feedback if routing to same loop
            if (self.pitch_output_id == loop_id and 
                hasattr(self, 'pitch_feedback') and 
                self.pitch_feedback > 0):
                
                # Get previous buffer content
                prev_audio = self.loop_controls.loops[loop_id][
                    (self.loop_controls.loop_positions[loop_id] - 1) % 
                    self.loop_controls.loop_sizes[loop_id]
                ]
                
                # Mix with feedback
                processed = np.clip(
                    processed + (prev_audio * self.pitch_feedback),
                    -1.0, 1.0
                )
        
        # Then reverb
        if not self.reverb_bypass and loop_id == self.reverb_input_id:
            processed = self.reverb.apply(processed)
        
        return processed

    def route_effect_outputs(self, loop_id, processed_audio):
        """Route processed audio to effect output loops based on settings"""
        # Handle pitch shift routing
        if (not self.pitch_bypass and 
            loop_id == self.pitch_input_id and 
            self.pitch_output_id in self.loop_controls.loops):
            
            out_pos = self.loop_controls.loop_positions[self.pitch_output_id]
            if self.pitch_overdub:
                self.loop_controls.loops[self.pitch_output_id][out_pos] = np.clip(
                    self.loop_controls.loops[self.pitch_output_id][out_pos] + processed_audio,
                    -1.0, 1.0
                )
            else:
                self.loop_controls.loops[self.pitch_output_id][out_pos] = processed_audio
        
        # Handle reverb routing
        if (not self.reverb_bypass and 
            loop_id == self.reverb_input_id and 
            self.reverb_output_id in self.loop_controls.loops):
            
            out_pos = self.loop_controls.loop_positions[self.reverb_output_id]
            if self.reverb_overdub:
                self.loop_controls.loops[self.reverb_output_id][out_pos] = np.clip(
                    self.loop_controls.loops[self.reverb_output_id][out_pos] + processed_audio,
                    -1.0, 1.0
                )
            else:
                self.loop_controls.loops[self.reverb_output_id][out_pos] = processed_audio
        
        # Handle gate routing
        if (not self.gate_bypass and 
            loop_id == self.gate_input_id and 
            self.gate_output_id in self.loop_controls.loops):
            
            out_pos = self.loop_controls.loop_positions[self.gate_output_id]
            if self.gate_overdub:
                self.loop_controls.loops[self.gate_output_id][out_pos] = np.clip(
                    self.loop_controls.loops[self.gate_output_id][out_pos] + processed_audio,
                    -1.0, 1.0
                )
            else:
                self.loop_controls.loops[self.gate_output_id][out_pos] = processed_audio

    def update_loop_length(self, loop_id, length):
        with self.lock:
            if loop_id in self.loop_controls.loops:
                self.loop_controls.update_loop_length(loop_id, length)

    def add_loop(self, length):
        loop_id = self.next_loop_id
        size = int(self.rate / self.chunk * length)
        
        self.loops[loop_id] = np.zeros((size, self.chunk), dtype=self.format)
        self.loop_sizes[loop_id] = size
        self.loop_positions[loop_id] = 0
        self.muted_loops[loop_id] = False
        self.soloed_loops[loop_id] = False
        
        self.next_loop_id += 1
        return loop_id

    def delete_loop(self, loop_id):
        if len(self.loops) <= 1:
            raise ValueError("Cannot delete - must have at least one loop")
        
        del self.loops[loop_id]
        del self.loop_sizes[loop_id]
        del self.loop_positions[loop_id]
        del self.muted_loops[loop_id]
        del self.soloed_loops[loop_id]
        
        if self.current_loop_id == loop_id:
            self.current_loop_id = min(self.loops.keys()) if self.loops else None

    def _is_effect_input_routed(self, loop_id):
        """Check if this loop is an effect input being routed to a different output"""
        return ((not self.gate_bypass and loop_id == self.gate_input_id and self.gate_output_id != loop_id) or
                (not self.pitch_bypass and loop_id == self.pitch_input_id and self.pitch_output_id != loop_id) or
                (not self.reverb_bypass and loop_id == self.reverb_input_id and self.reverb_output_id != loop_id))

    def process_effects(self, loop_id, audio_data):
        """Process audio through all active effects and handle routing"""
        processed = audio_data.copy()
        
        # Gate processing
        if not self.gate_bypass and loop_id == self.gate_input_id:
            processed = self.gate.apply(processed)
            if self.gate_output_id in self.loop_controls.loops:
                self._route_effect_output(loop_id, processed, self.gate_output_id, self.gate_overdub)
        
        # Pitch processing
        if not self.pitch_bypass and loop_id == self.pitch_input_id:
            processed = self.pitch_shift.apply(processed)
            if self.pitch_output_id in self.loop_controls.loops:
                self._route_effect_output(loop_id, processed, self.pitch_output_id, self.pitch_overdub)
        
        # Reverb processing
        if not self.reverb_bypass and loop_id == self.reverb_input_id:
            processed = self.reverb.apply(processed)
            if self.reverb_output_id in self.loop_controls.loops:
                self._route_effect_output(loop_id, processed, self.reverb_output_id, self.reverb_overdub)
        
        return processed

    def _route_effect_output(self, src_loop_id, processed_audio, dest_loop_id, overdub):
        """Route processed audio to another loop"""
        dest_pos = self.loop_controls.loop_positions[dest_loop_id]
        if overdub:
            self.loop_controls.loops[dest_loop_id][dest_pos] = np.clip(
                self.loop_controls.loops[dest_loop_id][dest_pos] + processed_audio,
                -1.0, 1.0
            )
        else:
            self.loop_controls.loops[dest_loop_id][dest_pos] = processed_audio
        
        