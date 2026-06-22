from dataclasses import dataclass
import os
from vstools import FrameRangeN, FrameRangesN, SPath
from typing import Literal


assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])


@dataclass
class Source:
    source: SPath | None = None
    source_s: SPath | None = None
    op: FrameRangeN | None = None
    op_type: Literal[1, 2] | None = None
    op_offset: int | None = None # Sparkles 19 frames after start
    ed: FrameRangeN | None = None
    outro: FrameRangeN | None = None
    side: FrameRangeN | None = None
    preview: FrameRangeN | None = None


sources = {
    "01": Source(op=(1654, 3813), op_type=1, op_offset=1,
                 ed=(30881, 33038),
                 outro=(33038, 33926)),
    "02": Source(op=(2566, 4723), op_type=1, op_offset=0,
                 ed=(30737, 32894),
                 outro=(32894, 33926)),
    "03": Source(op=(600, 2758), op_type=1, op_offset=0,
                 ed=(31099, 33256),
                 outro=(32894, 33928)),
    "04": Source(op=(1152, 3309), op_type=1, op_offset=0,
                 ed=(31505, 33663),
                 outro=(33663, 33927)),
    "05": Source(op=(912, 3069), op_type=1, op_offset=0,
                 ed=(30786, 32943),
                 side=(32943, 33927)),
    "06": Source(op=(3045, 5203), op_type=2, op_offset=0,
                 ed=(30809, 32966),
                 side=(32966, 33926)),
    "07": Source(op=(1104, 3261), op_type=2, op_offset=0,
                 ed=(31768, 33926)),
    "08": Source(op=(3213, 5371), op_type=2, op_offset=0,
                 ed=(26280, 28437),
                 outro=(28437, 33926)),
    "09": Source(op=(1918, 4077), op_type=2, op_offset=0,
                 preview=(33926, None)),
    "10": Source(op=(2350, 4507), op_type=2, op_offset=0,
                 ed=(31768, 33926),
                 preview=(33926, None)),
    "11": Source(op=(456, 2614), op_type=2, op_offset=0,
                 outro=(33475, 33926),
                 preview=(33926, None)),
    "12": Source(op=(6738, 8894), op_type=2, op_offset=0,
                 ed=(29993, 32152),
                 outro=(32152, None))
}

for episode in sources:
    matches = list(raws.glob(f"A*.S01E{episode}.*.JPN.*b.mkv"))
    assert(len(matches) == 1), str(matches)
    sources[episode].source = matches[0]

for episode in sources:
    matches = list(raws.glob(f"[S* - {episode} *.mkv"))
    assert(len(matches) == 1), str(matches)
    sources[episode].source_s = matches[0]
