#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from vstools import core, DitherType, finalize_clip, initialize_clip
from vsdenoise import DFTTest

assert "EPISODE" in os.environ, "You need to pass the episode to encode via commandline parameters, or via environmental variable \"EPISODE\""
episode = os.environ["EPISODE"]


src = core.ffms2.Source(SPath("Intermediate") / f"{episode}.mkv",
                        cachefile=SPath("Intermediate") / f"{episode}.mkv.ffms2")
src = initialize_clip(src)

final_dn = DFTTest().denoise(src, {0.0:0.52, 0.4:0.36, 0.5:0.24, 0.7:0.20, 1.0:0.12}, tr=0)

final = finalize_clip(final_dn, dither_type=DitherType.NONE)

final.set_output()
