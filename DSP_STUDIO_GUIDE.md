
 ### Designed by Mehdi sehati shal | version v3.0 | date : 2026-02-05
 ---
 ---
# Advanced DSP Studio Pro - Comprehensive Guide

Advanced DSP Studio Pro is an industrial-grade engineering workbench designed for real-time digital signal processing, filter analysis, and embedded firmware code generation. It bridges the gap between high-level filter theory and low-level C implementation.

---

## 📋 Table of Contents
1. [Installation & Launch](#1-installation--launch)
2. [Signal Generation & Verification](#2-signal-generation--verification)
3. [Dual-Stage Filtering Engine](#3-dual-stage-filtering-engine)
4. [Sensor Data Import & Analysis](#4-sensor-data-import--analysis)
5. [Analytics Dashboard](#5-analytics-dashboard)
6. [Embedded C-Code Architect](#6-embedded-c-code-architect)
7. [Operational Guidelines & Tips](#7-operational-guidelines--tips)

---

## 1. Installation & Launch

### Environment Requirements
The studio is powered by Python 3.8+ and requires the following scientific libraries:
*   `numpy`, `scipy`, `matplotlib`, `customtkinter`, `PyWavelets`, `filterpy`.

### How to Run
1.  **Manual Start**: Open your terminal in the project directory and run:
    ```bash
    python advanced_dsp_studio.py
    ```
2.  **Batch Launch**: Double-click the provided `run_studio.bat` file. It will automatically verify your environment, check for missing dependencies, and launch the application.

---

## 2. Signal Generation & Verification

The software features a multi-mode **Signal Synthesizer** for stressed-testing your filter designs:

*   **Sines Mode**: Dual independent oscillators with frequency and amplitude control + variable Gaussian noise.
*   **Impulse Mode**: Sends a single mathematical spike. Used to check the **Settling Time** and **Ringing** of your filter.
*   **Step Mode**: A sudden jump from 0 to 1. Used to measure **Filter Lag** and **Overshoot**—critical for balancing robots/drones.
*   **Sweep (Chirp) Mode**: A frequency slide from Start to Stop. Acts as a "Live Bode Plot" to see the filter roll-off in real-time.
*   **Playback Control**: Use the **Play/Pause (⏯)** button in the sidebar to freeze the signal and analyze a specific wave pattern.

---

## 3. Dual-Stage Filtering Engine

Advanced DSP Studio Pro uses a sequential serial processing architecture:

### Stage 1: Standard Filter (Classical DSP)
*   **IIR Models**: Butterworth, Chebyshev I & II, Elliptic (Cauer), Bessel.
*   **FIR Windows**: Kaiser (with Beta control), Hamming, Hanning, Blackman, Rectangular, and Gaussian.
*   **Specialized Filters**: High-Speed Notch, Parks-McClellan, and Minimum Phase FIR filters.

### Stage 2: Complex/AI Layer (Advanced Algorithms)
*   **Kalman Filter**: 1D state estimator for sensor smoothing.
*   **Savitzky-Golay**: Preserves high-frequency peaks while removing jitter.
*   **Adaptive LMS Filter**: Self-tuning filter for noise cancellation.
*   **Wavelet Denoising**: Multi-level decomposition for non-stationary signals.
*   **Median Filter**: Non-linear spike removal for sensor glitches.

---

## 4. Sensor Data Import & Analysis

Specifically designed for **Bosch/InvenSense Accel-Gyro** logs:
*   **Axis Selection**: Quickly toggle between **AX, AY, AZ, GX, GY, GZ** with instant graph updates.
*   **Auto-Fs Detection**: The platform automatically calculates the sampling rate (Hz) from the timestamps in your CSV.
*   **Smart Scaling**: The Oscilloscope automatically adjusts for high-offset signals (like **AZ at 9.8m/s²** gravity).

---

## 5. Analytics Dashboard

View your filter behavior through seven interactive modules:
1.  **Oscilloscope**: Real-time Raw vs. Filtered comparison.
2.  **FFT Spectrum**: Frequency domain power distribution.
3.  **Magnitude (dB)**: Stopband attenuation and passband ripple.
4.  **Impulse Response**: Time-domain DNA of the filter.
5.  **Z-Plane Map**: Stability check (ensure red Xs are inside the unit circle).
6.  **Phase Response**: Phase rotation and group delay.
7.  **Linear Gain**: Pure voltage-ratio multiplier profile.

---

## 6. Embedded C-Code Architect

Generate production-ready code via the **"Calculate & Analyze"** wizard:

*   **SOS (Biquads)**: Generates Second-Order Sections for high-order IIR stability.
*   **Fixed-Point Export**: Tailored `Q1.15` or `Q1.31` scaling for units without an FPU.
*   **ARM CMSIS-DSP**: Native code generation for STM32 and other Cortex-M processors.
*   **Algorithm Fusion**: Export includes code for both your Standard filter and your Kalman/LMS layers.

---

## 7. Operational Guidelines & Tips

*   **Stability Warning**: If the Red X (Poles) in the Z-Plane move outside the white circle, your filter is **unstable**. Reduce the Order or check your Cutoff frequency.
*   **Lag vs. Smoothing**: Use **Step Mode** to see how much delay your filter adds. A lower cutoff makes a smoother signal but adds more lag—find the perfect balance for your control loop!
*   **Freezing**: If the UI stops responding due to extreme math, click the **Refresh/Reset** icon in the File menu or the sidebar header.

---
Designed by **Mehdi Sehati** 
[LinkedIn Profile](https://www.linkedin.com/in/mehdi-sehati-44356bb1/)
