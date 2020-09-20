CAMERAS = {'rpi':'http://localhost:8585/', 'rpzw':'http://192.168.1.249:8585/'}
# CAMERAS = {'rpzw':'http://192.168.1.249:8585/'}

# Configure the bot environment
ROBOT="dobot"           # "auriga" or "dobot" for now
PORT="/dev/ttyUSB0"

# Configure this experiment:
N_EXAMPLES=200
AXIS_REPS=2       # how many movements per joint before choosing another?
SWEEP_RANGE=90    # XXX we should make these relative!

USE_REVIEW_TOOL=0
REVIEW_FREQ=0.2   # how often should we open review tool after shooting? range 0-1
REVIEW_TOOL_COMMAND="vlc --play-and-exit {} &"
POST_DELAY=1
EXAMPLE_DELAY=1 # pause to resetup

# folders
TOOL="jointrecording-v2"
CONFIG_FILE=TOOL+"-config.json"
SUMMARY_FILE="ALL.json"
DATA="data/joint-videos-v2"

import base64
import datetime
import json
import os
import random
import sys
import time

import requests

from util import timestamp

from botadapter import AurigaAdapter, DobotAdapter

if ROBOT == "auriga":
    bot = AurigaAdapter()
if ROBOT == "dobot":
    bot = DobotAdapter()

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

def collectstills(fn):
    results = {}
    for name, url in CAMERAS.items():
        r = requests.get(url=url+'pic')
        resp = r.json()
        data = base64.b64decode(resp['data']) 
        print(data[:4])
        print(f'collectcams({name},{fn}): {len(data)//1024}kb')
        if len(data) != resp['size']:
            print('collectcams(): WARNING: bad size')
        results.update({name: data})
    return results

def promptexperiment():
    if os.path.exists(CONFIG_FILE):
        last = json.loads(open(CONFIG_FILE, "r").read())
    else:
        last = "new experiment"
    experiment = input(f'Enter name of experiment [{last}]:\n')
    experiment = experiment if experiment else last
    exp = experiment.lower().replace(r'[^a-z0-9-]+', '')
    open(CONFIG_FILE, "w").write(json.dumps(exp))
    return exp

def init():
    print(f'camera sources: {CAMERAS}')
    
    dev = bot.start(PORT)
    pose = bot.pose()
    print(f'initial pose: {pose}')
    if len(pose.keys()) == 0 or len(bot.movable_joints()) == 0:
        print(f'no joints active! cannot continue.')
        sys.exit(1)

    exp = promptexperiment()
    path = os.path.join(DATA, TOOL, f'{exp}-{timestamp()}')
    os.makedirs(path, exist_ok=True)
    print(f'path: {path}')

    all_examples = []

    exp_config = {
        "SWEEP_RANGE": SWEEP_RANGE, "AXIS_REPS": AXIS_REPS,
        "N_EXAMPLES": N_EXAMPLES, "JOINT_RANGES": bot.joint_ranges()
    };

    for i in range(N_EXAMPLES):
        rs1 = bot.pose()
        print(f'rs1: {rs1}')

        ts = timestamp()
        test_slug = f"{i}"
        jf = os.path.join(path, f"{test_slug}-joints.json")

        goal = {x: tweak(x, rs1[x]) for x in rs1}
        goal = bot.sanitize(goal)
        print(f'goal: {goal}')
        # todo check validity
        bot.move_wait(goal)
        time.sleep(POST_DELAY)

        rs2 = bot.pose()
        print(f'rs2: {rs2}')

        rsj = json.dumps({"from": rs1, "to": rs2, "goal": goal, "exp_config": exp_config})
        open(jf, 'w').write(rsj)

        vids = collectstills(test_slug)
        fnames = []
        for cam, data in vids.items():
            uniqf = f"{test_slug}-{cam}.jpg"
            vf = os.path.join(path, uniqf)
            open(vf, 'wb').write(data)
            fnames.append(uniqf)
            if USE_REVIEW_TOOL:
                if i == 0 or 1-random.random() > REVIEW_FREQ:
                    os.system(REVIEW_TOOL_COMMAND.format(vf))
        
        all_examples.append({"timestamp": ts, "fnames": fnames, "joints": rs2})

        bot.move_wait(rs1)
        time.sleep(EXAMPLE_DELAY)

        all_dump = {"exp_config": exp_config, "examples": all_examples}
        open(os.path.join(path, SUMMARY_FILE), "w").write(json.dumps(all_dump))

        print(f"saved to path: {path}")

    bot.close()

init()
