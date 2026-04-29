from vsmuxtools import FFV1, settings_builder_5fish_svt_av1_psy, settings_builder_x265, Setup, SVTAV1, x265
from vstools import SPath

from sources import intermediates, main_encodes, mini_encodes


def intermediate(episode, final):
    Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")

    FFV1().encode(final, outfile=intermediates[episode])



def main(episode, final):
    Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")

    settings = settings_builder_x265(asm="avx512", hist_scenecut="", frames=final.num_frames,
                                     crf=11.30, aq_mode=5, aq_strength=0.60)
    x265(settings, resumable=False, csv=False).encode(final, outfile=main_encodes[episode])



def mini(episode, final, src_sd):
    Setup(episode, config_file=None, work_dir=SPath("Temp") / f"{episode}.vsmuxtools.tmp")

    fgs_table = SPath("grain.tbl")
    settings = settings_builder_5fish_svt_av1_psy(preset=2,
                                                  crf=24.40,
                                                  lineart_psy_bias=6,
                                                  texture_psy_bias=3,
                                                  hierarchical_levels=4,
                                                  balancing_luminance_lambda_bias=0.5,
                                                  psy_bias_optimize_b=1,
                                                  dlf_bias_min_dlf="0,0",
                                                  fgs_table=str(fgs_table))
    SVTAV1(**settings, sd_clip=src_sd).encode(final, outfile=mini_encodes[episode])
