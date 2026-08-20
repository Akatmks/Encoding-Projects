import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsdeband import pfdeband
from vsdenoise import DFTTest, frequency_merge, MotionMode, MVTools, Prefilter, prefilter_to_full_range, SADMode
from functools import partial
from vskernels import Spline16
from vsmasktools import Morpho
from vsmuxtools import Setup, SVTAV1
import vsmlrt
from vsrgtools import bilateral, fast_line_darken, gauss_blur
from vsscale import Rescale
from vstools import core, depth, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, join, replace_ranges, Sar, SPath, vs

from sources import sources



assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources

source = sources[episode]



print(f"Source: \t{source.source.name}")
src = src_sd = initialize_clip(core.bs.VideoSource(source.source, showprogress=False))



if source.op:
    op_src = []
    for op_ep in sources:
        if sources[op_ep].op and sources[op_ep].op_offset == 0:
            assert(sources[op_ep].op[1] - sources[op_ep].op[0] == 2159)
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source))[sources[op_ep].op[0]:sources[op_ep].op[1]])

    def low_filtered_arithmetic_op(clips, **_):
        assert len(clips) == 10
        return core.akarin.Expr(clips, """
src0 src1 src2 src3 src4 src5 src6 src7 src8 src9
sort10 drop3 + + + 0.25 * result! drop3
result@
""")
    def high_power_op(clips, **_):
        assert len(clips) == 10
        expr = ""
        for i in range(10):
            expr += f"""
src{i}abs = abs($src{i} - 32768)
src{i}sign = $src{i} >= 32768 ? 1 : -1
src{i}pow = copysign(src{i}abs ** 5, src{i}sign)
"""
        expr += """
sum = (src0pow + src1pow + src2pow + src3pow + src4pow + src5pow + src6pow + src7pow + src8pow + src9pow) * 0.1
sumabs = abs(sum)
sumsign = sum >= 0 ? 1 : -1
RESULT = copysign(sumabs ** 0.2, sumsign) + 32768
"""
        return core.llvmexpr.Expr(clips, expr, infix=1)
    op_merge = frequency_merge(*op_src, lowpass=bilateral, mode_low=low_filtered_arithmetic_op, mode_high=high_power_op)

    if source.op_offset == 0:
        merge = insert_clip(src, op_merge, source.op[0])
    elif source.op_offset == 1:
        merge = insert_clip(src, op_merge[0], source.op[0])
        merge = insert_clip(src, op_merge[:-1], source.op[0] + 1)
    else:
        raise AssertionError
else:
    merge = src


merge_f = depth(merge, 32, vs.FLOAT)

bore_f = merge_f.bore.SinglePlane(top=3, bottom=3, left=3, right=3, plane=0)
bore_f = bore_f.bore.SinglePlane(top=1, bottom=1, left=1, right=1, plane=1)
bore_f = bore_f.bore.SinglePlane(top=1, bottom=1, left=1, right=1, plane=2)

bore = depth(bore_f, 16)



bore_y = get_y(bore)

rs = Rescale(bore_y, width=1280, height=720, kernel=Spline16())
ds = rs.upscale
ds = Sar.from_clip(bore_y).apply(ds)

ds_diff = core.akarin.Expr([ds, bore_y], "x y - 32768 +")
ds_dn = DFTTest(backend=DFTTest.Backend.CPU).denoise(ds_diff, {0.0:0.06, 0.4:0.10, 0.6:0.60, 1.00:1.00})
ds_noise = core.akarin.Expr([ds, ds_diff, ds_dn], "x y z - -")

ds_repair = fast_line_darken(ds_noise, strength=4, threshold=0, protection=0)
expr = """
closest = -1
dist = 65536
"""
for X, Y in [                              (-3, 0),
             ( 0, -3),                                                ( 0,  3),
                                           ( 3, 0),
                                 (-2, -1),          (-2, 1),
                       (-1, -2),                             (-1, 2),
                       ( 1, -2),                             ( 1, 2),
                                 ( 2, -1),          ( 2, 1),
                                           (-2, 0), 
                        ( 0, -2),                             ( 0, 2),
                                           ( 2, 0), 
                                 (-1, -1),          (-1, 1), 
                                 ( 1, -1),          ( 1, 1),
                                           (-1, 0), 
                                 ( 0, -1),          ( 0, 1), 
                                           ( 1, 0),
                                           ( 0, 0)]:
    expr += f"""
curr = $y[{X},{Y}]
curr_dist = abs(curr - $x)
"""
    expr += """
if (curr_dist == 0) {
    closest = curr
    goto final
} else {
    if (curr_dist <= dist) {
        dist = curr_dist
        closest = curr
    }
}
"""
expr += """
final:
RESULT = nth_2((closest + $x) * 0.5, $x, $y)
"""
ds_repair = core.llvmexpr.Expr([ds_repair, bore_y], expr, infix=1)


tclip = bore.resize.Bicubic(filter_param_a=0, filter_param_b=0.5, \
                            width=1920, height=1088, src_left=0, src_top=-4, src_width=1920, src_height=1088, \
                            format=vs.YUV444PS, range=1) # Apparently YUV444 gives the best result. Who knows why
tclip = vsmlrt.inference(tclip, SPath(vsmlrt.models_path) / "ppocr" / "ml_PP-OCRv3_det.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
tclip = tclip.std.Crop(top=4, bottom=4)
tclip = depth(tclip, 16, dither_type=DitherType.NONE)
# tclip = tclip.vszip.PlaneMinMax(prop="TClip")

ds_tclip = Morpho.maximum(tclip, iterations=22)
ds_tclip = gauss_blur(ds_tclip, sigma=1.2)

ds_final = core.std.MaskedMerge(ds_repair, bore_y, ds_tclip)
ds_final = replace_ranges(ds_repair, ds_final, source.credits, exclusive=True)
ds_final = join(ds_final, bore)



cambi = depth(src, 10).cambi.Cambi(window_size=16)


db_1 = pfdeband(ds_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[1.4, 0.7, 0.7], grain=0), dark_thr=0.4, bright_thr=0.4, elast=1.6)
db_2 = pfdeband(ds_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[2.0, 1.0, 1.0], grain=0), dark_thr=0.5, bright_thr=0.5, elast=1.6)
db_3 = pfdeband(ds_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[3.0, 1.5, 1.5], grain=0), dark_thr=0.7, bright_thr=0.7, elast=1.6)
db_4 = pfdeband(ds_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[4.0, 2.0, 2.0], grain=0), dark_thr=0.9, bright_thr=0.9, elast=1.6)
db_5 = pfdeband(ds_final, prefilter=bilateral, debander=lambda clip, *_, **__: clip.vszipcu.Deband(threshold=[5.0, 2.0, 2.0], grain=0), dark_thr=1.1, bright_thr=1.1, elast=1.6)
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
db = ds_final.std.FrameEval(eval=partial(deband_eval, db_1=db_1, db_2=db_2, db_3=db_3, db_4=db_4, db_5=db_5), prop_src=cambi)

mv = MVTools(ds_final, search_clip=lambda clip: Prefilter.DFTTEST(prefilter_to_full_range(clip, slope=4.0)))

mv.analyze(tr=6, blksize=32, overlap=16, truemotion=MotionMode.COHERENCE, divide=2)
mv.recalculate(thsad=16, blksize=8, overlap=4, dct=SADMode.ADAPTIVE_SATD_DCT, truemotion=MotionMode.COHERENCE)

dn = mv.degrain(db_1, db, tr=6, thsad=26)



final = finalize_clip(dn, dither_type=DitherType.NONE)


if "__main__" in dir(__main__):
    setup = Setup(episode, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")
    
    output = SPath("Video") / f"{episode}.ivf"
    fgs_table = SPath("grain.tbl")
    
    SVTAV1(preset=2, crf=17.20,
           lineart_psy_bias=5, texture_psy_bias=4,
           dlf_bias_max_dlf="12,2", dlf_bias_min_dlf="4,0",
           cdef_bias_max_cdef="4,1,2,0", texture_cdef_bias_max_cdef="2,0,0,0",
           fgs_table=str(fgs_table),
           progress=2, sd_clip=src_sd).encode(final, outfile=output)
else:
    final.set_output()
