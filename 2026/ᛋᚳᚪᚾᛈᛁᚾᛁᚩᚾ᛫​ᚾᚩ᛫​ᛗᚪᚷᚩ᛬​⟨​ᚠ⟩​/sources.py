from dataclasses import dataclass
import os
from vstools import FrameRangeN, FrameRangesN, SPath


assert "RAWS_DIRECTORY" in os.environ, "You need to set environmental variable \"RAWS_DIRECTORY\" to the directory containing the source files"
raws = SPath(os.environ["RAWS_DIRECTORY"])


@dataclass
class Source:
    source: SPath | None = None
    source_t: SPath | None = None
    op: FrameRangeN | None = None
    ed: FrameRangeN | None = None
    text: FrameRangesN | None = None


sources = {
    "01": Source(op=(4531, 6690), # Every episode 2159
                 ed=(34813, 36971),
                 text=[(6762, 6882), (36971, None)]),
    "02": Source(op=(0, 2159),
                 ed=(32200, 34357),
                 text=[(2231, 2417), (34357, 34477), (34477, None)]),
    "03": Source(op=(528, 2687),
                 ed=(32488, 34647),
                 text=[(2687, 2885), (34647, None)]),
    "04": Source(op=(0, 2159),
                 ed=(32488, 34645),
                 text=[(3795, 3965), (34645, None)])
}

for episode in sources:
    matches = list(raws.glob(f"[S* - {episode} *"))
    assert(len(matches) == 1)
    sources[episode].source = matches[0]

for episode in sources:
    matches = list(raws.glob(f"C*.S01E{episode}*b.mkv"))
    assert(len(matches) == 1)
    sources[episode].source_t = matches[0]
