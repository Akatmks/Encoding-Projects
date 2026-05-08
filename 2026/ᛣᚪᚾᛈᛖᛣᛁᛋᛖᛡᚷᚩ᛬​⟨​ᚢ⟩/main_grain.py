from vstools import SPath

file = SPath("grain.bin")

seed_pool = [65506, 65501, 65484, 65476, 65466, 65464, 65420, 65417, 65391, 65345, 65333, 65299,
             65260, 64921, 64917, 64831, 64774, 64693, 64448, 64436, 64435, 64423, 64384, 64332,
             64285, 64274, 64240, 64189, 64176, 64126, 64113, 64093, 63947, 63647, 63580, 63507,
             63504, 63456, 63023, 62518, 62359, 62258, 62156, 62143, 62040, 61851, 61692, 61482,
             61476, 60973, 60878, 60711, 60619, 60584, 60537, 60501, 60123, 59991, 59929, 59846,
             59724, 59669, 59665, 59637, 59625, 59621, 59180, 59119]

size = 40000

import random

seeds = [63504]

while(len(seeds) < size):
    n = random.choice(seed_pool)

    if n not in seeds[-32:]:
        seeds.append(n)

with file.open("wb") as f:
    for seed in seeds:
        f.write((1).to_bytes(4, byteorder="little", signed=True))
        f.write((seed).to_bytes(2, byteorder="little", signed=False))
        f.write((1).to_bytes(4, byteorder="little", signed=True))

        for n in "7 0 0 16 0 18 8 70 7 234 4 235 0 255 0".split():
            f.write((int(n)).to_bytes(4, byteorder="little", signed=True))
        f.write((0).to_bytes(4, byteorder="little", signed=True))
        f.write((0).to_bytes(4, byteorder="little", signed=True))
        f.write((9).to_bytes(4, byteorder="little", signed=True))

        f.write((3).to_bytes(4, byteorder="little", signed=True))
        for n in "3 4 3 3 3 3 3 3 4 2 0 2 3 3 3 2 -7 -19 -4 1 3 2 0 -18".split():
            f.write((int(n)).to_bytes(4, byteorder="little", signed=True))
        f.write((7).to_bytes(4, byteorder="little", signed=True))
        f.write((0).to_bytes(4, byteorder="little", signed=True))

        f.write((1).to_bytes(4, byteorder="little", signed=True))
        f.write((1).to_bytes(4, byteorder="little", signed=True))
