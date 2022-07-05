
import os
from distutils.core import setup

REQUIREMENTS = [line.strip() for line in open("requirements.txt").readlines()]

curr_dir = os.path.abspath(os.path.dirname(__file__))


def get_file_text(file_name):
    with open(os.path.join(curr_dir, file_name), "r", encoding="utf-8") as in_file:
        return in_file.read()


version = {}
_version_file = os.path.join(curr_dir, "_version.py")
with open(_version_file) as fp:
    exec(fp.read(), version)


setup(name='heresy-card-builder',
      version=version["VERSION"],
      description='GUI tool for creating T.I.M.E Stories card decks',
      author='Randall Frank',
      author_email='frogboots.000@gmail.com',
      url='https://github.com/randall-frank/heresy-card-builder',
      project_urls={'Information': 'http://heresy.mrtrashcan.com/'},
      packages=['distutils', 'distutils.command'],
      python_requires=">=3.8",
      license="MIT",
      package_dir={"": "src"},
      long_description=get_file_text("README.md"),
      long_description_content_type="text/markdown",
      install_requires=REQUIREMENTS,
      )
