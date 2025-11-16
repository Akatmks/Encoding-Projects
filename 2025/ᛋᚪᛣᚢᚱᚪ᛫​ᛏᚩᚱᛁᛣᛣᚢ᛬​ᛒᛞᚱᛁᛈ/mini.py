#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

from vstools import core, DitherType, finalize_clip, initialize_clip, SPath
from vsdeband import pfdeband, placebo_deband
from vsdenoise import DFTTest

assert "EPISODE" in os.environ, "You need to pass the episode to encode via commandline parameters, or via environmental variable \"EPISODE\""
episode = os.environ["EPISODE"]


src = core.ffms2.Source(SPath("Intermediate") / f"{episode}.mkv",
                        cachefile=SPath("Intermediate") / f"{episode}.mkv.ffindex")
src = initialize_clip(src)

final_dn = DFTTest().denoise(src, {0.0:0.54, 0.4:0.48, 0.5:0.24, 0.6:0.48, 0.8:0.48, 0.9:0.24, 1.0:0.24}, tr=1)

final_db = pfdeband(final_dn, thr=2.1, radius=22, debander=placebo_deband)

final = finalize_clip(final_db, dither_type=DitherType.ATKINSON)


# ---------------------------------------------------------------------
# Set the port used by the dispatch server. You can set it to any port
# of your preference, as long as you set it the same in `Server.py`,
# `Server-Shutdown.py` and your filtering vpy script.
port = 18861
# ---------------------------------------------------------------------
# Copy every line in this file to your filtering vpy script. The
# optimal place to paste this is after you've imported vapoursynth and
# all the vsfunc's, and after you've loaded the source file, but before
# any filtering using VRAM is created / performed.
# ---------------------------------------------------------------------

import rpyc
import time

c = rpyc.connect("localhost", port)
tid = c.root.register()
while not c.root.request_release(tid):
    time.sleep(0.1)


final.set_output()
