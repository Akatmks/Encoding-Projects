#!/usr/bin/env python3

import dfttest2
import os
from vstools import core, depth, initialize_clip, SPath


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")
lwi_file = SPath(os.environ["LWI_FILE"])

src = core.lsmas.LWLibavSource(source_file, cachefile=lwi_file)
src = initialize_clip(src)


dn = dfttest2.DFTTest(src, slocation=[0.00,0.1, 0.35,0.1, 0.39,5.0, 0.43,20.0, 1.00,20.0], tbsize=1, planes=[0])


out = dn

out = depth(out, 10)
out.set_output()
