#!/usr/bin/env python3

from vsdenoise import BM3D
import dfttest2
from vsdehalo import edge_cleaner
import os
from vstools import core, depth, initialize_clip, SPath


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
lwi_file = SPath(os.environ["LWI_FILE"])

src = core.lsmas.LWLibavSource(source_file, cachefile=lwi_file)
src = initialize_clip(src)


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


ref = dfttest2.DFTTest(src, slocation=[0.00,0.0, 0.35,0.0, 0.39,5.0, 0.43,40.0, 1.00,40.0], tbsize=1)
dn = BM3D(src, sigma=0.33, refine=2, ref=ref).final()
dh = edge_cleaner(dn, strength=8, rmode=16)


out = dh

out = depth(out, 10)
out.set_output()
