import argparse
from pathlib import Path
import pysubs2
from pysubs2.time import ms_to_frames, frames_to_ms

parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
parser.add_argument("--offset", type=int, default=0)
parser.add_argument("-o", "--output", type=Path, required=True)
args = parser.parse_args()

subs = pysubs2.load(args.input)
previous = {}
for line in subs:
    line.start = line.start + args.offset
    line.end = line.end + args.offset
    # line.start = frames_to_ms(ms_to_frames(line.start + args.offset, 24000/1001), 24000/1001)
    # line.end = frames_to_ms(ms_to_frames(line.end + args.offset, 24000/1001), 24000/1001)
subs.save(args.output)
