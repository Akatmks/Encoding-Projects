import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsaa import based_aa
from vsexprtools import norm_expr
from vsdeband import pfdeband, placebo_deband
from vsdehalo import fine_dehalo, dehalo_alpha
from vsdenoise import DFTTest, frequency_merge, mc_degrain, Prefilter, wnnm
from vsmasktools import FreyChen, Morpho
import vsmlrt
from vsmuxtools import settings_builder_5fish_svt_av1_psy, Setup, SVTAV1
from vsrgtools import bilateral
from vstools import core, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, SPath, vs

from sources import sources


assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources


print(f"Source: \t{sources[episode].source.name}")
src = src_sd = initialize_clip(core.bs.VideoSource(sources[episode].source))


if sources[episode].op:
    op_src = []
    for op_ep in sources:
        if sources[op_ep].op:
            op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source))[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])

    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))

    src = insert_clip(src, op_merge, sources[episode].op[0])
    op_len = sources[episode].op[1] - sources[episode].op[0]
    if op_len > 2157:
        src = insert_clip(src, op_merge[2152:op_len-2157+2152], sources[episode].op[0] + 2157)


ref = mc_degrain(src, tr=2, refine=1, thsad=140)
dn = wnnm(src, sigma=1.40, tr=1, ref=ref)

dn_dcb = DFTTest().denoise(dn, sigma=20, planes=[0])
dn_dcb_diff = core.akarin.Expr([dn_dcb, dn], ["x y - 64 * 32768 +", ""])
dn_dcb_diff = dn_dcb_diff.dctf.DCTFilter(factors=[0.03125, 0, 0, 0, 0, 0, 0, 0,
                                                  0,       0, 0, 0, 0, 0, 0, 0,
                                                  0,       0, 0, 0, 0, 0, 0, 0,
                                                  0,       0, 0, 0, 0, 0, 0, 0,
                                                  0,       0, 0, 0, 0, 0, 0, 0,
                                                  0,       0, 0, 0, 0, 0, 0, 0,
                                                  0,       0, 0, 0, 0, 0, 0, 0,
                                                  0,       0, 0, 0, 0, 0, 0, 0.75], planes=[0])
dn_dcb = core.akarin.Expr([dn, dn_dcb_diff], ["y 1024 - 64 / x +", ""])


aa_mask = FreyChen().edgemask(get_y(dn_dcb))
aa_mask = aa_mask.akarin.Expr("x 4000 - 10 *")
aa_mask = Morpho.maximum(aa_mask, iterations=2)
aa = based_aa(dn_dcb, supersampler=False, mask=aa_mask, nrad=3, mdis=6)


dh = dehalo_alpha(aa, darkstr=0.05, highsens=25)

cclip = dh.resize.Bicubic(filter_param_a=0, filter_param_b=0.5, \
                          width=1920, height=1088, src_left=0, src_top=-4, src_width=1920, src_height=1088, \
                          format=vs.RGBS, range=1)
cclip = vsmlrt.inference(cclip, SPath(vsmlrt.models_path) / "anime-segmentation" / "isnet_is.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
cclip = Morpho.maximum(cclip, iterations=4)
cclip = cclip.std.Crop(top=4, bottom=4)

dh_mask = fine_dehalo.mask(aa, edgemask=FreyChen(), thmi=15, thma=100, thlimi=35, thlima=85, rx=2, ry=2)
dh_mask_inclusive = fine_dehalo.mask(aa, edgemask=FreyChen(), thmi=15, thma=100, thlimi=35, thlima=80, rx=1, ry=1, edgeproc=1.0, exclude=False)
dh_mask = core.akarin.Expr([dh_mask, dh_mask_inclusive, cclip], """
x y + 0.70 *
z 0.85 * 0.15 + 65535 * min
""")

dh = core.std.MaskedMerge(aa, dh, dh_mask)

dh_final_ref = bilateral(aa, ref=dh, sigmaR=6 / 255, sigmaS=12)
dh_final = norm_expr([aa, dh, dh_final_ref], "y z < y z + 0.5 * x min y ?")


db = pfdeband(dh_final, thr=1.25, debander=placebo_deband)


final = finalize_clip(db, dither_type=DitherType.NONE)


if "__main__" in dir(__main__):
    setup = Setup(episode, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")
    
    output = SPath("Video") / f"{episode}.ivf"
    fgs_table = SPath("grain.tbl")
    
    settings = settings_builder_5fish_svt_av1_psy(
        preset=2,
        crf=28.00,
        noise_level_thr=23000,
        balancing_luminance_q_bias=20.0,
        enable_variance_boost=0,
        qm_min=8,
        chroma_qm_min=12,
        noise_norm_strength=0,
        ac_bias=1.0,
        dlf_sharpness=7,
        fgs_table=str(fgs_table)
    )
    SVTAV1(**settings, sd_clip=src_sd).encode(final, outfile=output)
else:
    final.set_output()
