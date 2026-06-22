from dataclasses import dataclass
import os
from vstools import FrameRangeN, FrameRangesN, SPath
from typing import Literal


assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])


@dataclass
class Source:
    source_j: SPath | None = None
    source_d: SPath | None = None
    source_m: SPath | None = None
    op: FrameRangeN | None = None
    op_type: Literal[1, 2] | None = None
    ed: FrameRangeN | None = None
    ed_as_op: bool = False
    preview: FrameRangeN | None = None


sources = {
    "01": Source(op=(30354, 32513), op_type=1, # in when chapters!
                 ed=(33687, 35126),
                 preview=(35126, None)),
    "02": Source(op=(528, 2686), op_type=1,
                 ed=(29995, 32154),
                 preview=(33688, None)),
    "03": Source(op=(0, 2158), op_type=1,
                 ed=(31527, 34404),
                 preview=(34404, None)),
    "04": Source(op=(3261, 5419), op_type=1,
                 ed=(30952, 33109),
                 preview=(33685, None)),
    "05": Source(op=(1080, 3237), op_type=1,
                 ed=(31328, 33687),
                 preview=(33687, None)),
    "06": Source(op=(3093, 5251), op_type=1,
                 ed=(31528, 33686),
                 preview=(33686, None)),
    "07": Source(op=(1798, 3957), op_type=1,
                 ed=(33687, 35844),
                 preview=(35844, None)),
    "08": Source(op=(1918, 4077), op_type=1,
                 ed=(31098, 33255),
                 preview=(33687, None)),
    "09": Source(op=(1392, 3549), op_type=1,
                 ed=(27765, 29924),
                 preview=(35844, None)),
    "10": Source(op=(336, 2494), op_type=1,
                 ed=(33399, 35557),
                 preview=(36564, None)),
    "11": Source(op=(0, 2158), op_type=2,
                 ed=(31526, 33685),
                 preview=(33685, None)),
}

for episode in sources:
    matches = list(raws.glob(f"N*.S01E{episode}.*JPN.*b.mkv"))
    assert(len(matches) == 1)
    sources[episode].source_j = matches[0]

    matches = list(raws.glob(f"N*.S01E{episode}.*DUAL.*b.mkv"))
    if (len(matches) == 1):
        assert(len(matches) == 1)
        sources[episode].source_d = matches[0]

    matches = list(raws.glob(f"N*.S01E{episode}.*MULTi.*b.mkv"))
    if (len(matches) == 1):
        assert(len(matches) == 1)
        sources[episode].source_m = matches[0]
