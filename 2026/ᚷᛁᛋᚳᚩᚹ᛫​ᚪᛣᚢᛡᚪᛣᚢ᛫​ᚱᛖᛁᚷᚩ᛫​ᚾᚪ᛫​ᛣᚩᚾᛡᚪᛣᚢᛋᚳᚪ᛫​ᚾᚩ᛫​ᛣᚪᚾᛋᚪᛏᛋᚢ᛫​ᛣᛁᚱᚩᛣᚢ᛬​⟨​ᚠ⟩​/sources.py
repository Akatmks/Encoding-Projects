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
    ed: FrameRangeN | None = None
    outro: FrameRangeN | None = None


sources = {
    "01": Source(op=(1654, 3813),
                 ed=(30881, 33038),
                 outro=(33038, 33926))
}

for episode in sources:
    matches = list(raws.glob(f"A*.S01E{episode}.*b.mkv"))
    assert(len(matches) == 1)
    sources[episode].source = matches[0]

for episode in sources:
    matches = list(raws.glob(f"[S* - {episode} *.mkv"))
    assert(len(matches) == 1)
    sources[episode].source_s = matches[0]
