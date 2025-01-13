import subprocess
import sys

import heresycardbuilder


def test_version() -> None:
    cmd = [sys.executable, "-m", "heresycardbuilder.build_deck", "--version"]
    output = subprocess.run(cmd, capture_output=True)
    text = output.stdout.decode("ascii")
    assert "build_deck" in text
    assert str(heresycardbuilder.__version__) in text
