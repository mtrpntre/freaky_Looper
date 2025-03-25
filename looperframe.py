import wx
import numpy as np
from components.reverb import Reverb
from components.gate import Gate

class LooperFrame(wx.Frame):
    def __init__(self, looper):
        super().__init__(None, title="Audio Looper", size=(1000, 700))
        self.looper = looper
        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.main_sizer)

        # Initialize all UI components first
        self.reverb_input_choice = None
        self.reverb_output_choice = None
        self.reverb_decay_slider = None
        self.reverb_wet_slider = None
        self.bypass_reverb_button = None
        self.reverb_overdub_button = None

        self.gate_input_choice = None
        self.gate_output_choice = None
        self.gate_threshold_slider = None      
        self.bypass_gate_button = None
        self.gate_overdub_button = None

        # Create controls
        self.create_top_controls()
        self.create_loop_controls()
        self.create_bottom_controls()

        # Initialize loop controls UI
        self.loop_controls = []
        for i in range(len(self.looper.loop_controls.loop_sizes)):
            initial_length = int(self.looper.loop_controls.loop_sizes[i] * self.looper.chunk / self.looper.rate)
            self.add_loop_controls(i, initial_length)

        # Update UI state
        self.update_selected_loop_highlight()
        self.update_effect_controls()

    def create_top_controls(self):
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Recording section
        recording_box = wx.StaticBox(self.panel, label="Recording")
        recording_sizer = wx.StaticBoxSizer(recording_box, wx.VERTICAL)
        
        self.recording_button = wx.Button(self.panel, label="Record: Off")
        self.recording_button.Bind(wx.EVT_BUTTON, self.toggle_recording)
        recording_sizer.Add(self.recording_button, 0, wx.ALL|wx.EXPAND, 5)
        
        self.overdub_button = wx.Button(self.panel, label="Overdub: Off")
        self.overdub_button.Bind(wx.EVT_BUTTON, self.toggle_overdub)
        recording_sizer.Add(self.overdub_button, 0, wx.ALL|wx.EXPAND, 5)
        
        self.start_recording_button = wx.Button(self.panel, label="Start Session")
        self.start_recording_button.Bind(wx.EVT_BUTTON, self.start_recording_session)
        recording_sizer.Add(self.start_recording_button, 0, wx.ALL|wx.EXPAND, 5)
        
        self.stop_recording_button = wx.Button(self.panel, label="Stop Session")
        self.stop_recording_button.Bind(wx.EVT_BUTTON, self.stop_recording_session)
        self.stop_recording_button.Disable()
        recording_sizer.Add(self.stop_recording_button, 0, wx.ALL|wx.EXPAND, 5)
        
        self.save_recording_button = wx.Button(self.panel, label="Save Recording")
        self.save_recording_button.Bind(wx.EVT_BUTTON, self.save_recording)
        self.save_recording_button.Disable()
        recording_sizer.Add(self.save_recording_button, 0, wx.ALL|wx.EXPAND, 5)
        
        top_sizer.Add(recording_sizer, 1, wx.EXPAND|wx.ALL, 5)

        # Reverb section
        reverb_box = wx.StaticBox(self.panel, label="Reverb")
        reverb_sizer = wx.StaticBoxSizer(reverb_box, wx.VERTICAL)
        
        self.bypass_reverb_button = wx.Button(self.panel, label="Bypass Reverb: On")
        reverb_sizer.Add(self.bypass_reverb_button, 0, wx.ALL|wx.EXPAND, 5)
        
        reverb_controls = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)

        reverb_controls.Add(wx.StaticText(self.panel, label="Delay (ms):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.reverb_delay_slider = wx.Slider(self.panel, value=150, minValue=50, maxValue=500)
        reverb_controls.Add(self.reverb_delay_slider, 0, wx.EXPAND)
        
        reverb_controls.Add(wx.StaticText(self.panel, label="Input Loop:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.reverb_input_choice = wx.Choice(self.panel, choices=[f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))])
        self.reverb_input_choice.SetSelection(0)
        reverb_controls.Add(self.reverb_input_choice, 0, wx.EXPAND)
        
        reverb_controls.Add(wx.StaticText(self.panel, label="Output Loop:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.reverb_output_choice = wx.Choice(self.panel, choices=[f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))])
        self.reverb_output_choice.SetSelection(0)
        reverb_controls.Add(self.reverb_output_choice, 0, wx.EXPAND)
        
        reverb_controls.Add(wx.StaticText(self.panel, label="Decay:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.reverb_decay_slider = wx.Slider(self.panel, value=50, minValue=0, maxValue=100)
        reverb_controls.Add(self.reverb_decay_slider, 0, wx.EXPAND)
        
        reverb_controls.Add(wx.StaticText(self.panel, label="Wet/Dry:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.reverb_wet_slider = wx.Slider(self.panel, value=50, minValue=0, maxValue=100)
        reverb_controls.Add(self.reverb_wet_slider, 0, wx.EXPAND)

        self.reverb_overdub_button = wx.Button(self.panel, label="Reverb Overdub: Off")
        reverb_sizer.Add(self.reverb_overdub_button, 0, wx.ALL|wx.EXPAND, 5)
        
        reverb_sizer.Add(reverb_controls, 1, wx.EXPAND|wx.ALL, 5)
        top_sizer.Add(reverb_sizer, 1, wx.EXPAND|wx.ALL, 5)

        # Gate section
        gate_box = wx.StaticBox(self.panel, label="Gate")
        gate_sizer = wx.StaticBoxSizer(gate_box, wx.VERTICAL)
        
        self.bypass_gate_button = wx.Button(self.panel, label="Bypass Gate: On")
        gate_sizer.Add(self.bypass_gate_button, 0, wx.ALL|wx.EXPAND, 5)
        
        gate_controls = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)
        
        gate_controls.Add(wx.StaticText(self.panel, label="Input Loop:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.gate_input_choice = wx.Choice(self.panel, choices=[f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))])
        self.gate_input_choice.SetSelection(0)
        gate_controls.Add(self.gate_input_choice, 0, wx.EXPAND)
        
        gate_controls.Add(wx.StaticText(self.panel, label="Output Loop:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.gate_output_choice = wx.Choice(self.panel, choices=[f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))])
        self.gate_output_choice.SetSelection(0)
        gate_controls.Add(self.gate_output_choice, 0, wx.EXPAND)
        
        gate_controls.Add(wx.StaticText(self.panel, label="Threshold:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.gate_threshold_slider = wx.Slider(self.panel, value=10, minValue=0, maxValue=100)
        gate_controls.Add(self.gate_threshold_slider, 0, wx.EXPAND)

        self.gate_overdub_button = wx.Button(self.panel, label="Gate Overdub: Off")
        gate_sizer.Add(self.gate_overdub_button, 0, wx.ALL|wx.EXPAND, 5)

        gate_controls.Add(wx.StaticText(self.panel, label="Attack (ms):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.gate_attack_slider = wx.Slider(self.panel, value=5, minValue=1, maxValue=50)
        gate_controls.Add(self.gate_attack_slider, 0, wx.EXPAND)
        
        gate_controls.Add(wx.StaticText(self.panel, label="Release (ms):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.gate_release_slider = wx.Slider(self.panel, value=100, minValue=10, maxValue=500)
        gate_controls.Add(self.gate_release_slider, 0, wx.EXPAND)
        
        gate_sizer.Add(gate_controls, 1, wx.EXPAND|wx.ALL, 5)
        top_sizer.Add(gate_sizer, 1, wx.EXPAND|wx.ALL, 5)

        self.main_sizer.Add(top_sizer, 0, wx.EXPAND)

        # Now bind all the events after controls are created
        self.bind_events()

    def bind_events(self):
        """Bind all control events after UI is initialized"""
        self.reverb_input_choice.Bind(wx.EVT_CHOICE, self.on_reverb_input_change)
        self.reverb_output_choice.Bind(wx.EVT_CHOICE, self.on_reverb_output_change)
        self.reverb_decay_slider.Bind(wx.EVT_SLIDER, self.on_reverb_decay_change)
        self.reverb_wet_slider.Bind(wx.EVT_SLIDER, self.on_reverb_wet_change)
        self.gate_input_choice.Bind(wx.EVT_CHOICE, self.on_gate_input_change)
        self.gate_output_choice.Bind(wx.EVT_CHOICE, self.on_gate_output_change)
        self.gate_threshold_slider.Bind(wx.EVT_SLIDER, self.on_gate_threshold_change)
        self.bypass_reverb_button.Bind(wx.EVT_BUTTON, self.toggle_bypass_reverb)
        self.reverb_overdub_button.Bind(wx.EVT_BUTTON, self.toggle_reverb_overdub)
        self.bypass_gate_button.Bind(wx.EVT_BUTTON, self.toggle_bypass_gate)
        self.gate_overdub_button.Bind(wx.EVT_BUTTON, self.toggle_gate_overdub)
        self.reverb_delay_slider.Bind(wx.EVT_SLIDER, self.on_reverb_delay_change)
        self.gate_attack_slider.Bind(wx.EVT_SLIDER, self.on_gate_attack_change)
        self.gate_release_slider.Bind(wx.EVT_SLIDER, self.on_gate_release_change)

    def create_loop_controls(self):
        self.scroll_panel = wx.ScrolledWindow(self.panel)
        self.scroll_panel.SetScrollRate(10, 10)
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_panel.SetSizer(self.scroll_sizer)
        self.main_sizer.Add(self.scroll_panel, 1, wx.EXPAND|wx.ALL, 10)

    def create_bottom_controls(self):
        self.status_label = wx.StaticText(self.panel, label="Ready")
        self.status_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.main_sizer.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        self.quit_button = wx.Button(self.panel, label="Quit")
        self.quit_button.Bind(wx.EVT_BUTTON, self.on_quit)
        self.main_sizer.Add(self.quit_button, 0, wx.ALL|wx.CENTER, 10)

    def update_effect_controls(self):
        self.bypass_reverb_button.SetLabel(f"Bypass Reverb: {'On' if self.looper.reverb_bypass else 'Off'}")
        self.reverb_overdub_button.SetLabel(f"Reverb Overdub: {'On' if self.looper.reverb_overdub else 'Off'}")
        self.reverb_decay_slider.SetValue(int(self.looper.reverb.decay * 100))
        self.reverb_wet_slider.SetValue(int(self.looper.reverb.wet * 100))
        self.reverb_delay_slider.SetValue(int(self.looper.reverb.delay_ms))
        
        self.bypass_gate_button.SetLabel(f"Bypass Gate: {'On' if self.looper.gate_bypass else 'Off'}")
        self.gate_overdub_button.SetLabel(f"Gate Overdub: {'On' if self.looper.gate_overdub else 'Off'}")
        self.gate_threshold_slider.SetValue(int(self.looper.gate.threshold * 100))
        self.gate_attack_slider.SetValue(int(self.looper.gate.attack_ms))
        self.gate_release_slider.SetValue(int(self.looper.gate.release_ms))

    def add_loop_controls(self, loop_index, initial_length):
        loop_sizer = wx.BoxSizer(wx.HORIZONTAL)

        loop_label = wx.StaticText(self.scroll_panel, label=f"Loop {loop_index + 1}:")
        loop_sizer.Add(loop_label, 0, wx.ALL | wx.CENTER, 5)

        mute_button = wx.Button(self.scroll_panel, 
                            label="Unmute" if self.looper.loop_controls.muted_loops[loop_index] else "Mute")
        mute_button.Bind(wx.EVT_BUTTON, lambda event, i=loop_index: self.toggle_mute(i))
        loop_sizer.Add(mute_button, 0, wx.ALL | wx.CENTER, 5)

        solo_button = wx.Button(self.scroll_panel,
                            label="Unsolo" if self.looper.loop_controls.soloed_loops[loop_index] else "Solo")
        solo_button.Bind(wx.EVT_BUTTON, lambda event, i=loop_index: self.toggle_solo(i))
        loop_sizer.Add(solo_button, 0, wx.ALL | wx.CENTER, 5)

        text_ctrl = wx.TextCtrl(self.scroll_panel, value=f"{initial_length:.1f}", size=(50, 25))
        text_ctrl.Bind(wx.EVT_TEXT, lambda event, i=loop_index: self.on_text_input_change(i, event))
        loop_sizer.Add(text_ctrl, 0, wx.ALL | wx.CENTER, 5)

        slider = wx.Slider(self.scroll_panel, value=int((initial_length - 1.0) * 10), 
                        minValue=0, maxValue=90, size=(200, 30))
        slider.Bind(wx.EVT_SLIDER, lambda event, i=loop_index: self.on_slider_change(i, event))
        loop_sizer.Add(slider, 0, wx.ALL | wx.CENTER, 5)

        loop_length_value = wx.StaticText(self.scroll_panel, label=f"{initial_length:.1f} s")
        loop_sizer.Add(loop_length_value, 0, wx.ALL | wx.CENTER, 5)

        select_button = wx.Button(self.scroll_panel, label="Select")
        select_button.Bind(wx.EVT_BUTTON, lambda event, i=loop_index: self.select_loop(i))
        loop_sizer.Add(select_button, 0, wx.ALL | wx.CENTER, 5)

        clear_button = wx.Button(self.scroll_panel, label="Clear")
        clear_button.Bind(wx.EVT_BUTTON, lambda event, i=loop_index: self.clear_loop(i))
        loop_sizer.Add(clear_button, 0, wx.ALL | wx.CENTER, 5)

        delete_button = wx.Button(self.scroll_panel, label="Delete")
        delete_button.Bind(wx.EVT_BUTTON, lambda event, i=loop_index: self.delete_loop(i))
        loop_sizer.Add(delete_button, 0, wx.ALL | wx.CENTER, 5)

        self.scroll_sizer.Add(loop_sizer, 0, wx.ALL | wx.CENTER, 5)
        self.loop_controls.append((
            loop_label, text_ctrl, slider, loop_length_value,
            select_button, mute_button, solo_button,
            clear_button, delete_button, loop_sizer
        ))

    def toggle_recording(self, event):
        """Toggle the recording state."""
        self.looper.loop_controls.is_recording = not self.looper.loop_controls.is_recording
        self.recording_button.SetLabel(f"Recording: {'On' if self.looper.loop_controls.is_recording else 'Off'}")

    def toggle_overdub(self, event):
        """Toggle the overdubbing state."""
        self.looper.loop_controls.is_overdubbing = not self.looper.loop_controls.is_overdubbing
        self.overdub_button.SetLabel(f"Overdub: {'On' if self.looper.loop_controls.is_overdubbing else 'Off'}")

    def start_recording_session(self, event):
        """Start a recording session."""
        self.looper.start_recording_session()
        self.start_recording_button.Disable()
        self.stop_recording_button.Enable()
        self.save_recording_button.Disable()
        self.status_label.SetLabel("Recording session started.")

    def stop_recording_session(self, event):
        """Stop the recording session."""
        self.looper.stop_recording_session()
        self.start_recording_button.Enable()
        self.stop_recording_button.Disable()
        self.save_recording_button.Enable()
        self.status_label.SetLabel("Recording session stopped. Ready to save.")

    def save_recording(self, event):
        """Save the recorded audio to a file."""
        with wx.FileDialog(self, "Save WAV file", wildcard="WAV files (*.wav)|*.wav",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            filepath = file_dialog.GetPath()
            try:
                self.looper.save_recording(filepath)
                self.status_label.SetLabel(f"Recording saved to {filepath}.")
            except Exception as e:
                wx.MessageBox(f"Failed to save recording: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def toggle_bypass_reverb(self, event):
        """Toggle the reverb bypass state."""
        self.looper.reverb_bypass = not self.looper.reverb_bypass
        self.bypass_reverb_button.SetLabel(f"Bypass Reverb: {'On' if self.looper.reverb_bypass else 'Off'}")

    def on_reverb_input_change(self, event):
        """Update the reverb input loop."""
        self.looper.reverb_input_loop = self.reverb_input_choice.GetSelection()

    def on_reverb_output_change(self, event):
        """Update the reverb output loop."""
        self.looper.reverb_output_loop = self.reverb_output_choice.GetSelection()

    def on_reverb_decay_change(self, event):
        """Update the reverb decay."""
        self.looper.reverb.decay = self.reverb_decay_slider.GetValue() / 100.0

    def on_reverb_wet_change(self, event):
        """Update the reverb wet/dry mix."""
        self.looper.reverb.wet = self.reverb_wet_slider.GetValue() / 100.0

    def on_reverb_delay_change(self, event):
        """Update the reverb delay time."""
        self.looper.reverb.delay_ms = self.reverb_delay_slider.GetValue()

    def on_gate_attack_change(self, event):
        """Update the gate attack time."""
        self.looper.gate.attack_ms = self.gate_attack_slider.GetValue()

    def on_gate_release_change(self, event):
        """Update the gate release time."""
        self.looper.gate.release_ms = self.gate_release_slider.GetValue()

    def on_gate_input_change(self, event):
        """Update the gate input loop."""
        self.looper.gate_input_loop = self.gate_input_choice.GetSelection()

    def on_gate_output_change(self, event):
        """Update the gate output loop."""
        self.looper.gate_output_loop = self.gate_output_choice.GetSelection()

    def on_gate_threshold_change(self, event):
        """Update the gate threshold."""
        self.looper.gate.threshold = self.gate_threshold_slider.GetValue() / 100.0

    def toggle_bypass_reverb(self, event):
        """Toggle the reverb bypass state."""
        self.looper.reverb_bypass = not self.looper.reverb_bypass
        self.bypass_reverb_button.SetLabel(f"Bypass Reverb: {'On' if self.looper.reverb_bypass else 'Off'}")

    def toggle_reverb_overdub(self, event):
        """Toggle the reverb overdub state."""
        self.looper.reverb_overdub = not self.looper.reverb_overdub
        self.reverb_overdub_button.SetLabel(f"Reverb Overdub: {'On' if self.looper.reverb_overdub else 'Off'}")

    def toggle_bypass_gate(self, event):
        """Toggle the gate bypass state."""
        self.looper.gate_bypass = not self.looper.gate_bypass
        self.bypass_gate_button.SetLabel(f"Bypass Gate: {'On' if self.looper.gate_bypass else 'Off'}")

    def toggle_gate_overdub(self, event):
        """Toggle the gate overdub state."""
        self.looper.gate_overdub = not self.looper.gate_overdub
        self.gate_overdub_button.SetLabel(f"Gate Overdub: {'On' if self.looper.gate_overdub else 'Off'}")


    def toggle_mute(self, loop_index):
        """Toggle the mute state of a loop."""
        with self.looper.lock:
            self.looper.loop_controls.muted_loops[loop_index] = not self.looper.loop_controls.muted_loops[loop_index]
            self.update_mute_button(loop_index)

    def toggle_solo(self, loop_index):
        """Toggle the solo state of a loop."""
        with self.looper.lock:
            if not self.looper.loop_controls.soloed_loops[loop_index]:
                self.looper.loop_controls.soloed_loops = [False] * len(self.looper.loop_controls.loops)
            self.looper.loop_controls.soloed_loops[loop_index] = not self.looper.loop_controls.soloed_loops[loop_index]
            for i in range(len(self.looper.loop_controls.loops)):
                self.update_solo_button(i)

    def update_mute_button(self, loop_index):
        """Update the mute button label."""
        controls = self.loop_controls[loop_index]
        mute_button = controls[5]  # Mute button is the 6th item in the tuple
        mute_button.SetLabel("Unmute" if self.looper.loop_controls.muted_loops[loop_index] else "Mute")

    def update_solo_button(self, loop_index):
        """Update the solo button label."""
        controls = self.loop_controls[loop_index]
        solo_button = controls[6]  # Solo button is the 7th item in the tuple
        solo_button.SetLabel("Unsolo" if self.looper.loop_controls.soloed_loops[loop_index] else "Solo")

    def update_selected_loop_highlight(self):
        """Highlight the currently selected loop."""
        for i, (label, *_) in enumerate(self.loop_controls):
            if i == self.looper.loop_controls.current_loop:  # Updated to use loop_controls
                label.SetForegroundColour(wx.Colour(0, 128, 0))  # Green for selected loop
            else:
                label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black for other loops
            label.Refresh()

    def select_loop(self, loop_index):
        """Select a loop for recording."""
        if loop_index < len(self.looper.loop_controls.loops):  # Updated to use loop_controls
            self.looper.loop_controls.current_loop = loop_index  # Updated to use loop_controls
            self.update_selected_loop_highlight()
            self.status_label.SetLabel(f"Selected Loop {loop_index + 1} for recording.")

    def on_slider_change(self, loop_index, event):
        """Update the loop length when the slider is moved."""
        slider = self.loop_controls[loop_index][2]  # Slider is the 3rd item in the tuple
        slider_value = slider.GetValue()
        loop_length = 1.0 + (slider_value / 10.0)  # Scale to 1.0 to 10.0 seconds

        # Update the text input and loop length value display
        self.loop_controls[loop_index][1].SetValue(f"{loop_length:.1f}")  # TextCtrl
        self.loop_controls[loop_index][3].SetLabel(f"{loop_length:.1f} s")  # StaticText

        # Update the loop length in the AudioLooper
        self.looper.loop_controls.update_loop_length(loop_index, loop_length)

    def on_text_input_change(self, loop_index, event):
        """Update the slider when the text input is changed."""
        text_ctrl = self.loop_controls[loop_index][1]  # TextCtrl is the 2nd item in the tuple
        try:
            value = float(text_ctrl.GetValue())
            value = max(1.0, min(10.0, value))  # Clamp value between 1.0 and 10.0
            slider_value = int((value - 1.0) * 10)  # Scale to slider range (0 to 90)
            self.loop_controls[loop_index][2].SetValue(slider_value)  # Slider
            self.loop_controls[loop_index][3].SetLabel(f"{value:.1f} s")  # StaticText
            self.looper.loop_controls.update_loop_length(loop_index, value)
        except ValueError:
            pass  # Ignore invalid input

    def clear_loop(self, loop_index):
        """Clear the audio data of a specific loop."""
        if loop_index < len(self.looper.loop_controls.loops):
            with self.looper.lock:
                self.looper.loop_controls.clear_loop(loop_index)
            self.status_label.SetLabel(f"Cleared Loop {loop_index + 1}.")

    def delete_loop(self, loop_index):
        """Delete a loop and its controls."""
        if len(self.looper.loop_controls.loops) <= 1:
            wx.MessageBox("You must have at least one loop!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Remove the loop from the AudioLooper
        with self.looper.lock:
            self.looper.loop_controls.loops.pop(loop_index)
            self.looper.loop_controls.loop_sizes.pop(loop_index)
            self.looper.loop_controls.loop_positions.pop(loop_index)
            self.looper.loop_controls.muted_loops.pop(loop_index)
            self.looper.loop_controls.soloed_loops.pop(loop_index)

            # Adjust current_loop if needed
            if self.looper.loop_controls.current_loop >= loop_index:
                self.looper.loop_controls.current_loop = max(0, self.looper.loop_controls.current_loop - 1)

        # Remove the controls from the GUI
        controls = self.loop_controls.pop(loop_index)
        for control in controls[:-1]:  # Exclude the sizer
            control.Destroy()
        self.scroll_sizer.Detach(controls[-1])  # Detach the sizer

        # Update remaining loop labels
        for i, (label, *_) in enumerate(self.loop_controls):
            label.SetLabel(f"Loop {i + 1}:")

        self.scroll_panel.Layout()
        self.update_selected_loop_highlight()

    def on_quit(self, event):
        """Quit the application with proper cleanup"""
        # Disable all audio processing first
        self.looper.is_running = False
        
        # Stop any active recording
        if hasattr(self.looper, 'is_recording') and self.looper.is_recording:
            self.looper.is_recording = False
        
        # Close the frame after cleanup
        def safe_close():
            self.looper.stop()
            self.Destroy()
        
        # Use CallAfter to ensure UI updates complete
        wx.CallAfter(safe_close)

