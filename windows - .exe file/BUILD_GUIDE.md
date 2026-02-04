# 📦 Windows Executable Generation Guide

This folder contains the automated tools required to package the **Advanced DSP Studio Pro** into a standalone `.exe` file for Windows.

---

## 🚀 Quick Start (One-Click)

The easiest way to generate a new executable is to simply run the provided batch script:

1.  Open the `exeGEN` folder.
2.  Double-click **`build_exe.bat`**.
3.  Wait for the process to complete (it usually takes 1-2 minutes).
4.  Once finished, your final application will be located in the **`dist`** folder.

---

## 🛠️ How it Works

The generation process uses **PyInstaller** and relies on two main components in this folder:

### 1. `build_exe.bat` (The Automator)
This script performs several critical tasks:
*   **Environment Verification**: Checks if Python and PyInstaller are correctly installed.
*   **Cleanup**: Removes previous `build` and `dist` folders to ensure a fresh, clean compilation.
*   **Compilation**: Executes the PyInstaller engine using the project's specific `.spec` configuration.
*   **Error Handling**: Provides real-time feedback if any dependency is missing or if the build fails.

### 2. `advanced_dsp_studio.spec` (The Blueprint)
This is the configuration file for the build. It contains instructions for:
*   **Path Mapping**: Correctly linking the source code from the parent directory.
*   **Custom UI Support**: Explicitly collecting and bundling the `customtkinter` assets.
*   **Executable Properties**: Setting the app name, icon (if applicable), and disabling the console window for a professional GUI experience.

---

## ⚠️ Troubleshooting

### "PyInstaller not found"
The batch script will attempt to install it for you automatically. If it fails, open your terminal and run:
```bash
pip install pyinstaller
```

### "Access Denied" or Permissions Errors
Ensure that the `dist` or `build` folders (or the `.exe` itself) are not currently open in another window or running in the background while you try to build.

### Anti-Virus Warnings
Some Windows Anti-Virus software may flag a freshly built `.exe` as "unrecognized." This is normal for unsigned custom scripts. You can safely "Run Anyway" or add the `dist` folder to your exceptions list.

---
Designed by **Mehdi Sehati** 
