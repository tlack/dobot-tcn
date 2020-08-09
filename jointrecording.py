CAMERAS = {'rpi':'http://localhost:8585/', 'rpzw':'http://192.168.1.249:8585/'}
# CAMERAS = {'rpzw':'http://192.168.1.249:8585/'}

# Configure the bot environment
ROBOT="auriga"           # "auriga" or "dobot" for now
PORT="/dev/ttyUSB3"

# Configure this experiment:
N_EXAMPLES=50
AXIS_REPS=10      # how many movements per joint before choosing another?
SWEEP_RANGE=40    # XXX we should make these relative!

USE_REVIEW_TOOL=1
REVIEW_TOOL_COMMAND="vlc --play-and-exit {}"
PRE_DELAY=1
POST_DELAY=1
EXAMPLE_DELAY=0.5 # pause to resetup

TOOL="jointrecording"
DATA="data"

if ROBOT == "auriga":
    from auriga import Auriga
if ROBOT == "dobot":
    from pydobot import pydobot

import base64
import datetime
import json
import os
import random
import sys
import time

import requests

class BotAdapter:
    _pose = {}
    def start(self):
        pass
    def pose(self):
        pass
    def home(self):
        pass
    def move_wait(self, joints):
        pass
    def movable_joints(self):
        pass

class DobotAdapter(BotAdapter):
    def start(self):
        self.device = pydobot.Dobot(port=PORT, verbose=True)
        self._pose = self._getpose()
        self._home = self._pose;
    def _getpose(self):
        # TODO gripper
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        return {'x': x, 'y': y, 'z': z, 'r':j1, '1': j1, '2':j2, '3':j3, '4':j4};
    def pose(self):
        self._pose = _getpose()
        return self._pose
    def home(self):
        self.move_wait(self._home)
    def move_wait(self, joints):
        self.device.move_to(joints['x'], joints['y'], joints['z'], joints['r'], wait=True)
    def movable_joints(self):
        return ['x', 'y', 'z', 'r']
    def close(self):
        self.device.close()

class AurigaAdapter(BotAdapter):
    def start(self):
        self.device = Auriga.Auriga(PORT)
        self._pose = self._getpose()
        self._home = self._pose
    def _getpose(self):
        return self.device.pose()
    def close(self):
        self.device.close()
    def pose(self):
        self._pose = self._getpose()
        return self._pose
    def home(self):
        self.move_wait(self._home)
    def move_wait(self, joints):
        goal = {x: joints[x] for x in self._pose.keys()}
        for k, v in goal.items():
            self.device.move(k, v) # XXX does this wait?
    def movable_joints(self):
        return list(self._pose.keys())

if ROBOT == "auriga":
    bot = AurigaAdapter()
if ROBOT == "dobot":
    bot = DobotAdapter()

def timestamp():
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')

_lucky_axis = "x"

def tweak(axis, value):
    global _lucky_axis
    if random.randint(0, AXIS_REPS) == 0:
        _lucky_axis = random.choice(bot.movable_joints())
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

    dev = bot.start()
    pose = bot.pose()
    print(f'initial pose: {pose}')
    if len(pose.keys()) == 0 or len(bot.movable_joints()) == 0:
        print(f'no joints active! cannot continue.')
        sys.exit(1)

    for i in range(N_EXAMPLES):
        rs1 = bot.pose()
        print(f'rs1: {rs1}')

        ts = timestamp()
        test_slug = f"{i}-{ts}"
        jf = os.path.join(path, f"{test_slug}-joints.json")
        startcams(test_slug)
        time.sleep(PRE_DELAY)

        goal = {x: tweak(x, rs1[x]) for x in rs1}
        print(f'goal: {goal}')
        # todo check validity
        bot.move_wait(goal)

        rs2 = bot.pose()
        print(f'rs2: {rs2}')

        rsj = json.dumps({"from": rs1, "to": rs2, "goal": goal})
        open(jf, 'w').write(rsj)

        time.sleep(POST_DELAY)

        stopcams()
        vids = collectcams(test_slug)
        for cam, data in vids.items():
            vf = os.path.join(path, f"{test_slug}-{cam}.h264")
            open(vf, 'wb').write(data)
            if USE_REVIEW_TOOL:
                os.system(REVIEW_TOOL_COMMAND.format(vf))

        bot.move_wait(rs1)
        time.sleep(EXAMPLE_DELAY)
        print(f"saved to path: {path}")

    bot.close()

init()
