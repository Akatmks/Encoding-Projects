from dataclasses import dataclass
import os
from vstools import FrameRangeN, FrameRangesN, SPath
from typing import Literal


assert "VOL_01_BDMV_DIR" in os.environ
assert "VOL_02_BDMV_DIR" in os.environ
assert "WEB_DL_DIR" in os.environ

vol_01_bdmv = SPath(os.environ["VOL_01_BDMV_DIR"])
vol_02_bdmv = SPath(os.environ["VOL_02_BDMV_DIR"])
web_dl = SPath(os.environ["WEB_DL_DIR"])


@dataclass
class Source:
    source_bd: SPath
    source_web: SPath | None = None
    op: FrameRangeN | None = None
    op_type: Literal[1, 2, 3, 4] | None = None # 1: Red, 2: Tan, 3: Teal, 4: Gold
    ed: FrameRangeN | None = None
    text: FrameRangesN | None = None


sources = {
    "01": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(4531, 6690), op_type=1, # Every episode 2159
                 ed=(34813, 36971),
                 text=[(6762, 6882), (36971, None)]),
    "02": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00004.m2ts",
                 op=(0, 2159), op_type=1,
                 ed=(32200, 34357),
                 text=[(2231, 2417), (34357, 34477), (34477, None)]),
    "03": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00005.m2ts",
                 op=(528, 2687), op_type=1,
                 ed=(32488, 34647),
                 text=[(2687, 2885), (34647, None)]),
    "04": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00006.m2ts",
                 op=(0, 2159), op_type=1,
                 ed=(32488, 34645),
                 text=[(3795, 3965), (34645, None)]),
    "05": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00007.m2ts",
                 op=(1152, 3309), op_type=2, # 2157
                 ed=(32487, 34644),
                 text=[(3597, 3801), (34644, None)]),
    "06": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00008.m2ts",
                 op=(1152, 3309), op_type=3, # 2157
                 ed=(32488, 34645),
                 text=[(3309, 3549), (34645, None)]),
    "07": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00002.m2ts",
                 op=(576, 2735), op_type=3,
                 ed=(32489, 34646),
                 text=[(2795, 2945), (34646, None)]),
    "08": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00003.m2ts",
                 op=(0, 2159), op_type=3,
                 ed=(32489, 34646),
                 text=[(3046, 3262), (34646, None)]),
    "09": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00005.m2ts",
                 op=(1703, 3861), op_type=3, # 2158
                 ed=(32488, 34645),
                 text=[(1068, 1248), (34645, None)]),
    "10": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00006.m2ts",
                 op=(744, 2903), op_type=3,
                 ed=(32489, 34646),
                 text=[(2903, 3083), (34646, None)]),
    "11": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00007.m2ts",
                 op=(0, 2159), op_type=3,
                 ed=(32489, 34646),
                 text=[(2159, 2358), (34646, None)]),
    "12": Source(source_bd=vol_02_bdmv / "BDMV" / "STREAM" / "00008.m2ts",
                 op=(0, 2159), op_type=4,
                 ed=(32247, None),
                 text=[(2159, 2371)]),
    "NCOP01": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00009.m2ts",
                     op=(0, None)),
    "NCOP02": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00010.m2ts",
                     op=(0, None)),
    "NCOP03": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00015.m2ts",
                     op=(0, None)),
    "NCOP04": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00016.m2ts",
                     op=(0, None)),
    "NCED": Source(source_bd=vol_01_bdmv / "BDMV" / "STREAM" / "00017.m2ts",
                   ed=(0, None)),
}

for episode in sources:
    if matches := list(web_dl.glob(f"[S* - {episode} *")):
        assert(len(matches) == 1)
        sources[episode].source_web = matches[0]
