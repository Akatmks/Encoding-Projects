#!/usr/bin/env python3

from pathlib import Path
import argparse
import os
import re
import subprocess
import tomllib

file_dir = Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument("--cpu-usage", type=float)
parser.add_argument("directory", type=Path)
args = parser.parse_args()

main_dir = args.directory
temp_dir = main_dir / "Temp"
output_dir = main_dir / "Output"

temp_dir.mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)

for main_file in main_dir.iterdir():
    if (match := re.match(r"\[izu\] Elfen Lied - ([\w\(\) ]+) \[\w\wBD-Remux\] \[\w+\].mkv", main_file.name)):
        name = match.group(1)
        output_file = output_dir / (name + ".mkv")
        if not output_file.exists():
            env = dict(os.environ)
            env["SOURCE_FILE"] = str(main_file)
            if args.cpu_usage is not None:
                env["USAGE"] = str(args.cpu_usage)
            

            zones_string = ""
            toml_file = main_file.with_suffix(".toml")
            assert toml_file.exists()
            with toml_file.open("rb") as f:
                toml = tomllib.load(f)
            if "OP" in toml:
                env["OP_START"] = str(toml["OP"]["start"])
                env["OP_END"] = str(toml["OP"]["end"])
                zones_string += f" {toml["OP"]["start"]} {toml["OP"]["end"]} OP"
            if "ED" in toml:
                env["ED_START"] = str(toml["ED"]["start"])
                env["ED_END"] = str(toml["ED"]["end"])
                zones_string += f" {toml["ED"]["start"]} {toml["ED"]["end"]} ED"


            commands = ["python", file_dir / "^Progression-Boost.py",
                        "--temp", temp_dir / (name + ".boost.tmp"),
                        "--resume",
                        "--input", main_file,
                        "--encode-input", file_dir / "^Filtering-Boosting.py",
                        "--zones-string", zones_string,
                        "--output-scenes", temp_dir / (name + ".scenes.json"),
                        "--output-roi-maps", temp_dir / (name + ".roi-maps")
                       ]
            subprocess.run(commands, env=env, text=True)

            if not (temp_dir / (name + ".scenes.json")).exists() or \
               not (temp_dir / (name + ".roi-maps")).exists():
                print(f"Boosting exited unexpectedly for \"{main_file.name}\".")
                print(f"Skipping encoding for the file.")

                continue


            print("The next command is a failsafe, and it's normal for the next command to fail.")
            commands = ["python", file_dir / "^Server-Shutdown.py"]
            subprocess.run(commands, env=env, text=True)

            commands = ["python", file_dir / "^Server.py"]
            subprocess.Popen(commands, env=env, text=True)

            commands = ["av1an", "-y",
                        "--temp", temp_dir / (name + ".tmp"),
                        "--resume",
                        "--keep",
                        "--verbose",
                        "-i", file_dir / "^Filtering.py",
                        "-o", output_dir / (name + ".mkv"),
                        "--scenes", temp_dir / (name + ".scenes.json"),
                        "--chunk-method", "bestsource",
                        "--pix-format", "yuv420p10le",
                        "--workers", "6",
                        "--encoder", "svt-av1",
                        "--no-defaults",
                        "--video-params", "Thank you, Altair!",
                        "--concat", "mkvmerge"
                       ]
            subprocess.run(commands, env=env, text=True)
                       
            commands = ["python", file_dir / "^Server-Shutdown.py"]
            subprocess.run(commands, env=env, text=True)

            if not (temp_dir / (name + ".scenes.json")).exists() or \
               not (temp_dir / (name + ".roi-maps")).exists():
                print(f"Encoding exited unexpectedly for \"{main_file.name}\".")

                continue
