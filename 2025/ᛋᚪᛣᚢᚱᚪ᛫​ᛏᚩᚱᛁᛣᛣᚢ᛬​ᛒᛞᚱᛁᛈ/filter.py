import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from argparse import ArgumentParser
from vstools import SPath

from intermediate import encode_intermediate
from filterchain import filterchain


parser = ArgumentParser()
parser.add_argument("episode", type=str, nargs="?", default=None)
args = parser.parse_args()
if args.episode is not None:
    episode = args.episode
else:
    assert "EPISODE" in os.environ, "You need to pass the episode to encode via commandline parameters, or via environmental variable \"EPISODE\""
    episode = SPath(os.environ["EPISODE"])


filterchain_results = filterchain(episode)

if "__main__" in dir(__main__): 
    encode_intermediate(episode, filterchain_results)
else:
    filterchain_results.final.set_output()
