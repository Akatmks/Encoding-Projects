import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsdeband import pfdeband, placebo_deband
from vsdenoise import deblock_qed, DFTTest, frequency_merge, MotionMode, MVTools, Prefilter, SADMode
from vskernels import Hermite
from vsmuxtools import settings_builder_5fish_svt_av1_psy, Setup, SVTAV1
from vsrgtools import bilateral, MeanMode
from vstools import core, finalize_clip, initialize_clip, SPath


# src_399 = initialize_clip(core.bs.VideoSource("Sources/399.mp4", showprogress=False))
# src_248 = initialize_clip(core.bs.VideoSource("Sources/248.webm", showprogress=False))
src_137 = src_sd = initialize_clip(core.bs.VideoSource("Sources/137.mp4", showprogress=False))
src_400 = initialize_clip(core.bs.VideoSource("Sources/400.mp4", showprogress=False))
src_400 = Hermite().scale(src_400, 1920, 1080)
src_271 = initialize_clip(core.bs.VideoSource("Sources/271.webm", showprogress=False))
src_271 = Hermite().scale(src_271, 1920, 1080)
src_401 = initialize_clip(core.bs.VideoSource("Sources/401.mp4", showprogress=False))
src_401 = Hermite().scale(src_401, 1920, 1080)
src_313 = initialize_clip(core.bs.VideoSource("Sources/313.webm", showprogress=False))
src_313 = Hermite().scale(src_313, 1920, 1080)


db_137 = deblock_qed(src_137, (28, 30))


def low_mean(clips, **kwargs):
    return MeanMode.ARITHMETIC(clips[1:], **kwargs)
def high_adder(clips, **_):
    return core.llvmexpr.Expr(clips, """
xabs = abs($x - 32768)
yabs = abs($y - 32768)
zabs = abs($z - 32768)
aabs = abs($a - 32768)
babs = abs($b - 32768)
xsign = $x >= 32768 ? 1 : -1
ysign = $y >= 32768 ? 1 : -1
zsign = $z >= 32768 ? 1 : -1
asign = $a >= 32768 ? 1 : -1
bsign = $b >= 32768 ? 1 : -1
xpow = copysign(xabs ** 5, xsign)
ypow = copysign(yabs ** 5, ysign)
zpow = copysign(zabs ** 5, zsign)
apow = copysign(aabs ** 5, asign)
bpow = copysign(babs ** 5, bsign)
sum = (xpow + ypow + zpow + apow + bpow) * 0.5
sumabs = abs(sum)
sumsign = sum >= 0 ? 1 : -1
RESULT = copysign(sumabs ** 0.2, sumsign) + 32768
""", infix=1)

merge = frequency_merge(db_137, src_400, src_271, src_401, src_313,
                        lowpass=lambda clip: bilateral(clip, sigmaR=0.03),
                        mode_low=low_mean, mode_high=high_adder)

             
mv = MVTools(merge, search_clip=Prefilter.DFTTEST)

mv.analyze(tr=2, blksize=32, overlap=16, truemotion=MotionMode.COHERENCE, divide=2)
mv.recalculate(thsad=40, blksize=8, overlap=4, dct=SADMode.ADAPTIVE_SATD_DCT, truemotion=MotionMode.COHERENCE)

dg = mv.degrain(merge, merge, tr=2, thsad=40)


db = pfdeband(dg, radius=2.2, debander=placebo_deband, dark_thr=0.4, bright_thr=0.4, elast=1.9)


final = finalize_clip(db)


if "__main__" in dir(__main__):
    Setup("00", config_file=None, work_dir=SPath("Temp") / f"vsmuxtools.tmp")

    output = SPath("Video") / f"encode.ivf"
    fgs_table = SPath("grain.tbl")

    settings = settings_builder_5fish_svt_av1_psy(
        preset=2,
        crf=11.00,
        lineart_psy_bias=7,
        texture_psy_bias=7,
        satd_bias=0.50,
        dlf_bias_max_dlf="2,0",
        dlf_sharpness=7,
        texture_cdef_bias_max_cdef="0,0,0,0",
        fgs_table=str(fgs_table)
    )
    SVTAV1(**settings, sd_clip=src_sd).encode(final, outfile=output)
else:
    final.set_output()
