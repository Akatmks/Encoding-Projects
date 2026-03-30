import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsdeband import pfdeband, placebo_deband
from vsdenoise import DFTTest
from muxtools import Setup
from vsmuxtools import settings_builder_x264, x264
from vstools import core, DitherType, finalize_clip, initialize_clip, SPath, vs


from sources import sources

assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources

print(f"Source: \t{sources[episode].source.name}")
src = src_sd = initialize_clip(core.bs.VideoSource(sources[episode].source))


dn = DFTTest().denoise(src, {0.0:0.45, 0.4:0.60, 0.6:12.00, 1.0:15.00}, planes=[0])
dn = DFTTest().denoise(dn, {0.0:0.08, 0.4:0.10, 0.6:1.00, 1.0:1.20}, planes=[1, 2])

db = pfdeband(dn, thr=1.3, debander=placebo_deband)

final = finalize_clip(db, bits=8, dither_type=DitherType.NONE)

final = final.assrender.TextSub(sources[episode].source_sub, fontdir="Fonts")


if "__main__" in dir(__main__):
    setup = Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")

    output = SPath("Encode") / f"{episode}.264"

    settings = settings_builder_x264(threads=24, bframes=8,
                                     crf=17.777777, mbtree=True,
                                     dct_decimate=True, cqmfile="M4G_High_Detail_V3.1.qm", deblock=[0, 0])
    x264 = x264(settings, qp_clip=src_sd, resumable=False).encode(final, outfile=output)
else:
    final.set_output()
