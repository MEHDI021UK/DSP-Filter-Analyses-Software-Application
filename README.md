Advanced DSP Studio Pro software

**Date:** 2026-01-20 Advanced DSP Studio Pro - v1.0 
**Topics:** Filter types, FIR/IIR design, sensor recommendations, stability, Z-transform, resources.

**Date:** 2026-02-04 
Release Notes: Advanced DSP Studio Pro - v2.0 (Industrial Edition)
The Advanced DSP Studio Pro has been upgraded to a high-performance industrial tool designed for real-world sensor fusion, motion analysis, and embedded systems development. This version introduces a breakthrough Dual-Stage Filtering Engine and native support for high-precision accelerometer and gyroscope data.


# Digital Signal Processing (DSP) & Filters — Tutorials
---
- ## Table of contents
- [Quick reference — Tables](#quick-reference--tables)
	- [Sensor filter recommendations](#sensor-filter-recommendations)
	- [Other filter types (beyond basic LPF/HPF/BP/BS + FIR/IIR)](#other-filter-types-beyond-basic-lpfhpfbpbs--firiir)
- [1. Filter Types Overview](#1-filter-types-overview)
- [2. Sensor Filter Recommendations](#2-sensor-filter-recommendations)
- [3. Other Filter Types (Beyond LPF/HPF/BP/BS + FIR/IIR)](#3-other-filter-types-beyond-lpfhpfbpbs--firiir)
- [4. FIR — Finite Impulse Response](#4-fir--finite-impulse-response)
- [5. IIR — Infinite Impulse Response](#5-iir--infinite-impulse-response)
- [6. Filter Selection by Application](#6-filter-selection-by-application)
- [7. Three Practical Filter Examples](#7-three-practical-filter-examples)
- [8. Stability & Risk Analysis](#8-stability--risk-analysis)
- [9. Practical Visualization](#9-practical-visualization)
- [10. DSP Concepts (Plain Language)](#10-dsp-concepts-plain-language)
- [11. Cutoff Frequency & Nyquist](#11-cutoff-frequency--nyquist)
- [12. Resources & References](#12-resources--references)
- [13. Embedded C filter code (LPF, HPF, EMA, IIR, FIR)](#13-embedded-c-filter-code-lpf-hpf-ema-iir-fir)
  
  ---
- ## Quick reference — Tables
- ### Sensor filter recommendations
  
  | Sensor Type | Typical Noise / Problem | Recommended Filter | Architecture | Cutoff / Parameters | Why |
  |-------------|--------------------------|--------------------|--------------|---------------------|-----|
  | Accelerometer | High-freq vibration, motor/electrical noise | LPF | IIR Butterworth 2–4 | 10–30 Hz | Keeps motion, removes noise |
  | Gyroscope | Drift, high-freq noise | LPF + HPF | IIR 2–3 | LPF: 20–50 Hz, HPF: 0.01–0.5 Hz | Noise + drift correction |
  | Magnetometer | Magnetic interference, spikes | LPF + Median | IIR or FIR | 5–15 Hz | Smooths jitter, removes spikes |
  | IMU (Accel+Gyro+Mag) | Drift + noise all axes | Complementary or Kalman | Fusion algorithm | — | Best for orientation |
  | Microphone / Audio | Background noise, 50/60 Hz hum | LPF + Notch | FIR or IIR | LPF: 8–20 kHz, Notch: 50/60 Hz | Voice/music quality |
  | PPG (Heart Rate) | Motion artifact, light noise | Band-Pass | IIR 2–4 | 0.5–5 Hz | Keeps heart rate band |
  | ECG | Mains hum, muscle noise, baseline wander | Band-Pass + Notch | FIR preferred or IIR | 0.5–40 Hz, Notch: 50/60 Hz | Preserves QRS shape (phase) |
  | Temperature | Slow thermal noise, spikes | LPF + Moving Average | IIR or FIR | 0.1–1 Hz | Temperature is slow |
  | Barometer / Pressure | High-freq from movement | LPF | IIR order 2 | 1–5 Hz | Pressure is slow-varying |
  | GPS | Multipath, jumps | LPF or Kalman | — | 0.1–1 Hz | Smooths position |
  | Camera / Image | Salt & pepper, Gaussian noise | Median + Gaussian | Spatial FIR | — | Reduces pixel noise |
  | Force / Strain Gauge | Electrical noise, vibration | LPF | IIR 2–3 | 10–50 Hz | Keeps slow force changes |
- ### Other filter types (beyond basic LPF/HPF/BP/BS + FIR/IIR)
  
  | Filter | Type | Main Use | Advantage | Typical Application |
  |--------|------|----------|-----------|----------------------|
  | Kalman | Optimal estimation | Sensor fusion | Best accuracy, noise + uncertainty | Drones, phones, robots |
  | EKF | Non-linear Kalman | Non-linear sensors | Works with non-linear systems | Orientation |
  | UKF | Non-linear Kalman | Strong non-linearities | More accurate than EKF | Advanced robotics |
  | Complementary | Simple fusion | Accel + gyro | Low computation, real-time | Low-cost IMU, Arduino |
  | Moving Average | Simple FIR | Smoothing | Very simple & fast | Beginner, temperature |
  | Median | Non-linear | Spike / salt & pepper | Removes outliers well | Images, sensor spikes |
  | Savitzky–Golay | Polynomial smoothing | Preserve peaks/shape | Good for analytical signals | ECG, spectroscopy |
  | Wavelet Denoising | Multi-resolution | Different frequency scales | Non-stationary noise | Audio, medical |
  | Adaptive (LMS/RLS) | Adaptive | Time-varying noise | Auto-adjusts coefficients | Echo/noise cancellation |
  | Notch | Band-Stop | Single frequency (50/60 Hz) | Narrow rejection | Audio, ECG, mains |
  | Particle | Monte Carlo | Non-linear / non-Gaussian | Complex distributions | Robotics, tracking |
  | Wiener | Optimal linear | Known noise statistics | Theoretically optimal | Image restoration |
  | Matched | Correlation | Known signal in noise | Maximizes SNR | Radar, communications |
  
  ---
- ## 1. Filter Types Overview
  
  ```
  FILTER
  │
  ├── 1) PURPOSE: Frequency Behavior (WHAT it does)
  │   │
  │   ├── Low-Pass Filter (LPF)
  │   │   ├── Passes low frequencies
  │   │   └── Attenuates high frequencies
  │   │
  │   ├── High-Pass Filter (HPF)
  │   │   ├── Passes high frequencies
  │   │   └── Removes low frequencies / DC
  │   │
  │   ├── Band-Pass Filter (BPF)
  │   │   └── Passes a limited frequency band
  │   │
  │   ├── Band-Stop Filter (BSF)
  │   │   └── Rejects a frequency band
  │   │
  │   ├── Notch Filter
  │   │   └── Narrow Band-Stop (single known frequency)
  │   │
  │   └── All-Pass Filter (APF)
  │       └── Flat magnitude, modifies phase only
  │
  ├── 2) DOMAIN: Where it is implemented
  │   │
  │   ├── Analog Filter
  │   │   ├── RC
  │   │   ├── Active (Op-Amp)
  │   │   └── LC
  │   │
  │   └── Digital Filter
  │       │
  │       ├── 3) STRUCTURE: Mathematical realization (HOW)
  │       │   │
  │       │   ├── FIR (Finite Impulse Response)
  │       │   │   ├── Properties: No feedback, Always stable, Linear phase possible
  │       │   │   ├── Subtypes: Moving Average (SMA), Windowed FIR (Rectangular, Hamming, Hann, Blackman), Equiripple (Parks–McClellan)
  │       │   │   └── Typical use: Audio, biomedical (ECG, EEG), measurement
  │       │   │
  │       │   └── IIR (Infinite Impulse Response)
  │       │       ├── Properties: Feedback present, Efficient (low order), Nonlinear phase
  │       │       ├── Subtypes: EMA, Single-pole/zero, Biquad (2nd-order sections)
  │       │       └── Typical use: Embedded, control loops, real-time
  │       │
  │       └── 4) DESIGN PROTOTYPE: Frequency response shape
  │           ├── Butterworth — Maximally flat, smooth transition
  │           ├── Chebyshev Type I — Ripple in passband, sharper cutoff
  │           ├── Chebyshev Type II — Flat passband, ripple in stopband
  │           ├── Elliptic (Cauer) — Ripple in both bands, steepest transition
  │           └── FIR-specific: Window-based, Equiripple (minimax)
  ```
  
  ![Filter overview](../assets/image_1770068628149_0.png)
  
  ---
- ## 2. Sensor Filter Recommendations
  
  | Sensor Type | Typical Noise / Problem | Recommended Filter | Architecture | Cutoff / Parameters | Why |
  |-------------|--------------------------|--------------------|--------------|---------------------|-----|
  | Accelerometer | High-freq vibration, motor/electrical noise | LPF | IIR Butterworth 2–4 | 10–30 Hz | Keeps motion, removes noise |
  | Gyroscope | Drift, high-freq noise | LPF + HPF | IIR 2–3 | LPF: 20–50 Hz, HPF: 0.01–0.5 Hz | Noise + drift correction |
  | Magnetometer | Magnetic interference, spikes | LPF + Median | IIR or FIR | 5–15 Hz | Smooths jitter, removes spikes |
  | IMU (Accel+Gyro+Mag) | Drift + noise all axes | Complementary or Kalman | Fusion algorithm | — | Best for orientation |
  | Microphone / Audio | Background noise, 50/60 Hz hum | LPF + Notch | FIR or IIR | LPF: 8–20 kHz, Notch: 50/60 Hz | Voice/music quality |
  | PPG (Heart Rate) | Motion artifact, light noise | Band-Pass | IIR 2–4 | 0.5–5 Hz | Keeps heart rate band |
  | ECG | Mains hum, muscle noise, baseline wander | Band-Pass + Notch | FIR preferred or IIR | 0.5–40 Hz, Notch: 50/60 Hz | Preserves QRS shape (phase) |
  | Temperature | Slow thermal noise, spikes | LPF + Moving Average | IIR or FIR | 0.1–1 Hz | Temperature is slow |
  | Barometer / Pressure | High-freq from movement | LPF | IIR order 2 | 1–5 Hz | Pressure is slow-varying |
  | GPS | Multipath, jumps | LPF or Kalman | — | 0.1–1 Hz | Smooths position |
  | Camera / Image | Salt & pepper, Gaussian noise | Median + Gaussian | Spatial FIR | — | Reduces pixel noise |
  | Force / Strain Gauge | Electrical noise, vibration | LPF | IIR 2–3 | 10–50 Hz | Keeps slow force changes |
  
  ---
- ## 3. Other Filter Types (Beyond LPF/HPF/BP/BS + FIR/IIR)
  id:: 69825d62-32db-4eca-80a1-ce0e6ce0c85a
  
  | Filter | Type | Main Use | Advantage | Typical Application |
  |--------|------|----------|-----------|----------------------|
  | Kalman | Optimal estimation | Sensor fusion | Best accuracy, noise + uncertainty | Drones, phones, robots |
  | EKF | Non-linear Kalman | Non-linear sensors | Works with non-linear systems | Orientation |
  | UKF | Non-linear Kalman | Strong non-linearities | More accurate than EKF | Advanced robotics |
  | Complementary | Simple fusion | Accel + gyro | Low computation, real-time | Low-cost IMU, Arduino |
  | Moving Average | Simple FIR | Smoothing | Very simple & fast | Beginner, temperature |
  | Median | Non-linear | Spike / salt & pepper | Removes outliers well | Images, sensor spikes |
  | Savitzky–Golay | Polynomial smoothing | Preserve peaks/shape | Good for analytical signals | ECG, spectroscopy |
  | Wavelet Denoising | Multi-resolution | Different frequency scales | Non-stationary noise | Audio, medical |
  | Adaptive (LMS/RLS) | Adaptive | Time-varying noise | Auto-adjusts coefficients | Echo/noise cancellation |
  | Notch | Band-Stop | Single frequency (50/60 Hz) | Narrow rejection | Audio, ECG, mains |
  | Particle | Monte Carlo | Non-linear / non-Gaussian | Complex distributions | Robotics, tracking |
  | Wiener | Optimal linear | Known noise statistics | Theoretically optimal | Image restoration |
  | Matched | Correlation | Known signal in noise | Maximizes SNR | Radar, communications |
  
  ---
- ## 4. FIR — Finite Impulse Response
  
  **Idea:** Output depends only on **past and current inputs** (no feedback).
  
  **General form:**
  
  ```
  y[n] = b0·x[n] + b1·x[n-1] + b2·x[n-2] + ... + bM·x[n-M]
  ```
- ### FIR design methods
- **Moving Average** — Simple
- **Windowed Sinc** — Hamming, Hanning, Blackman
- **Parks–McClellan** — Equiripple
- **Least Squares**
- **Multirate FIR** — Decimation, Interpolation
- ### FIR advantages
- **100% stable**
- **Linear phase** (very important for sensors)
- ### Coefficient design methods
- **Window method:** Multiply an ideal (Sinc) filter by a window (e.g. Hamming) to limit length.  
  *Advantage:* Simple and fast. *Disadvantage:* No precise control over ripple.
- **Parks–McClellan:** Equiripple design that minimizes maximum error.  
  *Advantage:* Best response for a given order. *Disadvantage:* Heavier design computation.
- ### MATLAB example (FIR low-pass, Hamming)
  
  ```matlab
  % Filter specs
  fs = 1000;           % Sampling frequency (Hz)
  f_cutoff = 100;      % Cutoff frequency (Hz)
  N = 50;              % Filter order (number of coefficients - 1)
  
  % Normalize cutoff (0 to 1)
  Wn = f_cutoff / (fs / 2);
  
  % Design FIR low-pass with Hamming window
  b_fir = fir1(N, Wn, 'low', hamming(N+1));
  
  % Plot frequency response
  freqz(b_fir, 1, 1024, fs);
  title('Frequency response of designed FIR filter');
  ```
  
  **Online tool:** [t-filter.engineerjs.com](http://t-filter.engineerjs.com/)
  
  ---
- ## 5. IIR — Infinite Impulse Response
  
  **Idea:** Output depends on **input and past outputs** (feedback).
  
  **General form:**
  
  ```
  y[n] = b0·x[n] + ... + bM·x[n-M]
     − a1·y[n-1] − a2·y[n-2] − ...
  ```
- ### IIR design (classic analog-based)
- **Butterworth** — Maximally flat passband, relatively linear phase.
- **Chebyshev Type I** — Passband ripple, steeper cutoff.
- **Chebyshev Type II** — Stopband ripple, steeper cutoff.
- **Elliptic (Cauer)** — Ripple in both bands, steepest transition for given order.
  
  **Implementation:** Use **Biquad** (second-order sections) for numerical stability, especially in fixed-point (e.g. Q15, Q31) on microcontrollers.
- ### IIR advantages
- Low order
- Fast
- Low CPU use
  
  ![IIR / Biquad structure](../assets/image_1770069383132_0.png)
- ### MATLAB example (IIR Butterworth, SOS)
  
  ```matlab
  % IIR (Butterworth) specs
  fs = 1000;
  fc = 100;      % Cutoff frequency
  order = 4;
  Wn = fc / (fs / 2);
  
  % Design and get coefficients as SOS (second-order sections)
  [z, p, k] = butter(order, Wn, 'low');
  [sos, g] = zp2sos(z, p, k);
  
  % Plot frequency response
  freqz(sos, g, 1024, fs);
  title('IIR (Butterworth) frequency response');
  
  % Check stability: pole-zero plot
  zplane(z, p);
  title('Pole and zero locations');
  ```
  
  **Python (scipy):**  
  `b, a = signal.butter(N, Wn, 'low')`  
  `b, a = signal.cheby1(N, rp, Wn, 'low')`
  
  ---
- ## 6. Filter Selection by Application
- **Sensor noise (low-pass):**  
  White noise, slow signal → **IIR (low order, e.g. 2)** is enough.  
  Pulse shape important → **FIR (Hamming/Blackman)**.
- **Control loops:**  
  **IIR (Biquad)** is standard. Low delay is critical for stability.  
  *Warning:* Account for IIR nonlinear phase in controller design.
- **Audio:**  
  **FIR** for equalizer and crossover (linear phase).  
  **IIR** for simple bass/treble (efficient).
- **Mains noise (50/60 Hz):**  
  **IIR Biquad notch** is common — narrow band, little effect on nearby frequencies.
  
  ---
- ## 7. Three Practical Filter Examples
- ### Filter A: Moving Average (FIR)
  
  4-point moving average:
- **Time domain:**  
  \(y[n] = \frac{1}{4}(x[n] + x[n-1] + x[n-2] + x[n-3])\)
- **Z-domain:**  
  \(H(z) = \frac{1}{4}(1 + z^{-1} + z^{-2} + z^{-3}) = \frac{1}{4}\frac{1 - z^{-4}}{1 - z^{-1}}\)
- **Stability:** Poles at \(z = 0\) (inside unit circle). **Always stable.**  
  *Source:* Oppenheim & Schafer, *Discrete-Time Signal Processing* (2009).
- ### Filter B: Hamming-windowed FIR (low-pass)
- **Goal:** Pass &lt; 1 Hz, attenuate &gt; 2 Hz.
- **Specs:** \(f_c = 1.0\) Hz, order \(N = 20\).
- **Method:** `fir1` window method (truncated sinc).  
  *Source:* [MathWorks: fir1](https://www.mathworks.com/help/signal/ref/fir1.html)
- **Z-domain:** \(H(z) = \sum_{k=0}^{19} b_k z^{-k}\)
- ### Filter C: IIR Butterworth (Biquad)
- **Specs:** \(f_c = 1.0\) Hz, 2nd-order section.
- **Method:** Bilinear transform from analog Butterworth.  
  *Source:* [Analog Devices: IIR Filter Design](https://www.analog.com/en/design-center/design-hardware-and-software/tutorials/mixed-signal/dsp/iir-filter-design-101.html)
- **Z-domain:** \(H(z) = \frac{b_0 + b_1 z^{-1} + b_2 z^{-2}}{1 + a_1 z^{-1} + a_2 z^{-2}}\)
  
  ![IIR Biquad Z-domain](../assets/image_1769895640446_0.png)
  
  ---
- ## 8. Stability & Risk Analysis
  
  For embedded systems, an unstable IIR can drive the output to saturation.
- ### Stability rule
  
  A linear discrete-time system is **stable if and only if** all poles of \(H(z)\) lie **inside the unit circle** in the Z-plane:
- \(|p_k| < 1\) for all \(k\) → **Stable**
- \(|p_k| = 1\) → **Marginally stable**
- \(|p_k| > 1\) → **Unstable** (output grows without bound)
- ### Sensitivity (fixed-point)
  
  In fixed-point (e.g. Q15, Q31), IIR filters with poles near the unit circle (high Q) are sensitive.
  
  **Recommendation:** Use **SOS (Biquad cascade)** instead of Direct Form II with large coefficients.  
  *Source:* [Analog Devices: IIR Filter Structures](https://www.analog.com/en/design-center/design-hardware-and-software/tutorials/mixed-signal/dsp/iir-filter-design-101.html)
  
  ---
- ## 9. Practical Visualization
  
  For validation, plot:
  
  1. **Time domain** — Input and output overlay to see noise reduction.
  2. **Frequency response** — Check that unwanted frequencies are sufficiently attenuated.
  3. **Phase & group delay:**
	- FIR: phase should be linear.
	- IIR: group delay changes strongly near resonances (poles).
	  
	  **MATLAB example:**
	  
	  ```matlab
	  % Phase and group delay
	  [h, w] = freqz(sos, g, 1024, fs);
	  phi = angle(h);           % Phase
	  gd = grpdelay(sos, g, 1024, fs);  % Group delay
	  
	  figure;
	  subplot(2,1,1); plot(w, phi); title('Phase');
	  subplot(2,1,2); plot(w, gd); title('Group Delay');
	  ```
	  
	  ---
- ## 10. DSP Concepts (Plain Language)
- ### DFT / Fourier — what does it mean?
  
  Fourier says: *“I test your data with different rotation speeds. Where it matches, that frequency is present.”*
- Very slow rotation → true trend (e.g. temperature).
- Fast rotation → noise.
  
  **Output of Fourier:** It does **not** tell you “when”; it tells you **which frequencies** are in the data.
- ### Z-transform — why a complex variable?
  
  In discrete systems, data are **samples**, so we use **step-wise rotation** instead of continuous sinusoids.
  
  **Z** means: *rotation and simultaneous growth or decay.*
- Rotation → frequency
- Magnitude → stable vs unstable
  
  **Rule:** If poles are **inside** the unit circle → system is **stable**.
- ### Pole
  
  A **pole** is where the system “likes to get stuck”:
- Near origin → response dies quickly.
- Near unit circle → more oscillation.
- **Outside** unit circle → instability (output blows up).
- ### Zero
  
  A **zero** is where the system **suppresses** a frequency.  
  Put a zero on a noise frequency → that noise is reduced.
  
  **Simple summary:** Pole = emphasis/resonance; Zero = cancellation.
- ### Nyquist (short)
  
  If \(F_s = 10\) Hz, you **cannot correctly represent** anything above 5 Hz.  
  Noise above that → aliasing → errors. That is why anti-aliasing filtering matters.
- ### Sampling theorem (Nyquist–Shannon)
  
  To represent a signal with maximum frequency \(f_{max}\) without loss, you must sample at **at least** \(F_s \geq 2 \cdot f_{max}\).  
  **Nyquist frequency** = \(F_s / 2\). Frequencies above Nyquist fold back (alias) into the 0–Nyquist range and cannot be recovered. So: design your **cutoff below Nyquist**, and use an anti-aliasing filter before sampling if the signal has high-frequency content.
- ### Aliasing
  
  When a signal has components above \(F_s/2\), they appear in the spectrum as **lower** frequencies. Example: 7 Hz with \(F_s = 10\) Hz looks like 3 Hz. The only fix is to **filter before sampling** so that nothing above Nyquist enters the ADC.
- ### Convolution
  
  Filtering in the time domain is **convolution**: \(y[n] = (h * x)[n] = \sum_k h[k]\, x[n-k]\). The sequence \(h[n]\) is the filter’s **impulse response**. So: feed a single “1” at time 0 and zeros elsewhere; the output is \(h[n]\). FIR: \(h[n]\) has finite length. IIR: \(h[n]\) is infinitely long (in theory).
- ### Impulse response
- **FIR:** Impulse response has a finite number of non-zero samples; after that it is exactly zero.
- **IIR:** Impulse response never becomes exactly zero; it decays (if stable).  
  The **order** of a filter is related to how many past samples (and for IIR, past outputs) it uses.
- ### Passband, stopband, transition band
- **Passband** — Frequencies you want to keep; gain ≈ 1 (0 dB).
- **Stopband** — Frequencies you want to remove; gain ≪ 1 (large attenuation in dB).
- **Transition band** — Between passband and stopband; gain drops from ≈1 to ≈0. Steeper transition usually means higher filter order or more computation.
- ### Decibels (dB)
  
  Attenuation is often in **dB**: \(\text{dB} = 20 \log_{10}(|H|)\).
- 0 dB = no change.
- −20 dB = 1/10 in amplitude.
- −40 dB = 1/100.  
  Specs like “−40 dB in the stopband” mean the filter reduces those frequencies to 1% of the input level.
- ### Group delay
  
  **Group delay** = \(-\frac{d\phi}{d\omega}\) (negative derivative of phase vs frequency). It is the **time delay** (in samples or seconds) that each frequency component experiences. For **linear phase** (e.g. symmetric FIR), group delay is constant → no phase distortion. IIR filters usually have **non-constant** group delay → different frequencies are delayed differently, which can distort sharp transients.
- ### Bilinear transform
  
  IIR digital filters are often designed by starting from an **analog** prototype (Butterworth, Chebyshev, etc.). The **bilinear transform** maps the analog \(s\)-plane to the digital \(z\)-plane: \(s \leftrightarrow \frac{2}{T}\frac{1-z^{-1}}{1+z^{-1}}\). It preserves stability (left-half \(s\)-plane → inside unit circle) but **warps** frequency: analog and digital frequencies do not match 1:1, especially near Nyquist. Design tools apply **prewarping** so the digital cutoff matches the desired value.
- ### Difference equation
  
  A digital filter is implemented with a **difference equation**:  
  \(y[n] = \sum_k b_k x[n-k] - \sum_m a_m y[n-m]\).  
  The \(b_k\) are **feedforward** (input) coefficients; the \(a_m\) are **feedback** (output) coefficients. FIR has only \(b_k\) (no \(a_m\)). IIR has both. This is what you actually code in C or assembly on a microcontroller.
- ### Very short summary
- **DSP** = seeing what is behind the numbers
- **Fourier** = seeing frequencies
- **FFT** = Fast Fourier
- **Z-transform** = language of discrete systems
- **Pole** = emphasis and stability
- **Zero** = frequency cancellation
- **Unit circle** = stability boundary
- **Nyquist** = sample at least 2× highest frequency; cutoff must be below \(F_s/2\)
- **Convolution** = time-domain filtering; impulse response defines the filter
- **Group delay** = delay per frequency; constant for linear-phase FIR  
  
  ---
- ## 11. Cutoff Frequency & Nyquist
- Cutoff frequency should be **below** the Nyquist limit (half of sampling frequency).
- IIR low-pass on accelerometer data: the digital filter is derived from the continuous-time RC low-pass; cutoff is set according to signal bandwidth and Nyquist.
  
  Low-pass filter applied to accelerometer data:
  
  ![Low-pass on accelerometer data](../assets/image_1769372749169_0.png)
  
  The IIR filter is derived from the RC low-pass:
  
  ![IIR from low-pass filter](../assets/image_1769372830491_0.png)
  
  Cutoff frequency:
  
  ![Cutoff frequency](../assets/image_1769372858507_0.png)
  
  ---
- ## 12. Resources & References
- ### Videos
- [DSP / filter intro](https://www.youtube.com/watch?v=PJ7Hg4xZLZc)
- [IIR filter with accelerometer data](https://www.youtube.com/watch?v=QRMe02kzVkA&list=PLXSyc11qLa1ZCn0JCnaaXOWN6Z46rK9jd&index=3)
- [Digital RC low-pass implementation](https://www.youtube.com/watch?v=MrbffdimDts&list=PLXSyc11qLa1ZCn0JCnaaXOWN6Z46rK9jd&index=1)
- [STM32 real-time FIR (CMSIS)](https://www.youtube.com/watch?v=lDskXTR6psY)
- [Software low-pass filter](https://www.youtube.com/watch?v=VDhmVrbSpqA)
- ### Tools & libraries
- **CMSIS-DSP FIR:** [ARM CMSIS-DSP FIR](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html)
- **Online FIR design:** [t-filter.engineerjs.com](http://t-filter.engineerjs.com/)
- **Octave** (MATLAB-like, for Z-transform / filter design): [GNU Octave for Windows](https://mirror.lyrahosting.com/gnu/octave/windows/)
  
  ![Octave for Z-transform / filter design](../assets/image_1769642808461_0.png)
- ### High-pass filter
  
  ![High-pass filter](../assets/image_1769645755784_0.png)
  
  ---
- ## 13. Embedded C filter code (LPF, HPF, EMA, IIR, FIR)
  
  Embedded C implementations: **1st-, 2nd-, and 4th-order** LPF/HPF, **EMA**, **IIR** (biquad), and **FIR**. Float-based; no heap. Open each block to view or copy.
  
  <details>
  <summary><strong>📄 embedded_filters.h</strong> — API and structs</summary>
  
  ```c
  /**
  * embedded_filters.h
  * First-order, second-order, and fourth-order LPF/HPF, EMA, IIR, and FIR
  * for embedded C. Float implementation; no heap allocation.
  */
  
  #ifndef EMBEDDED_FILTERS_H
  #define EMBEDDED_FILTERS_H
  
  #ifdef __cplusplus
  extern "C" {
  #endif
  
  /* ========== 1st-order low-pass (single pole) ========== */
  typedef struct {
  float y_prev;   /* previous output */
  float alpha;    /* smoothing factor, 0 < alpha <= 1 */
  } lpf1_t;
  
  void     lpf1_init(lpf1_t *f, float alpha);
  void     lpf1_set_cutoff(lpf1_t *f, float fc_Hz, float fs_Hz);
  float    lpf1_update(lpf1_t *f, float x);
  
  /* ========== 1st-order high-pass (DC blocker) ========== */
  typedef struct {
  float x_prev, y_prev;
  float alpha;    /* 0 < alpha < 1, larger = higher cutoff */
  } hpf1_t;
  
  void     hpf1_init(hpf1_t *f, float alpha);
  void     hpf1_set_cutoff(hpf1_t *f, float fc_Hz, float fs_Hz);
  float    hpf1_update(hpf1_t *f, float x);
  
  /* ========== 2nd-order IIR (biquad) LPF/HPF ========== */
  typedef struct {
  float b0, b1, b2, a1, a2;
  float x1, x2, y1, y2;  /* state (Direct Form II transposed) */
  } biquad_t;
  
  void     biquad_lpf2_init(biquad_t *f, float fc_Hz, float fs_Hz);
  void     biquad_hpf2_init(biquad_t *f, float fc_Hz, float fs_Hz);
  float    biquad_update(biquad_t *f, float x);
  
  /* ========== 4th-order IIR (two biquads in cascade) LPF/HPF ========== */
  typedef struct {
  biquad_t stage[2];
  } iir4_t;
  
  void     iir4_lpf_init(iir4_t *f, float fc_Hz, float fs_Hz);
  void     iir4_hpf_init(iir4_t *f, float fc_Hz, float fs_Hz);
  float    iir4_update(iir4_t *f, float x);
  
  /* ========== EMA (Exponential Moving Average) = 1st-order IIR LPF ========== */
  typedef struct {
  float y_prev;
  float alpha;    /* 0 < alpha <= 1 */
  } ema_t;
  
  void     ema_init(ema_t *f, float alpha);
  void     ema_set_cutoff(ema_t *f, float fc_Hz, float fs_Hz);
  float    ema_update(ema_t *f, float x);
  
  /* ========== Generic IIR (single biquad, any coefficients) ========== */
  void     iir_biquad_set_coeffs(biquad_t *f, float b0, float b1, float b2, float a1, float a2);
  float    iir_biquad_update(biquad_t *f, float x);
  
  /* ========== FIR (fixed max taps, ring buffer) ========== */
  #define FIR_MAX_TAPS  32
  
  typedef struct {
  float coeffs[FIR_MAX_TAPS];
  float buffer[FIR_MAX_TAPS];
  unsigned int num_taps;
  unsigned int head;   /* next write index */
  } fir_t;
  
  void     fir_init(fir_t *f, const float *coeffs, unsigned int num_taps);
  float    fir_update(fir_t *f, float x);
  void     fir_reset(fir_t *f);
  
  /* ========== Apply filter to array (in-place or to output) ========== */
  void     lpf1_filter_array(lpf1_t *f, const float *x, float *y, unsigned int n);
  void     hpf1_filter_array(hpf1_t *f, const float *x, float *y, unsigned int n);
  void     biquad_filter_array(biquad_t *f, const float *x, float *y, unsigned int n);
  void     iir4_filter_array(iir4_t *f, const float *x, float *y, unsigned int n);
  void     ema_filter_array(ema_t *f, const float *x, float *y, unsigned int n);
  void     fir_filter_array(fir_t *f, const float *x, float *y, unsigned int n);
  
  /* Helper: compute 1st-order LPF/EMA alpha from cutoff and sample rate */
  float    filter_alpha_from_cutoff(float fc_Hz, float fs_Hz);
  
  #ifdef __cplusplus
  }
  #endif
  
  #endif /* EMBEDDED_FILTERS_H */
  ```
  
  </details>
  
  <details>
  <summary><strong>📄 embedded_filters.c</strong> — Implementations</summary>
  
  ```c
  /**
  * embedded_filters.c
  * Implementations: 1st/2nd/4th-order LPF & HPF, EMA, IIR biquad, FIR.
  * Float; no heap. Suitable for ARM Cortex-M, AVR, etc.
  */
  
  #include "embedded_filters.h"
  #include <math.h>
  #include <string.h>
  
  #ifndef M_PI
  #define M_PI 3.14159265358979323846f
  #endif
  
  /* ----- 1st-order LPF: y = alpha*x + (1-alpha)*y_prev ----- */
  void lpf1_init(lpf1_t *f, float alpha) {
  f->y_prev = 0.0f;
  f->alpha = alpha;
  }
  
  float filter_alpha_from_cutoff(float fc_Hz, float fs_Hz) {
  float t = (float)(2.0 * M_PI * (double)fc_Hz / (double)fs_Hz);
  if (t > 1.0f) t = 1.0f;
  return 1.0f - expf(-t);
  }
  
  void lpf1_set_cutoff(lpf1_t *f, float fc_Hz, float fs_Hz) {
  f->alpha = filter_alpha_from_cutoff(fc_Hz, fs_Hz);
  }
  
  float lpf1_update(lpf1_t *f, float x) {
  float y = f->alpha * x + (1.0f - f->alpha) * f->y_prev;
  f->y_prev = y;
  return y;
  }
  
  void lpf1_filter_array(lpf1_t *f, const float *x, float *y, unsigned int n) {
  for (unsigned int i = 0; i < n; i++)
  y[i] = lpf1_update(f, x[i]);
  }
  
  /* ----- 1st-order HPF: DC blocker ----- */
  void hpf1_init(hpf1_t *f, float alpha) {
  f->x_prev = 0.0f;
  f->y_prev = 0.0f;
  f->alpha = alpha;
  }
  
  void hpf1_set_cutoff(hpf1_t *f, float fc_Hz, float fs_Hz) {
  f->alpha = filter_alpha_from_cutoff(fc_Hz, fs_Hz);
  }
  
  float hpf1_update(hpf1_t *f, float x) {
  float y = f->alpha * (f->y_prev + x - f->x_prev);
  f->x_prev = x;
  f->y_prev = y;
  return y;
  }
  
  void hpf1_filter_array(hpf1_t *f, const float *x, float *y, unsigned int n) {
  for (unsigned int i = 0; i < n; i++)
  y[i] = hpf1_update(f, x[i]);
  }
  
  /* ----- 2nd-order IIR biquad (Direct Form I) ----- */
  static void biquad_compute_lpf2(float fc_Hz, float fs_Hz, float *b0, float *b1, float *b2, float *a1, float *a2) {
  float w0 = 2.0f * M_PI * fc_Hz / fs_Hz;
  if (w0 > (float)(M_PI * 0.99)) w0 = (float)(M_PI * 0.99);
  float Q = 0.7071f;  /* Butterworth */
  float cosw = cosf(w0), sinw = sinf(w0);
  float alpha = sinw / (2.0f * Q);
  float A = 1.0f + alpha;
  *b0 = (1.0f - cosw) / (2.0f * A);
  *b1 = (1.0f - cosw) / A;
  *b2 = *b0;
  *a1 = -2.0f * cosw / A;
  *a2 = (1.0f - alpha) / A;
  }
  
  static void biquad_compute_hpf2(float fc_Hz, float fs_Hz, float *b0, float *b1, float *b2, float *a1, float *a2) {
  float w0 = 2.0f * M_PI * fc_Hz / fs_Hz;
  if (w0 > (float)(M_PI * 0.99)) w0 = (float)(M_PI * 0.99);
  float Q = 0.7071f;
  float cosw = cosf(w0), sinw = sinf(w0);
  float alpha = sinw / (2.0f * Q);
  float A = 1.0f + alpha;
  *b0 = (1.0f + cosw) / (2.0f * A);
  *b1 = -(1.0f + cosw) / A;
  *b2 = *b0;
  *a1 = -2.0f * cosw / A;
  *a2 = (1.0f - alpha) / A;
  }
  
  void biquad_lpf2_init(biquad_t *f, float fc_Hz, float fs_Hz) {
  biquad_compute_lpf2(fc_Hz, fs_Hz, &f->b0, &f->b1, &f->b2, &f->a1, &f->a2);
  f->x1 = f->x2 = f->y1 = f->y2 = 0.0f;
  }
  
  void biquad_hpf2_init(biquad_t *f, float fc_Hz, float fs_Hz) {
  biquad_compute_hpf2(fc_Hz, fs_Hz, &f->b0, &f->b1, &f->b2, &f->a1, &f->a2);
  f->x1 = f->x2 = f->y1 = f->y2 = 0.0f;
  }
  
  float biquad_update(biquad_t *f, float x) {
  float y = f->b0 * x + f->b1 * f->x1 + f->b2 * f->x2 - f->a1 * f->y1 - f->a2 * f->y2;
  f->x2 = f->x1; f->x1 = x;
  f->y2 = f->y1; f->y1 = y;
  return y;
  }
  
  void biquad_filter_array(biquad_t *f, const float *x, float *y, unsigned int n) {
  for (unsigned int i = 0; i < n; i++)
  y[i] = biquad_update(f, x[i]);
  }
  
  void iir_biquad_set_coeffs(biquad_t *f, float b0, float b1, float b2, float a1, float a2) {
  f->b0 = b0; f->b1 = b1; f->b2 = b2;
  f->a1 = a1; f->a2 = a2;
  f->x1 = f->x2 = f->y1 = f->y2 = 0.0f;
  }
  
  float iir_biquad_update(biquad_t *f, float x) {
  return biquad_update(f, x);
  }
  
  /* ----- 4th-order: two biquad stages (Butterworth) ----- */
  static void iir4_lpf_stage_coeffs(float fc_Hz, float fs_Hz, int stage, float *b0, float *b1, float *b2, float *a1, float *a2) {
  float w0 = 2.0f * M_PI * fc_Hz / fs_Hz;
  if (w0 > (float)(M_PI * 0.99)) w0 = (float)(M_PI * 0.99);
  float Q = (stage == 0) ? 0.541196f : 1.306563f;
  float cosw = cosf(w0), sinw = sinf(w0);
  float alpha = sinw / (2.0f * Q);
  float A = 1.0f + alpha;
  *b0 = (1.0f - cosw) / (2.0f * A);
  *b1 = (1.0f - cosw) / A;
  *b2 = *b0;
  *a1 = -2.0f * cosw / A;
  *a2 = (1.0f - alpha) / A;
  }
  
  static void iir4_hpf_stage_coeffs(float fc_Hz, float fs_Hz, int stage, float *b0, float *b1, float *b2, float *a1, float *a2) {
  float w0 = 2.0f * M_PI * fc_Hz / fs_Hz;
  if (w0 > (float)(M_PI * 0.99)) w0 = (float)(M_PI * 0.99);
  float Q = (stage == 0) ? 0.541196f : 1.306563f;
  float cosw = cosf(w0), sinw = sinf(w0);
  float alpha = sinw / (2.0f * Q);
  float A = 1.0f + alpha;
  *b0 = (1.0f + cosw) / (2.0f * A);
  *b1 = -(1.0f + cosw) / A;
  *b2 = *b0;
  *a1 = -2.0f * cosw / A;
  *a2 = (1.0f - alpha) / A;
  }
  
  void iir4_lpf_init(iir4_t *f, float fc_Hz, float fs_Hz) {
  for (int s = 0; s < 2; s++) {
  float b0, b1, b2, a1, a2;
  iir4_lpf_stage_coeffs(fc_Hz, fs_Hz, s, &b0, &b1, &b2, &a1, &a2);
  iir_biquad_set_coeffs(&f->stage[s], b0, b1, b2, a1, a2);
  }
  }
  
  void iir4_hpf_init(iir4_t *f, float fc_Hz, float fs_Hz) {
  for (int s = 0; s < 2; s++) {
  float b0, b1, b2, a1, a2;
  iir4_hpf_stage_coeffs(fc_Hz, fs_Hz, s, &b0, &b1, &b2, &a1, &a2);
  iir_biquad_set_coeffs(&f->stage[s], b0, b1, b2, a1, a2);
  }
  }
  
  float iir4_update(iir4_t *f, float x) {
  float v = biquad_update(&f->stage[0], x);
  return biquad_update(&f->stage[1], v);
  }
  
  void iir4_filter_array(iir4_t *f, const float *x, float *y, unsigned int n) {
  for (unsigned int i = 0; i < n; i++)
  y[i] = iir4_update(f, x[i]);
  }
  
  /* ----- EMA ----- */
  void ema_init(ema_t *f, float alpha) {
  f->y_prev = 0.0f;
  f->alpha = alpha;
  }
  
  void ema_set_cutoff(ema_t *f, float fc_Hz, float fs_Hz) {
  f->alpha = filter_alpha_from_cutoff(fc_Hz, fs_Hz);
  }
  
  float ema_update(ema_t *f, float x) {
  float y = f->alpha * x + (1.0f - f->alpha) * f->y_prev;
  f->y_prev = y;
  return y;
  }
  
  void ema_filter_array(ema_t *f, const float *x, float *y, unsigned int n) {
  for (unsigned int i = 0; i < n; i++)
  y[i] = ema_update(f, x[i]);
  }
  
  /* ----- FIR: ring buffer ----- */
  void fir_init(fir_t *f, const float *coeffs, unsigned int num_taps) {
  if (num_taps > FIR_MAX_TAPS) num_taps = FIR_MAX_TAPS;
  f->num_taps = num_taps;
  memcpy(f->coeffs, coeffs, num_taps * sizeof(float));
  memset(f->buffer, 0, sizeof(f->buffer));
  f->head = 0;
  }
  
  float fir_update(fir_t *f, float x) {
  f->buffer[f->head] = x;
  unsigned int idx = f->head;
  float sum = 0.0f;
  for (unsigned int i = 0; i < f->num_taps; i++) {
  sum += f->coeffs[i] * f->buffer[idx];
  idx = (idx == 0) ? (f->num_taps - 1) : (idx - 1);
  }
  f->head = (f->head + 1) % f->num_taps;
  return sum;
  }
  
  void fir_reset(fir_t *f) {
  memset(f->buffer, 0, f->num_taps * sizeof(float));
  f->head = 0;
  }
  
  void fir_filter_array(fir_t *f, const float *x, float *y, unsigned int n) {
  for (unsigned int i = 0; i < n; i++)
  y[i] = fir_update(f, x[i]);
  }
  ```
  
  </details>
  
  <details>
  <summary><strong>📄 example_usage.c</strong> — How to use LPF/IIR/EMA/FIR on arrays</summary>
  
  ```c
  /**
  * example_usage.c — Use with embedded_filters.c and embedded_filters.h
  */
  #include "embedded_filters.h"
  
  #define SAMPLE_RATE_HZ  1000.0f
  #define CUTOFF_HZ       50.0f
  #define ARRAY_LEN       64
  
  /* 1st-order LPF on array */
  void example_lpf1_on_array(void) {
  float adc_samples[ARRAY_LEN];
  float filtered[ARRAY_LEN];
  lpf1_t lpf;
  lpf1_init(&lpf, 0.1f);
  lpf1_set_cutoff(&lpf, CUTOFF_HZ, SAMPLE_RATE_HZ);
  lpf1_filter_array(&lpf, adc_samples, filtered, ARRAY_LEN);
  }
  
  /* In-place LPF (overwrite same array) */
  void example_lpf1_in_place(void) {
  float data[ARRAY_LEN];
  lpf1_t lpf;
  lpf1_init(&lpf, 0.1f);
  lpf1_set_cutoff(&lpf, CUTOFF_HZ, SAMPLE_RATE_HZ);
  lpf1_filter_array(&lpf, data, data, ARRAY_LEN);
  }
  
  /* 2nd-order IIR LPF on array */
  void example_iir2_lpf_on_array(void) {
  float raw[ARRAY_LEN], out[ARRAY_LEN];
  biquad_t bq;
  biquad_lpf2_init(&bq, CUTOFF_HZ, SAMPLE_RATE_HZ);
  biquad_filter_array(&bq, raw, out, ARRAY_LEN);
  }
  
  /* 4th-order IIR LPF on array */
  void example_iir4_lpf_on_array(void) {
  float raw[ARRAY_LEN], out[ARRAY_LEN];
  iir4_t iir4;
  iir4_lpf_init(&iir4, CUTOFF_HZ, SAMPLE_RATE_HZ);
  iir4_filter_array(&iir4, raw, out, ARRAY_LEN);
  }
  
  /* EMA on array */
  void example_ema_on_array(void) {
  float samples[ARRAY_LEN], smoothed[ARRAY_LEN];
  ema_t ema;
  ema_init(&ema, 0.2f);
  ema_filter_array(&ema, samples, smoothed, ARRAY_LEN);
  }
  
  /* FIR on array (e.g. 5-tap moving average) */
  void example_fir_on_array(void) {
  float fir_coeffs[] = { 0.2f, 0.2f, 0.2f, 0.2f, 0.2f };
  float input[ARRAY_LEN], output[ARRAY_LEN];
  fir_t fir;
  fir_init(&fir, fir_coeffs, 5);
  fir_filter_array(&fir, input, output, ARRAY_LEN);
  }
  
  /* One sample at a time (e.g. ADC interrupt) */
  void example_single_sample(void) {
  lpf1_t lpf;
  lpf1_init(&lpf, filter_alpha_from_cutoff(10.0f, 100.0f));
  float y = lpf1_update(&lpf, adc_value);
  }
  ```
  
  </details>
  
  <details>
  <summary><strong>📖 Explanation — Filter list, array usage, build</strong></summary>
  
  **Filter list**
  
  | Filter | Order | Type | Functions |
  |--------|-------|------|-----------|
  | Low-pass | 1st | IIR | `lpf1_init`, `lpf1_set_cutoff`, `lpf1_update`, `lpf1_filter_array` |
  | Low-pass | 2nd | IIR biquad | `biquad_lpf2_init`, `biquad_update`, `biquad_filter_array` |
  | Low-pass | 4th | IIR (2 biquads) | `iir4_lpf_init`, `iir4_update`, `iir4_filter_array` |
  | High-pass | 1st | IIR | `hpf1_init`, `hpf1_set_cutoff`, `hpf1_update`, `hpf1_filter_array` |
  | High-pass | 2nd / 4th | IIR | `biquad_hpf2_init` / `iir4_hpf_init` + same update/array APIs |
  | EMA | 1st | IIR | `ema_init`, `ema_set_cutoff`, `ema_update`, `ema_filter_array` |
  | IIR (any coeffs) | 2nd | Biquad | `iir_biquad_set_coeffs`, `iir_biquad_update` |
  | FIR | N taps | FIR | `fir_init`, `fir_update`, `fir_filter_array`, `fir_reset` |
  
  **Adding LPF or IIR to your array**
  
  - **Separate output (keep original):**  
  `lpf1_filter_array(&lpf, my_array, filtered, N);`  
  Use `filtered[]`.
  
  - **In-place (overwrite):**  
  `lpf1_filter_array(&lpf, my_array, my_array, N);`
  
  - **2nd- or 4th-order IIR:**  
  `biquad_lpf2_init(&bq, fc_Hz, fs_Hz);` then `biquad_filter_array(&bq, raw, out, N);`  
  Or `iir4_lpf_init` + `iir4_filter_array` for 4th order.
  
  - **One sample (e.g. interrupt):**  
  `float y = lpf1_update(&lpf, adc_value);`
  
  **Build:** Add `embedded_filters.c` to your project, `#include "embedded_filters.h"`, link with `-lm` for math.  
  **1st-order alpha:** `alpha = 1 - exp(-2π·fc/fs)`; use `filter_alpha_from_cutoff(fc, fs)` or `lpf1_set_cutoff` / `ema_set_cutoff`.  
  **FIR:** Max 32 taps; provide coefficients (e.g. from MATLAB or t-filter.engineerjs.com).
  
  </details>
  
  ---
  
  *End of journal — 2026-01-20*