#!/usr/bin/env python3

from vstools import core, vs

out = core.std.BlankClip(width=1920, height=1080, format=vs.YUV420P10, length=65, color=[192, 512, 512])
out = out.noise.Add(type=2, var=10.0, uvar=10.0, xsize=2.4, ysize=2.4)

out.set_output()
