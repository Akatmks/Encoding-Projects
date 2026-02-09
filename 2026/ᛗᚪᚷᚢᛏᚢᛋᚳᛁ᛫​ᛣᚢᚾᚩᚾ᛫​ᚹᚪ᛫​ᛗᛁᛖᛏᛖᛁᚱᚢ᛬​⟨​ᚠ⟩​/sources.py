from dataclasses import dataclass
import os
from vstools import FrameRangeN, FrameRangesN, SPath


assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])


@dataclass
class Source:
    source: SPath | None = None
    source_s: SPath | None = None
    op: FrameRangeN | None = None


sources = {
    "01": Source(op=(4269, 6426)), # Every episode 2157
    "02": Source(op=(2830, 4987)),
    "03": Source(op=(2734, 4891)),
    "04": Source(op=(3285, 5443)), # 2158!
    "05": Source(op=(1894, 4053)), # 2159!
    "06": Source(op=(864, 3021)),
    "07": Source(op=(2422, 4579))
}

for episode in sources:
    matches = list(raws.glob(f"[E* - {episode} *"))
    assert(len(matches) == 1)
    sources[episode].source = matches[0]

for episode in sources:
    matches = list(raws.glob(f"[S* - {episode} *"))
    assert(len(matches) == 1)
    sources[episode].source_s = matches[0]
