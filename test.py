import os
import whisper
import torch

gpu = "cuda" if torch.cuda.is_available() else "cpu"
import os
os.environ["WHISPER_CACHE_DIR"] = r"C:\path\to\whisper\cache"

# Load Whisper model
try:
    whisper_model = whisper.load_model("small", device=gpu)
    print("Whisper model loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")

# Define file path
test_file = r"D:\sample1.mp3"
absolute_path = os.path.abspath(test_file)
print(f"Whisper is trying to access: {absolute_path}")
print("Absolute Path:", absolute_path)

# Check file existence and accessibility
if os.path.exists(test_file):
    print("File exists and is accessible.")
else:
    print("File does not exist or is inaccessible.")
    exit(1)

if not os.access(absolute_path, os.R_OK):
    print(f"File is not readable: {absolute_path}")
    exit(1)

# Attempt transcription
try:
    result = whisper_model.transcribe(absolute_path, verbose=True)
    print("Sample transcription result:", result["text"])
except Exception as e:
    print(f"Error in Whisper model: {e}")
