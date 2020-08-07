CAMERAS = {'rpi':'http://localhost:8585/', 'rpzw':'http://192.168.1.249:8585/'}
# CAMERAS = {'rpzw':'http://192.168.1.249:8585/'}

PORT="/dev/ttyUSB0"
N_EXAMPLES=50
AXIS_REPS=2

SWEEP_RANGE=40

TOOL="joint-recording-one-axis"
DATA="data"

import base64
import datetime
import json
import os
import random
import time

from pydobot import pydobot
import requests

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

def startcams(fn):
    for name, url in CAMERAS.items():
        r = requests.get(url=url+'start', params={'fname': fn})
        print(f'startcams({name}): {r}')
        data = r.json()

def stopcams():
    for name, url in CAMERAS.items():
        r = requests.get(url=url+'stop')
        data = r.json()
        print(f'stopcams({name}): {data}')

def collectcams(fn):
    results = {}
    for name, url in CAMERAS.items():
        r = requests.get(url=url+'send', params={'fname': fn})
        resp = r.json()
        data = base64.b64decode(resp['data']) 
        print(data[:4])
        print(f'collectcams({name},{fn}): {len(data)//1024}kb')
        if len(data) != resp['size']:
            print('collectcams(): WARNING: bad size')
        results.update({name: data})
    return results

def promptexperiment():
    if os.path.exists("jointrecording.json"):
        last = json.loads(open("jointrecording.json", "r").read())
    else:
        last = "new experiment"
    experiment = input(f'Enter name of experiment [{last}]:\n')
    experiment = experiment if experiment else last
    exp = experiment.lower().replace(r'[^a-z0-9-]+', '')
    open("jointrecording.json", "w").write(json.dumps(exp))
    return exp

def init():
    print(f'camera sources: {CAMERAS}')
    exp = promptexperiment()
    path = os.path.join(DATA, TOOL, f'{exp}-{timestamp()}')
    os.makedirs(path, exist_ok=True)
    print(f'path: {path}')

    dev = botstart()

    for i in range(N_EXAMPLES):
        rs1 = botstate(dev)
        print(f'rs1: {rs1}')
        ts = timestamp()

        test_slug = f"{i}-{ts}"

        jf = os.path.join(path, f"{test_slug}-joints.json")

        startcams(test_slug)
        
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

        stopcams()
        vids = collectcams(test_slug)
        for cam, data in vids.items():
            vf = os.path.join(path, f"{test_slug}-{cam}.h264")
            open(vf, 'wb').write(data)

        move(dev, rs1)
        time.sleep(0.1)
        print(f"path: {path}")

    dev.close()

init()
