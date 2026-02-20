from dataclasses import dataclass
import os
from vstools import FrameRangeN, FrameRangesN, SPath
from typing import Literal


assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])


@dataclass
class Source:
    source: SPath | None = None
    source_t: SPath | None = None
    op: FrameRangeN | None = None
    op_type: Literal[1, 2, 3] | None = None # 1: Red, 2: Tan, 3: Teal
    ed: FrameRangeN | None = None
    text: FrameRangesN | None = None


sources = {
    "01": Source(op=(4531, 6690), op_type=1, # Every episode 2159
                 ed=(34813, 36971),
                 text=[(6762, 6882), (36971, None)]),
    "02": Source(op=(0, 2159), op_type=1,
                 ed=(32200, 34357),
                 text=[(2231, 2417), (34357, 34477), (34477, None)]),
    "03": Source(op=(528, 2687), op_type=1,
                 ed=(32488, 34647),
                 text=[(2687, 2885), (34647, None)]),
    "04": Source(op=(0, 2159), op_type=1,
                 ed=(32488, 34645),
                 text=[(3795, 3965), (34645, None)]),
    "05": Source(op=(1152, 3309), op_type=2,
                 ed=(32487, 34644),
                 text=[(3597, 3801), (34644, None)]),
    "06": Source(op=(1152, 3309), op_type=3,
                 ed=(32488, 34645),
                 text=[(3309, 3549), (34645, None)]),
    "07": Source(op=(576, 2735), op_type=3,
                 ed=(32489, 34646),
                 text=[(2795, 2945), (34646, None)]),
    "08": Source(op=(0, 2159), op_type=3,
                 ed=(32489, 34646),
                 text=[(3046, 3262), (34646, None)])
}

for episode in sources:
    if matches := list(raws.glob(f"[S* - {episode} *")):
        assert(len(matches) == 1)
        sources[episode].source = matches[0]

for episode in sources:
    if matches := list(raws.glob(f"C*.S01E{episode}*b.mkv")):
        assert(len(matches) == 1)
        sources[episode].source_t = matches[0]
