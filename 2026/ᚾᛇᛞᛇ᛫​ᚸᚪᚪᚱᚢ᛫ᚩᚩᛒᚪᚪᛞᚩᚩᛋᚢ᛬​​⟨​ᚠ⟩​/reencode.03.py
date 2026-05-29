import os
import sys
sys.path.insert(0, os.getcwd())

import __main__

from vsaa import based_aa
from vsdeband import pfdeband, placebo_deband
from vsdehalo import dehalo_alpha
from vsdenoise import DFTTest, frequency_merge
from vsmasktools import FreyChen, Morpho
import math
from vsrgtools import bilateral, MeanMode
from vstools import core, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, SPath
from vsmuxtools import settings_builder_5fish_svt_av1_psy, Setup, SVTAV1

from sources import sources



episode = "03"



print(f"Source: \t{sources[episode].source_j.name}")
src = src_sd = initialize_clip(core.bs.VideoSource(sources[episode].source_j, showprogress=False))
src = [src]

if sources[episode].source_d:
    print(f"Source: \t{sources[episode].source_d.name}")
    src.append(initialize_clip(core.bs.VideoSource(sources[episode].source_d, showprogress=False)))

if sources[episode].source_m:
    print(f"Source: \t{sources[episode].source_m.name}")
    src.append(initialize_clip(core.bs.VideoSource(sources[episode].source_m, showprogress=False)))



def high_adder(clips, **_):
    if len(clips) == 3:
        return core.llvmexpr.Expr(clips, """
xabs = abs($x - 32768)
yabs = abs($y - 32768)
zabs = abs($z - 32768)
xsign = $x >= 32768 ? 1 : -1
ysign = $y >= 32768 ? 1 : -1
zsign = $z >= 32768 ? 1 : -1
xpow = copysign(xabs ** 5, xsign)
ypow = copysign(yabs ** 5, ysign)
zpow = copysign(zabs ** 5, zsign)
sum = (xpow + ypow + zpow) * (2 / 3)
sumabs = abs(sum)
sumsign = sum >= 0 ? 1 : -1
RESULT = copysign(sumabs ** 0.2, sumsign) + 32768
""", infix=1)
    else:
        assert len(clips) == 2
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
def low_filter(clips, **_):
    merge = MeanMode.ARITHMETIC(clips)


    dn = DFTTest().denoise(merge, {0.0:0.06, 0.5:0.12, 0.7:0.60, 1.0:1.00}, tr=1, planes=[0])

    dn_y = get_y(dn)
    aa_mask = FreyChen().edgemask(dn_y)
    aa_mask = aa_mask.akarin.Expr("x 5600 - 24 *")
    aa_mask = Morpho.inflate(aa_mask, iterations=1)

    aa = based_aa(dn, mask=aa_mask, rfactor=1.5)


    dh_mask = Morpho.maximum(aa_mask, iterations=2)
    
    dh = dehalo_alpha(aa, brightstr=0.45, highsens=25)
    dh = core.std.MaskedMerge(aa, dh, dh_mask, planes=[0])
    dh = core.akarin.Expr([dh, aa], ["x y - 45 + 0 min y +", ""])
    
    dh_final_ref = bilateral(aa, ref=dh, sigmaR=5 / 255, sigmaS=12, planes=[0])
    dh_final = core.akarin.Expr([aa, dh, dh_final_ref], ["y z < z x min y ?", ""])


    return dh_final
merge = frequency_merge(*src, lowpass=lambda clip: DFTTest().denoise(clip, 4.0), mode_low=low_filter, mode_high=high_adder)



# if sources[episode].op:
#     op_src = []
#     op_src_2058 = []
#     op_src_2059 = []
#     for op_ep in sources:
#         if sources[op_ep].op:
#             op_ep_len = sources[op_ep].op[1] - sources[op_ep].op[0]
#             for source in ["source_j", "source_d", "source_m"]:
#                 if hasattr(sources[op_ep], source) and getattr(sources[op_ep], source):
#                     op_ep_src = initialize_clip(core.bs.VideoSource(getattr(sources[op_ep], source)))
#                     if len(op_src) < 12:
#                         op_src.append(op_ep_src[sources[op_ep].op[0]:sources[op_ep].op[0]+2157])
#                     if op_ep_len >= 2158:
#                         if len(op_src_2058) < 12:
#                             op_src_2058.append(op_ep_src[sources[op_ep].op[0]+2158-1])
#                     if op_ep_len >= 2159:
#                         if len(op_src_2059) < 12:
#                             op_src_2059.append(op_ep_src[sources[op_ep].op[0]+2159-1])

#                 if len(op_src_2059) >= 12:
#                     break
#         if len(op_src_2059) >= 12:
#             break

#     if episode != "01":
#         print(f"\t\tfrequency_merge source check in progress", file=sys.stderr, end="\r")
#         for fno, fr in enumerate(core.vszip.PlaneMinMax(core.akarin.Expr([src[0][sources[episode].op[0]:sources[episode].op[0]+2157], op_src[0]], ["x y - abs", ""]), prop="Luma")[::49].frames()):
#             if fr.props["LumaMax"] > 72 << 8:
#                 print(f"\033[1;31m\t\tfrequency_merge source check error on frame {fno * 49} ({fno * 49 + sources[episode].op[0]})\033[0m", file=sys.stderr)
#         else:
#             print(f"\t\tfrequency_merge source check complete   ", file=sys.stderr)

#     op_len = sources[episode].op[1] - sources[episode].op[0]
#     op_merge = frequency_merge(*op_src, lowpass=lambda clip: DFTTest().denoise(clip))
#     merge = insert_clip(merge, op_merge, sources[episode].op[0])
#     if op_len >= 2158:
#         op_merge = frequency_merge(*op_src_2058, lowpass=lambda clip: DFTTest().denoise(clip))
#         merge = insert_clip(merge, op_merge, sources[episode].op[0] + 2158 - 1)
#     if op_len >= 2159:
#         op_merge = frequency_merge(*op_src_2059, lowpass=lambda clip: DFTTest().denoise(clip))
#         merge = insert_clip(merge, op_merge, sources[episode].op[0] + 2159 - 1)



db = pfdeband(merge, thr=1.7, debander=placebo_deband)

final = finalize_clip(db, dither_type=DitherType.NONE)



Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")

fgs_table = SPath("grain.tbl")

main = SPath("Video") / f"{episode}-main.ivf"
assert main.exists()

part_1 = SPath("Video") / f"{episode}-1.ivf"
if not part_1.exists():
    part_1_final = final[31724:31899]
    part_1_src_sd = src_sd[31724:31899]
    (SPath("Temp") / f"{episode}.vsmuxtools.tmp" / "svt_av1_scene_detection_cache.json").unlink()
    settings = settings_builder_5fish_svt_av1_psy(preset=2,
                                                  crf=19.60,
                                                  lineart_psy_bias=3,
                                                  texture_psy_bias=6,
                                                  psy_bias_optimize_b=1,
                                                  fgs_table=str(fgs_table))
    SVTAV1(**settings, sd_clip=part_1_src_sd).encode(part_1_final, outfile=part_1)

part_2 = SPath("Video") / f"{episode}-2.ivf"
if not part_2.exists():
    part_2_final = final[31899:34285]
    part_2_src_sd = src_sd[31899:34285]
    wan_gop = math.ceil((34285 - 31899) / 2)
    wan_gop = math.ceil((wan_gop - 1) / 16) * 16 + 1
    settings = settings_builder_5fish_svt_av1_psy(scd=0,
                                                  keyint=wan_gop,
                                                  preset=2,
                                                  crf=34.60,
                                                  lineart_psy_bias=3,
                                                  texture_psy_bias=6,
                                                  psy_bias_optimize_b=1,
                                                  fgs_table=str(fgs_table))
    SVTAV1(**settings).encode(part_2_final, outfile=part_2)

part_3 = SPath("Video") / f"{episode}-3.ivf"
if not part_3.exists():
    part_3_final = final[34285:34452]
    part_3_src_sd = src_sd[34285:34452]
    (SPath("Temp") / f"{episode}.vsmuxtools.tmp" / "svt_av1_scene_detection_cache.json").unlink()
    settings = settings_builder_5fish_svt_av1_psy(preset=2,
                                                  crf=19.60,
                                                  lineart_psy_bias=3,
                                                  texture_psy_bias=6,
                                                  psy_bias_optimize_b=1,
                                                  fgs_table=str(fgs_table))
    SVTAV1(**settings, sd_clip=part_3_src_sd).encode(part_3_final, outfile=part_3)

output = SPath("Video") / f"{episode}.ivf"
with output.open("wb") as out_f:
    with main.open("rb") as main_f:
        def copy_header(in_f, out_f):
            header = in_f.read(32)
            out_f.write(header)
        def discard_header(in_f):
            in_f.seek(32, 1)

        def copy_frame(in_f, out_f, fno):
            size = in_f.read(4)
            in_f.seek(8, 1)
            data = in_f.read(int.from_bytes(size, byteorder="little", signed=False))

            out_f.write(size)
            out_f.write(fno.to_bytes(8, byteorder="little", signed=False))
            out_f.write(data)
        def discard_frame(in_f):
            size = in_f.read(4)
            in_f.seek(8, 1)
            in_f.seek(int.from_bytes(size, byteorder="little", signed=False), 1)

        copy_header(main_f, out_f)
        for i in range(0, 31724):
            copy_frame(main_f, out_f, i)

        with part_1.open("rb") as part_1_f:
            discard_header(part_1_f)
            for i in range(31724, 31899):
                copy_frame(part_1_f, out_f, i)

        with part_2.open("rb") as part_2_f:
            discard_header(part_2_f)
            for i in range(31899, 34285):
                copy_frame(part_2_f, out_f, i)

        with part_3.open("rb") as part_3_f:
            discard_header(part_3_f)
            for i in range(34285, 34452):
                copy_frame(part_3_f, out_f, i)

        for i in range(31724, 34452):
            discard_frame(main_f)
        for i in range(34452, final.num_frames):
            copy_frame(main_f, out_f, i)
