import os
import sys
sys.path.insert(0, os.getcwd())

from vsdeband import Grainer, pfdeband, placebo_deband
from vsdehalo import dehalo_alpha, fine_dehalo
from vsdenoise import deblock_qed, DFTTest, frequency_merge
from vsmasktools import FreyChen, Morpho
import vsmlrt
from vsrgtools import bilateral
from vstools import core, depth, DitherType, finalize_clip, initialize_clip, SPath, vs

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



if sources[episode].source_web:
    dn_web = src_web.dctf.DCTFilter(factors=[1,   1, 1, 1, 1, 1, 1, 0.9,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             1,   1, 1, 1, 1, 1, 1, 1,
                                             0.9, 1, 1, 1, 1, 1, 1, 0.55], planes=[0])
    dn_web = DFTTest(backend=DFTTest.Backend.OLD).denoise(dn_web, {0.00:0.06, 0.40:0.09, 0.70:0.30, 1.00:0.30}, tr=1, sbsize=8, sosize=6)

dn_bd = DFTTest(backend=DFTTest.Backend.OLD).denoise(src_bd, {0.00:0.06, 0.40:0.15, 0.70:0.30, 1.00:0.30}, tr=1, sbsize=8, sosize=6)


if sources[episode].source_web:
    mg_web = dn_web.fmtc.resample(w=1920, h=1080, kernel="blackmanminlobe", taps=[12, 6], fh=[1/1.250, 1/1.425], fv=[1/1.250, 1/1.375])
    def high_adder(clips, **_):
        return core.llvmexpr.Expr(clips, """
xabs = abs($x - 32768)
yabs = abs($y - 32768)
xsign = $x >= 32768 ? 1 : -1
ysign = $y >= 32768 ? 1 : -1
RESULT = 0
if (xsign == ysign) {
  RESULT = xabs ** 3 + yabs ** 3
} else {
  RESULT = abs(xabs ** 3 - yabs ** 3)
}
RESULT = RESULT ** (1/3)
if (xabs >= yabs) {
  RESULT = copysign(RESULT, xsign) + 32768
} else {
  RESULT = copysign(RESULT, ysign) + 32768
}
""", infix=1)
    mg_merge = frequency_merge(mg_web, dn_bd, lowpass=lambda clip: DFTTest().denoise(clip, {0.0:5.0, 0.4:4.0, 0.6:2.0, 1.0:1.0}), mode_high=high_adder)
    mg_merge = frequency_merge(mg_web, mg_merge, lowpass=lambda clip: deblock_qed(clip, quant=(32, 24), alpha=(2, 1), beta=(3, 2)), mode_low=mg_merge, mode_high=mg_web)
    dl = core.akarin.Expr([mg_merge, mg_web, dn_web], "x y - z +")
else:
    dl = dn_bd



pro = DFTTest().denoise(dl, {0.0:0.1, 0.5:0.2, 0.7:5.0, 1.0:5.0}, planes=[0])

cclip = pro.resize.Bicubic(filter_param_a=0, filter_param_b=0.5, \
                           width=1920, height=1088, src_left=0, src_top=-4, src_width=1920, src_height=1088, \
                           format=vs.RGBS, range=1)
cclip = vsmlrt.inference(cclip, SPath(vsmlrt.models_path) / "anime-segmentation" / "isnet_is.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
cclip = cclip.akarin.Expr("x 0.15 - 1.3 *")
cclip = Morpho.maximum(cclip, iterations=4)
cclip = cclip.std.Crop(top=4, bottom=4)

dh_mask = fine_dehalo.mask(pro, edgemask=FreyChen(), thmi=5, thma=100, thlimi=25, thlima=70, rx=2, ry=2)
dh_mask_inclusive = fine_dehalo.mask(pro, edgemask=FreyChen(), thmi=5, thma=100, thlimi=35, thlima=80, rx=1, ry=1, edgeproc=1.0, exclude=False)
dh_mask = core.akarin.Expr([dh_mask, dh_mask_inclusive, cclip], "x 0.80 * y 0.70 * + z 65535 * min")

dh = dehalo_alpha(pro, brightstr=0.80, highsens=25)

dh = core.std.MaskedMerge(pro, dh, dh_mask, planes=[0])

dh_final_ref = bilateral(pro, ref=dh, sigmaR=3/255, sigmaS=6, planes=[0])
dh_final = core.akarin.Expr([pro, dh, dh_final_ref], "y z < y z + 0.5 * x min y ?")

dh_re = core.akarin.Expr([dh_final, pro, dl], "x y - z +")


db = pfdeband(dh_re, thr=1.2, debander=placebo_deband)

cclip_16 = depth(cclip, 16, dither_type=DitherType.NONE)
db = core.std.MaskedMerge(dh_re, db, cclip_16, planes=[0])



rg = Grainer.PERLIN(db, strength=(1.4, 0.3), size=2.2,
                        luma_scaling=1, temporal=(0.50, 3), seed=274810)

rg_cclip = cclip_16.akarin.Expr("x 15000 max")
rg = core.std.MaskedMerge(db, rg, rg_cclip, planes=[0])


final = finalize_clip(rg)


final.set_output()
