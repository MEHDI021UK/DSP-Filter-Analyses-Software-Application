import numpy as np
from scipy import signal
try:
    import pywt
except ImportError:
    pywt = None
try:
    from filterpy.kalman import KalmanFilter
except ImportError:
    KalmanFilter = None

def apply_kalman_filter(data, process_noise=1e-5, measurement_noise=1e-2):
    """
    Kalman Filter for 1D signal.
    Data: 1D array of measurements.
    """
    if KalmanFilter is None:
        return data
    
    n = len(data)
    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.x = np.array([[data[0]]]) # Initial state
    kf.F = np.array([[1.]])      # State transition matrix
    kf.H = np.array([[1.]])      # Measurement function
    kf.P *= 10.                  # Covariance matrix
    kf.R = measurement_noise     # Measurement noise
    kf.Q = process_noise         # Process noise
    
    filtered = np.zeros(n)
    for i in range(n):
        kf.predict()
        kf.update(data[i])
        filtered[i] = kf.x[0, 0]
    return filtered

def apply_savgol_filter(data, window_length=11, polyorder=2):
    """
    Savitzky-Golay filter.
    Best for smoothing data while preserving features.
    """
    # window_length must be odd and > polyorder
    if window_length % 2 == 0:
        window_length += 1
    if window_length <= polyorder:
        window_length = polyorder + 1
        if window_length % 2 == 0: window_length += 1
        
    return signal.savgol_filter(data, window_length, polyorder)

def apply_median_filter(data, kernel_size=3):
    """
    Median filter for spike removal.
    """
    if kernel_size % 2 == 0:
        kernel_size += 1
    return signal.medfilt(data, kernel_size)

def apply_wavelet_denoising(data, wavelet='db4', level=2):
    """
    Wavelet denoising using soft thresholding.
    """
    if pywt is None:
        return data
    
    coeffs = pywt.wavedec(data, wavelet, level=level)
    # Estimate noise standard deviation (using Median Absolute Deviation of highest frequency subband)
    sigma = (1/0.6745) * np.median(np.abs(coeffs[-1] - np.median(coeffs[-1])))
    # Universal threshold
    uthresh = sigma * np.sqrt(2 * np.log(len(data)))
    # Soft thresholding
    new_coeffs = [coeffs[0]] + [pywt.threshold(c, value=uthresh, mode='soft') for c in coeffs[1:]]
    return pywt.waverec(new_coeffs, wavelet)

def apply_lms_filter(data, mu=0.01, order=32):
    """
    LMS Adaptive Filter (Self-Correction / Prediction mode if no reference).
    Here we use data[n-1] to predict data[n].
    """
    n = len(data)
    weights = np.zeros(order)
    output = np.zeros(n)
    error = np.zeros(n)
    
    # Using the data to predict itself (1-step ahead prediction for noise cancellation demo)
    for i in range(order, n):
        x = data[i-order:i][::-1] # Input vector (previous samples)
        y = np.dot(weights, x)
        e = data[i] - y
        weights = weights + 2 * mu * e * x
        output[i] = y
        error[i] = e
        
    return output

def get_complex_filter_info(filter_type):
    info = {
        "Kalman": "Best for: Real-time sensor smoothing and prediction.\nData Type: Linear time-series with Gaussian noise.\nKey Params: Process Noise (Q) and Measurement Noise (R).",
        "Savitzky-Golay": "Best for: Smoothing numerical data without losing peak information.\nData Type: Values with high-frequency noise.\nKey Params: Window length and Polynomial order.",
        "Median": "Best for: Removing 'spikes' or 'salt and pepper' noise from sensor data.\nData Type: Signals with outliers.\nKey Params: Kernel size (odd integer).",
        "Wavelet": "Best for: Advanced denoising where noise and signal frequencies overlap.\nData Type: Non-stationary signals (ECG, audio).\nKey Params: Wavelet type (db1-db38) and Level.",
        "Adaptive (LMS)": "Best for: Cancelling periodic noise or acoustic echoes.\nData Type: Noise-corrupted signals.\nKey Params: Learning rate (Step size) and Filter order."
    }
    return info.get(filter_type, "Standard DSP filtering.")
