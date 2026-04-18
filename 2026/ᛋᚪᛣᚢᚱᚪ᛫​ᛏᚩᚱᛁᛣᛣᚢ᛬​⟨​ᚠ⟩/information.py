#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from argparse import ArgumentParser

from sources import sources

sys.stdout.reconfigure(encoding="utf-8")


parser = ArgumentParser()
parser.add_argument("item", type=str, choices=["source", "trim_start"])
parser.add_argument("episode", type=str)
args = parser.parse_args()
episode = args.episode
assert episode in sources


if args.item == "source":
    print(sources[episode].source.as_posix(), end="")
elif args.item == "trim_start":
    print(sources[episode].trim[0], end="")
