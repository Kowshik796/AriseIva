import sys
from pathlib import Path

# Add root directory and backend paths to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

speech_dir = root_dir / "backend" / "speechtosign"
if str(speech_dir) not in sys.path:
    sys.path.insert(0, str(speech_dir))

sign_dir = root_dir / "backend" / "signtospeech"
if str(sign_dir) not in sys.path:
    sys.path.insert(0, str(sign_dir))

from app import app
