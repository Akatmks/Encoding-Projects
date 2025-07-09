from vsdehalo import fine_dehalo, dehalo_sigma, edge_cleaner
from vsdenoise import bm3d, mc_degrain, nl_means
from vsdenoise.blockmatch import BM3D
from vskernels import Bicubic
from vsmasktools import ExLaplacian3, FreyChen, Kayyali, Morpho, Scharr
import vsmlrt
import os
from privatevsfunc import private_aa
from vsscale import descale_error_mask, Rescale
from vstools import core, depth, DitherType, get_y, initialize_clip, join, SPath, vs


source_file = SPath(os.environ["SOURCE_FILE"])
if not source_file.exists():
    raise FileNotFoundError("Source file not found.")

src = core.lsmas.LWLibavSource(source_file)
src = initialize_clip(src)


cclip = src.resize.Bicubic(filter_param_a=0, filter_param_b=0.5, \
                           width=1920, height=1088, src_left=0, src_top=-4, src_width=1920, src_height=1088, \
                           format=vs.RGBS, range=1) # 1886 transfer works the best
cclip = vsmlrt.inference(cclip, SPath(vsmlrt.models_path) / "anime-segmentation" / "isnet_is.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
cclip = Morpho.maximum(cclip)
cclip = cclip.akarin.Expr("""
                           x[-2,-5] x[-1,-5] x[0,-5] x[1,-5] x[2,-5]
                  x[-3,-4] x[-2,-4] x[-1,-4] x[0,-4] x[1,-4] x[2,-4] x[3,-4]
         x[-4,-3] x[-3,-3] x[-2,-3] x[-1,-3] x[0,-3] x[1,-3] x[2,-3] x[3,-3] x[4,-3]
x[-5,-2] x[-4,-2] x[-3,-2] x[-2,-2] x[-1,-2] x[0,-2] x[1,-2] x[2,-2] x[3,-2] x[4,-2] x[5,-2]
x[-5,-1] x[-4,-1] x[-3,-1] x[-2,-1] x[-1,-1] x[0,-1] x[1,-1] x[2,-1] x[3,-1] x[4,-1] x[5,-1]
x[-5,0]  x[-4,0]  x[-3,0]  x[-2,0]  x[-1,0]  x[0,0]  x[1,0]  x[2,0]  x[3,0]  x[4,0]  x[5,0]
x[-5,1]  x[-4,1]  x[-3,1]  x[-2,1]  x[-1,1]  x[0,1]  x[1,1]  x[2,1]  x[3,1]  x[4,1]  x[5,1]
x[-5,2]  x[-4,2]  x[-3,2]  x[-2,2]  x[-1,2]  x[0,2]  x[1,2]  x[2,2]  x[3,2]  x[4,2]  x[5,2]
         x[-4,3]  x[-3,3]  x[-2,3]  x[-1,3]  x[0,3]  x[1,3]  x[2,3]  x[3,3]  x[4,3]
                  x[-3,4]  x[-2,4]  x[-1,4]  x[0,4]  x[1,4]  x[2,4]  x[3,4]
                           x[-2,5]  x[-1,5]  x[0,5]  x[1,5]  x[2,5]
sort97 drop8 cluster! drop85 high! drop2
high@ 0.95 > x 0.85 > and 1 x ? continue!
cluster@ 0.10 > high@ 0.95 < and continue@ 0.75 < and continue@ 1.333333333333 * 3 pow 3 pow 0.75 * continue@ ? continue!
continue@ 0.10 > continue@ 0 ?
""")
cclip = Morpho.inflate(cclip)
cclip = cclip.std.Crop(top=4, bottom=4)
cclip = depth(cclip, 16, dither_type=DitherType.NONE)


src_y = get_y(src)

b_dg_y = mc_degrain(src_y, tr=2, refine=2, thsad=160)
b_dn_y = bm3d(src_y, ref=b_dg_y, sigma=0.7, profile=BM3D.Profile.LOW_COMPLEXITY)

c_dn_y = bm3d(src_y, sigma=3.1, profile=BM3D.Profile.LOW_COMPLEXITY)

dn_y = core.std.MaskedMerge(b_dn_y, c_dn_y, cclip)

dn_uv = nl_means(src, h=0.44, tr=2, planes=[1, 2])


aa_y = private_aa(dn_y, strength=0.95)

combine = join(aa_y, dn_uv)


b_dh = fine_dehalo(combine, brightstr=1.0, rx=2.5, ry=2.5, exclude=False)

b_mask_dh = fine_dehalo(combine, brightstr=1.0, rx=2.5, ry=2.5, edgemask=ExLaplacian3(), thmi=120, thma=120, exclude=False)
b_mask_dh = core.akarin.Expr([get_y(b_mask_dh), get_y(combine)], "y x - subtract! subtract@ 200 > subtract@ 0 ? 256 *")
b_mask_dh = Morpho.dilation(b_mask_dh, radius=2)
b_mask_dh = Morpho.closing(b_mask_dh, radius=7)
b_mask_dh = Morpho.inflate(b_mask_dh, radius=3)

rs = Rescale(src_y, 810.000, kernel=Bicubic(b=1.0, c=0.0)).rescale
b_mask_descale = descale_error_mask(src, rs, thr=0.01, expands=0, blur=0, tr=3)
b_mask_descale = Morpho.dilation(b_mask_descale, radius=3)
b_mask_descale = Morpho.inflate(b_mask_descale, radius=4, multiply=2.0)

b_dh_filtered_y = core.akarin.Expr([get_y(b_dh), get_y(combine), b_mask_dh, b_mask_descale], """
z 65535 / a 65535 / * filter!
filter@ y * 1 filter@ - x * +
""")
b_dh_filtered = join(b_dh_filtered_y, combine)

c_dh = edge_cleaner(combine, strength=7, edgemask=Kayyali())

c_dh_refine_1 = edge_cleaner(c_dh, strength=15, edgemask=Scharr())

c_dh_refine_2 = dehalo_sigma(c_dh_refine_1, sigma=1.2)
c_dh_mask = fine_dehalo.mask(c_dh_refine_1, rx=2.4, ry=2.4, edgemask=FreyChen(), thmi=100, thma=140, edgeproc=1.0, exclude=False)
c_dh_refine_2 = core.std.MaskedMerge(c_dh_refine_1, c_dh_refine_2, c_dh_mask)

final = core.std.MaskedMerge(b_dh_filtered, c_dh_refine_2, cclip)


out = depth(final, 10, dither_type=DitherType.NONE)
out.set_output()
