import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsdeband import pfdeband
from vsdenoise import DFTTest, frequency_merge, MotionMode, MVTools, Prefilter, prefilter_to_full_range, SADMode
from functools import partial
from vskernels import Hermite, Spline16
from lvsfunc import LHzDelowpass
from vsmasktools import Morpho, XxpandMode
from vsmuxtools import Setup, SVTAV1
import vsmlrt
from rekt import rektlvls
from vsrgtools import bilateral, fast_line_darken, gauss_blur
from vsscale import Rescale
from vstools import core, depth, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, join, replace_ranges, Sar, SPath, vs

from sources_ova import ova_source as source



print(f"Source: \t{source.source.name}")
src = initialize_clip(core.bs.VideoSource(source.source, showprogress=False))
src = src.std.AssumeFPS(fpsnum=24000, fpsden=1001)
src = src_sd = Sar(numerator=6, denominator=5).apply(src)



bore = join(rektlvls(get_y(src), colnum=[714, 715, 717, 718, 719], colval=[-2, 1, -7, 6, 23]), src)



dlp = LHzDelowpass.DoubleTaps_4_4_125_1375_mpeg2().apply(bore)

var_mask = core.akarin.Expr([get_y(dlp), get_y(bore)], """
x[-1,-1] dup * x[0,-1] dup * x[1,-1] dup * 
x[-1,0]  dup * x[0,0]  dup * x[1,0]  dup * 
x[-1,1]  dup * x[0,1]  dup * x[1,1]  dup * 
+ + + + + + + + 9 /
x[-1,-1] x[0,-1] x[1,-1] 
x[-1,0]  x[0,0]  x[1,0]  
x[-1,1]  x[0,1]  x[1,1]  
+ + + + + + + + 9 / dup *
- sqrt

y[-1,-1] dup * y[0,-1] dup * y[1,-1] dup * 
y[-1,0]  dup * y[0,0]  dup * y[1,0]  dup * 
y[-1,1]  dup * y[0,1]  dup * y[1,1]  dup * 
+ + + + + + + + 9 /
y[-1,-1] y[0,-1] y[1,-1] 
y[-1,0]  y[0,0]  y[1,0]  
y[-1,1]  y[0,1]  y[1,1]  
+ + + + + + + + 9 / dup *
- sqrt

- 50 + abs 50 - 250 *
""")

var_mask = Morpho.expand(var_mask, sw=1, mode=XxpandMode.LOSANGE)
var_mask = Morpho.inpand(var_mask, sw=1, mode=XxpandMode.LOSANGE)

dlp_final = core.std.MaskedMerge(bore, dlp, var_mask)



cambi = depth(src, 10).cambi.Cambi(window_size=16)

db_1 = pfdeband(dlp_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[1.4, 0.7, 0.7], grain=0), dark_thr=0.4, bright_thr=0.4, elast=1.6)
db_2 = pfdeband(dlp_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[2.0, 1.0, 1.0], grain=0), dark_thr=0.5, bright_thr=0.5, elast=1.6)
db_3 = pfdeband(dlp_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[3.0, 1.5, 1.5], grain=0), dark_thr=0.7, bright_thr=0.7, elast=1.6)
db_4 = pfdeband(dlp_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[4.0, 2.0, 2.0], grain=0), dark_thr=0.9, bright_thr=0.9, elast=1.6)
db_5 = pfdeband(dlp_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[5.0, 2.0, 2.0], grain=0), dark_thr=1.1, bright_thr=1.1, elast=1.6)
def deband_eval(n, f, db_1, db_2, db_3, db_4, db_5):
    if f.props["CAMBI"] < 0.8:
        return db_1
    elif f.props["CAMBI"] < 1.6:
        return db_2
    elif f.props["CAMBI"] < 2.4:
        return db_3
    elif f.props["CAMBI"] < 3.2:
        return db_4
    else:
        return db_5
db = dlp_final.std.FrameEval(eval=partial(deband_eval, db_1=db_1, db_2=db_2, db_3=db_3, db_4=db_4, db_5=db_5), prop_src=cambi)

mv = MVTools(dlp_final, search_clip=lambda clip: Prefilter.DFTTEST(prefilter_to_full_range(clip, slope=4.0)))

mv.analyze(tr=6, blksize=16, overlap=8, truemotion=MotionMode.COHERENCE, divide=2)
mv.recalculate(thsad=16, blksize=4, overlap=2, dct=SADMode.ADAPTIVE_SATD_DCT, truemotion=MotionMode.COHERENCE)

dn = mv.degrain(db_1, db, tr=6, thsad=26)



final = finalize_clip(dn, dither_type=DitherType.NONE)


if "__main__" in dir(__main__):
    setup = Setup("OVA", config_file=None, work_dir=SPath("Temp") / f"OVA.vsmuxtools.tmp")
    
    output = SPath("Video") / f"OVA.ivf"
    fgs_table = SPath("grain_ova.tbl")
    
    SVTAV1(preset=2, crf=14.00,
           lineart_psy_bias=7, texture_psy_bias=4,
           satd_bias=0.50,
           fgs_table=str(fgs_table),
           progress=2, sd_clip=src_sd, resumable=False).encode(final, outfile=output)
else:
    final.set_output()
