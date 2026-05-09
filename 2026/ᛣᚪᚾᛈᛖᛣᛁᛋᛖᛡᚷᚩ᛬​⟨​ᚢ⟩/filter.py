import os
import sys
sys.path.insert(0, os.getcwd())

from vsdeband import Grainer, pfdeband, placebo_deband
from vsdehalo import dehalo_alpha, fine_dehalo
from vsdenoise import DFTTest, frequency_merge
from vsmasktools import FreyChen, Morpho
import vsmlrt
from vsrgtools import bilateral, contrasharpening_median, remove_grain
from vstools import core, depth, DitherType, finalize_clip, initialize_clip, insert_clip, SPath, vs

from sources import sources


assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources



print(f"\033[1mSource:\033[0m \t{sources[episode].source_bd.name}", file=sys.stderr)
src_bd = initialize_clip(core.bs.VideoSource(sources[episode].source_bd, showprogress=False))
if sources[episode].source_web:
    print(f"\033[1mSource:\033[0m \t{sources[episode].source_web.name}", file=sys.stderr)
    src_web = initialize_clip(core.bs.VideoSource(sources[episode].source_web, showprogress=False))

if sources[episode].source_web:
    for fno, fr in enumerate(core.vszip.PlaneMinMax(core.akarin.Expr([src_bd, src_web], ["x y - abs", ""]), prop="Luma").frames()):
        if fr.props["LumaMax"] > 64 << 8:
            print(f"\033[1;31m\t\tSource check error on frame {fno}\033[0m", file=sys.stderr)
    else:
        print(f"\t\tSource check complete", file=sys.stderr)


if sources[episode].op:
    op_src = []
    assert sources[episode].op[0] + 2157 <= sources[episode].op[1]
    op_src.append(src_web[sources[episode].op[0]:sources[episode].op[0]+2157])
    for op_ep in sources: # Episode 02 is the only episode starting with odd frame. This will always include it.
        if op_ep != episode and sources[op_ep].op:
            assert sources[op_ep].op[0] + 2157 <= sources[op_ep].op[1]
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_web, showprogress=False))[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])
            
        if len(op_src) >= 3:
            break
        
    assert len(op_src) == 3
    for fno, fr in enumerate(core.vszip.PlaneMinMax(core.akarin.Expr([op_src[0], op_src[-1]], ["x y - abs", ""]), prop="Luma")[::49].frames()):
        assert fr.props["LumaMax"] <= 64 << 8, f"{fno * 49}"
    else:
        print(f"\t\tfrequency_merge source check complete")

    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))

    src_web = insert_clip(src_web, op_merge, sources[episode].op[0])
    op_len = sources[episode].op[1] - sources[episode].op[0]
    if op_len > 2157:
        src_web = insert_clip(src_web, op_merge[2152:op_len-2157+2152], sources[episode].op[0] + 2157)

if sources[episode].op:
    op_src = []
    assert sources[episode].op[0] + 2157 <= sources[episode].op[1]
    op_src.append(src_bd[sources[episode].op[0]:sources[episode].op[0]+2157])
    for op_ep in sources:
        if op_ep != episode and sources[op_ep].op:
            assert sources[op_ep].op[0] + 2157 <= sources[op_ep].op[1]
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_bd, showprogress=False))[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])
            
        if len(op_src) >= 2:
            break
        
    assert len(op_src) == 2

    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))

    src_bd = insert_clip(src_bd, op_merge, sources[episode].op[0])
    op_len = sources[episode].op[1] - sources[episode].op[0]
    if op_len > 2157:
        src_bd = insert_clip(src_bd, op_merge[2152:op_len-2157+2152], sources[episode].op[0] + 2157)



if sources[episode].source_web:
    cclip = src_web
else:
    cclip = src_bd
cclip = cclip.resize.Bicubic(filter_param_a=0, filter_param_b=0.5, \
                             width=1920, height=1088, src_left=0, src_top=-4, src_width=1920, src_height=1088, \
                             format=vs.RGBS, range=1)
cclip = vsmlrt.inference(cclip, SPath(vsmlrt.models_path) / "anime-segmentation" / "isnet_is.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
cclip = cclip.std.Crop(top=4, bottom=4)
cclip = remove_grain(cclip, remove_grain.Mode.BINOMIAL_BLUR)
cclip = cclip.akarin.Expr("x 0.15 - 1.2 * 0 max 1 min")
dl_cclip = Morpho.maximum(cclip, iterations=2)
dl_cclip = depth(dl_cclip, 16, dither_type=DitherType.NONE)
dh_cclip = Morpho.maximum(dl_cclip, iterations=2)



if sources[episode].source_web:
    dn_web = src_web.dctf.DCTFilter(factors=[1,   1, 1, 1, 1, 1, 1, 0.8,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             0.8, 1, 1, 1, 1, 1, 1, 0.4], planes=[0])
    dn_web = DFTTest(backend=DFTTest.Backend.OLD).denoise(dn_web, {0.00:0.06, 0.40:0.09, 0.70:0.24, 1.00:0.24}, tr=0, sbsize=8, sosize=6)


if sources[episode].source_web:
    mg_web = dn_web.fmtc.resample(w=1920, h=1080, kernel="blackmanminlobe", taps=[12, 6], fh=[1/1.250, 1/1.425], fv=[1/1.250, 1/1.375])

    c_merge = frequency_merge(mg_web, src_bd, lowpass=lambda clip: DFTTest().denoise(clip, {0.0:5.0, 0.4:4.0, 0.6:2.0, 1.0:1.0}), mode_high=mg_web)
    c_merge = contrasharpening_median(c_merge, mg_web)

    def high_adder(clips, **_):
        return core.llvmexpr.Expr(clips, """
xabs = abs($x - 32768)
yabs = abs($y - 32768)
xsign = $x >= 32768 ? 1 : -1
ysign = $y >= 32768 ? 1 : -1
RESULT = 0
if (xsign == ysign) {
  RESULT = xabs ** 5 + yabs ** 5
} else {
  RESULT = abs(xabs ** 5 - yabs ** 5)
}
RESULT = RESULT ** 0.2
if (xabs >= yabs) {
  RESULT = copysign(RESULT, xsign) + 32768
} else {
  RESULT = copysign(RESULT, ysign) + 32768
}
""", infix=1)
    b_merge = frequency_merge(mg_web, src_bd, lowpass=lambda clip: DFTTest().denoise(clip, {0.0:5.0, 0.4:4.0, 0.6:2.0, 1.0:1.0}), mode_high=high_adder)

    merge = core.std.MaskedMerge(b_merge, c_merge, dl_cclip, planes=[0])

    dl = core.akarin.Expr([merge, mg_web, dn_web], "x y - z +")
else:
    dl = src_bd



pro = DFTTest().denoise(dl, {0.0:0.1, 0.5:0.2, 0.7:5.0, 1.0:5.0}, planes=[0])

dh_mask = fine_dehalo.mask(pro, edgemask=FreyChen(), thmi=5, thma=100, thlimi=25, thlima=70, rx=2, ry=2)
dh_mask_inclusive = fine_dehalo.mask(pro, edgemask=FreyChen(), thmi=5, thma=100, thlimi=35, thlima=80, rx=1, ry=1, edgeproc=1.0, exclude=False)
dh_mask = core.akarin.Expr([dh_mask, dh_mask_inclusive, dh_cclip], "x 0.80 * y 0.70 * + z min")

dh = dehalo_alpha(pro, brightstr=0.80, highsens=25)

dh = core.std.MaskedMerge(pro, dh, dh_mask, planes=[0])

dh_final_ref = bilateral(pro, ref=dh, sigmaR=3/255, sigmaS=6, planes=[0])
dh_final = core.akarin.Expr([pro, dh, dh_final_ref], "y z < y z + 0.5 * x min y ?")

dh_re = core.akarin.Expr([dh_final, pro, dl], "x y - z +")



db = pfdeband(dh_re, thr=1.2, debander=placebo_deband)

rg = Grainer.PERLIN(db, strength=(1.6, 0.3), size=2.2,
                        luma_scaling=1, temporal=(0.50, 3), seed=274810)

rg = core.std.MaskedMerge(dh_re, rg, dl_cclip, planes=[0])


final = finalize_clip(rg)

final.set_output()
