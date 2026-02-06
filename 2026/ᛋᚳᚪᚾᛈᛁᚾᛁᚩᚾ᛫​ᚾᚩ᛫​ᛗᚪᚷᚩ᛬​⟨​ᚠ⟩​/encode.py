import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsaa import based_aa
from vsdenoise import bm3d, DFTTest, frequency_merge, mc_degrain, nl_means
from vskernels import Bilinear
from vsmuxtools import settings_builder_5fish_svt_av1_psy, Setup, SVTAV1
from vsscale import Rescale
from vsTAAmbk import TAAmbk
from vstools import core, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, join, replace_ranges, SPath, vs

from sources import sources


assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources


if sources[episode].source:
    print(f"\033[1mSource:\033[0m \t{sources[episode].source.name}")
    src = src_sd = initialize_clip(core.bs.VideoSource(sources[episode].source))

    if sources[episode].source_t:
        src_t = initialize_clip(core.bs.VideoSource(sources[episode].source_t))
        diff_t = src.std.PlaneStats(src_t, prop="Luma")
        for fr in diff_t[:2000].frames():
            assert fr.props["LumaDiff"] == 0
        else:
            print(f"\t\tSource check complete")
else:
    assert sources[episode].source_t
    print(f"\033[1mSource:\033[0m \t{sources[episode].source_t.name}")
    src = src_sd = initialize_clip(core.bs.VideoSource(sources[episode].source_t))


if sources[episode].op:
    op_src = []
    for op_ep in sources:
        if sources[op_ep].op:
            if sources[op_ep].source:
                op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source))[sources[op_ep].op[0]:sources[op_ep].op[0]+2159])
            else:
                assert sources[op_ep].source_t
                op_src.append(initialize_clip(core.bs.VideoSource(sources[op_ep].source_t))[sources[op_ep].op[0]:sources[op_ep].op[0]+2159])

    op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))

    src = insert_clip(src, op_merge, sources[episode].op[0])
    # op_len = sources[episode].op[1] - sources[episode].op[0]
    # if op_len > 2159:
    #     src_merge = insert_clip(src_merge, op_merge[2154:op_len-2159+2154], sources[episode].op[0] + 2159)


src_y = get_y(src)
rs = Rescale(src_y, width=1500, height=843.75, kernel=Bilinear(), downscaler=Bilinear(linear=True))

ds = rs.upscale
re = rs.rescale

ds_sub = core.akarin.Expr([ds, re], "x y -", format=vs.GRAYS)
ds_soften = core.akarin.Expr([ds, re, ds_sub], """
z 0 >
    z[-1,-1] z[0,-1] z[1,-1] z[-1,0] z[0,0] z[1,0] z[-1,1] z[0,1] z[1,1]
    sort9 least1! least2! drop7 least1@ 0 min least2@ 0 min + 0.5 * lim!
    y x - 0.3 * lim@ max x +
    x 0.8 * y 0.2 * + ?
""")

ds_noise = core.akarin.Expr([ds_soften, re, src_y], "z y - x +")
ds_noise = join(ds_noise, src)

aa_opp = TAAmbk(src_y, aatype=2, mclip=src.std.BlankClip(format=vs.GRAY16, color=65535))
aa_opp = core.akarin.Expr([aa_opp, src_y], """
x y - diff!
diff@ 0 =
    0
    diff@ 0 >
        diff@ 200 - 0 max
        diff@ 200 + 0 min ? ?
""", format=vs.GRAYS)
aa_opp = core.akarin.Expr([aa_opp, src_y], """
x 0 =
    y
    x 0 >
    x[0,-1] 0 > x[0,1] 0 > x[-1,0] 0 > x[1,0] 0 >
    or or or and
    x 0 <
    x[0,-1] 0 < x[0,1] 0 < x[-1,0] 0 < x[1,0] 0 <
    or or or and or
        y x +
        y ? ?
""", format=vs.GRAY16)
aa_opp = join(aa_opp, src)

aa_ed = based_aa(src, supersampler=False, mask_thr=80)

lineart_final = ds_noise
lineart_final = replace_ranges(lineart_final, aa_opp, sources[episode].op, exclusive=True)
lineart_final = replace_ranges(lineart_final, src, (sources[episode].op[0] + 1737, sources[episode].op[0] + 2000), exclusive=True)
lineart_final = replace_ranges(lineart_final, aa_ed, sources[episode].ed, exclusive=True)
lineart_final = replace_ranges(lineart_final, src, sources[episode].text, exclusive=True)


decheckerboard = lineart_final.dctf.DCTFilter(factors=[1, 1, 1, 1, 1, 1, 1, 1,
                                                       1, 1, 1, 1, 1, 1, 1, 1,
                                                       1, 1, 1, 1, 1, 1, 1, 1,
                                                       1, 1, 1, 1, 1, 1, 1, 1,
                                                       1, 1, 1, 1, 1, 1, 1, 1,
                                                       1, 1, 1, 1, 1, 1, 1, 1,
                                                       1, 1, 1, 1, 1, 1, 1, 1,
                                                       1, 1, 1, 1, 1, 1, 1, 0.65])

ref = mc_degrain(lineart_final, tr=2, refine=1, thsad=120)
dn_y = bm3d(lineart_final, sigma=0.95, tr=2, profile=bm3d.Profile.LOW_COMPLEXITY, ref=ref, planes=[0])
dn_yuv = nl_means(dn_y, h=0.24, s=1, tr=2, ref=ref, planes=[1, 2])

dn_fine = decheckerboard
dn_fine = replace_ranges(dn_fine, dn_yuv, sources[episode].op, exclusive=True)
dn_fine = replace_ranges(dn_fine, dn_y, sources[episode].ed, exclusive=True)

dn_final = DFTTest().denoise(dn_fine, {0.0:0.04, 0.48:0.04, 0.60:0.16, 1.0:0.32}, tr=1, planes=[0])


final = finalize_clip(dn_final, dither_type=DitherType.NONE)


if "__main__" in dir(__main__):
    setup = Setup(episode, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")
    
    output = SPath("Video") / f"{episode}.ivf"
    fgs_table = SPath("grain.tbl")
    
    settings = settings_builder_5fish_svt_av1_psy(
        preset=2,
        crf=29.50,
        balancing_luminance_q_bias=7.0,
        balancing_r0_dampening_layer=-3,
        enable_variance_boost=0,
        qm_min=9,
        chroma_qm_min=11,
        noise_norm_strength=4,
        ac_bias=3.0,
        variance_md_bias_thr=5.5,
        dlf_bias_max_dlf="6,2",
        fgs_table=str(fgs_table)
    )
    SVTAV1(**settings, sd_clip=src_sd).encode(final, outfile=output)
else:
    final.set_output()
