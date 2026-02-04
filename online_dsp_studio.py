import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import (butter, cheby1, cheby2, ellip, bessel, iirfilter,
                          firwin, lfilter, filtfilt, tf2zpk, freqz, impulse, dlti, chirp)
from scipy.fft import fft, fftfreq
import pandas as pd
import io
import complex_filters as cf

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Advanced DSP Studio Pro", layout="wide", initial_sidebar_state="expanded")

def apply_custom_style():
    st.markdown("""
        <style>
        .main {
            background-color: #0e1117;
            color: #ffffff;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #00d1ff;
            color: black;
            font-weight: bold;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #00b8e6;
            box-shadow: 0px 0px 15px #00d1ff;
        }
        .reportview-container .main .block-container {
            padding-top: 2rem;
        }
        h1, h2, h3 {
            color: #00d1ff !important;
            font-family: 'Inter', sans-serif;
        }
        .sidebar .sidebar-content {
            background-image: linear-gradient(#2e3131, #1e1e1e);
        }
        div[data-testid="stMetricValue"] {
            color: #00d1ff;
        }
        .plot-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- CORE MATH LOGIC ---

class SignalGenerator:
    def __init__(self, fs=2000, duration=0.5):
        self.fs = fs
        self.duration = duration
        self.t = np.arange(0, duration, 1/fs)
        self.waveform = "Sines"
        self.noise_lvl = 0.05
        self.sines = [{"freq": 10, "amp": 1.0}, {"freq": 500, "amp": 0.5}]
        self.sweep_start = 10.0
        self.sweep_end = 800.0
        self.sweep_amp = 1.0
        self.base_signal = None
        self.imported_data = None

    def get_signal(self):
        if self.imported_data is not None:
            return self.imported_data
        
        y = np.zeros_like(self.t)
        if self.waveform == "Sines":
            for s in self.sines:
                y += s["amp"] * np.sin(2 * np.pi * s["freq"] * self.t)
        elif self.waveform == "Impulse":
            y[len(y)//4] = 1.0
        elif self.waveform == "Step":
            y[len(y)//4:] = 1.0
        elif self.waveform == "Sweep":
            y = self.sweep_amp * chirp(self.t, f0=self.sweep_start, 
                                      f1=self.sweep_end, 
                                      t1=self.duration, method='linear')
        self.base_signal = y
        return y + self.noise_lvl * np.random.normal(size=len(self.t))

# --- APP INITIALIZATION ---
if 'sig_gen' not in st.session_state:
    st.session_state.sig_gen = SignalGenerator()

sig_gen = st.session_state.sig_gen

# --- SIDEBAR: SIGNAL GENERATOR ---
with st.sidebar:
    st.title("DSP Studio Pro")
    st.markdown("---")
    
    st.header("Signal Control")
    source = st.radio("Signal Source", ["Synthesizer", "CSV Import"])
    
    if source == "Synthesizer":
        wf = st.selectbox("Waveform", ["Sines", "Impulse", "Step", "Sweep"])
        sig_gen.waveform = wf
        sig_gen.noise_lvl = st.slider("Noise Intensity", 0.0, 1.0, 0.05)
        
        if wf == "Sines":
            sig_gen.sines[0]["freq"] = st.slider("Sine 1 Frequency (Hz)", 1, 1000, 10)
            sig_gen.sines[0]["amp"] = st.slider("Sine 1 Amplitude", 0.1, 2.0, 1.0)
            sig_gen.sines[1]["freq"] = st.slider("Sine 2 Frequency (Hz)", 1, 1000, 500)
            sig_gen.sines[1]["amp"] = st.slider("Sine 2 Amplitude", 0.1, 2.0, 0.5)
        elif wf == "Sweep":
            sig_gen.sweep_start = st.slider("Start Frequency (Hz)", 1, 500, 10)
            sig_gen.sweep_end = st.slider("Stop Frequency (Hz)", 500, 2000, 800)
            sig_gen.sweep_amp = st.slider("Sweep Amplitude", 0.1, 2.0, 1.0)
    else:
        uploaded_file = st.file_uploader("Upload Sensor Trace (CSV)", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file, skiprows=1, header=None)
            axis = st.selectbox("Select Axis", ["AX", "AY", "AZ", "GX", "GY", "GZ"])
            axis_map = {"AX": 1, "AY": 2, "AZ": 3, "GX": 4, "GY": 5, "GZ": 6}
            sig_gen.imported_data = df.iloc[:, axis_map[axis]].values
            st.success(f"Channel {axis} Loaded: {len(sig_gen.imported_data)} samples")

    st.markdown("---")
    st.header("Filter Settings")
    fs = st.number_input("System Fs (Hz)", value=2000, min_value=1)
    sig_gen.fs = fs
    
    f_class = st.selectbox("Filter Class", ["IIR (Recursive)", "FIR (Window)"])
    f_type = st.selectbox("Response Type", ["Low-Pass", "High-Pass", "Band-Pass", "Band-Stop"])
    
    if f_class == "IIR (Recursive)":
        prototype = st.selectbox("Prototype", ["Butterworth", "Chebyshev I", "Chebyshev II", "Elliptic", "Bessel"])
        order = st.slider("Filter Order", 1, 12, 4)
    else:
        prototype = st.selectbox("Window Function", ["Hamming", "Hann", "Blackman", "Kaiser"])
        order = st.slider("Num Taps", 4, 128, 31)

    if f_type in ["Low-Pass", "High-Pass"]:
        fc1 = st.slider("Cutoff Freq (Hz)", 1.0, fs/2 - 1, fs/4)
        pass_freqs = fc1
    else:
        fc1 = st.slider("Low Cutoff (Hz)", 1.0, fs/2 - 10, fs/10)
        fc2 = st.slider("High Cutoff (Hz)", fc1 + 10, fs/2 - 1, fs/3)
        pass_freqs = [fc1, fc2]

    st.markdown("---")
    st.header("Refinement Layer")
    complex_mode = st.selectbox("Aux Filter", ["None", "Kalman", "Savitzky-Golay", "Median", "Wavelet"])

# --- MAIN ENGINE ---

# Generate Filter
nyq = 0.5 * fs
b, a = [1.0], [1.0]
sos = None

try:
    if f_class == "IIR (Recursive)":
        btype = f_type.lower().replace("-", "")
        if prototype == "Butterworth":
            b, a = butter(order, pass_freqs, btype=btype, fs=fs)
            sos = butter(order, pass_freqs, btype=btype, fs=fs, output='sos')
        elif prototype == "Chebyshev I":
            b, a = cheby1(order, 0.5, pass_freqs, btype=btype, fs=fs)
            sos = cheby1(order, 0.5, pass_freqs, btype=btype, fs=fs, output='sos')
        elif prototype == "Chebyshev II":
            b, a = cheby2(order, 40, pass_freqs, btype=btype, fs=fs)
            sos = cheby2(order, 40, pass_freqs, btype=btype, fs=fs, output='sos')
        elif prototype == "Elliptic":
            b, a = ellip(order, 0.5, 40, pass_freqs, btype=btype, fs=fs)
            sos = ellip(order, 0.5, 40, pass_freqs, btype=btype, fs=fs, output='sos')
        elif prototype == "Bessel":
            b, a = bessel(order, pass_freqs, btype=btype, fs=fs)
            sos = bessel(order, pass_freqs, btype=btype, fs=fs, output='sos')
    else:
        f_win = prototype.lower()
        if f_type == "Low-Pass":
            b = firwin(order, fc1, window=f_win, fs=fs)
        elif f_type == "High-Pass":
            b = firwin(order + (1 if order % 2 == 0 else 0), fc1, window=f_win, fs=fs, pass_zero=False)
        elif f_type == "Band-Pass":
            b = firwin(order, [fc1, fc2], window=f_win, fs=fs, pass_zero=False)
        elif f_type == "Band-Stop":
            b = firwin(order, [fc1, fc2], window=f_win, fs=fs, pass_zero=True)
        a = [1.0]
except Exception as e:
    st.error(f"Design Error: {e}")

# Process Signal
raw_sig = sig_gen.get_signal()
if f_class == "IIR (Recursive)" and sos is not None:
    # Use SOS for better numerical stability in real applications
    from scipy.signal import sosfiltfilt
    filtered = sosfiltfilt(sos, raw_sig)
else:
    filtered = filtfilt(b, a, raw_sig)

# Complex Refinement
if complex_mode == "Kalman":
    filtered = cf.apply_kalman_filter(filtered)
elif complex_mode == "Savitzky-Golay":
    filtered = cf.apply_savgol_filter(filtered)
elif complex_mode == "Median":
    filtered = cf.apply_median_filter(filtered)
elif complex_mode == "Wavelet":
    filtered = cf.apply_wavelet_denoising(filtered)

# --- VISUALIZATION TABS ---
st.title("Signal Analytics")

tab1, tab2, tab3, tab4 = st.tabs(["Time & Frequency", "Filter Bode", "Z-Plane & Stability", "C-Code Architect"])

with tab1:
    st.subheader("Oscilloscope")
    fig, ax = plt.subplots(figsize=(14, 5), facecolor='#0e1117')
    ax.set_facecolor('#1e1e1e')
    ax.plot(raw_sig, color='grey', alpha=0.4, label="Raw")
    ax.plot(filtered, color='#00d1ff', linewidth=2, label="Filtered")
    ax.set_xlabel("Samples")
    ax.set_ylabel("Amplitude")
    ax.grid(True, color='grey', alpha=0.2)
    ax.legend()
    ax.tick_params(colors='white')
    st.pyplot(fig)

    st.subheader("FFT Spectrum")
    N = len(filtered)
    yf = fft(filtered)
    xf = fftfreq(N, 1/fs)[:N//2]
    mag = 2.0/N * np.abs(yf[:N//2])
    fig_f, ax_f = plt.subplots(figsize=(14, 5), facecolor='#0e1117')
    ax_f.set_facecolor('#1e1e1e')
    ax_f.fill_between(xf, mag, color='#00ff88', alpha=0.3)
    ax_f.plot(xf, mag, color='#00ff88', linewidth=1.5)
    ax_f.set_xlabel("Frequency (Hz)")
    ax_f.set_ylabel("Magnitude")
    ax_f.grid(True, color='grey', alpha=0.2)
    ax_f.tick_params(colors='white')
    st.pyplot(fig_f)

with tab2:
    w, h = freqz(b, a, worN=2000, fs=fs)
    
    st.subheader("Magnitude Response (dB)")
    fig_m, ax_m = plt.subplots(figsize=(14, 5), facecolor='#0e1117')
    ax_m.set_facecolor('#1e1e1e')
    ax_m.plot(w, 20 * np.log10(np.maximum(np.abs(h), 1e-5)), color='#ffcc00')
    ax_m.set_xlabel("Frequency (Hz)")
    ax_m.set_ylabel("Gain (dB)")
    ax_m.set_ylim([-80, 5])
    ax_m.grid(True, color='grey', alpha=0.2)
    ax_m.tick_params(colors='white')
    st.pyplot(fig_m)
        
    st.subheader("Phase Response")
    fig_p, ax_p = plt.subplots(figsize=(14, 5), facecolor='#0e1117')
    ax_p.set_facecolor('#1e1e1e')
    ax_p.plot(w, np.angle(h), color='#ff00ff')
    ax_p.set_xlabel("Frequency (Hz)")
    ax_p.set_ylabel("Phase (radians)")
    ax_p.grid(True, color='grey', alpha=0.2)
    ax_p.tick_params(colors='white')
    st.pyplot(fig_p)

with tab3:
    st.subheader("Z-Plane Poles/Zeros")
    z, p, k = tf2zpk(b, a)
    fig_z, ax_z = plt.subplots(figsize=(8, 8), facecolor='#0e1117')
    ax_z.set_facecolor('#1e1e1e')
    unit_circle = plt.Circle((0,0), 1, color='white', fill=False, linestyle='--')
    ax_z.add_artist(unit_circle)
    ax_z.scatter(np.real(z), np.imag(z), s=60, marker='o', edgecolors='#00ff88', facecolors='none', label='Zeros')
    ax_z.scatter(np.real(p), np.imag(p), s=60, marker='x', color='#ff4444', label='Poles')
    ax_z.set_xlim([-1.5, 1.5])
    ax_z.set_ylim([-1.5, 1.5])
    ax_z.axhline(0, color='white', alpha=0.3)
    ax_z.axvline(0, color='white', alpha=0.3)
    ax_z.set_aspect('equal')
    ax_z.legend()
    ax_z.tick_params(colors='white')
    st.pyplot(fig_z)
        
    st.subheader("Impulse Response")
    # Calc impulse response for 100 samples
    t_imp = np.arange(100)
    imp = np.zeros(100)
    imp[0] = 1.0
    h_imp = lfilter(b, a, imp)
    fig_i, ax_i = plt.subplots(figsize=(14, 5), facecolor='#0e1117')
    ax_i.set_facecolor('#1e1e1e')
    markerline, stemlines, baseline = ax_i.stem(t_imp, h_imp, markerfmt='o', basefmt='grey')
    plt.setp(markerline, color='#00d1ff')
    plt.setp(stemlines, color='#00d1ff')
    ax_i.set_xlabel("Samples")
    ax_i.set_ylabel("Amplitude")
    ax_i.grid(True, color='grey', alpha=0.2)
    ax_i.tick_params(colors='white')
    st.pyplot(fig_i)

with tab4:
    st.subheader("Embedded C-Code Generation")
    
    c_col1, c_col2 = st.columns([1, 2])
    
    with c_col1:
        data_type = st.selectbox("Precision", ["float32_t", "q15_t (Fixed)", "q31_t (Fixed)"])
        style = st.selectbox("Format", ["Standard C", "ARM CMSIS-DSP"])
        use_sos = st.checkbox("Use SOS (Biquads)", value=True) if f_class == "IIR (Recursive)" else False

    # Generate the code
    code_buffer = io.StringIO()
    code_buffer.write(f"/*\n * DSP Studio Pro Auto-Generated Filter\n")
    code_buffer.write(f" * Type: {f_class} {prototype} {f_type}\n")
    code_buffer.write(f" * Order: {order} | Fs: {fs}Hz\n")
    code_buffer.write(f" */\n\n#include <stdint.h>\n\n")
    
    if f_class == "IIR (Recursive)":
        if use_sos and sos is not None:
            code_buffer.write(f"#define NUM_STAGES {len(sos)}\n")
            code_buffer.write(f"float32_t coeffs[{len(sos)*5}] = {{\n")
            for section in sos:
                # SOS format in scipy: [b0, b1, b2, a0, a1, a2] -> a0 is usually 1.0
                c = [section[0], section[1], section[2], -section[4], -section[5]]
                code_buffer.write(f"    {', '.join([f'{x:.8f}f' for x in c])},\n")
            code_buffer.write("};\n\n")
            code_buffer.write("float32_t state[NUM_STAGES * 2] = {0};\n\n")
            code_buffer.write("// Process function using Biquad Direct Form II Transposed\n")
            code_buffer.write("float32_t Filter_Process(float32_t in) {\n")
            code_buffer.write("    float32_t x = in;\n")
            code_buffer.write("    for(int i=0; i<NUM_STAGES; i++) {\n")
            code_buffer.write("        float32_t *c = &coeffs[i*5];\n")
            code_buffer.write("        float32_t *s = &state[i*2];\n")
            code_buffer.write("        float32_t y = c[0]*x + s[0];\n")
            code_buffer.write("        s[0] = c[1]*x - c[3]*y + s[1];\n")
            code_buffer.write("        s[1] = c[2]*x - c[4]*y;\n")
            code_buffer.write("        x = y;\n")
            code_buffer.write("    }\n")
            code_buffer.write("    return x;\n}")
        else:
            code_buffer.write(f"#define ORDER {len(a)-1}\n")
            code_buffer.write(f"static const float B_COEFFS[] = {{{', '.join([f'{x:.8f}f' for x in b])}}};\n")
            code_buffer.write(f"static const float A_COEFFS[] = {{{', '.join([f'{x:.8f}f' for x in a])}}};\n")
            code_buffer.write(f"static float w[{len(a)}] = {{0}};\n\n")
            code_buffer.write("float Filter_Process(float in) {\n")
            code_buffer.write("    float wn = in;\n")
            code_buffer.write("    for(int i=1; i<=ORDER; i++) wn -= A_COEFFS[i] * w[i];\n")
            code_buffer.write("    float out = B_COEFFS[0] * wn;\n")
            code_buffer.write("    for(int i=1; i<=ORDER; i++) out += B_COEFFS[i] * w[i];\n")
            code_buffer.write("    for(int i=ORDER; i>1; i--) w[i] = w[i-1];\n")
            code_buffer.write("    w[1] = wn;\n")
            code_buffer.write("    return out;\n}")
    else:
        code_buffer.write(f"#define NUM_TAPS {len(b)}\n")
        code_buffer.write(f"static const float TAPS[] = {{{', '.join([f'{x:.8f}f' for x in b])}}};\n")
        code_buffer.write(f"static float delay_chain[{len(b)}] = {{0}};\n\n")
        code_buffer.write("float Filter_Process(float in) {\n")
        code_buffer.write("    float out = 0;\n")
        code_buffer.write("    delay_chain[0] = in;\n")
        code_buffer.write("    for(int i=0; i<NUM_TAPS; i++) out += TAPS[i] * delay_chain[i];\n")
        code_buffer.write("    for(int i=NUM_TAPS-1; i>0; i--) delay_chain[i] = delay_chain[i-1];\n")
        code_buffer.write("    return out;\n}")

    st.code(code_buffer.getvalue(), language='c')
    st.download_button("Download C Header", code_buffer.getvalue(), file_name="dsp_filter.h")

# --- FOOTER ---
st.markdown("---")
st.markdown("Designed with passion by **Mehdi Sehati** | [GitHub](https://github.com/mehdisehati) | [LinkedIn](https://www.linkedin.com/in/mehdi-sehati-44356bb1/)")

