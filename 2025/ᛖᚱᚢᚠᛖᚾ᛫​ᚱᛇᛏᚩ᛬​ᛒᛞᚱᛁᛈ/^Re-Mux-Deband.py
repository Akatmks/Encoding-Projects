#!/usr/bin/env python3

import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("file", type=Path)
args = parser.parse_args()

video_file = args.file
temp_dir = video_file.parent.parent / "Temp" / (video_file.stem + ".tmp")

assert (temp_dir / "encode" / "00000.ivf").exists()

command = ["mkvmerge", "--output", video_file, "["]

for chunk in sorted((temp_dir / "encode").iterdir()):
    command += [chunk]

command += ["]"]

subprocess.run(command)
