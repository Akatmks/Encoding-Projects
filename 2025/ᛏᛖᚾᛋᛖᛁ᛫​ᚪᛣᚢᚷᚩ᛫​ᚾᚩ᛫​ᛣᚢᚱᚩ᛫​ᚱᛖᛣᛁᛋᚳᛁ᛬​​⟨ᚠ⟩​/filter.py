import os
import sys
sys.path.insert(0, os.getcwd())

from vsdehalo import dehalo_alpha, fine_dehalo
from vsdenoise import DFTTest, frequency_merge, Prefilter, mc_degrain
from vsexprtools import norm_expr
from vsmasktools import FreyChen, Morpho
import vsmlrt
from vsrgtools import bilateral
from vstools import core, depth, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, join, SPath, vs

from sources import sources



assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources



src = []
print(f"Source: {sources[episode].source_e.name}", file=sys.stderr)
src.append(initialize_clip(core.bs.VideoSource(sources[episode].source_e)))
if sources[episode].source_y:
    print(f"Source: {sources[episode].source_y.name}", file=sys.stderr)
    src.append(initialize_clip(core.bs.VideoSource(sources[episode].source_y)))
if sources[episode].source_2:
    print(f"Source: {sources[episode].source_2.name}", file=sys.stderr)
    src.append(initialize_clip(core.bs.VideoSource(sources[episode].source_2)))

if len(src) > 1:
    src_merge = frequency_merge(*src, lowpass=lambda clip: DFTTest().denoise(clip))
else:
    src_merge = src[0]



if sources[episode].op:
    op_src = []
    for op_ep in sources:
        if sources[op_ep].op:
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_e))[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])
            if sources[op_ep].source_y:
                op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_y))[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])
            if sources[op_ep].source_2:
                op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_2))[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])

    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))

    src_merge = insert_clip(src_merge, op_merge, sources[episode].op[0])
    op_len = sources[episode].op[1] - sources[episode].op[0]
    if op_len > 2157:
        src_merge = insert_clip(src_merge, op_merge[2152:op_len-2157+2152], sources[episode].op[0] + 2157)



cclip = src_merge.resize.Bicubic(filter_param_a=0, filter_param_b=0.5, \
                                 width=1920, height=1088, src_left=0, src_top=-4, src_width=1920, src_height=1088, \
                                 format=vs.RGBS, range=1)
cclip = vsmlrt.inference(cclip, SPath(vsmlrt.models_path) / "anime-segmentation" / "isnet_is.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
cclip = Morpho.maximum(cclip, iterations=4)
cclip = cclip.akarin.Expr("""
                 x[0,-2]
        x[-1,-1] x[0,-1] x[1,-1]
x[-2,0] x[-1,0]  x[0,0]  x[1,0]  x[2,0]
        x[-1,1]  x[0,1]  x[1,1]
                 x[0,2]
sort13 drop10 high! drop2
high@ 0.90 > x 0.85 > and x x 9 pow ? continue!
continue@ 0.15 > continue@ 0 ?
""")
cclip = cclip.std.Crop(top=4, bottom=4)

dn_cclip = cclip.resize.Bilinear(width=240, height=135)
dn_cclip = dn_cclip.akarin.Expr("""
x[-1,-1] x[-1,1] x[0,0] x[1,-1] x[1,1]
sort5 drop1 observe! drop3 observe@ x max
2 *
""")
dn_cclip = dn_cclip.resize.Point(width=1920, height=1080)
dn_cclip = depth(dn_cclip, 16, dither_type=DitherType.NONE)

dh_cclip = cclip.akarin.Expr("x 0.45 max 1.0 min")
dh_cclip = Morpho.inflate(dh_cclip, radius=1)



dn = DFTTest().denoise(src_merge, {0.0:0.10, 0.40:0.10, 0.60:0.30, 0.80:0.80, 1.00:1.30}, tr=1)
dn_refine = mc_degrain(dn, blksize=32, thsad=80, tr=1, prefilter=Prefilter.DFTTEST(), planes=[0])
dn_refine = core.std.MaskedMerge(dn, dn_refine, dn_cclip)

dn_diff = core.akarin.Expr([dn_refine, src_merge], ["x y - 64 * 32768 +"])
dn_diff_dct = dn_diff.dctf.DCTFilter(factors=[1,    0.95, 0.85, 0.7,  0.5,  0.5,  0.6,  0.6,
                                              0.95, 0.98, 0.95, 0.92, 0.85, 0.85, 0.85, 0.95,
                                              0.85, 0.95, 0.98, 0.98, 0.95, 0.98, 1,    1,
                                              0.7,  0.92, 0.98, 1,    0.98, 1,    1,    1,
                                              0.5,  0.85, 0.95, 0.98, 0.98, 1,    1,    1,
                                              0.5,  0.85, 0.98, 1,    1,    1,    1,    1,
                                              0.6,  0.85, 1,    1,    1,    1,    1,    1,
                                              0.6,  0.95, 1,    1,    1,    1,    1,    1])
dn_dct = core.akarin.Expr([src_merge, dn_diff_dct], ["y 32768 - 64 / x +"])



dn_dct_y = get_y(dn_dct)
dh_dn = DFTTest().denoise(dn_dct_y, {0.0:0.10, 0.4:0.10, 0.6:0.80, 1.0:0.80})

dh = dehalo_alpha(dh_dn, blur=[1.30, 1.55], ss=2, brightstr=0.95)

dh_mask = fine_dehalo.mask(dh_dn, edgemask=FreyChen(), thmi=25, thma=100, thlimi=35, thlima=70, rx=1, ry=1)
dh_mask_inclusive = fine_dehalo.mask(dh_dn, edgemask=FreyChen(), thmi=25, thma=100, thlimi=35, thlima=70, rx=1, ry=1, edgeproc=1.0, exclude=False)
dh_mask = core.akarin.Expr([dh_mask, dh_mask_inclusive, dh_cclip], "x 0.90 * y 0.50 * + z *")

dh = core.std.MaskedMerge(dh_dn, dh, dh_mask)

dh_final_ref = bilateral(dh_dn, ref=dh, sigmaR=8 / 255, sigmaS=10)
dh_final = norm_expr([dh_dn, dh, dh_final_ref], "y z < y z + 0.5 * y ? x min")

dh_final = core.akarin.Expr([dh_final, dn_dct_y, dh_dn], "y z - x +")
dh_final = join(dh_final, dn_dct)



final = finalize_clip(dh_final, dither_type=DitherType.NONE)
final.set_output()
