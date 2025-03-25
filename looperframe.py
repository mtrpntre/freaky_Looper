import wx
import numpy as np
from effects.reverb import ReverbEffect
from effects.gate import GateEffect


class LooperFrame(wx.Frame):
    def __init__(self, looper):
        super().__init__(None, title="Audio Looper", size=(1000, 700))
        self.looper = looper
        self.loop_controls = []  # Stores UI controls for each loop
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

        # Initialize loop controls for existing loops
        for loop_id in self.looper.loop_controls.loops:
            loop_length = self.looper.loop_controls.loop_sizes[loop_id] * self.looper.chunk / self.looper.rate
            self._add_loop_control(loop_id, len(self.loop_controls) + 1, loop_length)

    def _create_top_controls(self):
        """Create the top control panel"""
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._create_recording_controls(top_sizer)
        self._create_reverb_controls(top_sizer)
        self._create_gate_controls(top_sizer)
        self._create_pitch_controls(top_sizer)
        self.main_sizer.Add(top_sizer, 0, wx.EXPAND)

    def _create_recording_controls(self, parent_sizer):
        """Create recording controls"""
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

    def _create_pitch_controls(self, parent_sizer):
        """Create pitch shift effect controls"""
        box = wx.StaticBox(self.panel, label="Pitch Shift")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Bypass and Overdub buttons
        self.bypass_pitch_button = self._create_button("Bypass Pitch: On", self.toggle_bypass_pitch)
        self.pitch_overdub_button = self._create_button("Pitch Overdub: Off", self.toggle_pitch_overdub)

        # Semitones control
        semitones_sizer = wx.BoxSizer(wx.HORIZONTAL)
        semitones_sizer.Add(wx.StaticText(self.panel, label="Semitones:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        
        self.pitch_semitones_slider = wx.Slider(
            self.panel, value=0, minValue=-24, maxValue=24, 
            style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS
        )
        semitones_sizer.Add(self.pitch_semitones_slider, 1, wx.EXPAND)
        
        # Add the text control for precise semitone entry
        self.pitch_semitones_text = wx.TextCtrl(self.panel, value="0", size=(50, -1))
        self.pitch_semitones_text.SetToolTip("Enter semitones (-24 to 24)")
        semitones_sizer.Add(self.pitch_semitones_text, 0, wx.LEFT|wx.RIGHT, 5)

        # Feedback control
        feedback_sizer = wx.BoxSizer(wx.HORIZONTAL)
        feedback_sizer.Add(wx.StaticText(self.panel, label="Feedback:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        
        self.pitch_feedback_slider = wx.Slider(
            self.panel, value=0, minValue=0, maxValue=90,  # 0-90% feedback
            style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS
        )
        feedback_sizer.Add(self.pitch_feedback_slider, 1, wx.EXPAND)
        
        # Feedback value display
        self.pitch_feedback_text = wx.StaticText(self.panel, label="0%")
        feedback_sizer.Add(self.pitch_feedback_text, 0, wx.LEFT|wx.RIGHT, 5)

        # Input/output routing
        params = [
            ("Input Loop:", "pitch_input_choice", []),
            ("Output Loop:", "pitch_output_choice", []),
            ("Quality:", "pitch_quality_choice", ["Low", "Medium", "High"])
        ]
        grid = self._create_parameter_grid(params)

        # Add controls to sizer
        sizer.Add(self.bypass_pitch_button, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(semitones_sizer, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(feedback_sizer, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(grid, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(self.pitch_overdub_button, 0, wx.ALL|wx.EXPAND, 5)
        
        # Bind events
        self.pitch_semitones_slider.Bind(wx.EVT_SLIDER, self._on_pitch_semitones_slider_change)
        self.pitch_semitones_text.Bind(wx.EVT_TEXT, self._on_pitch_semitones_text_change)
        self.pitch_feedback_slider.Bind(wx.EVT_SLIDER, self._on_pitch_feedback_change)
        
        parent_sizer.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)

    def _create_reverb_controls(self, parent_sizer):
        """Create reverb controls"""
        box = wx.StaticBox(self.panel, label="Reverb")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.bypass_reverb_button = self._create_button("Bypass Reverb: On", self.toggle_bypass_reverb)
        self.reverb_overdub_button = self._create_button("Reverb Overdub: Off", self.toggle_reverb_overdub)

        params = [
            ("Delay (ms):", "reverb_delay_slider", 150, 50, 500),
            ("Input Loop:", "reverb_input_choice", []),
            ("Output Loop:", "reverb_output_choice", []),
            ("Decay:", "reverb_decay_slider", 50, 0, 100),
            ("Wet/Dry:", "reverb_wet_slider", 50, 0, 100)
        ]

        grid = self._create_parameter_grid(params)
        sizer.Add(self.bypass_reverb_button, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(grid, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(self.reverb_overdub_button, 0, wx.ALL|wx.EXPAND, 5)
        parent_sizer.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)

    def _create_gate_controls(self, parent_sizer):
        """Create gate controls"""
        box = wx.StaticBox(self.panel, label="Gate")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.bypass_gate_button = self._create_button("Bypass Gate: On", self.toggle_bypass_gate)
        self.gate_overdub_button = self._create_button("Gate Overdub: Off", self.toggle_gate_overdub)

        params = [
            ("Input Loop:", "gate_input_choice", []),
            ("Output Loop:", "gate_output_choice", []),
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
        """Create parameter grid"""
        grid = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)
        for label, name, *args in parameters:
            grid.Add(wx.StaticText(self.panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            
            if "slider" in name:
                ctrl = wx.Slider(self.panel, value=args[0], minValue=args[1], maxValue=args[2])
            else:
                ctrl = wx.Choice(self.panel, choices=args[0])
                ctrl.SetSelection(0)
            
            setattr(self, name, ctrl)
            grid.Add(ctrl, 0, wx.EXPAND)
        return grid

    def _create_button(self, label, handler):
        """Helper to create styled buttons"""
        btn = wx.Button(self.panel, label=label)
        btn.Bind(wx.EVT_BUTTON, handler)
        return btn

    def _create_loop_controls(self):
        """Create loop controls area"""
        loop_container = wx.BoxSizer(wx.VERTICAL)
        
        # Add Loop button
        add_loop_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_loop_button = wx.Button(self.panel, label="+ Add Loop")
        self.add_loop_button.Bind(wx.EVT_BUTTON, self._on_add_loop)
        add_loop_sizer.AddStretchSpacer(1)
        add_loop_sizer.Add(self.add_loop_button, 0, wx.CENTER)
        add_loop_sizer.AddStretchSpacer(1)
        loop_container.Add(add_loop_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        # Scrollable area for loops
        self.scroll_panel = wx.ScrolledWindow(self.panel)
        self.scroll_panel.SetScrollRate(10, 10)
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_panel.SetSizer(self.scroll_sizer)
        loop_container.Add(self.scroll_panel, 1, wx.EXPAND)

        self.main_sizer.Add(loop_container, 1, wx.EXPAND|wx.ALL, 10)

    def _create_bottom_controls(self):
        """Create bottom controls"""
        self.status_label = wx.StaticText(self.panel, label="Ready")
        self.status_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, 
                                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.main_sizer.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        self.quit_button = self._create_button("Quit", self.on_quit)
        self.main_sizer.Add(self.quit_button, 0, wx.ALL|wx.CENTER, 10)

    def _add_loop_control(self, loop_id, display_number, initial_length):
        """Add controls for a single loop"""
        loop_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        control = {
            'id': loop_id,
            'display_number': display_number,
            'sizer': loop_sizer
        }
        
        # Label
        control['label'] = wx.StaticText(self.scroll_panel, label=f"Loop {display_number}:")
        loop_sizer.Add(control['label'], 0, wx.ALL | wx.CENTER, 5)

        # Text control for length
        control['text'] = wx.TextCtrl(self.scroll_panel, value=f"{initial_length:.1f}", size=(50, 25))
        
        # Slider for length
        control['slider'] = wx.Slider(self.scroll_panel, value=int((initial_length - 1.0) * 10), 
                                    minValue=0, maxValue=90, size=(200, 30))
        
        # Length display
        control['length_label'] = wx.StaticText(self.scroll_panel, label=f"{initial_length:.1f} s")
        
        # Action buttons
        control['select'] = wx.Button(self.scroll_panel, label="Select")
        control['mute'] = wx.Button(self.scroll_panel, label="Mute")
        control['solo'] = wx.Button(self.scroll_panel, label="Solo")
        control['clear'] = wx.Button(self.scroll_panel, label="Clear")
        control['delete'] = wx.Button(self.scroll_panel, label="Delete")

        # Add controls to sizer
        for key in ['text', 'slider', 'length_label', 'select', 
                'clear', 'delete', 'mute', 'solo']:
            loop_sizer.Add(control[key], 0, wx.ALL | wx.CENTER, 5)

        # Store the control
        self.loop_controls.append(control)

        # Bind events
        control['text'].Bind(wx.EVT_TEXT, lambda e, lid=loop_id: self._on_loop_text_change(lid, e))
        control['slider'].Bind(wx.EVT_SLIDER, lambda e, lid=loop_id: self._on_loop_slider_change(lid, e))
        control['select'].Bind(wx.EVT_BUTTON, lambda e, lid=loop_id: self.select_loop(lid))
        control['mute'].Bind(wx.EVT_BUTTON, lambda e, lid=loop_id: self.toggle_mute(lid))
        control['solo'].Bind(wx.EVT_BUTTON, lambda e, lid=loop_id: self.toggle_solo(lid))
        control['clear'].Bind(wx.EVT_BUTTON, lambda e, lid=loop_id: self.clear_loop(lid))
        control['delete'].Bind(wx.EVT_BUTTON, lambda e, lid=loop_id: self.delete_loop(lid))

        self.scroll_sizer.Add(loop_sizer, 0, wx.ALL | wx.CENTER, 5)

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

        # Pitch shift controls
        self.pitch_input_choice.Bind(wx.EVT_CHOICE, self._on_pitch_input_change)
        self.pitch_output_choice.Bind(wx.EVT_CHOICE, self._on_pitch_output_change)
        self.pitch_semitones_slider.Bind(wx.EVT_SLIDER, self._on_pitch_semitones_change)
        self.pitch_quality_choice.Bind(wx.EVT_CHOICE, self._on_pitch_quality_change)

    def _update_ui_state(self):
        """Update UI elements to reflect current state"""
        self._update_selected_loop_highlight()
        self._update_effect_controls()
        self._update_effect_menus()

    def _update_effect_controls(self):
        """Update effect controls"""
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

        # Pitch shift controls
        self.bypass_pitch_button.SetLabel(f"Bypass Pitch: {'On' if self.looper.pitch_bypass else 'Off'}")
        self.pitch_overdub_button.SetLabel(f"Pitch Overdub: {'On' if self.looper.pitch_overdub else 'Off'}")
        
        # Update semitones controls without triggering events
        self.pitch_semitones_text.Unbind(wx.EVT_TEXT)
        self.pitch_semitones_slider.Unbind(wx.EVT_SLIDER)
        
        self.pitch_semitones_text.ChangeValue(str(self.looper.pitch_shift.semitones))
        self.pitch_semitones_slider.SetValue(self.looper.pitch_shift.semitones)
        
        self.pitch_semitones_text.Bind(wx.EVT_TEXT, self._on_pitch_semitones_text_change)
        self.pitch_semitones_slider.Bind(wx.EVT_SLIDER, self._on_pitch_semitones_slider_change)
        
        # Set quality selection
        quality_index = ["low", "medium", "high"].index(self.looper.pitch_shift.quality.lower())
        self.pitch_quality_choice.SetSelection(quality_index)

    def _update_effect_menus(self):
        """Update effect menus with current loops"""
        loop_names = [f"Loop {control['display_number']}" for control in self.loop_controls]
        
        # Reverb menus
        self.reverb_input_choice.SetItems(loop_names)
        self.reverb_output_choice.SetItems(loop_names)
        
        # Set default selections if not set
        if len(self.loop_controls) > 0:
            if self.looper.reverb_input_id is None:
                self.looper.reverb_input_id = self.loop_controls[0]['id']
            if self.looper.reverb_output_id is None:
                self.looper.reverb_output_id = self.loop_controls[0]['id']
            
            # Find current selections
            input_idx = next((i for i, c in enumerate(self.loop_controls) 
                            if c['id'] == self.looper.reverb_input_id), 0)
            output_idx = next((i for i, c in enumerate(self.loop_controls) 
                            if c['id'] == self.looper.reverb_output_id), 0)
            
        self.reverb_input_choice.SetSelection(input_idx)
        self.reverb_output_choice.SetSelection(output_idx)
        
        # Gate menus
        self.gate_input_choice.SetItems(loop_names)
        self.gate_output_choice.SetItems(loop_names)
        
        # Set default selections if not set
        if len(self.loop_controls) > 0:
            if self.looper.gate_input_id is None:
                self.looper.gate_input_id = self.loop_controls[0]['id']
            if self.looper.gate_output_id is None:
                self.looper.gate_output_id = self.loop_controls[0]['id']
            
            # Find current selections
            input_idx = next((i for i, c in enumerate(self.loop_controls) 
                            if c['id'] == self.looper.gate_input_id), 0)
            output_idx = next((i for i, c in enumerate(self.loop_controls) 
                            if c['id'] == self.looper.gate_output_id), 0)
            
        self.gate_input_choice.SetSelection(input_idx)
        self.gate_output_choice.SetSelection(output_idx)

        # Update pitch shift menus
        self.pitch_input_choice.SetItems(loop_names)
        self.pitch_output_choice.SetItems(loop_names)
        
        # Set default selections if not set
        if len(self.loop_controls) > 0:
            if self.looper.pitch_input_id is None:
                self.looper.pitch_input_id = self.loop_controls[0]['id']
            if self.looper.pitch_output_id is None:
                self.looper.pitch_output_id = self.loop_controls[0]['id']
            
            input_idx = next((i for i, c in enumerate(self.loop_controls) 
                            if c['id'] == self.looper.pitch_input_id), 0)
            output_idx = next((i for i, c in enumerate(self.loop_controls) 
                            if c['id'] == self.looper.pitch_output_id), 0)
            
            self.pitch_input_choice.SetSelection(input_idx)
            self.pitch_output_choice.SetSelection(output_idx)

    def _update_selected_loop_highlight(self):
        """Highlight the currently selected loop"""
        current_id = self.looper.loop_controls.current_loop_id
        for control in self.loop_controls:
            control['label'].SetForegroundColour(
                wx.Colour(0, 128, 0) if control['id'] == current_id 
                else wx.Colour(0, 0, 0))
            control['label'].Refresh()

    def _on_loop_slider_change(self, loop_id, event):
        """Handle slider changes"""
        for control in self.loop_controls:
            if control['id'] == loop_id:
                value = 1.0 + (control['slider'].GetValue() / 10.0)
                
                # Temporarily unbind to prevent recursion
                control['text'].Unbind(wx.EVT_TEXT)
                control['text'].SetValue(f"{value:.1f}")
                control['text'].Bind(wx.EVT_TEXT,
                    lambda e, lid=loop_id: self._on_loop_text_change(lid, e))
                
                control['length_label'].SetLabel(f"{value:.1f} s")
                self.looper.update_loop_length(loop_id, value)
                break

    def _on_loop_text_change(self, loop_id, event):
        """Handle text changes"""
        for control in self.loop_controls:
            if control['id'] == loop_id:
                try:
                    value = max(1.0, min(10.0, float(control['text'].GetValue())))
                    slider_value = int((value - 1.0) * 10)
                    
                    # Temporarily unbind to prevent recursion
                    control['slider'].Unbind(wx.EVT_SLIDER)
                    control['slider'].SetValue(slider_value)
                    control['slider'].Bind(wx.EVT_SLIDER, 
                        lambda e, lid=loop_id: self._on_loop_slider_change(lid, e))
                    
                    control['length_label'].SetLabel(f"{value:.1f} s")
                    self.looper.update_loop_length(loop_id, value)
                except ValueError:
                    pass
                break

    # Effect parameter handlers
    def _on_reverb_input_change(self, event):
        if self.reverb_input_choice.GetSelection() < len(self.loop_controls):
            control = self.loop_controls[self.reverb_input_choice.GetSelection()]
            self.looper.reverb_input_id = control['id']
    def _on_reverb_output_change(self, event):
        if self.reverb_output_choice.GetSelection() < len(self.loop_controls):
            control = self.loop_controls[self.reverb_output_choice.GetSelection()]
        self.looper.reverb_output_id = control['id']
    def _on_reverb_decay_change(self, event): 
        self.looper.reverb.decay = self.reverb_decay_slider.GetValue() / 100.0
    def _on_reverb_wet_change(self, event): 
        self.looper.reverb.wet = self.reverb_wet_slider.GetValue() / 100.0
    def _on_reverb_delay_change(self, event): 
        self.looper.reverb.delay_ms = self.reverb_delay_slider.GetValue()
    def _on_gate_input_change(self, event):
        if self.gate_input_choice.GetSelection() < len(self.loop_controls):
            control = self.loop_controls[self.gate_input_choice.GetSelection()]
            self.looper.gate_input_id = control['id']

    def _on_gate_output_change(self, event):
        if self.gate_output_choice.GetSelection() < len(self.loop_controls):
            control = self.loop_controls[self.gate_output_choice.GetSelection()]
            self.looper.gate_output_id = control['id']
    def _on_gate_threshold_change(self, event): 
        self.looper.gate.threshold = self.gate_threshold_slider.GetValue() / 100.0
    def _on_gate_attack_change(self, event): 
        self.looper.gate.attack_ms = self.gate_attack_slider.GetValue()
    def _on_gate_release_change(self, event): 
        self.looper.gate.release_ms = self.gate_release_slider.GetValue()

    # Button actions

    def toggle_recording(self, event):
        self.looper.loop_controls.is_recording = not self.looper.loop_controls.is_recording
        self.recording_button.SetLabel(f"Recording: {'On' if self.looper.loop_controls.is_recording else 'Off'}")
        if self.looper.loop_controls.is_recording:
            self.status_label.SetLabel(f"Recording to Loop {self._get_display_number(self.looper.loop_controls.current_loop_id)} (real-time monitoring)")

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

    def toggle_mute(self, loop_id):
        """Toggle mute for a loop"""
        with self.looper.lock:
            if loop_id in self.looper.loop_controls.muted_loops:
                self.looper.loop_controls.muted_loops[loop_id] = not self.looper.loop_controls.muted_loops[loop_id]
                self.update_mute_button(loop_id)

    def toggle_solo(self, loop_id):
        """Toggle solo for a loop"""
        with self.looper.lock:
            if loop_id in self.looper.loop_controls.soloed_loops:
                if not self.looper.loop_controls.soloed_loops[loop_id]:
                    # Clear other solos if enabling this one
                    for lid in self.looper.loop_controls.soloed_loops:
                        self.looper.loop_controls.soloed_loops[lid] = False
                        self.update_solo_button(lid)
                
                self.looper.loop_controls.soloed_loops[loop_id] = not self.looper.loop_controls.soloed_loops[loop_id]
                self.update_solo_button(loop_id)

    def select_loop(self, loop_id):
        """Select a loop for recording"""
        with self.looper.lock:
            if loop_id in self.looper.loop_controls.loops:
                self.looper.loop_controls.current_loop_id = loop_id
                self._update_selected_loop_highlight()
                self.status_label.SetLabel(f"Selected Loop {self._get_display_number(loop_id)} for recording.")

    def clear_loop(self, loop_id):
        """Clear a loop's audio"""
        with self.looper.lock:
            if loop_id in self.looper.loop_controls.loops:
                self.looper.loop_controls.loops[loop_id].fill(0)
                self.status_label.SetLabel(f"Cleared Loop {self._get_display_number(loop_id)}.")

    def delete_loop(self, loop_id):
        """Delete a loop"""
        if len(self.looper.loop_controls.loops) <= 1:
            wx.MessageBox("You must have at least one loop!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Find and remove the UI control
        for i, control in enumerate(self.loop_controls):
            if control['id'] == loop_id:
                # Destroy all controls
                for key in ['label', 'text', 'slider', 'length_label',
                          'select', 'mute', 'solo', 'clear', 'delete']:
                    control[key].Destroy()
                self.scroll_sizer.Detach(control['sizer'])
                del self.loop_controls[i]
                break

        # Remove from audio backend
        with self.looper.lock:
            try:
                self.looper.loop_controls.delete_loop(loop_id)
            except ValueError as e:
                wx.MessageBox(str(e), "Error", wx.OK | wx.ICON_ERROR)
                return

        # Update remaining UI controls
        for i, control in enumerate(self.loop_controls):
            control['display_number'] = i + 1
            control['label'].SetLabel(f"Loop {i + 1}:")

        self._update_effect_menus()
        self.scroll_panel.Layout()
        self._update_selected_loop_highlight()
        self.status_label.SetLabel(f"Deleted loop. {len(self.loop_controls)} loops remaining.")

    def update_mute_button(self, loop_id):
        """Update mute button label"""
        for control in self.loop_controls:
            if control['id'] == loop_id:
                control['mute'].SetLabel(
                    "Unmute" if self.looper.loop_controls.muted_loops[loop_id] 
                    else "Mute")
                break

    def update_solo_button(self, loop_id):
        """Update solo button label"""
        for control in self.loop_controls:
            if control['id'] == loop_id:
                control['solo'].SetLabel(
                    "Unsolo" if self.looper.loop_controls.soloed_loops[loop_id] 
                    else "Solo")
                break

    def _get_display_number(self, loop_id):
        """Get display number for a loop ID"""
        for control in self.loop_controls:
            if control['id'] == loop_id:
                return control['display_number']
        return 0

    def _on_add_loop(self, event):
        """Add a new loop"""
        new_length = 4.0
        
        with self.looper.lock:
            loop_id = self.looper.loop_controls._add_loop(new_length)
        
        # Add to UI with sequential display number
        display_number = len(self.loop_controls) + 1
        self._add_loop_control(loop_id, display_number, new_length)
        self.scroll_panel.Layout()
        self._update_effect_menus()
        self.status_label.SetLabel(f"Added Loop {display_number} ({new_length}s)")


    def _on_pitch_input_change(self, event):
        if self.pitch_input_choice.GetSelection() < len(self.loop_controls):
            control = self.loop_controls[self.pitch_input_choice.GetSelection()]
            self.looper.pitch_input_id = control['id']
            print(f"Pitch input set to loop {control['display_number']}")  # Debug

    def _on_pitch_output_change(self, event):
        if self.pitch_output_choice.GetSelection() < len(self.loop_controls):
            control = self.loop_controls[self.pitch_output_choice.GetSelection()]
            self.looper.pitch_output_id = control['id']
            print(f"Pitch output set to loop {control['display_number']}")  # Debug

    def _on_pitch_semitones_change(self, event):
        semitones = self.pitch_semitones_slider.GetValue()
        self.looper.pitch_shift.semitones = semitones
        print(f"Pitch semitones set to {semitones}")  # Debug

    def _on_pitch_quality_change(self, event):
        quality = self.pitch_quality_choice.GetStringSelection().lower()
        self.looper.pitch_shift.set_quality(quality)
        print(f"Pitch quality set to {quality}")  # Debug

    def _on_pitch_feedback_change(self, event):
        """Handle feedback slider changes"""
        feedback = self.pitch_feedback_slider.GetValue() / 100.0  # Convert to 0.0-0.9 range
        self.looper.pitch_feedback = feedback
        print(f"Pitch feedback set to {feedback:.2f}")

    # Add button handlers
    def toggle_bypass_pitch(self, event):
        self.looper.pitch_bypass = not self.looper.pitch_bypass
        state = "OFF" if self.looper.pitch_bypass else "ON"
        self.bypass_pitch_button.SetLabel(f"Bypass Pitch: {'On' if self.looper.pitch_bypass else 'Off'}")
        print(f"Pitch effect bypass: {state}")
        print(f"Current settings:")
        print(f"  Input loop: {self.looper.pitch_input_id}")
        print(f"  Output loop: {self.looper.pitch_output_id}")
        print(f"  Semitones: {self.looper.pitch_shift.semitones}")
        print(f"  Quality: {self.looper.pitch_shift.quality}")

    def toggle_pitch_overdub(self, event):
        self.looper.pitch_overdub = not self.looper.pitch_overdub
        self.pitch_overdub_button.SetLabel(f"Pitch Overdub: {'On' if self.looper.pitch_overdub else 'Off'}")

    def _on_pitch_semitones_text_change(self, event):
        """Handle text changes for semitones"""
        try:
            value = int(self.pitch_semitones_text.GetValue())
            value = max(-24, min(24, value))  # Clamp to range

             # Update text control with clamped value
            if value != int(self.pitch_semitones_text.GetValue()):
                self.pitch_semitones_text.ChangeValue(str(value))
        
            
            # Update text control with clamped value
            self.pitch_semitones_text.ChangeValue(str(value))
            
            # Update slider without triggering its event
            self.pitch_semitones_slider.Unbind(wx.EVT_SLIDER)
            self.pitch_semitones_slider.SetValue(value)
            self.pitch_semitones_slider.Bind(wx.EVT_SLIDER, self._on_pitch_semitones_slider_change)
            
            
            # Update pitch effect with corrected direction
            self.looper.pitch_shift.semitones = value
            print(f"Pitch set to {value} semitones (negative = lower, positive = higher)")
        except ValueError:
            current = self.looper.pitch_shift.semitones
            self.pitch_semitones_text.ChangeValue(str(current))
           

    def _on_pitch_semitones_slider_change(self, event):
        """Handle slider changes for semitones"""
        value = self.pitch_semitones_slider.GetValue()
        
        # Update text control without triggering its event
        self.pitch_semitones_text.Unbind(wx.EVT_TEXT)
        self.pitch_semitones_text.ChangeValue(str(value))
        self.pitch_semitones_text.Bind(wx.EVT_TEXT, self._on_pitch_semitones_text_change)
        
        # Update pitch effect
        self.looper.pitch_shift.semitones = value
        print(f"Pitch semitones set to {value} (from slider)")

    def _on_pitch_feedback_change(self, event):
        """Handle feedback slider changes"""
        feedback = self.pitch_feedback_slider.GetValue()
        self.looper.pitch_feedback = feedback / 100.0  # Convert to 0.0-0.9 range
        self.pitch_feedback_text.SetLabel(f"{feedback}%")
        print(f"Pitch feedback set to {feedback}%")

    def on_quit(self, event):
        """Quit the application"""
        self.looper.is_running = False
        
        if hasattr(self.looper, 'is_recording') and self.looper.is_recording:
            self.looper.is_recording = False
        
        def safe_close():
            self.looper.stop()
            self.Destroy()
        
        wx.CallAfter(safe_close)