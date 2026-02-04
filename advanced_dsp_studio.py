import numpy as np
import tkinter as tk
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.fft import fft, fftfreq
from scipy.signal import (butter, cheby1, cheby2, ellip, iirnotch,
                          firwin, lfilter, filtfilt, tf2zpk, freqz, chirp)
import customtkinter as ctk
import complex_filters

# Styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SignalGenerator:
    def __init__(self, fs=2000, duration=0.5):
        self.fs = fs
        self.duration = duration
        self.t = np.arange(0, duration, 1/fs)
        self.sines = [
            {"freq": 10, "amp": 1.0, "phase": 0},
            {"freq": 500, "amp": 0.5, "phase": 0}
        ]
        self.noise_lvl = 0.05
        self.imported_data = None
        self.raw_matrix = None # For multi-column CSVs
        self.mode = "Synth" # Synth or Import
        self.waveform = "Sines"
        self.sweep_start = 10.0
        self.sweep_end = 800.0
        self.sweep_duration = 0.5
        self.sweep_amp = 1.0

    def get_signal(self):
        if self.mode == "Import" and self.imported_data is not None:
            return self.imported_data
        
        y = np.zeros_like(self.t)
        if self.waveform == "Sines":
            for s in self.sines:
                y += s["amp"] * np.sin(2 * np.pi * s["freq"] * self.t + s["phase"])
        elif self.waveform == "Impulse":
            y[len(y)//4] = 1.0 # Standard impulse spike
        elif self.waveform == "Step":
            y[len(y)//4:] = 1.0 # Step response stimulus
        elif self.waveform == "Sweep":
            y = self.sweep_amp * chirp(self.t, f0=min(self.sweep_start, self.fs/2-1), 
                                      f1=min(self.sweep_end, self.fs/2-1), 
                                      t1=self.duration, method='linear')
            
        y += self.noise_lvl * np.random.normal(size=len(self.t))
        return y

class DSPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Advanced DSP Studio Pro")
        self.geometry("1600x950")

        # State Variables
        self.sig_gen = SignalGenerator(fs=2000)
        self.filter_resp = ctk.StringVar(value="Low-Pass")
        self.filter_class = ctk.StringVar(value="IIR")
        self.filter_proto = ctk.StringVar(value="Butterworth")
        self.cutoff_1 = 300.0
        self.cutoff_2 = 800.0 
        self.order = 4
        self.ripple = 1.0 
        self.atten = 40.0 
        self.beta = 5.0
        self.notch_q = 30.0
        self.low_bw = ctk.BooleanVar(value=True) # Logic placeholder
        self.min_phase = ctk.BooleanVar(value=False)
        self.gauss_std = 7.0
        self.pm_width = 50.0 # Transition width for Parks-McClellan
        self.import_triggered = False
        self.high_bw = ctk.BooleanVar(value=False)
        self.show_briefs = ctk.BooleanVar(value=True)
        self.show_complex = ctk.BooleanVar(value=False)
        self.complex_filter = ctk.StringVar(value="Kalman")
        self._force_redraw = False
        self._crash_count = 0 
        self.fs_val = ctk.StringVar(value="2000")
        self.running = True # Playback state
        
        # C-Code Export Settings
        self.c_data_type = ctk.StringVar(value="Float32")
        self.c_impl_style = ctk.StringVar(value="Standard C")
        self.c_iir_struct = ctk.StringVar(value="Cascaded Biquads (SOS)")
        
        self.sine_controls = [] # For hiding/showing
        self.sweep_controls = []
        
        # Complex Filter Parameters
        self.kf_q = 1e-4; self.kf_r = 1e-2
        self.sg_win = 11; self.sg_poly = 2
        self.med_ker = 3
        self.wt_wave = "db4"; self.wt_lev = 2
        self.lms_mu = 0.01; self.lms_ord = 32
        
        self.import_format = ctk.StringVar(value="Raw ADC File")
        self.accel_axis = ctk.StringVar(value="AX")
        
        self.freq_sliders = []
        self.param_sliders = {}
        
        self.setup_ui()
        self.init_menu()
        
        # Optimization: Store last state to avoid redundant calculations/draws
        self._last_filter_params = None
        self.b, self.a = np.array([1.0]), np.array([1.0])
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_loop()

    def on_closing(self):
        self.quit()
        self.destroy()

    def init_menu(self):
        self.menubar = tk.Menu(self)
        
        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="New Project (Reset)", command=self.manual_refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        self.menubar.add_cascade(label="File", menu=file_menu)
        
        # View Menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        view_menu.add_checkbutton(label="Extended Range", variable=self.high_bw, command=self.update_bw_range)
        view_menu.add_checkbutton(label="Show Briefs", variable=self.show_briefs, command=self.toggle_briefs)
        self.menubar.add_cascade(label="View", menu=view_menu)
        
        # Tutorial Menu
        self.menubar.add_command(label="Tutorial", command=self.open_tutorial)
        
        # About Menu
        self.menubar.add_command(label="About", command=self.show_about)

        # Polynomial Menu
        poly_menu = tk.Menu(self.menubar, tearoff=0)
        poly_menu.add_command(label="Polynomial Analysis (Coming Soon)", state="disabled")
        self.menubar.add_cascade(label="Polynomial", menu=poly_menu)
        
        self.configure(menu=self.menubar)

    def open_tutorial(self):
        webbrowser.open("https://github.com/MEHDI021UK/DSP-Filter-Analyses-Software-Application?tab=readme-ov-file#1-filter-types-overview")

    def open_linkedin(self):
        webbrowser.open("https://www.linkedin.com/in/mehdi-sehati-44356bb1/")

    def show_about(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title("About Advanced DSP Studio Pro")
        about_win.geometry("500x400")
        about_win.attributes("-topmost", True)
        
        content = (
            "Advanced DSP Studio Pro is an industrial-grade engineering workbench "
            "designed for real-time digital signal processing, filter analysis, "
            "and embedded firmware code generation.\n\n"
            "It bridges the gap between high-level filter theory and low-level C implementation.\n\n"
            "-----------------------------------\n"
            "Designed by: Mehdi Sehati"
        )
        
        ctk.CTkLabel(about_win, text="Advanced DSP Studio Pro", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        txt = ctk.CTkLabel(about_win, text=content, wraplength=400, justify="center")
        txt.pack(pady=10, padx=20)
        
        ctk.CTkButton(about_win, text="Visit LinkedIn Profile", fg_color="#0077B5", 
                      command=self.open_linkedin).pack(pady=20)
        
        ctk.CTkButton(about_win, text="Close", command=about_win.destroy).pack(pady=10)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkScrollableFrame(self, width=350)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Header with Refresh Icon/Button
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(header_frame, text="DSP Controls", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left", padx=10)
        
        self.playback_btn = ctk.CTkButton(header_frame, text="⏸", width=40, font=ctk.CTkFont(size=18),
                                         fg_color="#333", hover_color="#555", command=self.toggle_playback)
        self.playback_btn.pack(side="right", padx=10)

        # System Sampling Rate (Fs) - Input Box
        self.fs_frame = ctk.CTkFrame(self.sidebar)
        self.fs_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.fs_frame, text="System Spectrum Range", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=2)
        fs_row = ctk.CTkFrame(self.fs_frame, fg_color="transparent"); fs_row.pack(fill="x", pady=2)
        ctk.CTkLabel(fs_row, text="Sampling Fs (Hz):", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        self.fs_entry = ctk.CTkEntry(fs_row, width=80, textvariable=self.fs_val)
        self.fs_entry.pack(side="right", padx=5)

        # Signal Input Selection
        self.source_segmented = ctk.CTkSegmentedButton(self.sidebar, values=["Synth", "Import"], 
                                                      command=self.toggle_source)
        self.source_segmented.set("Synth")
        self.source_segmented.pack(pady=5, padx=10, fill="x")

        # Range & UI Toggles
        self.toggles_frame = ctk.CTkFrame(self.sidebar)
        self.toggles_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkCheckBox(self.toggles_frame, text="Extended range (10kHz)", 
                        variable=self.high_bw, command=self.update_bw_range).pack(pady=2, anchor="w", padx=5)
        ctk.CTkCheckBox(self.toggles_frame, text="Show Graph Briefs", 
                        variable=self.show_briefs, command=self.toggle_briefs).pack(pady=2, anchor="w", padx=5)
        
        ctk.CTkCheckBox(self.toggles_frame, text="FIR Minimum Phase", 
                        variable=self.min_phase).pack(pady=2, anchor="w", padx=5)

        # Synth Group
        # Synth Group
        self.synth_group = ctk.CTkFrame(self.sidebar)
        self.synth_group.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(self.synth_group, text="Signal Synthesizer", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=2)

        # Stimulus Selector FIRST
        stim_frame = ctk.CTkFrame(self.synth_group, fg_color="transparent")
        stim_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(stim_frame, text="Waveform Type:", font=ctk.CTkFont(size=11)).pack(pady=2)
        self.stim_selector = ctk.CTkSegmentedButton(stim_frame, values=["Sines", "Impulse", "Step", "Sweep"],
                                                   command=self.toggle_waveform_ui)
        self.stim_selector.set("Sines")
        self.stim_selector.pack(pady=2, padx=10, fill="x")

        # Sine & Noise Params
        params = [
            ("Sine 1 Freq", 0, 1000, 10, lambda v: self.set_sine(0, "freq", v)),
            ("Sine 1 Amp", 0, 2, 1.0, lambda v: self.set_sine(0, "amp", v)),
            ("Sine 2 Freq", 0, 1000, 500, lambda v: self.set_sine(1, "freq", v)),
            ("Sine 2 Amp", 0, 2, 0.5, lambda v: self.set_sine(1, "amp", v)),
            ("Noise Level", 0, 1, 0.05, lambda v: setattr(self.sig_gen, 'noise_lvl', float(v)))
        ]
        
        for i, (label, low, high, start, cmd) in enumerate(params):
            sc = ctk.CTkFrame(self.synth_group, fg_color="transparent"); sc.pack(fill="x", pady=2)
            hf = ctk.CTkFrame(sc, fg_color="transparent"); hf.pack(fill="x")
            ctk.CTkLabel(hf, text=label, font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            vl = ctk.CTkLabel(hf, text=str(start), font=ctk.CTkFont(size=11, weight="bold"), text_color="#fc0")
            vl.pack(side="right", padx=5)
            
            # Unit logic for labels
            unit = "Hz" if "Freq" in label else ("V" if "Amp" in label or "Level" in label else "")
            def make_update(c, l, u, lbl):
                def update_cmd(v):
                    fmt = f"{float(v):.1f}" if float(v) > 1 else f"{float(v):.3f}"
                    l.configure(text=f"{fmt} {u}"); c(v)
                return update_cmd
            
            s = ctk.CTkSlider(sc, from_=low, to=high, command=make_update(cmd, vl, unit, label))
            s.set(start); s.pack(fill="x")
            if "Freq" in label: self.freq_sliders.append(s)
            if "Sine" in label: self.sine_controls.append(sc)

        # Sweep Params (Start, Stop, Duration, Amplitude)
        sweep_params = [
            ("Sweep Start Freq", 1, 1000, 10, lambda v: setattr(self.sig_gen, 'sweep_start', float(v))),
            ("Sweep Stop Freq", 1, 1000, 800, lambda v: setattr(self.sig_gen, 'sweep_end', float(v))),
            ("Sweep Amplitude", 0, 2, 1.0, lambda v: setattr(self.sig_gen, 'sweep_amp', float(v))),
            ("Sweep Duration (s)", 0.1, 2.0, 0.5, lambda v: self.update_sweep_domain(v))
        ]

        for label, low, high, start, cmd in sweep_params:
            sc = ctk.CTkFrame(self.synth_group, fg_color="transparent")
            # We don't pack them yet
            hf = ctk.CTkFrame(sc, fg_color="transparent"); hf.pack(fill="x")
            ctk.CTkLabel(hf, text=label, font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            vl = ctk.CTkLabel(hf, text=str(start), font=ctk.CTkFont(size=11, weight="bold"), text_color="#00ff88")
            vl.pack(side="right", padx=5)
            
            unit = "Hz" if "Freq" in label else "s"
            def make_sw_update(c, l, u):
                def up(v):
                    fmt = f"{float(v):.1f}" if float(v) > 1 else f"{float(v):.2f}"
                    l.configure(text=f"{fmt} {u}"); c(v)
                return up
            
            s = ctk.CTkSlider(sc, from_=low, to=high, command=make_sw_update(cmd, vl, unit))
            s.set(start); s.pack(fill="x")
            self.sweep_controls.append(sc)
            if "Freq" in label: self.freq_sliders.append(s)

        # Import Group
        self.import_group = ctk.CTkFrame(self.sidebar)
        ctk.CTkLabel(self.import_group, text="Data Import", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        ctk.CTkLabel(self.import_group, text="Import Format", font=ctk.CTkFont(size=11)).pack(pady=2)
        self.fmt_menu = ctk.CTkOptionMenu(self.import_group, values=["Raw ADC File", "Accel-Gyro CSV"], 
                                         variable=self.import_format, command=self.on_format_change)
        self.fmt_menu.pack(pady=2, padx=10)
        
        self.axis_frame = ctk.CTkFrame(self.import_group, fg_color="transparent")
        self.axis_btns = ctk.CTkSegmentedButton(self.axis_frame, values=["AX", "AY", "AZ", "GX", "GY", "GZ"],
                                               variable=self.accel_axis, command=self.update_axis_data)
        self.axis_btns.pack(pady=5)
        
        self.import_btn = ctk.CTkButton(self.import_group, text="Load Data (CSV/TXT)", command=self.load_file)
        self.import_btn.pack(pady=5, padx=10)
        self.file_label = ctk.CTkLabel(self.import_group, text="Pending Import...", font=ctk.CTkFont(size=10))
        self.file_label.pack()
        self.import_run_btn = ctk.CTkButton(self.import_group, text="▶ Run Analysis", fg_color="#ff7b00", 
                                            command=self.trigger_import_run)

        # Filter Hierarchy
        self.f_frame = ctk.CTkFrame(self.sidebar)
        self.f_frame.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(self.f_frame, text="Filter Configuration", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        ctk.CTkLabel(self.f_frame, text="Response Type").pack()
        self.resp_menu = ctk.CTkOptionMenu(self.f_frame, values=["None", "Low-Pass", "High-Pass", "Band-Pass", "Band-Stop", "Notch"], 
                                           variable=self.filter_resp, command=self.force_update)
        self.resp_menu.pack(pady=5)

        ctk.CTkLabel(self.f_frame, text="Filter Class").pack()
        self.class_menu = ctk.CTkOptionMenu(self.f_frame, values=["None", "IIR", "FIR", "Adaptive (LMS)", "Lattice"], 
                                            variable=self.filter_class, command=lambda v: (self.update_proto_options(v), self.force_update(v)))
        self.class_menu.pack(pady=5)

        ctk.CTkLabel(self.f_frame, text="Design Method / Prototype").pack()
        self.proto_menu = ctk.CTkOptionMenu(self.f_frame, values=[], variable=self.filter_proto, command=self.force_update)
        self.proto_menu.pack(pady=5)
        
        self.param_group = self.create_param_group("Filter Parameters", [
            ("Order", 1, 12, 4, lambda v: setattr(self, 'order', int(float(v)))),
            ("Cutoff 1 (Low/Center)", 1, 1000, 300, lambda v: setattr(self, 'cutoff_1', float(v))),
            ("Cutoff 2 (High)", 1, 1000, 800, lambda v: setattr(self, 'cutoff_2', float(v))),
            ("Passband Ripple (dB)", 0.1, 10, 1, lambda v: setattr(self, 'ripple', float(v))),
            ("Stopband Atten (dB)", 10, 80, 40, lambda v: setattr(self, 'atten', float(v))),
            ("Kaiser Beta", 0.1, 15, 5, lambda v: setattr(self, 'beta', float(v))),
            ("Notch Quality (Q)", 1, 100, 30, lambda v: setattr(self, 'notch_q', float(v))),
            ("Gaussian StdDev", 0.1, 20, 7, lambda v: setattr(self, 'gauss_std', float(v))),
            ("PM Trans. Width", 1, 500, 50, lambda v: setattr(self, 'pm_width', float(v)))
        ])

        # New Toggle Location: Below Parameters
        self.complex_toggle = ctk.CTkCheckBox(self.sidebar, text="Enable Complex/AI Filter Layer", 
                                              variable=self.show_complex, command=self.toggle_complex_visibility,
                                              fg_color="#ff7b00", hover_color="#e66e00")
        self.complex_toggle.pack(pady=10, padx=10)

        # Complex Studio Group (Hidden by default)
        self.complex_group = ctk.CTkFrame(self.sidebar)
        ctk.CTkLabel(self.complex_group, text="Advanced Algorithms", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.complex_menu = ctk.CTkOptionMenu(self.complex_group, 
                                             values=["Kalman", "Savitzky-Golay", "Wavelet", "Adaptive (LMS)", "Median"],
                                             variable=self.complex_filter, command=self.update_complex_ui)
        self.complex_menu.pack(pady=5)
        
        self.complex_info_box = ctk.CTkTextbox(self.complex_group, height=100, font=ctk.CTkFont(size=11), fg_color="#1a1a1a")
        self.complex_info_box.pack(fill="x", padx=10, pady=5)
        
        self.comp_param_frame = ctk.CTkFrame(self.complex_group, fg_color="transparent")
        self.comp_param_frame.pack(fill="x", pady=5)
        
        self.update_complex_ui("Kalman")

        # C-Code Export Settings Group
        self.c_settings_group = ctk.CTkFrame(self.sidebar)
        self.c_settings_group.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(self.c_settings_group, text="C-Code Export Settings", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        ctk.CTkLabel(self.c_settings_group, text="Data Type", font=ctk.CTkFont(size=11)).pack()
        ctk.CTkOptionMenu(self.c_settings_group, values=["Float32", "Fixed Q15", "Fixed Q31"], 
                          variable=self.c_data_type, fg_color="#444").pack(pady=2, padx=10, fill="x")
        
        ctk.CTkLabel(self.c_settings_group, text="Implementation style", font=ctk.CTkFont(size=11)).pack()
        ctk.CTkOptionMenu(self.c_settings_group, values=["Standard C", "ARM CMSIS-DSP"], 
                          variable=self.c_impl_style, fg_color="#444").pack(pady=2, padx=10, fill="x")
        
        ctk.CTkLabel(self.c_settings_group, text="IIR Structure", font=ctk.CTkFont(size=11)).pack()
        ctk.CTkOptionMenu(self.c_settings_group, values=["Direct Form II", "Cascaded Biquads (SOS)"], 
                          variable=self.c_iir_struct, fg_color="#444").pack(pady=2, padx=10, fill="x")

        # Analyze Button - ALWAYS AT BOTTOM
        self.calc_btn = ctk.CTkButton(self.sidebar, text="Calculate & Analyze", 
                                      fg_color="#28a745", hover_color="#218838",
                                      command=self.show_report)
        self.calc_btn.pack(pady=10, padx=10, fill="x", side="bottom")

        self.update_proto_options("IIR")
        self.toggle_source("Synth") 

        # --- Main View (Scrollable) ---
        self.main_view = ctk.CTkScrollableFrame(self)
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_view.grid_columnconfigure(0, weight=1)
        self.main_view.grid_columnconfigure(1, weight=1)
        self.main_view._scrollbar.configure(height=0) 
        
        self.cards = {}
        self.create_all_plot_cards()

    def create_all_plot_cards(self):
        plots = [
            ("time", "Signal Oscilloscope (Time Domain)", 
             "AIM: To visualize the instantaneous amplitude changes of the signal in high resolution.\n"
             "UTILITY: Crucial for comparing input vs output waveforms directly. It helps you identify clipping, saturation, and time-domain phase shifts in your firmware implementation."),
            
            ("fft", "Frequency Spectrum (FFT)",
             "AIM: To decompose the complex time signal into its constituent sine frequency components.\n"
             "UTILITY: Essential for identifying exact noise frequencies and harmonics. Verifies that the filter has effectively suppressed the target interference bands."),
            
            ("resp", "Magnitude Response (dB)",
             "AIM: To show the mathematical transfer function of the filter in logarithmic scale.\n"
             "UTILITY: This is the primary design chart. Use it to measure transition bandwidth (slope), confirm the -3dB cutoff point, and verify stopband attenuation levels required by your system."),
            
            ("impulse", "Impulse Response (h[n])",
             "AIM: To observe the filter's output when stimulated by a single unit-impulse pulse.\n"
             "UTILITY: Defines the 'memory' and ringing behavior of the filter. Use it to determine settling time and identify potential instability or oscillation issues in your code."),
            
            ("pz", "Z-Plane Stability Map",
             "AIM: To map the complex roots (poles and zeros) of the filter's transfer function.\n"
             "UTILITY: The ultimate tool for stability verification. Any pole outside the unit circle indicates an unstable filter that will overflow in hardware. Zeros show frequencies where the gain is exactly zero."),
            
            ("phase", "Phase Response (Radians)",
             "AIM: To visualize how the filter rotates the phase of different frequency components.\n"
             "UTILITY: Critical for high-fidelity audio and digital communications. Non-linear phase can smear pulse shapes, causing data errors even if the magnitude response is correct."),
            
            ("gain_lin", "Linear Gain Profile",
             "AIM: To view the gain as a simple multiplier (0.0 to 1.0) rather than logarithmic decibels.\n"
             "UTILITY: Simplifies real-world voltage sensitivity calculations. Knowing exactly what percentage of a sensor's input voltage translates to the output simplifies ADC scaling.")
        ]

        for key, title, desc in plots:
            card = ctk.CTkFrame(self.main_view, fg_color="#242424", corner_radius=0)
            card.pack(fill="x", pady=10, padx=0)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color="#00d1ff").pack(pady=5)
            
            # Cinematic Full-Width Figure
            fig = plt.figure(figsize=(14, 6), facecolor='#242424') 
            ax = fig.add_subplot(111); ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='white'); ax.xaxis.label.set_color('white'); ax.yaxis.label.set_color('white')
            ax.grid(True, color='#444444', linestyle='--')
            
            # Edge-to-Edge Margins
            fig.subplots_adjust(left=0.06, right=0.98, top=0.94, bottom=0.12)
            
            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.get_tk_widget().pack(fill="both", expand=True, pady=0, padx=0)
            
            info = ctk.CTkTextbox(card, height=120, font=ctk.CTkFont(size=12, family="Consolas"), fg_color="#1a1a1a", border_width=0)
            info.pack(fill="x", padx=15, pady=5)
            info.insert("1.0", desc)
            info.configure(state="disabled")
            
            self.cards[key] = {"card": card, "fig": fig, "ax": ax, "canvas": canvas, "info": info}

    def toggle_briefs(self):
        for k in self.cards:
            self.cards[k]["card"].pack_forget()
            self.cards[k]["card"].grid_forget()
        
        if self.show_briefs.get():
            for k in self.cards:
                self.cards[k]["card"].pack(fill="x", pady=10, padx=0)
                self.cards[k]["info"].pack(fill="x", padx=15, pady=5)
                self.cards[k]["fig"].set_size_inches(14, 6)
                self.cards[k]["canvas"].draw()
        else:
            for i, k in enumerate(self.cards):
                r, c = divmod(i, 2)
                self.cards[k]["card"].grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
                self.cards[k]["info"].pack_forget()
                self.cards[k]["fig"].set_size_inches(8, 5) # Scale down slightly for grid
                self.cards[k]["canvas"].draw()

    def create_group(self, name, sliders):
        group_frame = ctk.CTkFrame(self.sidebar)
        group_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(group_frame, text=name, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=2)
        for label, low, high, start, cmd in sliders:
            sc = ctk.CTkFrame(group_frame, fg_color="transparent"); sc.pack(fill="x", pady=2)
            hf = ctk.CTkFrame(sc, fg_color="transparent"); hf.pack(fill="x")
            ctk.CTkLabel(hf, text=label, font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            unit = "Hz" if "Freq" in label or "Fs" in label else ("dB" if "dB" in label else "pk")
            vl = ctk.CTkLabel(hf, text=f"{start} {unit}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00d1ff")
            vl.pack(side="right", padx=2)
            def make_update(c, l, u): return lambda v: (l.configure(text=f"{float(v):.1f} {u}"), c(v))
            s = ctk.CTkSlider(sc, from_=low, to=high, command=make_update(cmd, vl, unit))
            s.set(start); s.pack(fill="x")
            if any(key in label for key in ["Freq", "Fs", "Cutoff"]): 
                self.freq_sliders.append(s)
        return group_frame

    def create_param_group(self, name, sliders):
        group_frame = ctk.CTkFrame(self.sidebar)
        group_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(group_frame, text=name, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=2)
        for label, low, high, start, cmd in sliders:
            sc = ctk.CTkFrame(group_frame, fg_color="transparent"); sc.pack(fill="x", pady=2)
            hf = ctk.CTkFrame(sc, fg_color="transparent"); hf.pack(fill="x")
            ctk.CTkLabel(hf, text=label, font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
            unit = "Hz" if "Cutoff" in label else ("dB" if "dB" in label else "")
            vl = ctk.CTkLabel(hf, text=f"{start} {unit}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00d1ff")
            vl.pack(side="right", padx=2)
            def make_update(c, l, u, lb):
                def update_cmd(v):
                    fmt = f"{int(float(v))}" if "Order" in lb else f"{float(v):.1f}"
                    l.configure(text=f"{fmt} {u}"); c(v)
                return update_cmd
            s = ctk.CTkSlider(sc, from_=low, to=high, command=make_update(cmd, vl, unit, label))
            s.set(start); s.pack(fill="x"); self.param_sliders[label] = sc
            if any(key in label for key in ["Freq", "Fs", "Cutoff"]): 
                self.freq_sliders.append(s)
        return group_frame

    def update_bw_range(self):
        new_max = 10000 if self.high_bw.get() else 1000
        for s in self.freq_sliders:
            # Update all frequency sliders (Sines and Cutoffs)
            s.configure(to=new_max)
            if s.get() > new_max: s.set(new_max)
        
        # Update the Fs Slider itself (Spectrum range)
        fs_max = 20000 if self.high_bw.get() else 2000
        self.fs_slider.configure(to=fs_max)
        if self.fs_slider.get() > fs_max: self.fs_slider.set(fs_max)

    def toggle_source(self, mode):
        self.sig_gen.mode = mode
        if mode == "Synth":
            self.import_group.pack_forget()
            self.synth_group.pack(fill="x", pady=5, padx=5, after=self.source_segmented)
        else:
            self.synth_group.pack_forget()
            self.import_group.pack(fill="x", pady=5, padx=5, after=self.source_segmented)
        
        # Ensure FS input and filtering frames are always visible
        self.fs_frame.pack(fill="x", pady=5, padx=5, before=self.source_segmented)
        self.f_frame.pack(fill="x", pady=10, padx=5, after=self.toggles_frame)
        self.param_group.pack(fill="x", pady=5, padx=5, after=self.f_frame)
        self.update_ui_visibility()

    def toggle_complex_visibility(self):
        if self.show_complex.get():
            self.complex_group.pack(fill="x", pady=5, padx=5, before=self.calc_btn)
        else:
            self.complex_group.pack_forget()

    def force_update(self, *args):
        self._force_redraw = True
        self.update_ui_visibility()

    def toggle_waveform_ui(self, choice):
        setattr(self.sig_gen, 'waveform', choice)
        # Hide All
        for sc in self.sine_controls: sc.pack_forget()
        for sc in self.sweep_controls: sc.pack_forget()
        
        if choice == "Sines":
            for sc in self.sine_controls: sc.pack(fill="x", pady=2)
        elif choice == "Sweep":
            for sc in self.sweep_controls: sc.pack(fill="x", pady=2)
            
        self.force_update()

    def update_sweep_domain(self, val):
        val = float(val)
        self.sig_gen.duration = val
        self.sig_gen.t = np.arange(0, val, 1/self.sig_gen.fs)
        self.force_update()

    def update_complex_ui(self, choice):
        self.force_update()
        # Update Info
        self.complex_info_box.configure(state="normal")
        self.complex_info_box.delete("1.0", "end")
        self.complex_info_box.insert("1.0", complex_filters.get_complex_filter_info(choice))
        self.complex_info_box.configure(state="disabled")
        
        # Clear params
        for widget in self.comp_param_frame.winfo_children():
            widget.destroy()
            
        # Add relevant sliders
        if choice == "Kalman":
            self.add_comp_slider("Process Noise (Q) log", -6, -1, -4, lambda v: setattr(self, 'kf_q', 10**float(v)))
            self.add_comp_slider("Meas. Noise (R) log", -4, 1, -2, lambda v: setattr(self, 'kf_r', 10**float(v)))
        elif choice == "Savitzky-Golay":
            self.add_comp_slider("Window Length", 3, 51, 11, lambda v: setattr(self, 'sg_win', int(float(v))))
            self.add_comp_slider("Polynomial Order", 1, 5, 2, lambda v: setattr(self, 'sg_poly', int(float(v))))
        elif choice == "Median":
            self.add_comp_slider("Kernel Size", 3, 31, 3, lambda v: setattr(self, 'med_ker', int(float(v))))
        elif choice == "Wavelet":
             # Simplified wavelet selection
            ctk.CTkLabel(self.comp_param_frame, text="Wavelet: db4", font=ctk.CTkFont(size=10)).pack()
            self.add_comp_slider("Decomposition Level", 1, 5, 2, lambda v: setattr(self, 'wt_lev', int(float(v))))
        elif choice == "Adaptive (LMS)":
            self.add_comp_slider("Learning Rate (mu)", 0.001, 0.1, 0.01, lambda v: setattr(self, 'lms_mu', float(v)))
            self.add_comp_slider("Filter Order", 8, 128, 32, lambda v: setattr(self, 'lms_ord', int(float(v))))

    def add_comp_slider(self, label, low, high, start, cmd):
        f = ctk.CTkFrame(self.comp_param_frame, fg_color="transparent"); f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        v_lbl = ctk.CTkLabel(f, text=str(start), font=ctk.CTkFont(size=11, weight="bold"), text_color="#00d1ff")
        v_lbl.pack(side="right", padx=5)
        def _up(v):
            v_lbl.configure(text=f"{float(v):.2f}")
            cmd(v)
        s = ctk.CTkSlider(f, from_=low, to=high, command=_up); s.set(start); s.pack(fill="x", padx=5)

    def trigger_import_run(self):
        self.import_triggered = True; self.f_frame.pack(fill="x", pady=10, padx=5)
        self.param_group.pack(fill="x", pady=5, padx=5); self.calc_btn.pack(pady=10, padx=10, fill="x"); self.update_ui_visibility()

    def toggle_playback(self):
        self.running = not self.running
        if self.running:
            self.playback_btn.configure(text="⏸", fg_color="#333")
            self.update_loop() # Restart if it stopped
        else:
            self.playback_btn.configure(text="▶", fg_color="#28a745")

    def manual_refresh(self):
        """Force a full reset of the engine state to unfreeze."""
        self._last_filter_params = None
        self._force_redraw = True
        self._crash_count = 0
        # Trigger an immediate calculation
        try:
            self.update_loop(force=True)
            self.file_label.configure(text_color="#00d1ff") # Indicator of pulse
        except: pass

    def on_format_change(self, choice):
        if choice == "Accel-Gyro CSV": self.axis_frame.pack(pady=5)
        else: self.axis_frame.pack_forget()

    def update_axis_data(self, *args):
        if self.sig_gen.raw_matrix is not None:
            axis_map = {"AX": 1, "AY": 2, "AZ": 3, "GX": 4, "GY": 5, "GZ": 6}
            col_idx = axis_map.get(self.accel_axis.get(), 1)
            # Ensure index is safe
            if col_idx < self.sig_gen.raw_matrix.shape[1]:
                self.sig_gen.imported_data = self.sig_gen.raw_matrix[:, col_idx]
                self.import_triggered = True # Refresh graphs
                self._force_redraw = True

    def load_file(self):
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt *.csv")])
        if path:
            try:
                fmt = self.import_format.get()
                if fmt == "Raw ADC File":
                    data = np.loadtxt(path, delimiter=",")
                    if data.ndim > 1: data = data[:, 0]
                    self.sig_gen.raw_matrix = None
                else: # Accel-Gyro CSV
                    # Skip header line, use columns 1-6 (time is index 0)
                    data_raw = np.loadtxt(path, delimiter=",", skiprows=1)
                    self.sig_gen.raw_matrix = data_raw
                    # Auto select appropriate FS from time diff if possible
                    if data_raw.shape[0] > 1:
                        avg_dt = np.mean(np.diff(data_raw[:10, 0]))
                        if avg_dt > 0: self.fs_val.set(str(int(1/avg_dt)))
                    
                    axis_map = {"AX": 1, "AY": 2, "AZ": 3, "GX": 4, "GY": 5, "GZ": 6}
                    col_idx = axis_map.get(self.accel_axis.get(), 1)
                    data = data_raw[:, col_idx]
                
                self.sig_gen.imported_data = data
                self.import_triggered = True # Auto-trigger analysis
                self._force_redraw = True
                self.file_label.configure(text=f"Loaded: {path.split('/')[-1]}", text_color="#00ff00")
                
                self.fs_frame.pack(fill="x", pady=5, padx=5, before=self.source_segmented)
            except Exception as e: self.file_label.configure(text=f"Error: {e}", text_color="#ff4444")

    def update_ui_visibility(self, *args):
        resp = self.filter_resp.get(); proto = self.filter_proto.get(); f_class = self.filter_class.get()
        
        # 1. First, hide everything to start fresh
        for key in self.param_sliders:
            self.param_sliders[key].pack_forget()
            
        # 2. Only hide everything if the Response Type is 'None'
        if resp == "None":
            return
            
        # 3. Always show Order and Cutoff 1 if any filter response is active
        # This allows tuning even if the class/prototype is bypassed (None)
        self.param_sliders["Order"].pack(fill="x", pady=2)
        self.param_sliders["Cutoff 1 (Low/Center)"].pack(fill="x", pady=2)
        
        # 4. Hide advanced parameters if the implementation is bypassed
        if f_class == "None" or proto == "None":
            return
            
        # 5. Conditional parameters based on implementation
        if resp in ["Band-Pass", "Band-Stop"]:
            self.param_sliders["Cutoff 2 (High)"].pack(fill="x", pady=2)
        
        # Conditionals
        if resp in ["Band-Pass", "Band-Stop"]:
            self.param_sliders["Cutoff 2 (High)"].pack(fill="x", pady=2)
            
        if f_class == "IIR":
            if proto in ["Chebyshev I", "Elliptic"]:
                self.param_sliders["Passband Ripple (dB)"].pack(fill="x", pady=2)
            if proto in ["Chebyshev II", "Elliptic"]:
                self.param_sliders["Stopband Atten (dB)"].pack(fill="x", pady=2)
            if proto == "Gaussian":
                self.param_sliders["Gaussian StdDev"].pack(fill="x", pady=2)
        
        if resp == "Notch":
            self.param_sliders["Notch Quality (Q)"].pack(fill="x", pady=2)
            
        if f_class == "FIR":
            if proto == "Kaiser": self.param_sliders["Kaiser Beta"].pack(fill="x", pady=2)
            if proto == "Gaussian": self.param_sliders["Gaussian StdDev"].pack(fill="x", pady=2)
            if proto == "Parks-McClellan": self.param_sliders["PM Trans. Width"].pack(fill="x", pady=2)

    def set_sine(self, idx, key, val): self.sig_gen.sines[idx][key] = float(val)

    def update_proto_options(self, choice):
        if choice == "None": opts = ["None"]
        elif choice == "IIR": opts = ["None", "Butterworth", "Chebyshev I", "Chebyshev II", "Elliptic", "Bessel", "Gaussian"]
        elif choice == "FIR": 
            opts = ["None", "Parks-McClellan", "Raised Cosine", "Gaussian", "Rectangular", "Kaiser", "Hamming", "Hanning", "Blackman"]
        elif choice == "Adaptive (LMS)": opts = ["Standard LMS", "Normalized LMS"]
        else: opts = ["Grey-Markel", "All-Pass Lattice"]
        self.proto_menu.configure(values=opts); self.filter_proto.set(opts[0]); self.update_ui_visibility()

    def get_filter(self, fs, output='ba'):
        res = self.filter_resp.get(); f_class = self.filter_class.get(); proto = self.filter_proto.get(); nyq = fs / 2
        if res == "None" or f_class == "None" or proto == "None": return np.array([1.0]), np.array([1.0])
        c1 = np.clip(self.cutoff_1, 0.1, nyq - 1); c2 = np.clip(self.cutoff_2, c1 + 0.1, nyq - 1)
        btype = 'low'
        if res == "High-Pass": btype = 'high'
        elif res == "Band-Pass": btype = 'bandpass'
        elif res == "Band-Stop": btype = 'bandstop'
        Wn = c1/nyq if res in ["Low-Pass", "High-Pass", "Notch"] else [c1/nyq, c2/nyq]
        if res == "Notch": return iirnotch(c1/nyq, self.notch_q)
        try:
            if f_class == "IIR":
                from scipy.signal import bessel
                if proto == "Butterworth": return butter(self.order, Wn, btype=btype, output=output)
                elif proto == "Chebyshev I": return cheby1(self.order, self.ripple, Wn, btype=btype, output=output)
                elif proto == "Chebyshev II": return cheby2(self.order, self.atten, Wn, btype=btype, output=output)
                elif proto == "Elliptic": return ellip(self.order, self.ripple, self.atten, Wn, btype=btype, output=output)
                elif proto == "Bessel": return bessel(self.order, Wn, btype=btype, output=output)
                elif proto == "Gaussian": 
                    return butter(self.order, Wn, btype=btype, output=output) 
            else:
                from scipy.signal import remez, minimum_phase
                numtaps = self.order * 4 + 1
                if numtaps % 2 == 0: numtaps += 1 # Ensure odd for simpler PM
                
                if proto == "Parks-McClellan":
                    bw = self.pm_width / nyq
                    bands = [0, c1/nyq - bw/2, c1/nyq + bw/2, 1]
                    # Clamp bands to valid range [0, 1]
                    bands = np.clip(bands, 0, 1)
                    # Ensure bands are strictly increasing
                    for i in range(1, len(bands)):
                        if bands[i] <= bands[i-1]: bands[i] = bands[i-1] + 1e-5
                    bands = np.clip(bands, 0, 1)
                    b = remez(numtaps, bands, [1, 0])
                else:
                    win = proto.lower()
                    if win == "kaiser": win = ('kaiser', self.beta)
                    elif win == "gaussian": win = ('gaussian', self.gauss_std)
                    elif win == "rectangular": win = "boxcar"
                    elif win == "raised cosine": win = "hann" # Closest standard window
                    b = firwin(numtaps, Wn, pass_zero=(btype in ['low', 'bandstop']), window=win)
                
                if self.min_phase.get():
                    b = minimum_phase(b)
                return b, np.array([1.0])
        except: return np.array([1.0]), np.array([1.0])

    def show_report(self):
        fs = self.sig_gen.fs; b, a = self.get_filter(fs); z, p, k = tf2zpk(b, a)
        ftype = self.filter_resp.get(); fclass = self.filter_class.get()
        data_type = self.c_data_type.get()
        impl_style = self.c_impl_style.get()
        iir_struct = self.c_iir_struct.get()
        
        rw = ctk.CTkToplevel(self); rw.title(f"DSP Report: {fclass} {ftype}")
        rw.geometry("1100x950"); rw.attributes("-topmost", True)
        
        txt = ctk.CTkTextbox(rw, font=ctk.CTkFont(family="Consolas", size=13))
        txt.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. Header & Metadata
        rep = "/*" + "="*75 + "\n"
        rep += " * INDUSTRIAL DSP EXPORT - ADVANCED FIRMWARE ARCHITECT\n"
        rep += f" * Target: {fclass} {ftype} Filter\n"
        rep += f" * Format: {data_type} | Implementation: {impl_style}\n"
        rep += f" * Structure: {iir_struct if fclass == 'IIR' else 'Direct Form'}\n"
        rep += " " + "="*75 + "*/\n\n"
        
        rep += "#include <stdint.h>\n"
        rep += "#include <math.h>\n"
        if impl_style == "ARM CMSIS-DSP":
            rep += "#include \"arm_math.h\"\n"
        rep += "\n"
        
        rep += f"#define FS_HZ           {fs}\n"
        rep += f"#define FILTER_ORDER     {len(b)-1 if fclass == 'FIR' else self.order}\n"
        
        # 2. Coefficients Handling
        rep += "\n// --- COEFFICIENTS ---\n"
        
        if fclass == "IIR" and iir_struct == "Cascaded Biquads (SOS)":
            sos = self.get_filter(fs, output='sos')
            rep += f"#define NUM_STAGES       {sos.shape[0]}\n"
            
            if data_type == "Float32":
                rep += "static float sos_coeffs[] = {\n"
                for i, s in enumerate(sos):
                    # b0, b1, b2, a1, a2 (a0 is usually 1.0)
                    rep += f"    {s[0]:.10f}f, {s[1]:.10f}f, {s[2]:.10f}f, {s[4]:.10f}f, {s[5]:.10f}f, // Stage {i}\n"
                rep += "};\n"
            elif data_type == "Fixed Q15":
                rep += "static const int16_t sos_coeffs[] = {\n"
                for i, s in enumerate(sos):
                    b0, b1, b2 = s[0:3]; a1, a2 = s[4:6]
                    coeffs = [int(x * 32767) for x in [b0, b1, b2, -a1, -a2]] # Note inverted a in ARM/CMSIS
                    rep += f"    {', '.join(map(str, coeffs))}, // Stage {i}\n"
                rep += "};\n"
            
            # Implementation function
            if impl_style == "ARM CMSIS-DSP":
                rep += "\n// CMSIS-DSP Biquad Setup\n"
                rep += "static arm_biquad_casd_df1_inst_f32 S;\n"
                rep += "static float state[4 * NUM_STAGES];\n\n"
                rep += "void Filter_Init(void) {\n"
                rep += "    arm_biquad_cascade_df1_init_f32(&S, NUM_STAGES, sos_coeffs, state);\n"
                rep += "}\n\n"
                rep += "float Filter_Process(float in) {\n"
                rep += "    float out;\n"
                rep += "    arm_biquad_cascade_df1_f32(&S, &in, &out, 1);\n"
                rep += "    return out;\n"
                rep += "}\n"
            else:
                rep += "\n// Standard Biquad Implementation\n"
                rep += "typedef struct { float w1, w2; } BiquadState;\n"
                rep += "static BiquadState bq_states[NUM_STAGES];\n\n"
                rep += "float Filter_Process(float in) {\n"
                rep += "    float x = in;\n"
                rep += "    for(int i=0; i<NUM_STAGES; i++) {\n"
                rep += "        float *c = &sos_coeffs[i*5];\n"
                rep += "        float w = x - c[3]*bq_states[i].w1 - c[4]*bq_states[i].w2;\n"
                rep += "        x = c[0]*w + c[1]*bq_states[i].w1 + c[2]*bq_states[i].w2;\n"
                rep += "        bq_states[i].w2 = bq_states[i].w1; bq_states[i].w1 = w;\n"
                rep += "    }\n    return x;\n}\n"

        else: # Direct Form (IIR or FIR)
            if data_type == "Float32":
                rep += f"static const float B_COEFFS[] = {{{', '.join([f'{x:.10f}f' for x in b])}}};\n"
                if fclass == "IIR":
                    rep += f"static const float A_COEFFS[] = {{{', '.join([f'{x:.10f}f' for x in a])}}};\n"
            
            # Logic Function
            rep += f"\nfloat Filter_Process(float in) {{\n"
            if fclass == "FIR":
                rep += f"    static float x[FILTER_ORDER + 1] = {{0.0f}};\n"
                rep += "    float out = 0.0f; x[0] = in;\n"
                rep += "    for(int i=0; i<=FILTER_ORDER; i++) out += B_COEFFS[i] * x[i];\n"
                rep += "    for(int i=FILTER_ORDER; i>0; i--) x[i] = x[i-1];\n"
                rep += "    return out;\n"
            else: # Direct Form II IIR
                rep += f"    static float w[FILTER_ORDER + 1] = {{0.0f}};\n"
                rep += "    float wn = in;\n"
                for i in range(1, len(a)): rep += f"    wn -= A_COEFFS[{i}] * w[{i}];\n"
                rep += "    w[0] = wn; float out = 0.0f;\n"
                for i in range(len(b)): rep += f"    out += B_COEFFS[{i}] * w[{i}];\n"
                rep += "    for(int i=FILTER_ORDER; i>0; i--) w[i] = w[i-1];\n"
                rep += "    return out;\n"
            rep += "}\n\n"

        # 6. Complex Filter Implementation (If enabled)
        if self.show_complex.get():
            c_type = self.complex_filter.get()
            rep += "/* " + "="*75 + "\n"
            rep += f" * ADVANCED LAYER: {c_type.upper()}\n"
            rep += " " + "="*75 + " */\n\n"

            if c_type == "Kalman":
                rep += f"// Kalman Parameters: Q={self.kf_q:.10f}, R={self.kf_r:.6f}\n"
                rep += "float Kalman_Process(float p_in) {\n"
                rep += "    static float p_x = 0.0f; // State estimate\n"
                rep += "    static float p_p = 1.0f; // Estimate error covariance\n"
                rep += f"    const float p_q = {self.kf_q:.10f}f; // Process noise\n"
                rep += f"    const float p_r = {self.kf_r:.6f}f;  // Measurement noise\n\n"
                rep += "    // Prediction\n"
                rep += "    p_p = p_p + p_q;\n\n"
                rep += "    // Update\n"
                rep += "    float p_k = p_p / (p_p + p_r); // Kalman Gain\n"
                rep += "    p_x = p_x + p_k * (p_in - p_x);\n"
                rep += "    p_p = (1.0f - p_k) * p_p;\n\n"
                rep += "    return p_x;\n"
                rep += "}\n\n"
            
            elif c_type == "Savitzky-Golay":
                rep += f"// Savitzky-Golay (Window: {self.sg_win}, Poly: {self.sg_poly})\n"
                rep += "// Note: Optimized for the selected window on-chip\n"
                rep += f"#define SG_WINDOW {self.sg_win}\n"
                rep += "float SG_Process(float p_in) {\n"
                rep += f"    static float buffer[SG_WINDOW] = {{0.0f}};\n"
                rep += "    // Shift and add\n"
                rep += "    for(int i = SG_WINDOW-1; i > 0; i--) buffer[i] = buffer[i-1];\n"
                rep += "    buffer[0] = p_in;\n"
                rep += "    // Implementation typically uses precomputed coefficients weights[i]\n"
                rep += "    float out = 0.0f;\n"
                rep += "    // (Convolution with SG coefficients goes here)\n"
                rep += "    return out; // Placeholder for coefficients\n"
                rep += "}\n\n"
            
            elif c_type == "Median":
                rep += f"#define MED_SIZE {self.med_ker}\n"
                rep += "float Median_Process(float p_in) {\n"
                rep += "    static float buf[MED_SIZE] = {0.0f};\n"
                rep += "    // Sort and return middle value logic\n"
                rep += "    // (Standard sorting algorithm implemented here)\n"
                rep += "    return buf[MED_SIZE/2];\n"
                rep += "}\n\n"

            elif c_type == "Adaptive (LMS)":
                rep += f"#define LMS_ORDER {self.lms_ord}\n"
                rep += f"// LMS Step Size: {self.lms_mu:.5f}\n"
                rep += "float LMS_Process(float p_in) {\n"
                rep += "    static float w[LMS_ORDER] = {0.0f};\n"
                rep += "    static float x[LMS_ORDER] = {0.0f};\n"
                rep += f"    const float mu = {self.lms_mu:.5f}f;\n"
                rep += "    float y = 0.0f;\n"
                rep += "    for(int i=0; i<LMS_ORDER; i++) y += w[i]*x[i];\n"
                rep += "    float e = p_in - y;\n"
                rep += "    for(int i=0; i<LMS_ORDER; i++) w[i] += 2*mu*e*x[i];\n"
                rep += "    for(int i=LMS_ORDER-1; i>0; i--) x[i] = x[i-1];\n"
                rep += "    x[0] = p_in;\n"
                rep += "    return y;\n"
                rep += "}\n\n"
        
        txt.insert("1.0", rep); txt.configure(state="disabled")

    def update_loop(self, force=False):
        if not self.running and not force: return
        
        # Optimization: only process if signal exists or in synth mode
        if self.sig_gen.mode == "Import" and self.sig_gen.imported_data is None:
            self.after(300, self.update_loop); return
            
        try:
            fs_str = self.fs_val.get()
            fs = int(fs_str) if fs_str else 2000
        except: fs = 2000
        self.sig_gen.fs = fs
        
        # Wrapped analysis in try-except to prevent UI lockup on math errors
        try:
            # 1. Check if filter parameters changed
            current_params = (
                fs, self.filter_resp.get(), self.filter_class.get(), self.filter_proto.get(),
                self.cutoff_1, self.cutoff_2, self.order, self.ripple, self.atten,
                self.beta, self.notch_q, self.gauss_std, self.pm_width, self.min_phase.get(),
                self.show_complex.get(), self.complex_filter.get(),
                self.kf_q, self.kf_r, self.sg_win, self.sg_poly, self.med_ker, self.wt_lev, self.lms_mu, self.lms_ord
            )
            
            # Check if we need to recalculate the filter coefficient and redraw design plots
            filter_changed = (self._last_filter_params != current_params)
            
            # 2. Get Signal
            raw = self.sig_gen.get_signal()
            
            # 3. Dual-Stage Process
            # Stage 1: Standard Filter (IIR/FIR)
            if filter_changed:
                self.b, self.a = self.get_filter(fs)
                self._last_filter_params = current_params
            
            # Apply standard filter first
            stage1_out = filtfilt(self.b, self.a, raw) if len(self.a) > 1 or len(self.b) > 1 else raw
            
            # Stage 2: Complex Filter (If enabled)
            if self.show_complex.get():
                c_type = self.complex_filter.get()
                if c_type == "Kalman": 
                    filtered = complex_filters.apply_kalman_filter(stage1_out, self.kf_q, self.kf_r)
                elif c_type == "Savitzky-Golay": 
                    filtered = complex_filters.apply_savgol_filter(stage1_out, self.sg_win, self.sg_poly)
                elif c_type == "Median": 
                    filtered = complex_filters.apply_median_filter(stage1_out, self.med_ker)
                elif c_type == "Wavelet": 
                    filtered = complex_filters.apply_wavelet_denoising(stage1_out, wavelet=self.wt_wave, level=self.wt_lev)
                elif c_type == "Adaptive (LMS)":
                    filtered = complex_filters.apply_lms_filter(stage1_out, self.lms_mu, self.lms_ord)
                else:
                    filtered = stage1_out
            else:
                filtered = stage1_out
            N = len(filtered)
            yf = fft(filtered)
            xf = fftfreq(N, 1/fs)[:N//2]
            mag = 2.0/N * np.abs(yf[:N//2])
            
            # 4. Update Time & FFT Plots (Always updated if in Synth mode or if filter changed)
            # we only skip if in Import mode and nothing changed to save CPU.
            if self.sig_gen.mode == "Synth" or filter_changed or self._force_redraw or force:
                self._force_redraw = False
                ax_t = self.cards["time"]["ax"]; ax_t.clear()
                ax_t.plot(raw, color='#555', alpha=0.4, label="Raw")
                ax_t.plot(filtered, color='#00d1ff', label="Filtered")
                
                # Smart Scaling for Sensor Data (like AZ at 9.8m/s^2)
                if self.sig_gen.mode == "Import":
                    data_min = min(np.min(raw), np.min(filtered))
                    data_max = max(np.max(raw), np.max(filtered))
                    padding = max(0.5, (data_max - data_min) * 0.15)
                    ax_t.set_ylim([data_min - padding, data_max + padding])
                else:
                    ax_t.set_ylim([-3.5, 3.5])
                    
                ax_t.set_xlabel("Sample Index n", color='white', fontsize=9)
                ax_t.set_ylabel("Amplitude", color='white', fontsize=9)
                self.cards["time"]["canvas"].draw()
                
                ax_f = self.cards["fft"]["ax"]; ax_f.clear()
                ax_f.fill_between(xf, mag, color='#fc0', alpha=0.3)
                ax_f.plot(xf, mag, color='#fc0')
                ax_f.set_xlim([0, fs/2])
                ax_f.set_xlabel("Frequency [Hz]", color='white', fontsize=9)
                ax_f.set_ylabel("Magnitude", color='white', fontsize=9)
                self.cards["fft"]["canvas"].draw()
            
            # 5. Update Filter Design Plots (ONLY if parameters changed)
            if filter_changed or force:
                w, h = freqz(self.b, self.a, worN=1024, fs=fs)
                z, p, k = tf2zpk(self.b, self.a)
                imp_resp = lfilter(self.b, self.a, np.array([1.0] + [0.0]*119))
                
                # Magnitude Response
                ax_r = self.cards["resp"]["ax"]; ax_r.clear()
                ax_r.plot(w, 20*np.log10(np.maximum(abs(h), 1e-4)), color='#f0f', linewidth=2)
                ax_r.set_ylim([-80, 5]); ax_r.set_xlim([0, fs/2])
                ax_r.set_xlabel("Frequency [Hz]", color='white', fontsize=9)
                ax_r.set_ylabel("Gain [dB]", color='white', fontsize=9)
                self.cards["resp"]["canvas"].draw()
                
                # Impulse Response
                ax_i = self.cards["impulse"]["ax"]; ax_i.clear()
                ax_i.stem(np.arange(120), imp_resp, linefmt='#00ff88', markerfmt='D', basefmt=" ")
                ax_i.set_xlabel("Sample n", color='white', fontsize=9)
                ax_i.set_ylabel("h[n]", color='white', fontsize=9)
                self.cards["impulse"]["canvas"].draw()
                
                # Phase Response
                ax_ph = self.cards["phase"]["ax"]; ax_ph.clear()
                ax_ph.plot(w, np.angle(h), color='#ff4444')
                ax_ph.set_xlim([0, fs/2])
                ax_ph.set_xlabel("Frequency [Hz]", color='white', fontsize=9)
                ax_ph.set_ylabel("Phase [Radians]", color='white', fontsize=9)
                self.cards["phase"]["canvas"].draw()
                
                # Linear Gain
                ax_gl = self.cards["gain_lin"]["ax"]; ax_gl.clear()
                ax_gl.plot(w, np.abs(h), color='#00ff88')
                ax_gl.set_ylim([0, 1.2]); ax_gl.set_xlim([0, fs/2])
                ax_gl.set_xlabel("Frequency [Hz]", color='white', fontsize=9)
                ax_gl.set_ylabel("Gain [Linear]", color='white', fontsize=9)
                self.cards["gain_lin"]["canvas"].draw()
                
                # Pole-Zero Map
                ax_p = self.cards["pz"]["ax"]; ax_p.clear()
                ut = np.linspace(0, 2*np.pi, 100)
                ax_p.plot(np.cos(ut), np.sin(ut), 'w--', alpha=0.3)
                ax_p.scatter(np.real(z), np.imag(z), marker='o', edgecolors='#0f0', facecolors='none')
                ax_p.scatter(np.real(p), np.imag(p), marker='x', color='#f00')
                ax_p.set_aspect('equal')
                ax_p.set_xlabel("Real Part", color='white', fontsize=9)
                ax_p.set_ylabel("Imaginary Part", color='white', fontsize=9)
                self.cards["pz"]["canvas"].draw()
        except Exception as e:
            # Silent catch to prevent hard freeze; user can click Refresh to retry
            pass
            
        # Slower loop (200ms) to reduce CPU/Memory pressure
        self.after(200, self.update_loop)

if __name__ == "__main__":
    app = DSPApp(); app.mainloop()
