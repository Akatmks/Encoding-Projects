#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from argparse import ArgumentParser

from sources import sources

sys.stdout.reconfigure(encoding="utf-8")


parser = ArgumentParser()
parser.add_argument("item", type=str, choices=["source_web", "source_bd"])
parser.add_argument("episode", type=str)
args = parser.parse_args()
episode = args.episode
assert episode in sources


if args.item == "source_web":
    print(sources[episode].source_web.as_posix(), end="")
elif args.item == "source_bd":
    print(sources[episode].source_bd.as_posix(), end="")
