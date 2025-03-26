# 🎛️ freaky_Looper - Real-Time Audio Looper with FX

![Demo Screenshot](screenshot.png) *(optional image)*

A feature-rich audio looper with live effects processing, built for musicians and sound artists. Record, layer, and transform loops in real-time with Python.

## 🌟 Features
- **Multi-track looping** with overdubbing
- **Real-time FX chain**:
  - Reverb (decay/wet control)
  - Noise Gate (threshold/attack/release)
  - Pitch Shifting (-24 to +24 semitones)
- **Session recording** (export to WAV)
- **Smart routing** between loops and effects
- **Adjustable loop lengths** (1-10 seconds)
- **Mute/Solo** per track

## 🛠️ Tech Stack
- `sounddevice` - Low-latency audio I/O
- `wxPython` - Cross-platform GUI
- `numpy/scipy` - Audio processing
- Python 3.7+ (CPython recommended)

## 🚀 Installation

### Prerequisites
- **Audio Interface** (ASIO recommended for Windows)
- **Python 3.7+**

### Quick Start
```bash
git clone https://github.com/mtrpntre/freaky_Looper.git
cd freaky_Looper
pip install -r requirements.txt
python main.py