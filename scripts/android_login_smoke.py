"""Enter ONLY the disposable local development account on the test emulator.

Run after opening the login sheet and observing its username field position.
Never prints passwords, tokens or input command arguments.
"""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
credentials = json.loads((root / ".local/android/credentials.json").read_text())


def adb(*args):
    result = subprocess.run(["adb", "-s", "emulator-5554", *args], capture_output=True)
    if result.returncode:
        raise RuntimeError("ADB smoke action failed; inspect the emulator")


adb("shell", "input", "tap", "540", "1645")
adb("shell", "input", "text", "student_demo")
adb("shell", "input", "keyevent", "61")
adb("shell", "input", "text", credentials["users"]["student_demo"])
adb("shell", "input", "keyevent", "66")
print("Disposable development credentials entered; verify the resulting app state.")
