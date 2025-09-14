@echo off
echo Setting up RAG service with GPU support...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install CPU-only dependencies first
echo Installing base dependencies...
pip install -r requirements.txt

REM Check for NVIDIA GPU and install appropriate PyTorch
echo Checking for GPU support...
python -c "
import subprocess
import sys

try:
    # Try to detect NVIDIA GPU
    result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
    if result.returncode == 0:
        print('NVIDIA GPU detected, installing CUDA PyTorch...')
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch', 'torchvision', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cu118'], check=True)
    else:
        print('No NVIDIA GPU detected, installing CPU-only PyTorch...')
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch', 'torchvision', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cpu'], check=True)
except FileNotFoundError:
    print('nvidia-smi not found, installing CPU-only PyTorch...')
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch', 'torchvision', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cpu'], check=True)
except Exception as e:
    print(f'Error during PyTorch installation: {e}')
    print('Installing CPU-only PyTorch as fallback...')
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch', 'torchvision', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cpu'], check=True)
"

echo Setup complete! GPU support is now available.
echo Run 'python main.py' to start the server.
pause