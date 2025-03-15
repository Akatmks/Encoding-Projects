#!/usr/bin/env python3

import os
from psutil import cpu_percent
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
from time import sleep, time_ns
from threading import Lock
from rpyc import Service, ThreadedServer

required_vram = 4831838208
released_reserve_time = 8000000000
usage = float(os.environ["USAGE"])
port = 18860 + int(os.environ["EPISODE"])

nvmlInit()
handle = nvmlDeviceGetHandleByIndex(0)

class QueueService(Service):
    lock = Lock()
    queue = []
    released_reserve = []

    def locked_clean_reserve(self):
        self.released_reserve = [item for item in self.released_reserve if item > time_ns()]

    def exposed_register(self):
        with self.lock:
            sleep(0.001)
            tid = time_ns()
            self.queue.append(tid)
            return tid

    def exposed_request_release(self, tid):
        with self.lock:
            if self.queue[0] == tid or tid not in self.queue:
                self.locked_clean_reserve()

                free = nvmlDeviceGetMemoryInfo(handle).free - required_vram * len(self.released_reserve)
                if free >= required_vram and cpu_percent(interval=0.1) < usage:
                    self.queue.pop(0)
                    self.released_reserve.append(time_ns() + released_reserve_time)
                    return True
                    
            return False

    def exposed_shutdown(self):
        server.close()

server = ThreadedServer(QueueService(), port=port)
server.start()
