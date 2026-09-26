#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from argparse import ArgumentParser

from sources import sources

sys.stdout.reconfigure(encoding="utf-8")


parser = ArgumentParser()
parser.add_argument("item", type=str, choices=["source"])
args = parser.parse_args()

assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources

source = sources[episode]


if args.item == "source":
    assert source.source
    print(source.source.as_posix(), end="")
