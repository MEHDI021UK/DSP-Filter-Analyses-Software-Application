import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.fft import fft, fftfreq
from scipy.signal import (butter, cheby1, cheby2, ellip, iirnotch,
                          firwin, lfilter, filtfilt, tf2zpk, freqz)
import customtkinter as ctk

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
        self.mode = "Synth" # Synth or Import

    def get_signal(self):
        if self.mode == "Import" and self.imported_data is not None:
            return self.imported_data
        
        y = np.zeros_like(self.t)
        for s in self.sines:
            y += s["amp"] * np.sin(2 * np.pi * s["freq"] * self.t + s["phase"])
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
        self.import_triggered = False
        self.high_bw = ctk.BooleanVar(value=False)
        self.show_briefs = ctk.BooleanVar(value=True)
        self.freq_sliders = []
        self.param_sliders = {}
        
        self.setup_ui()
        self.update_loop()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkScrollableFrame(self, width=350)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="DSP Controls", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

        # System Sampling Rate (Fs) - Real-time control
        self.fs_frame = self.create_group("System Spectrum Range", [
            ("Sampling Fs", 100, 2000, 2000, lambda v: setattr(self.sig_gen, 'fs', int(float(v))))
        ])
        self.fs_slider = self.freq_sliders[-1] 

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

        # Synth Group
        self.synth_group = self.create_group("Signal Synthesizer", [
            ("Sine 1 Freq", 0, 1000, 10, lambda v: self.set_sine(0, "freq", v)),
            ("Sine 1 Amp", 0, 2, 1.0, lambda v: self.set_sine(0, "amp", v)),
            ("Sine 2 Freq", 0, 1000, 500, lambda v: self.set_sine(1, "freq", v)),
            ("Sine 2 Amp", 0, 2, 0.5, lambda v: self.set_sine(1, "amp", v)),
            ("Noise Level", 0, 1, 0.05, lambda v: setattr(self.sig_gen, 'noise_lvl', float(v)))
        ])

        # Import Group
        self.import_group = ctk.CTkFrame(self.sidebar)
        ctk.CTkLabel(self.import_group, text="Data Import", font=ctk.CTkFont(weight="bold")).pack(pady=5)
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
                                           variable=self.filter_resp, command=self.update_ui_visibility)
        self.resp_menu.pack(pady=5)

        ctk.CTkLabel(self.f_frame, text="Filter Class").pack()
        self.class_menu = ctk.CTkOptionMenu(self.f_frame, values=["IIR", "FIR", "Adaptive (LMS)", "Lattice"], 
                                            variable=self.filter_class, command=self.update_proto_options)
        self.class_menu.pack(pady=5)

        ctk.CTkLabel(self.f_frame, text="Design Method / Prototype").pack()
        self.proto_menu = ctk.CTkOptionMenu(self.f_frame, values=[], variable=self.filter_proto, command=self.update_ui_visibility)
        self.proto_menu.pack(pady=5)
        
        self.param_group = self.create_param_group("Filter Parameters", [
            ("Order", 1, 12, 4, lambda v: setattr(self, 'order', int(float(v)))),
            ("Cutoff 1 (Low/Center)", 1, 1000, 300, lambda v: setattr(self, 'cutoff_1', float(v))),
            ("Cutoff 2 (High)", 1, 1000, 800, lambda v: setattr(self, 'cutoff_2', float(v))),
            ("Passband Ripple (dB)", 0.1, 10, 1, lambda v: setattr(self, 'ripple', float(v))),
            ("Stopband Atten (dB)", 10, 80, 40, lambda v: setattr(self, 'atten', float(v))),
            ("Kaiser Beta", 0.1, 15, 5, lambda v: setattr(self, 'beta', float(v))),
            ("Notch Quality (Q)", 1, 100, 30, lambda v: setattr(self, 'notch_q', float(v)))
        ])

        # Analyze Button
        self.calc_btn = ctk.CTkButton(self.sidebar, text="Calculate & Analyze", 
                                      fg_color="#28a745", hover_color="#218838",
                                      command=self.show_report)
        self.calc_btn.pack(pady=10, padx=10, fill="x")

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
            self.import_group.pack_forget(); self.fs_frame.pack(fill="x", pady=5, padx=5, before=self.source_segmented)
            self.synth_group.pack(fill="x", pady=5, padx=5, after=self.source_segmented)
            self.f_frame.pack(fill="x", pady=10, padx=5); self.param_group.pack(fill="x", pady=5, padx=5)
            self.calc_btn.pack(pady=10, padx=10, fill="x"); self.update_ui_visibility()
        else:
            self.synth_group.pack_forget(); self.f_frame.pack_forget(); self.param_group.pack_forget()
            self.calc_btn.pack_forget(); self.import_group.pack(fill="x", pady=5, padx=5, after=self.source_segmented)
            if self.sig_gen.imported_data is None: self.fs_frame.pack_forget()
            else: self.fs_frame.pack(fill="x", pady=5, padx=5, before=self.source_segmented)

    def trigger_import_run(self):
        self.import_triggered = True; self.f_frame.pack(fill="x", pady=10, padx=5)
        self.param_group.pack(fill="x", pady=5, padx=5); self.calc_btn.pack(pady=10, padx=10, fill="x"); self.update_ui_visibility()

    def load_file(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt *.csv")])
        if path:
            try:
                data = np.loadtxt(path, delimiter=",")
                if data.ndim > 1: data = data[:, 0]
                self.sig_gen.imported_data = data
                self.file_label.configure(text=f"Loaded: {path.split('/')[-1]}", text_color="#00ff00")
                self.fs_frame.pack(fill="x", pady=5, padx=5, before=self.source_segmented)
                self.import_run_btn.pack(pady=10, padx=10)
            except Exception as e: self.file_label.configure(text=f"Error: {e}", text_color="#ff4444")

    def update_ui_visibility(self, *args):
        resp = self.filter_resp.get(); proto = self.filter_proto.get(); f_class = self.filter_class.get()
        
        # 1. First, hide everything to start fresh
        for key in self.param_sliders:
            self.param_sliders[key].pack_forget()
            
        # 2. If 'None' is selected, don't show any parameters
        if resp == "None":
            return
            
        # 3. Deterministic packing order for visibility
        # Order and Cutoff 1 are always visible for any active filter
        self.param_sliders["Order"].pack(fill="x", pady=2)
        self.param_sliders["Cutoff 1 (Low/Center)"].pack(fill="x", pady=2)
        
        # Conditionals
        if resp in ["Band-Pass", "Band-Stop"]:
            self.param_sliders["Cutoff 2 (High)"].pack(fill="x", pady=2)
            
        if f_class == "IIR":
            if proto in ["Chebyshev I", "Elliptic"]:
                self.param_sliders["Passband Ripple (dB)"].pack(fill="x", pady=2)
            if proto in ["Chebyshev II", "Elliptic"]:
                self.param_sliders["Stopband Atten (dB)"].pack(fill="x", pady=2)
        
        if resp == "Notch":
            self.param_sliders["Notch Quality (Q)"].pack(fill="x", pady=2)
            
        if f_class == "FIR" and proto == "Kaiser":
            self.param_sliders["Kaiser Beta"].pack(fill="x", pady=2)

    def set_sine(self, idx, key, val): self.sig_gen.sines[idx][key] = float(val)

    def update_proto_options(self, choice):
        if choice == "IIR": opts = ["Butterworth", "Chebyshev I", "Chebyshev II", "Elliptic"]
        elif choice == "FIR": opts = ["Hamming", "Hanning", "Blackman", "Rectangular", "Kaiser"]
        elif choice == "Adaptive (LMS)": opts = ["Standard LMS", "Normalized LMS"]
        else: opts = ["Grey-Markel", "All-Pass Lattice"]
        self.proto_menu.configure(values=opts); self.filter_proto.set(opts[0]); self.update_ui_visibility()

    def get_filter(self, fs):
        res = self.filter_resp.get(); f_class = self.filter_class.get(); proto = self.filter_proto.get(); nyq = fs / 2
        if res == "None": return np.array([1.0]), np.array([1.0])
        c1 = np.clip(self.cutoff_1, 0.1, nyq - 1); c2 = np.clip(self.cutoff_2, c1 + 0.1, nyq - 1)
        btype = 'low'
        if res == "High-Pass": btype = 'high'
        elif res == "Band-Pass": btype = 'bandpass'
        elif res == "Band-Stop": btype = 'bandstop'
        Wn = c1/nyq if res in ["Low-Pass", "High-Pass", "Notch"] else [c1/nyq, c2/nyq]
        if res == "Notch": return iirnotch(c1/nyq, self.notch_q)
        try:
            if f_class == "IIR":
                if proto == "Butterworth": return butter(self.order, Wn, btype=btype)
                elif proto == "Chebyshev I": return cheby1(self.order, self.ripple, Wn, btype=btype)
                elif proto == "Chebyshev II": return cheby2(self.order, self.atten, Wn, btype=btype)
                elif proto == "Elliptic": return ellip(self.order, self.ripple, self.atten, Wn, btype=btype)
            else:
                numtaps = self.order * 8 + 1; win = proto.lower()
                if win == "kaiser": win = ('kaiser', self.beta)
                elif win == "rectangular": win = "boxcar"
                b = firwin(numtaps, Wn, pass_zero=(btype in ['low', 'bandstop']), window=win)
                return b, np.array([1.0])
        except: return np.array([1.0]), np.array([1.0])

    def show_report(self):
        fs = self.sig_gen.fs; b, a = self.get_filter(fs); z, p, k = tf2zpk(b, a)
        ftype = self.filter_resp.get(); fclass = self.filter_class.get()
        rw = ctk.CTkToplevel(self); rw.title(f"DSP Report: {fclass} {ftype}")
        rw.geometry("1000x950"); rw.attributes("-topmost", True)
        
        txt = ctk.CTkTextbox(rw, font=ctk.CTkFont(family="Consolas", size=13))
        txt.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. Header & Metadata
        rep = "/*" + "="*75 + "\n"
        rep += " * INDUSTRIAL DSP EXPORT - ARCHITECT REPORT\n"
        rep += f" * Target: {fclass} {ftype} Filter\n"
        rep += " " + "="*75 + "*/\n\n"
        rep += f"#define FS_HZ           {fs}\n"
        rep += f"#define FILTER_ORDER     {len(b)-1}\n"
        rep += f"#define FILTER_TYPE      \"{ftype}\"\n"
        rep += f"#define DESIGN_METHOD    \"{self.filter_proto.get()}\"\n\n"
        
        # 2. Mathematical Transfer Function H(z)
        rep += "/* --- MATHEMATICAL TRANSFER FUNCTION H(z) ---\n"
        def fmt_z(coeffs):
            terms = []
            for i, c in enumerate(coeffs):
                if abs(c) < 1e-10: continue
                sign = "+ " if c >= 0 and i > 0 else ("- " if i > 0 else "")
                val = abs(c) if i > 0 else c
                if i == 0: terms.append(f"{val:.6f}")
                else: terms.append(f"{sign}{val:.6f}z^-{i}")
            return " ".join(terms)
        
        num = fmt_z(b); den = fmt_z(a)
        w = max(len(num), len(den))
        rep += f"      {num.center(w)}\nH(z) = {'-' * (w + 6)}\n      {den.center(w)}\n*/\n\n"
        
        # 3. Stability Summary
        stable = np.all(np.abs(p) < 1.0)
        rep += "// --- STABILITY ANALYSIS ---\n"
        rep += f"// Status: {'[OK] STABLE' if stable else '[!!] UNSTABLE - CHECK DESIGN'}\n"
        rep += f"// Max Pole Radius: {np.max(np.abs(p)) if len(p)>0 else 0:.6f}\n\n"
        
        # 4. Coefficients (Fixed Point)
        rep += "// --- FIXED POINT COEFFICIENTS ---\n"
        rep += "// Q1.15 Format (Scaled by 32767)\n"
        bq15 = np.round(b * 32767).astype(int); aq15 = np.round(a * 32767).astype(int)
        rep += f"static const int16_t B_Q15[] = {{{', '.join(map(str, bq15))}}};\n"
        rep += f"static const int16_t A_Q15[] = {{{', '.join(map(str, aq15))}}};\n\n"
        
        # 5. Tailored C-Code Function
        func_name = f"{ftype.replace('-','')}_{fclass}_Process"
        rep += f"/* --- OPTIMIZED C IMPLEMENTATION: {fclass} {ftype} ---\n"
        rep += " * Structure: Direct Form II (Memory efficient)\n"
        rep += " */\n"
        rep += f"float {func_name}(float in_sample) {{\n"
        if fclass == "IIR":
            rep += f"    static float w[FILTER_ORDER + 1] = {{0.0f}};\n"
            rep += "    float out_sample = 0.0f;\n\n"
            rep += "    // Feedback (A coefficients)\n"
            rep += "    float wn = in_sample;\n"
            for i in range(1, len(a)):
                rep += f"    wn -= ({a[i]:.12f}f * w[{i}]);\n"
            rep += f"    w[0] = wn;\n\n"
            rep += "    // Feedforward (B coefficients)\n"
            for i in range(len(b)):
                rep += f"    out_sample += ({b[i]:.12f}f * w[{i}]);\n"
            rep += "\n    // Shift delay line\n"
            rep += f"    for(int i = FILTER_ORDER; i > 0; i--) w[i] = w[i-1];\n\n"
        else: # FIR
            rep += f"    static float x[FILTER_ORDER + 1] = {{0.0f}};\n"
            rep += "    float out_sample = 0.0f;\n\n"
            rep += "    x[0] = in_sample;\n"
            rep += "    for(int i = 0; i <= FILTER_ORDER; i++) {\n"
            rep += "        out_sample += B_COEFS[i] * x[i];\n"
            rep += "    }\n"
            rep += "    for(int i = FILTER_ORDER; i > 0; i--) x[i] = x[i-1];\n"
            
        rep += "    return out_sample;\n"
        rep += "}\n\n"
        
        txt.insert("1.0", rep); txt.configure(state="disabled")

    def update_loop(self):
        if self.sig_gen.mode == "Import" and not self.import_triggered: self.after(200, self.update_loop); return
        fs = int(self.fs_slider.get())
        self.sig_gen.fs = fs
        if self.sig_gen.mode == "Synth": self.sig_gen.t = np.arange(0, self.sig_gen.duration, 1/fs)
        raw = self.sig_gen.get_signal(); b, a = self.get_filter(fs)
        filtered = filtfilt(b, a, raw) if len(a) > 1 or len(b) > 1 else raw
        N = len(filtered); yf = fft(filtered); xf = fftfreq(N, 1/fs)[:N//2]; mag = 2.0/N * np.abs(yf[:N//2])
        w, h = freqz(b, a, worN=1024, fs=fs); z, p, k = tf2zpk(b, a)
        imp_resp = lfilter(b, a, np.array([1.0] + [0.0]*119))
        
        ax_t = self.cards["time"]["ax"]; ax_t.clear(); ax_t.plot(raw, color='#555', alpha=0.4); ax_t.plot(filtered, color='#00d1ff'); ax_t.set_ylim([-3.5,3.5]); self.cards["time"]["canvas"].draw()
        
        ax_f = self.cards["fft"]["ax"]; ax_f.clear(); ax_f.fill_between(xf, mag, color='#fc0', alpha=0.3); ax_f.plot(xf, mag, color='#fc0')
        ax_f.set_xlim([0, fs/2]); self.cards["fft"]["canvas"].draw()
        
        ax_r = self.cards["resp"]["ax"]; ax_r.clear(); ax_r.plot(w, 20*np.log10(np.maximum(abs(h), 1e-4)), color='#f0f', linewidth=2)
        ax_r.set_ylim([-80, 5]); ax_r.set_xlim([0, fs/2]); self.cards["resp"]["canvas"].draw()
        
        ax_i = self.cards["impulse"]["ax"]; ax_i.clear(); ax_i.stem(np.arange(120), imp_resp, linefmt='#00ff88', markerfmt='D', basefmt=" "); self.cards["impulse"]["canvas"].draw()
        
        ax_ph = self.cards["phase"]["ax"]; ax_ph.clear(); ax_ph.plot(w, np.angle(h), color='#ff4444')
        ax_ph.set_xlim([0, fs/2]); self.cards["phase"]["canvas"].draw()
        
        ax_gl = self.cards["gain_lin"]["ax"]; ax_gl.clear(); ax_gl.plot(w, np.abs(h), color='#00ff88')
        ax_gl.set_ylim([0, 1.2]); ax_gl.set_xlim([0, fs/2]); self.cards["gain_lin"]["canvas"].draw()
        
        ax_p = self.cards["pz"]["ax"]; ax_p.clear(); ut=np.linspace(0,2*np.pi,100); ax_p.plot(np.cos(ut),np.sin(ut),'w--',alpha=0.3)
        ax_p.scatter(np.real(z),np.imag(z),marker='o',edgecolors='#0f0',facecolors='none'); ax_p.scatter(np.real(p),np.imag(p),marker='x',color='#f00')
        ax_p.set_aspect('equal'); self.cards["pz"]["canvas"].draw()
        
        self.after(100, self.update_loop)

if __name__ == "__main__":
    app = DSPApp(); app.mainloop()
