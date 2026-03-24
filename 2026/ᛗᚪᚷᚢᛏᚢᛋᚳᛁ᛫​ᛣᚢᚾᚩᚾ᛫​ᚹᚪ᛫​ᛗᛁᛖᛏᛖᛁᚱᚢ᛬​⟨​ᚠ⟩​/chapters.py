import os
import sys
sys.path.insert(0, os.getcwd())

from sources import sources


assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources

source = sources[episode]


def frame_to_timestamp(frame_number):
    # Precise duration calculation
    total_ms = round((frame_number * 1001) / 24)  # Math: (F * 1001 / 24000) * 1000
    
    # Use divmod to carry overflows up the chain
    # divmod(a, b) returns (a // b, a % b)
    total_seconds, milliseconds = divmod(total_ms, 1000)
    total_minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(total_minutes, 60)
    
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"


with open(f"Misc/Chapters/{episode}.txt", "w") as f:
    i = 1

    if source.op[0] != 0:
        f.write(f"CHAPTER{i:02}={frame_to_timestamp(0)}\n")
        f.write(f"CHAPTER{i:02}NAME=Avant\n")
        i += 1

    f.write(f"CHAPTER{i:02}={frame_to_timestamp(source.op[0])}\n")
    f.write(f"CHAPTER{i:02}NAME=Opening\n")
    i += 1

    f.write(f"CHAPTER{i:02}={frame_to_timestamp(source.op[1])}\n")
    f.write(f"CHAPTER{i:02}NAME=Episode\n")
    i += 1

    f.write(f"CHAPTER{i:02}={frame_to_timestamp(source.ed[0])}\n")
    f.write(f"CHAPTER{i:02}NAME=Ending\n")
    i += 1

    if (source.outro != None):
        f.write(f"CHAPTER{i:02}={frame_to_timestamp(source.ed[1])}\n")
        f.write(f"CHAPTER{i:02}NAME=Outro\n")
        i += 1

        if (source.outro[1] != None):
            f.write(f"CHAPTER{i:02}={frame_to_timestamp(source.outro[1])}\n")
            f.write(f"CHAPTER{i:02}NAME=Preview\n")
            i += 1

    elif (source.ed[1] != None):
        f.write(f"CHAPTER{i:02}={frame_to_timestamp(source.ed[1])}\n")
        f.write(f"CHAPTER{i:02}NAME=Preview\n")
        i += 1
