#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from argparse import ArgumentParser

from encode import intermediate
from filterchain import cache_intermediate, intermediate_filterchain
from sources import sources


parser = ArgumentParser()
parser.add_argument("episode", type=str, nargs="?", default=None)
args = parser.parse_args()
if args.episode is not None:
    episode = args.episode
else:
    assert "EPISODE" in os.environ, "You need to pass the episode to encode via commandline parameters, or via environmental variable \"EPISODE\""
    episode = os.environ["EPISODE"]
assert episode in sources


final = intermediate_filterchain(episode)

if "__main__" in dir(__main__):
    intermediate(episode, final)
    cache_intermediate(episode)
else:
    final.set_output()
