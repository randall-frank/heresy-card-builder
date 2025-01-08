import os
import subprocess

from setuptools import setup


def rebuild_qt_resources() -> None:
    repo_dir = os.path.dirname(__file__)
    if not os.path.isdir(os.path.join(repo_dir, "media")):
        return

    prev_cwd = os.getcwd()
    os.chdir("src/heresycardbuilder")

    try:
        print("compiling qt resource files...")
        rcc_cmd = [
            "pyside6-rcc",
            "card_editor_res.qrc",
            "-o",
            "card_editor_res_rc.py",
        ]
        subprocess.run(rcc_cmd)

        print("compiling qt ui files...")
        uic_cmd = [
            "pyside6-uic",
            "card_editor_main.ui",
            "-o",
            "ui_card_editor_main.py",
        ]
        subprocess.run(uic_cmd)

    finally:
        os.chdir(prev_cwd)


rebuild_qt_resources()
setup()
