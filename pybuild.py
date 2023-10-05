#
# T.I.M.E Stories card editor
# Copyright (C) Randall Frank
# See LICENSE for details
#
import argparse
import os
import platform
import subprocess
import sys

generated_files = ("card_editor_res_rc.py", "ui_card_editor_main.py")


def get_app(name: str) -> str:
    if platform.system().startswith("Win"):
        pydir = os.path.dirname(sys.executable)
        return os.path.join(pydir, "Scripts", name)
    else:
        return name


def run_command(appname: str, args: list):
    app = get_app(appname)
    cmd = [app]
    cmd.extend(args)
    print("Running:", cmd)
    ret = subprocess.run(cmd, capture_output=True, text=True)
    print(ret.stdout)


def precommit() -> None:
    print(f"== precommit {'='*10}")
    # isort
    args = ["."]
    for filename in generated_files:
        args.extend(["--skip", filename])
    run_command("isort", args)
    # flake8
    exclude = "--exclude=" + ",".join(generated_files)
    args = [".", exclude, "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"]
    run_command("flake8", args)
    args = [".", exclude, "--count", "--exit-zero", "--max-line-length=127", "--statistics"]
    run_command("flake8", args)


def build() -> None:
    print(f"== build {'='*10}")
    run_command("pyside6-rcc", ["card_editor_res.qrc", "-o", "card_editor_res_rc.py"])
    run_command("pyside6-uic", ["card_editor_main.ui", "-o", "ui_card_editor_main.py"])


def run() -> None:
    print(f"== run {'='*10}")
    cmd = [sys.executable, "card_editor.py"]
    subprocess.run(cmd)


def clean() -> None:
    print(f"== clean {'='*10}")
    for filename in generated_files:
        try:
            os.remove(filename)
        except OSError:
            pass


parser = argparse.ArgumentParser(description="Build the cardbuilder application.")
parser.add_argument("command", type=str, choices=["build", "precommit", "clean", "run"], help="The build command to execute")

args = parser.parse_args()
if args.command == "build":
    build()
elif args.command == "precommit":
    precommit()
elif args.command == "clean":
    clean()
elif args.command == "run":
    run()

sys.exit(0)
