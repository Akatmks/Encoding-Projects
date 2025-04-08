#!/usr/bin/env python3

import os
import rpyc
import sys

port = 18860 + int(os.environ["EPISODE"])
c = rpyc.connect("localhost", port)

try:
    c.root.shutdown()
except EOFError:
    pass
