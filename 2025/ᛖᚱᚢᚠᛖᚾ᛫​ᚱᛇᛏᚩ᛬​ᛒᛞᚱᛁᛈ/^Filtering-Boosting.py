from vsdenoise import DFTTest
from vstools import core, depth, DitherType, initialize_clip, SPath


import os

source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")

src = core.bs.VideoSource(source_file)
src = initialize_clip(src)


dn = DFTTest().denoise(src, {0.0:0.3, 0.4:0.4, 0.6:1.0, 1.0:1.0}, planes=[0])
dn = DFTTest().denoise(dn, {0.0:0.1, 0.4:0.2, 0.6:0.5, 1.0:0.5}, planes=[1, 2])


final = depth(dn, 10, dither_type=DitherType.NONE)


final.set_output()
