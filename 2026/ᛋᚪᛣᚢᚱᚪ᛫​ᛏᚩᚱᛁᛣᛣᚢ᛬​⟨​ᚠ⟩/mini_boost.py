#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from vstools import core, SPath

assert "EPISODE" in os.environ, "You need to pass the episode to encode via commandline parameters, or via environmental variable \"EPISODE\""
episode = os.environ["EPISODE"]

src = core.ffms2.Source(SPath("Intermediate") / f"{episode}.mkv",
                        cachefile=SPath("Intermediate") / f"{episode}.mkv.ffindex")

src.set_output()
