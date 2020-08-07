PORT="/dev/ttyUSB0"
N_EXAMPLES=50
AXIS_REPS=10

SWEEP_RANGE=40

TOOL="joint-recording-one-axis"
DATA="data"

import datetime
import json
import os
import random
import time

from picamera import PiCamera
from pydobot import pydobot

def botstart():
    device = pydobot.Dobot(port=PORT, verbose=True)
    (x, y, z, r, j1, j2, j3, j4) = botstate(device)
    print(f'botstart() x:{x} y:{y} z:{z} j1:{j1} j2:{j2} j3:{j3} j4:{j4}')
    return device

def botstate(device):
    pose = device.pose()
    return pose

def timestamp():
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')

def move(dev, coord):
    if len(coord) == 8:
        (x, y, z, r, j1, j2, j3, j4) = coord
    else:
        (x, y, z, r) = coord
    res = dev.move_to(x, y, z, r, wait=True)
    print(f'move(): {res}')

_lucky_axis = "x"
def tweak(axis, value):
    global _lucky_axis
    if random.randint(0, AXIS_REPS) == 0:
        _lucky_axis = random.choice(["x", "y", "z", "r"])
        print(f"new lucky axis: {_lucky_axis}")

    if _lucky_axis == axis:
        return value + random.randint(SWEEP_RANGE * -1, SWEEP_RANGE)
    else:
        return value

def init():
    experiment = input('Enter name of experiment:\n')
    exp = experiment.lower().replace(r'[^a-z0-9-]+', '');
    path = os.path.join(DATA, TOOL, exp, timestamp())
    os.makedirs(path, exist_ok=True)
    print(f'path: {path}')

    camera = PiCamera()
    dev = botstart()

    for i in range(N_EXAMPLES):
        rs1 = botstate(dev)
        print(f'rs1: {rs1}')
        ts = timestamp()

        jf = os.path.join(path, f"{i}-{ts}-joints.json")
        vf = os.path.join(path, f"{i}-{ts}.h264")
        
        camera.start_preview()
        camera.start_recording(vf)
        time.sleep(0.5)
        
        (x, y, z, r, j1, j2, j3, j4) = rs1

        goal = (tweak('x', x), tweak('y', y), tweak('z', z), tweak('r', r))
        print(f'goal: {goal}')
        # todo check validity

        res = move(dev, goal)
        print(f'move_to(): {res}')
        rs2 = botstate(dev)
        print(f'rs2: {rs2}')
        rsj = json.dumps({"from": rs1, "to": rs2, "goal": goal})
        open(jf, 'w').write(rsj)
        time.sleep(0.5)
        camera.stop_recording()
        camera.stop_preview()

        move(dev, rs1)
        time.sleep(0.1)
        print(f"path: {path}")

    dev.close()

init()
