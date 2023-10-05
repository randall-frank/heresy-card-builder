import os
import subprocess
import sys

# get the executable names
root = os.path.dirname(sys.executable)
rcc = os.path.join(root, "scripts", "pyside6-rcc")
uic = os.path.join(root, "scripts", "pyside6-uic")

print("Compiling resource file...")
rcc_cmd = [rcc, "card_editor_res.qrc", "-o", "card_editor_res_rc.py"]
subprocess.run(rcc_cmd)

print("Compiling ui file...")
uic_cmd = [uic, "card_editor_main.ui", "-o", "ui_card_editor_main.py"]
subprocess.run(uic_cmd)
