import os
import sys
sys.path.insert(0, os.getcwd())

import json
from vsmuxtools.utils.source import generate_keyframes
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from vstools import core, SPath

from sources import sources



assert "EPISODE" in os.environ
episode = os.environ["EPISODE"]
assert episode in sources



cache = SPath("Temp") / f"{episode}.cfg"

if sources[episode].source_web:
    print(f"\033[1mSource:\033[0m \t{sources[episode].source_web.name}")
    clip = core.bs.VideoSource(sources[episode].source_web, showprogress=False)
else:
    print(f"\033[1mSource:\033[0m \t{sources[episode].source_bd.name}")
    clip = core.bs.VideoSource(sources[episode].source_bd, showprogress=False)



min_scene_length = 129
min_still_scene_length = 193
max_scene_length = 321

frames = generate_keyframes(clip, 0)

diff_clip = clip.std.PlaneStats(clip[0] + clip, plane=0, prop="Luma")

frames.append(len(clip))
head = -1  # Because the result from generate_keyframes doesn't have `0`
current_frame = 0
svt_av1_frames = [0]
while head < len(frames) - 1:
    head += 1

    # Choosing between WWXD selected frames within the limit of min_scene_length and max_scene_length
    if frames[head] - current_frame < min_scene_length:
        if head != len(frames) - 1:
            continue

        else:
            current_frame = frames[head]
            svt_av1_frames.append(current_frame)  # Only to get popped

    elif frames[head] - current_frame <= max_scene_length:
        available_frames = []
        for looka_head in range(head, len(frames)):
            if frames[looka_head] - current_frame <= max_scene_length:
                available_frames.append(frames[looka_head])
            else:
                break

        selected_head = None
        for structure in [16, 8, 4, 2]:
            for available_head in range(len(available_frames) - 1, -1, -1):
                if (available_frames[available_head] - current_frame) % structure == 1:
                    selected_head = available_head
                    break
            if selected_head is not None:
                break

        if selected_head is None:
            selected_head = len(available_frames) - 1

        head = head + selected_head
        current_frame = frames[head]
        svt_av1_frames.append(current_frame)

    # If WWXD doesn't select anything within max_scene_length, try finding good frames using diffs.
    else:
        selected_frame = None
        diffs = np.array(
            [
                frame.props["LumaDiff"]
                for frame in diff_clip[current_frame + min_still_scene_length : current_frame + max_scene_length + 1].frames()
            ]
        )
        windows = sliding_window_view(diffs, 25)
        median = np.median(windows, axis=1).reshape((-1, 1))
        mad = np.median(np.abs(windows - median), axis=1).reshape((-1, 1))
        thr = (median + 3.0 * mad).reshape((-1,))
        thr = np.concatenate((np.full((12,), thr[0]), thr, np.full((12,), thr[-1])))
        motion_frames = np.argwhere(diffs > thr).reshape((-1,))
        motion_frames += current_frame + min_still_scene_length

        if motion_frames.shape[0] != 0:
            for structure in [16, 8]:
                for frame in motion_frames[::-1]:
                    if (frame - current_frame) % structure == 1:
                        selected_frame = int(frame)
                        break
                if selected_frame is not None:
                    break

        if selected_frame is None:
            selected_frame = current_frame + max_scene_length

        head -= 1
        current_frame = selected_frame
        svt_av1_frames.append(current_frame)

svt_av1_frames.pop()



cache_config = {
    "frames": clip.num_frames,
    "scenecuts": svt_av1_frames,
}
with cache.open("w") as cache_f:
    json.dump(cache_config, cache_f)
