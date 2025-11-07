import os
import sys
sys.path.insert(0, os.getcwd())

from vsaa import based_aa, EEDI3
from vsdeband import pfdeband, placebo_deband
from vsdenoise import bm3d, mc_degrain, nl_means, Prefilter
from vsmasktools import diff_creditless, Morpho, RScharr
import vsmlrt
from vsmuxtools import SourceFilter, src_file
from vskernels import Lanczos
from vsrgtools import gauss_blur, remove_grain
from vsscale import Rescale, Waifu2x
from vstools import core, depth, DitherType, finalize_clip, get_y, initialize_clip, insert_clip, join, replace_ranges, Sar, SPath, vs

from sources import sources
from vodesfunc_noise_mod import adaptive_grain, ntype4



def filterchain(episode):
    source_file = src_file(sources[episode].source, trim=sources[episode].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
    src = source_file.init_cut()

    if sources[episode].op is not None:
        op_file = src_file(sources["NCOP"].source, trim=sources["NCOP"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        op = op_file.init_cut()

    if sources[episode].ed is not None:
        assert sources[episode].ed_type in [1, 2]
        if sources[episode].ed_type == 1:
            ed_file = src_file(sources["NCED01"].source, trim=sources["NCED01"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        else:
            ed_file = src_file(sources["NCED02"].source, trim=sources["NCED02"].trim, preview_sourcefilter=SourceFilter.BESTSOURCE)
        ed = ed_file.init_cut()

    if len(sources[episode].preview_cards) > 0:
        preview_card_mask = core.bs.VideoSource(SPath(__file__) / ".." / "preview_card_mask.png", fpsnum=24000, fpsden=1001)
        preview_card_mask = depth(preview_card_mask, 16)
        preview_card_mask = preview_card_mask.std.Loop()



    rs = Rescale(src, width=1920*(1552-1)/(1920-1), height=1080*(873-1)/(1080-1), base_width=1552, base_height=873, kernel=Lanczos(2))


    descale = rs.descale
    cclip = src.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                               width=1552, height=873, src_width=1920+((1920-1)/(1552-1)-1), src_height=1080+((1080-1)/(873-1)-1), src_left=-((1920-1)/(1552-1)-1)/2, src_top=-((1080-1)/(873-1)-1)/2,
                               format=vs.YUV444P16)
    cclip = join(descale, cclip)
    cclip = cclip.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                                 width=1600, height=896, src_width=1600, src_height=896, src_left=-24, src_top=-11,
                                 format=vs.RGBS, range=1)
    
    cclip = vsmlrt.inference(cclip, SPath(vsmlrt.models_path) / "anime-segmentation" / "isnet_is.onnx", backend=vsmlrt.Backend.TRT(fp16=True))
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
    cclip = cclip.resize.Bicubic(filter_param_a=0, filter_param_b=0.5,
                                 width=3104, height=1746, src_width=1552, src_height=873, src_left=24, src_top=11)
    cclip = gauss_blur(cclip, sigma=1.6)
    cclip = Morpho.maximum(cclip, iterations=1)
    cclip = depth(cclip, 16, dither_type=DitherType.NONE)

    doubled = rs.doubled
    uniform_mask = doubled.std.PlaneStats(prop="Brightness")
    uniform_mask = uniform_mask.akarin.PropExpr(dict=lambda: dict(BrightnessThr="x.BrightnessAverage 65535 *"))
    uniform_mask = uniform_mask.akarin.PropExpr(dict=lambda: dict(BrightnessMultipler="65535 x.BrightnessThr 4096 - 0.1 max 0.51 * /"))
    uniform_mask = uniform_mask.akarin.Expr("""x.BrightnessThr x - x.BrightnessMultipler *""")
    uniform_mask = Morpho.opening(uniform_mask, radius=5)
    uniform_mask = gauss_blur(uniform_mask, sigma=0.8)
    uniform_mask = Morpho.erosion(uniform_mask, radius=1)

    aa_mask = core.akarin.Expr([cclip, uniform_mask], "x y min")

    aa = based_aa(doubled, supersampler=False, antialiaser=EEDI3(alpha=0.4), mask_thr=25)
    aa_diff = core.akarin.Expr([aa, doubled], "x y - 32768 +")
    aa = core.akarin.Expr([aa_diff, doubled], """
    x 32768 - diff!
    diff@ 0 >
                 x[-3,-4] x[-2,-4] x[-1,-4] x[0,-4] x[1,-4] x[2,-4] x[3,-4]
        x[-4,-3] x[-3,-3] x[-2,-3] x[-1,-3] x[0,-3] x[1,-3] x[2,-3] x[3,-3] x[4,-3]
        x[-4,-2] x[-3,-2] x[-2,-2] x[-1,-2] x[0,-2] x[1,-2] x[2,-2] x[3,-2] x[4,-2]
        x[-4,-1] x[-3,-1] x[-2,-1] x[-1,-1] x[0,-1] x[1,-1] x[2,-1] x[3,-1] x[4,-1]
        x[-4,0]  x[-3,0]  x[-2,0]  x[-1,0]          x[1,0]  x[2,0]  x[3,0]  x[4,0]
        x[-4,1]  x[-3,1]  x[-2,1]  x[-1,1]  x[0,1]  x[1,1]  x[2,1]  x[3,1]  x[4,1]
        x[-4,2]  x[-3,2]  x[-2,2]  x[-1,2]  x[0,2]  x[1,2]  x[2,2]  x[3,2]  x[4,2]
        x[-4,3]  x[-3,3]  x[-2,3]  x[-1,3]  x[0,3]  x[1,3]  x[2,3]  x[3,3]  x[4,3]
                 x[-3,4]  x[-2,4]  x[-1,4]  x[0,4]  x[1,4]  x[2,4]  x[3,4]
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min
        min min min min min  min min min min min  min min min min min darken!
        diff@ 32768 darken@ - min
        diff@ ?
    y +
    """)

    aa = core.std.MaskedMerge(doubled, aa, aa_mask)
    rs.doubled = aa
    

    descale_mask = src.std.BlankClip(format=vs.GRAY16)

    def process_oped_mask(oped_mask):
        oped_mask = remove_grain(oped_mask, mode=remove_grain.Mode.MINMAX_AROUND2)
        oped_mask = oped_mask.akarin.Expr("""
        x
                     x[-3,-4] x[-2,-4] x[-1,-4] x[0,-4] x[1,-4] x[2,-4] x[3,-4]
            x[-4,-3] x[-3,-3] x[-2,-3] x[-1,-3] x[0,-3] x[1,-3] x[2,-3] x[3,-3] x[4,-3]
            x[-4,-2] x[-3,-2] x[-2,-2] x[-1,-2] x[0,-2] x[1,-2] x[2,-2] x[3,-2] x[4,-2]
            x[-4,-1] x[-3,-1] x[-2,-1]                          x[2,-1] x[3,-1] x[4,-1]
            x[-4,0]  x[-3,0]  x[-2,0]                           x[2,0]  x[3,0]  x[4,0]
            x[-4,1]  x[-3,1]  x[-2,1]                           x[2,1]  x[3,1]  x[4,1]
            x[-4,2]  x[-3,2]  x[-2,2]  x[-1,2]  x[0,2]  x[1,2]  x[2,2]  x[3,2]  x[4,2]
            x[-4,3]  x[-3,3]  x[-2,3]  x[-1,3]  x[0,3]  x[1,3]  x[2,3]  x[3,3]  x[4,3]
                     x[-3,4]  x[-2,4]  x[-1,4]  x[0,4]  x[1,4]  x[2,4]  x[3,4]
            sort68 drop61 measure! drop6
            measure@ 0 ?
        """)
        oped_mask = Morpho.expand(oped_mask, sw=1)
        oped_mask = Morpho.inflate(oped_mask, radius=3, iterations=2)
        oped_mask = Morpho.closing(oped_mask, radius=3)
        return oped_mask

    if sources[episode].op is not None:
        op_mask = diff_creditless(src[sources[episode].op[0]+534:sources[episode].op[0]+609], op[534:609],
                                  thr=0.36, expand=-2, prefilter=True)
        op_mask = process_oped_mask(op_mask)
        descale_mask = insert_clip(descale_mask, op_mask, start_frame=sources[episode].op[0]+534)

    if sources[episode].ed is not None:
        assert sources[episode].ed[1] - sources[episode].ed[0] <= ed.num_frames

        if sources[episode].ed_type == 1:
            ed_mask = diff_creditless(src[sources[episode].ed[0]:sources[episode].ed[1]], ed,
                                      thr=0.18, expand=-2, prefilter=True)
        else:
            ed_mask = diff_creditless(src[sources[episode].ed[0]:sources[episode].ed[1]], ed,
                                      thr=0.36, expand=-2, prefilter=True)
        ed_mask = process_oped_mask(ed_mask)
        descale_mask = insert_clip(descale_mask, ed_mask, start_frame=sources[episode].ed[0])

    title_card_mask = descale_mask.std.BlankClip(format=vs.GRAY16, color=[65535])
    descale_mask = replace_ranges(descale_mask, title_card_mask, sources[episode].title_cards, exclusive=True)

    descale_mask = replace_ranges(descale_mask, preview_card_mask, sources[episode].preview_cards, exclusive=True)

    rs.credit_mask = descale_mask


    src_y = get_y(src)
    line_mask = RScharr().edgemask(src_y)
    line_mask = Morpho.maximum(line_mask)
    line_mask = line_mask.akarin.Expr("x 4800 > x 2 * 0 ? cont! cont@ 14400 > cont@ 14400 - 6 * 14400 + cont@ ?")
    line_mask = Morpho.inflate(line_mask, radius=1)
    
    rs.line_mask = line_mask


    ds = rs.upscale

    ds = Sar.from_clip(src).apply(ds)


    db_cclip = cclip.resize.Bilinear(width=1920, height=1080, src_width=2*1920*(1552-1)/(1920-1), src_height=2*1080*(873-1)/(1080-1), src_left=(1552-1)/(1920-1)-1, src_top=(873-1)/(1080-1)-1)
    db_cclip = Morpho.inflate(db_cclip, radius=1)
    
    dn_cclip = db_cclip.resize.Bilinear(width=240, height=135)
    dn_cclip = remove_grain(dn_cclip, mode=remove_grain.Mode.BINOMIAL_BLUR)
    dn_cclip = dn_cclip.akarin.Expr("x 3.5 * 65535 0.35 * max")
    dn_cclip = dn_cclip.resize.Point(width=1920, height=1080)
    
    ref = mc_degrain(ds, prefilter=Prefilter.DFTTEST(sloc={0.0:0.4, 0.4:0.6, 0.6:5.0, 1.0:8.0}), refine=2, thsad=160, tr=1)
    dn = bm3d(ds, ref=ref, sigma=1.07, tr=0, refine=2, profile=bm3d.Profile.LOW_COMPLEXITY, planes=[0])
    dn = core.std.MaskedMerge(ds, dn, dn_cclip, planes=[0])
    dn = nl_means(dn, ref=ref, h=0.21, tr=2, planes=[1, 2])

    db = pfdeband(dn, debander=placebo_deband, thr=1.8, radius=12.0, dark_thr=0.4, bright_thr=0.4, elast=2.0)
    db = core.std.MaskedMerge(dn, db, db_cclip)


    final = finalize_clip(db)
    return final



def main_filterchain(episode):
    src = core.ffms2.Source(SPath("Intermediate") / f"{episode}.mkv",
                            cachefile=SPath("Intermediate") / f"{episode}.mkv.ffms2")
    src = initialize_clip(src)

    rg = adaptive_grain(src, strength=[1.5, 0.0], size=[2*(1552-1)/(1920-1), 2*(873-1)/(1080-1)],
                             luma_scaling=13.2, temporal_radius=5, temporal_average=50, seed=274810,
                             **ntype4)
    rg = adaptive_grain(rg, strength=[0.0, 4.0], size=[4*(1552-1)/(1920-1), 4*(873-1)/(1080-1)],
                            luma_scaling=13.2, temporal_radius=5, temporal_average=50, seed=274810,
                            **ntype4)

    final = finalize_clip(rg, dither_type=DitherType.NONE)
    return final
