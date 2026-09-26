#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from argparse import ArgumentParser

from sources_ova import ova_source as source

sys.stdout.reconfigure(encoding="utf-8")


parser = ArgumentParser()
parser.add_argument("item", type=str, choices=["source"])
args = parser.parse_args()


if args.item == "source":
    assert source.source
    print(source.source.as_posix(), end="")
