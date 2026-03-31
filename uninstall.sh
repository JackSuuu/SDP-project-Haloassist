#!/usr/bin/env bash

echo "This will remove:"
echo "  - .venv/ (Python virtual environment)"
echo "  - *.gguf (LLM model file)"
echo "  - *.ts (CLIP model file)"
echo "  - perception/models/ (vosk speech model)"
echo "  - ~/Library/Application Support/Ultralytics/ (Ultralytics cache)"
echo "  - ~/.cache/huggingface/ (Hugging Face download cache)"
echo ""
read -p "Continue? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

rm -rf .venv
echo "Removed .venv/"

rm -f *.gguf *.ts
echo "Removed model file(s)"

rm -rf perception/models
echo "Removed vosk speech model"

rm -rf ~/Library/Application\ Support/Ultralytics
echo "Removed Ultralytics cache"

rm -rf ~/.cache/huggingface
echo "Removed Hugging Face cache"

echo ""
echo "Done. The project folder and git history are untouched."
