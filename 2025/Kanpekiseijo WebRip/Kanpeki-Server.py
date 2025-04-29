#!/usr/bin/env python3

# Dispatch-Server
# Copyright (c) Akatsumekusa and contributors

# ---------------------------------------------------------------------
# These are the configs you will need to adjust based on your filtering
# vpy script and your system.
# ---------------------------------------------------------------------
# This `necessary_cpu` parameter denotes the expected amount of CPU
# used for each worker. This is the percentage of the CPU used with
# `100` denoting fully utilising all CPU threads on the system.
# 
# You should set this number to match the CPU usage for filtering, or
# encoding, whichever one is higher. There are next to no consequence
# to slightly underutilising or overloading your CPU. This parameter
# doesn't need to be very precise.
# 
# As an example, if your filtering doesn't use much CPU and you are
# using `--lp 3` on a system with 32 threads, you can set this value to
# `4 / 32 * 100` or `3 / 32 * 100` depending on your taste.
# If otherwise your filtering is CPU intensive, you should observe how
# much CPU it uses and set it accordingly. For example, if your
# filtering uses somewhere between 6 to 8 threads and you're still
# using `--lp 3` for encoding, set this to `7 / 32 * 100`.
necessary_cpu = 20
# ---------------------------------------------------------------------
# This `required_vram` parameter denotes the maximum amount of VRAM
# used for each worker in bytes.
# 
# Run VSPipe and filter to `/dev/null` and observe the amount of VRAM
# used. You should set this slightly higher than the number you
# observe just to be on the safe side.
#
# As an example, if your filtering is observed to use around 3.5 GiB of
# VRAM, set this to 3.75 GiB or `3.75 * 1073741824` just to be on the
# safe side.
#
# If you are just using the dispatch server for optimising CPU usage,
# and you don't care about VRAM, set this to `0`.
required_vram = 3.5 * 1073741824
# ---------------------------------------------------------------------
# It often takes time for filters to load and start processing frames.
# VRAM usage will gradually ramp up during this loading time, and it
# will be bad if we release a new worker while this is in progress. The
# dispatch server is designed to reserve the `necessary_cpu` and
# `required_vram` for newly released workers until it starts filtering
# and encoding.
# This `released_reserve_time` denotes the amount of time in
# nanoseconds during which `necessary_cpu` and `required_vram` will be
# reserved and subtracted from free CPU and VRAM calculation.
#
# Run VSPipe and observe how long it takes for it to occupy full VRAM.
# You should set this slightly higher than the amount of time you
# observe since it may load slower when CPU is near full. If at any
# time during the actual encoding that too much workers have been
# released that VRAM is completly exhausted while the encoding grinds
# to a halt, provided that you've set `required_vram` properly,
# increase this number.
# 
# If VRAM is not your problem and you're just using the dispatch server
# to optimise CPU usage, set it to something in the range of 1 to 2
# seconds or `1 * 1000000000` to  `2 * 1000000000`.
released_reserve_time = 12 * 1000000000
# ---------------------------------------------------------------------
# If you're not using a NVIDIA GPU, search for `nvml` in this script
# and replace it with a monitoring tool for your GPU brand.
# ---------------------------------------------------------------------
# Set the port used by the dispatch server. You can set it to any port
# of your preference, as long as you set it the same in `Server.py`,
# `Server-Shutdown.py` and your filtering vpy script.
port = 18861
# ---------------------------------------------------------------------
# You can set the maximum amount of CPU used for the dispatch server to
# release a new thread by setting "USAGE" in environment variable. This
# is for the case you want to perform other task on the system while
# the encoding is running. As an example, to only release a new worker
# when CPU dips below 60, run `USAGE=60 python Dispatch-Server.py &`.
import os
if "USAGE" in os.environ:
    usage = float(os.environ["USAGE"])
else:
    usage = 100 - necessary_cpu
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ---------------------------------------------------------------------

from psutil import cpu_percent
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
from time import sleep, time_ns
from threading import Lock
from rpyc import Service, ThreadedServer

nvmlInit()
handle = nvmlDeviceGetHandleByIndex(0)

class QueueService(Service):
    lock = Lock()
    queue = []
    released_reserve = []
    last_contact_first_in_queue = time_ns()

    def locked_clean_reserve(self):
        self.released_reserve = [item for item in self.released_reserve if item > time_ns()]

    def locked_reset_first_in_queue(self):
        self.last_contact_first_in_queue = time_ns()

    def locked_check_first_in_queue(self, tid):
        if self.queue[0] == tid:
            self.locked_reset_first_in_queue()
        else:
            if self.last_contact_first_in_queue < time_ns() - 10000000000:
                self.queue.pop(0)
                self.locked_reset_first_in_queue()

    def exposed_register(self):
        with self.lock:
            sleep(0.001)
            tid = time_ns()
            self.queue.append(tid)

            self.locked_check_first_in_queue(tid)

            return tid

    def exposed_request_release(self, tid):
        with self.lock:
            self.locked_check_first_in_queue(tid)

            if self.queue[0] == tid or tid not in self.queue:
                self.locked_clean_reserve()

                free = nvmlDeviceGetMemoryInfo(handle).free - required_vram * len(self.released_reserve)
                cpu = cpu_percent(interval=0.1) + necessary_cpu * len(self.released_reserve)
                if free >= required_vram and cpu < usage:
                    self.queue.pop(0)
                    self.released_reserve.append(time_ns() + released_reserve_time)

                    self.locked_reset_first_in_queue()

                    return True
                    
            return False

    def exposed_shutdown(self):
        server.close()

server = ThreadedServer(QueueService(), port=port)
server.start()
