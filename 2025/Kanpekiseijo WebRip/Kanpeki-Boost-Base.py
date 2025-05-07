#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.getcwd())

import dfttest2
from vstools import core, depth, initialize_clip, SPath, vs


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")


src = core.bs.VideoSource(source_file)
src = initialize_clip(src)
src = dfttest2.DFTTest(src, slocation=[0.0,0.38, 0.4,0.38, 0.6,0.21, 1.0,0.21], tbsize=1, planes=[0])
src = depth(src, 10)
src.set_output()
