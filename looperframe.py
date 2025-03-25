import wx
import numpy as np
from components.reverb import Reverb
from components.gate import Gate

class LooperFrame(wx.Frame):
    def __init__(self, looper):
        super().__init__(None, title="Audio Looper", size=(1000, 700))
        self.looper = looper
        self._init_ui()
        self._setup_event_handlers()
        self._update_ui_state()

    def _init_ui(self):
        """Initialize all UI components"""
        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.main_sizer)

        # Create control sections
        self._create_top_controls()
        self._create_loop_controls()
        self._create_bottom_controls()

        # Initialize loop controls
        self.loop_controls = []
        for i in range(len(self.looper.loop_controls.loop_sizes)):
            initial_length = int(self.looper.loop_controls.loop_sizes[i] * self.looper.chunk / self.looper.rate)
            self._add_loop_control(i, initial_length)

    def _create_top_controls(self):
        """Create the top control panel with recording and effects"""
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._create_recording_controls(top_sizer)
        self._create_reverb_controls(top_sizer)
        self._create_gate_controls(top_sizer)
        self.main_sizer.Add(top_sizer, 0, wx.EXPAND)

    def _create_recording_controls(self, parent_sizer):
        """Create recording control section"""
        recording_box = wx.StaticBox(self.panel, label="Recording")
        recording_sizer = wx.StaticBoxSizer(recording_box, wx.VERTICAL)

        controls = [
            ("recording_button", "Record: Off", self.toggle_recording),
            ("overdub_button", "Overdub: Off", self.toggle_overdub),
            ("start_recording_button", "Start Session", self.start_recording_session),
            ("stop_recording_button", "Stop Session", self.stop_recording_session),
            ("save_recording_button", "Save Recording", self.save_recording)
        ]

        for name, label, handler in controls:
            btn = wx.Button(self.panel, label=label)
            btn.Bind(wx.EVT_BUTTON, handler)
            recording_sizer.Add(btn, 0, wx.ALL|wx.EXPAND, 5)
            setattr(self, name, btn)

        self.stop_recording_button.Disable()
        self.save_recording_button.Disable()
        parent_sizer.Add(recording_sizer, 1, wx.EXPAND|wx.ALL, 5)

    def _create_reverb_controls(self, parent_sizer):
        """Create reverb effect controls"""
        box = wx.StaticBox(self.panel, label="Reverb")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Buttons
        self.bypass_reverb_button = self._create_button("Bypass Reverb: On", self.toggle_bypass_reverb)
        self.reverb_overdub_button = self._create_button("Reverb Overdub: Off", self.toggle_reverb_overdub)

        # Parameters
        params = [
            ("Delay (ms):", "reverb_delay_slider", 150, 50, 500),
            ("Input Loop:", "reverb_input_choice", [f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))]),
            ("Output Loop:", "reverb_output_choice", [f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))]),
            ("Decay:", "reverb_decay_slider", 50, 0, 100),
            ("Wet/Dry:", "reverb_wet_slider", 50, 0, 100)
        ]

        grid = self._create_parameter_grid(params)
        
        sizer.Add(self.bypass_reverb_button, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(grid, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(self.reverb_overdub_button, 0, wx.ALL|wx.EXPAND, 5)
        parent_sizer.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)

    def _create_gate_controls(self, parent_sizer):
        """Create gate effect controls"""
        box = wx.StaticBox(self.panel, label="Gate")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Buttons
        self.bypass_gate_button = self._create_button("Bypass Gate: On", self.toggle_bypass_gate)
        self.gate_overdub_button = self._create_button("Gate Overdub: Off", self.toggle_gate_overdub)

        # Parameters
        params = [
            ("Input Loop:", "gate_input_choice", [f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))]),
            ("Output Loop:", "gate_output_choice", [f"Loop {i+1}" for i in range(len(self.looper.loop_controls.loops))]),
            ("Threshold:", "gate_threshold_slider", 10, 0, 100),
            ("Attack (ms):", "gate_attack_slider", 5, 1, 50),
            ("Release (ms):", "gate_release_slider", 100, 10, 500)
        ]

        grid = self._create_parameter_grid(params)
        
        sizer.Add(self.bypass_gate_button, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(grid, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(self.gate_overdub_button, 0, wx.ALL|wx.EXPAND, 5)
        parent_sizer.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)

    def _create_parameter_grid(self, parameters):
        """Helper to create a grid of parameter controls"""
        grid = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)
        for label, name, *args in parameters:
            grid.Add(wx.StaticText(self.panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            
            if "slider" in name:
                ctrl = wx.Slider(self.panel, value=args[0], minValue=args[1], maxValue=args[2])
            else:  # choice control
                ctrl = wx.Choice(self.panel, choices=args[0])
                ctrl.SetSelection(0)
            
            setattr(self, name, ctrl)
            grid.Add(ctrl, 0, wx.EXPAND)
        return grid

    def _create_button(self, label, handler):
        """Helper to create a button with consistent styling"""
        btn = wx.Button(self.panel, label=label)
        btn.Bind(wx.EVT_BUTTON, handler)
        return btn

    def _create_loop_controls(self):
        """Create the scrollable loop controls area"""
        self.scroll_panel = wx.ScrolledWindow(self.panel)
        self.scroll_panel.SetScrollRate(10, 10)
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_panel.SetSizer(self.scroll_sizer)
        self.main_sizer.Add(self.scroll_panel, 1, wx.EXPAND|wx.ALL, 10)

    def _create_bottom_controls(self):
        """Create bottom status bar and quit button"""
        self.status_label = wx.StaticText(self.panel, label="Ready")
        self.status_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, 
                                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.main_sizer.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        self.quit_button = self._create_button("Quit", self.on_quit)
        self.main_sizer.Add(self.quit_button, 0, wx.ALL|wx.CENTER, 10)

    def _add_loop_control(self, loop_index, initial_length):
        """Add controls for a single loop with mute/solo on the right"""
        loop_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left side: Loop label and length controls
        loop_label = wx.StaticText(self.scroll_panel, label=f"Loop {loop_index + 1}:")
        loop_sizer.Add(loop_label, 0, wx.ALL | wx.CENTER, 5)

        # Length controls
        text_ctrl = wx.TextCtrl(self.scroll_panel, value=f"{initial_length:.1f}", size=(50, 25))
        text_ctrl.Bind(wx.EVT_TEXT, lambda evt, i=loop_index: self._on_loop_length_text_change(i, evt))
        loop_sizer.Add(text_ctrl, 0, wx.ALL | wx.CENTER, 5)

        slider = wx.Slider(self.scroll_panel, value=int((initial_length - 1.0) * 10), 
                        minValue=0, maxValue=90, size=(200, 30))
        slider.Bind(wx.EVT_SLIDER, lambda evt, i=loop_index: self._on_loop_length_slider_change(i, evt))
        loop_sizer.Add(slider, 0, wx.ALL | wx.CENTER, 5)

        length_label = wx.StaticText(self.scroll_panel, label=f"{initial_length:.1f} s")
        loop_sizer.Add(length_label, 0, wx.ALL | wx.CENTER, 5)

        # Action buttons (select, clear, delete)
        select_button = wx.Button(self.scroll_panel, label="Select")
        select_button.Bind(wx.EVT_BUTTON, lambda evt, i=loop_index: self.select_loop(i))
        loop_sizer.Add(select_button, 0, wx.ALL | wx.CENTER, 5)

        clear_button = wx.Button(self.scroll_panel, label="Clear")
        clear_button.Bind(wx.EVT_BUTTON, lambda evt, i=loop_index: self.clear_loop(i))
        loop_sizer.Add(clear_button, 0, wx.ALL | wx.CENTER, 5)

        delete_button = wx.Button(self.scroll_panel, label="Delete")
        delete_button.Bind(wx.EVT_BUTTON, lambda evt, i=loop_index: self.delete_loop(i))
        loop_sizer.Add(delete_button, 0, wx.ALL | wx.CENTER, 5)

        # Right side: Mute and Solo buttons (added last to appear on right)
        mute_button = wx.Button(self.scroll_panel, 
                            label="Unmute" if self.looper.loop_controls.muted_loops[loop_index] else "Mute")
        mute_button.Bind(wx.EVT_BUTTON, lambda evt, i=loop_index: self.toggle_mute(i))
        loop_sizer.Add(mute_button, 0, wx.ALL | wx.CENTER, 5)

        solo_button = wx.Button(self.scroll_panel,
                            label="Unsolo" if self.looper.loop_controls.soloed_loops[loop_index] else "Solo")
        solo_button.Bind(wx.EVT_BUTTON, lambda evt, i=loop_index: self.toggle_solo(i))
        loop_sizer.Add(solo_button, 0, wx.ALL | wx.CENTER, 5)

        self.scroll_sizer.Add(loop_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        # Store references to update later
        self.loop_controls.append((
            loop_label, text_ctrl, slider, length_label,
            select_button, mute_button, solo_button,
            clear_button, delete_button, loop_sizer
        ))

    def _setup_event_handlers(self):
        """Set up all event handlers"""
        # Reverb controls
        self.reverb_input_choice.Bind(wx.EVT_CHOICE, self._on_reverb_input_change)
        self.reverb_output_choice.Bind(wx.EVT_CHOICE, self._on_reverb_output_change)
        self.reverb_decay_slider.Bind(wx.EVT_SLIDER, self._on_reverb_decay_change)
        self.reverb_wet_slider.Bind(wx.EVT_SLIDER, self._on_reverb_wet_change)
        self.reverb_delay_slider.Bind(wx.EVT_SLIDER, self._on_reverb_delay_change)

        # Gate controls
        self.gate_input_choice.Bind(wx.EVT_CHOICE, self._on_gate_input_change)
        self.gate_output_choice.Bind(wx.EVT_CHOICE, self._on_gate_output_change)
        self.gate_threshold_slider.Bind(wx.EVT_SLIDER, self._on_gate_threshold_change)
        self.gate_attack_slider.Bind(wx.EVT_SLIDER, self._on_gate_attack_change)
        self.gate_release_slider.Bind(wx.EVT_SLIDER, self._on_gate_release_change)

    def _update_ui_state(self):
        """Update all UI elements to reflect current state"""
        self._update_selected_loop_highlight()
        self._update_effect_controls()

    def _update_effect_controls(self):
        """Update effect controls to match current settings"""
        # Reverb
        self.bypass_reverb_button.SetLabel(f"Bypass Reverb: {'On' if self.looper.reverb_bypass else 'Off'}")
        self.reverb_overdub_button.SetLabel(f"Reverb Overdub: {'On' if self.looper.reverb_overdub else 'Off'}")
        self.reverb_decay_slider.SetValue(int(self.looper.reverb.decay * 100))
        self.reverb_wet_slider.SetValue(int(self.looper.reverb.wet * 100))
        self.reverb_delay_slider.SetValue(int(self.looper.reverb.delay_ms))
        
        # Gate
        self.bypass_gate_button.SetLabel(f"Bypass Gate: {'On' if self.looper.gate_bypass else 'Off'}")
        self.gate_overdub_button.SetLabel(f"Gate Overdub: {'On' if self.looper.gate_overdub else 'Off'}")
        self.gate_threshold_slider.SetValue(int(self.looper.gate.threshold * 100))
        self.gate_attack_slider.SetValue(int(self.looper.gate.attack_ms))
        self.gate_release_slider.SetValue(int(self.looper.gate.release_ms))

    def _update_selected_loop_highlight(self):
        """Highlight the currently selected loop"""
        for i, (label, *_) in enumerate(self.loop_controls):
            label.SetForegroundColour(wx.Colour(0, 128, 0) if i == self.looper.loop_controls.current_loop 
                                   else wx.Colour(0, 0, 0))
            label.Refresh()

    def _on_loop_length_slider_change(self, loop_index, event):
        """Handle loop length slider changes"""
        slider = self.loop_controls[loop_index][2]
        loop_length = 1.0 + (slider.GetValue() / 10.0)
        
        # Prevent recursive events by changing value only if different
        current_text_value = float(self.loop_controls[loop_index][1].GetValue())
        if abs(loop_length - current_text_value) > 0.05:  # Small threshold to prevent floating point issues
            # Temporarily disable events while updating
            self.loop_controls[loop_index][1].Unbind(wx.EVT_TEXT)
            self.loop_controls[loop_index][1].SetValue(f"{loop_length:.1f}")
            self.loop_controls[loop_index][1].Bind(wx.EVT_TEXT, 
                lambda evt, i=loop_index: self._on_loop_length_text_change(i, evt))
            
            self._update_loop_length_ui(loop_index, loop_length)
            self.looper.loop_controls.update_loop_length(loop_index, loop_length)

    def _on_loop_length_text_change(self, loop_index, event):
        """Handle loop length text input changes"""
        text_ctrl = self.loop_controls[loop_index][1]
        try:
            value = max(1.0, min(10.0, float(text_ctrl.GetValue())))
            # Prevent recursive events by changing value only if different
            current_slider_value = self.loop_controls[loop_index][2].GetValue()
            new_slider_value = int((value - 1.0) * 10)
            
            if new_slider_value != current_slider_value:
                # Temporarily disable events while updating
                self.loop_controls[loop_index][2].Unbind(wx.EVT_SLIDER)
                self.loop_controls[loop_index][2].SetValue(new_slider_value)
                self.loop_controls[loop_index][2].Bind(wx.EVT_SLIDER, 
                    lambda evt, i=loop_index: self._on_loop_length_slider_change(i, evt))
                
                self._update_loop_length_ui(loop_index, value)
                self.looper.loop_controls.update_loop_length(loop_index, value)
        except ValueError:
            pass

    def _update_loop_length_ui(self, loop_index, length):
        """Update all UI elements for loop length"""
        self.loop_controls[loop_index][1].SetValue(f"{length:.1f}")  # TextCtrl
        self.loop_controls[loop_index][3].SetLabel(f"{length:.1f} s")  # StaticText

    # Event handlers for effect parameters
    def _on_reverb_input_change(self, event): self.looper.reverb_input_loop = self.reverb_input_choice.GetSelection()
    def _on_reverb_output_change(self, event): self.looper.reverb_output_loop = self.reverb_output_choice.GetSelection()
    def _on_reverb_decay_change(self, event): self.looper.reverb.decay = self.reverb_decay_slider.GetValue() / 100.0
    def _on_reverb_wet_change(self, event): self.looper.reverb.wet = self.reverb_wet_slider.GetValue() / 100.0
    def _on_reverb_delay_change(self, event): self.looper.reverb.delay_ms = self.reverb_delay_slider.GetValue()
    def _on_gate_input_change(self, event): self.looper.gate_input_loop = self.gate_input_choice.GetSelection()
    def _on_gate_output_change(self, event): self.looper.gate_output_loop = self.gate_output_choice.GetSelection()
    def _on_gate_threshold_change(self, event): self.looper.gate.threshold = self.gate_threshold_slider.GetValue() / 100.0
    def _on_gate_attack_change(self, event): self.looper.gate.attack_ms = self.gate_attack_slider.GetValue()
    def _on_gate_release_change(self, event): self.looper.gate.release_ms = self.gate_release_slider.GetValue()

    # Button action methods
    def toggle_recording(self, event):
        self.looper.loop_controls.is_recording = not self.looper.loop_controls.is_recording
        self.recording_button.SetLabel(f"Recording: {'On' if self.looper.loop_controls.is_recording else 'Off'}")

    def toggle_overdub(self, event):
        self.looper.loop_controls.is_overdubbing = not self.looper.loop_controls.is_overdubbing
        self.overdub_button.SetLabel(f"Overdub: {'On' if self.looper.loop_controls.is_overdubbing else 'Off'}")

    def start_recording_session(self, event):
        self.looper.start_recording_session()
        self.start_recording_button.Disable()
        self.stop_recording_button.Enable()
        self.save_recording_button.Disable()
        self.status_label.SetLabel("Recording session started.")

    def stop_recording_session(self, event):
        self.looper.stop_recording_session()
        self.start_recording_button.Enable()
        self.stop_recording_button.Disable()
        self.save_recording_button.Enable()
        self.status_label.SetLabel("Recording session stopped. Ready to save.")

    def save_recording(self, event):
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
        self.looper.reverb_bypass = not self.looper.reverb_bypass
        self.bypass_reverb_button.SetLabel(f"Bypass Reverb: {'On' if self.looper.reverb_bypass else 'Off'}")

    def toggle_reverb_overdub(self, event):
        self.looper.reverb_overdub = not self.looper.reverb_overdub
        self.reverb_overdub_button.SetLabel(f"Reverb Overdub: {'On' if self.looper.reverb_overdub else 'Off'}")

    def toggle_bypass_gate(self, event):
        self.looper.gate_bypass = not self.looper.gate_bypass
        self.bypass_gate_button.SetLabel(f"Bypass Gate: {'On' if self.looper.gate_bypass else 'Off'}")

    def toggle_gate_overdub(self, event):
        self.looper.gate_overdub = not self.looper.gate_overdub
        self.gate_overdub_button.SetLabel(f"Gate Overdub: {'On' if self.looper.gate_overdub else 'Off'}")

    def toggle_mute(self, loop_index):
        with self.looper.lock:
            self.looper.loop_controls.muted_loops[loop_index] = not self.looper.loop_controls.muted_loops[loop_index]
            btn = getattr(self, f"loop{loop_index}_mute_button")
            btn.SetLabel("Unmute" if self.looper.loop_controls.muted_loops[loop_index] else "Mute")

    def toggle_solo(self, loop_index):
        with self.looper.lock:
            if not self.looper.loop_controls.soloed_loops[loop_index]:
                self.looper.loop_controls.soloed_loops = [False] * len(self.looper.loop_controls.loops)
            self.looper.loop_controls.soloed_loops[loop_index] = not self.looper.loop_controls.soloed_loops[loop_index]
            for i in range(len(self.looper.loop_controls.loops)):
                btn = getattr(self, f"loop{i}_solo_button")
                btn.SetLabel("Unsolo" if self.looper.loop_controls.soloed_loops[i] else "Solo")

    def select_loop(self, loop_index):
        if loop_index < len(self.looper.loop_controls.loops):
            self.looper.loop_controls.current_loop = loop_index
            self._update_selected_loop_highlight()
            self.status_label.SetLabel(f"Selected Loop {loop_index + 1} for recording.")

    def clear_loop(self, loop_index):
        if loop_index < len(self.looper.loop_controls.loops):
            with self.looper.lock:
                self.looper.loop_controls.clear_loop(loop_index)
            self.status_label.SetLabel(f"Cleared Loop {loop_index + 1}.")

    def delete_loop(self, loop_index):
        if len(self.looper.loop_controls.loops) <= 1:
            wx.MessageBox("You must have at least one loop!", "Error", wx.OK | wx.ICON_ERROR)
            return

        with self.looper.lock:
            # Remove loop from audio processing
            self.looper.loop_controls.loops.pop(loop_index)
            self.looper.loop_controls.loop_sizes.pop(loop_index)
            self.looper.loop_controls.loop_positions.pop(loop_index)
            self.looper.loop_controls.muted_loops.pop(loop_index)
            self.looper.loop_controls.soloed_loops.pop(loop_index)

            if self.looper.loop_controls.current_loop >= loop_index:
                self.looper.loop_controls.current_loop = max(0, self.looper.loop_controls.current_loop - 1)

        # Remove UI controls
        controls = self.loop_controls.pop(loop_index)
        for control in controls[:-1]:  # All except the sizer
            control.Destroy()
        self.scroll_sizer.Detach(controls[-1])

        # Update remaining loop labels
        for i, (label, *_) in enumerate(self.loop_controls):
            label.SetLabel(f"Loop {i + 1}:")

        self.scroll_panel.Layout()
        self._update_selected_loop_highlight()

    def update_mute_button(self, loop_index):
        """Update the mute button label."""
        controls = self.loop_controls[loop_index]
        mute_button = controls[5]  # Mute button is now 6th item in the tuple
        mute_button.SetLabel("Unmute" if self.looper.loop_controls.muted_loops[loop_index] else "Mute")

    def update_solo_button(self, loop_index):
        """Update the solo button label."""
        controls = self.loop_controls[loop_index]
        solo_button = controls[6]  # Solo button is now 7th item in the tuple
        solo_button.SetLabel("Unsolo" if self.looper.loop_controls.soloed_loops[loop_index] else "Solo")

    def on_quit(self, event):
        """Quit the application with proper cleanup"""
        self.looper.is_running = False
        
        if hasattr(self.looper, 'is_recording') and self.looper.is_recording:
            self.looper.is_recording = False
        
        def safe_close():
            self.looper.stop()
            self.Destroy()
        
        wx.CallAfter(safe_close)