#!/usr/bin/env bash
set -e

# Switch to fix-blur branch if not already on it
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "fix-blur" ]; then
  echo "Switching to fix-blur branch..."
  git checkout fix-blur
fi

# Create venv if it doesn't exist, then activate it
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r perception/requirements.txt
pip install -r visualization/requirements.txt
pip install "huggingface_hub[cli]"
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python

# Download model if not present
MODEL="functiongemma-270M-vosk-extractor-Q8_0-LoRA.gguf"
if [ ! -f "$MODEL" ]; then
  echo "Downloading model (this may take a moment)..."
  python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='CPryor/functiongemma-270M-vosk-extractor-Q8_0-LoRA', filename='$MODEL', local_dir='.')"
fi

# Download vosk speech model if not present
VOSK_MODEL_DIR="perception/models/vosk-model-small-en-us-0.15"
if [ ! -d "$VOSK_MODEL_DIR" ]; then
  echo "Downloading vosk speech model (~40MB)..."
  mkdir -p perception/models
  curl -L "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -o perception/models/vosk-model.zip
  unzip -q perception/models/vosk-model.zip -d perception/models/
  rm perception/models/vosk-model.zip
fi

# Launch each process in its own Terminal window so keyboard input works
PROJECT_DIR="$(pwd)"
VENV_ACTIVATE="$PROJECT_DIR/.venv/bin/activate"

echo "Opening Terminal windows..."

osascript <<EOF
tell application "Terminal"
    do script "cd '$PROJECT_DIR' && source '$VENV_ACTIVATE' && python visualization/server.py"
    do script "cd '$PROJECT_DIR' && source '$VENV_ACTIVATE' && python perception/src/main.py"
    activate
end tell
EOF

echo "Started. Two Terminal windows opened."
echo "  - Visualization: http://localhost:8000"
echo "  - Perception: hold 'b' and speak to set target"
