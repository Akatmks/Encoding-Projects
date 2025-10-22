from dataclasses import dataclass

@dataclass
class Source:
    episode: str
    source: SPath
    op: Trim | None = None
    ed: Trim | None = None
