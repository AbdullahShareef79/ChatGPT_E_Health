"""
Helper script to install PyAudio on Windows
Downloads pre-compiled wheel from unofficial Windows binaries
"""

import sys
import subprocess
import platform

def get_python_version():
    """Get Python version for wheel selection"""
    version = sys.version_info
    return f"cp{version.major}{version.minor}"

def get_architecture():
    """Detect if Python is 32-bit or 64-bit"""
    return "win_amd64" if sys.maxsize > 2**32 else "win32"

def install_pyaudio():
    """Install PyAudio using pre-compiled wheel"""
    print("🔧 Installing PyAudio for Windows...")
    print(f"Python version: {sys.version}")
    print(f"Architecture: {get_architecture()}")
    
    py_version = get_python_version()
    arch = get_architecture()
    
    # PyAudio wheel URL (from unofficial Windows binaries)
    wheel_url = f"https://download.lfd.uci.edu/pythonlibs/archived/PyAudio-0.2.11-{py_version}-{py_version}m-{arch}.whl"
    
    print(f"\n📥 Downloading PyAudio wheel...")
    print(f"URL: {wheel_url}\n")
    
    try:
        # Try installing from wheel
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", wheel_url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ PyAudio installed successfully!")
            print("\nYou can now use the microphone in the simulation.")
            print("Run: python simulation_gui.py")
        else:
            print("❌ Installation failed. Trying alternative method...")
            print("\nTry manual installation:")
            print(f"1. Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
            print(f"2. Look for: PyAudio‑0.2.11‑{py_version}‑{py_version}‑{arch}.whl")
            print(f"3. Run: pip install PyAudio‑0.2.11‑{py_version}‑{py_version}‑{arch}.whl")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📝 Alternative: Use text input (works perfectly!)")
        print("   The robot will still speak to you via TTS.")

if __name__ == "__main__":
    install_pyaudio()

