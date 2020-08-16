# folder containing a bunch of h264 and json files, any depth
VID_DIR='data/joint-videos'

# output frames here
FRAMES_DIR='data/joint-frames'

# save the index of these examples along w/ target (y) values
DATASET_FILE='data/training-frames.json'

# scale to 
W = 224
H = 224

# what type of robot's data are we looking at here?
FILTER_JOINTS_ONLY=['x', 'y', 'z', 'r', '1', '2', '3', '4']

# some of my training data was a list, not a dict - these are the labels that
# we'll apply to the joint observations in that case
LABEL_OLD_JOINTS=['x', 'y', 'z', 'r', '1', '2', '3', '4'];

import glob
import json
import os
from os import path
import sys

import cv2

from util import emit, noemit

def clear_old_frames():
    xx = glob.glob(FRAMES_DIR+"/*png")
    for x in xx:
        os.unlink(x)

def fix_joints(data):
    if type(data['from']) == type([]):
        data.update({'from': dict(zip(LABEL_OLD_JOINTS, data['from']))})
        # print('fixing',data['from'])
    if type(data['to']) == type([]):
        data.update({'to': dict(zip(LABEL_OLD_JOINTS, data['to']))})
        # print('fixing',data['to'])
    return data

def load_example(json_file):
    data = json.loads(open(json_file).read())
    data = fix_joints(data)
    vids = glob.glob(json_file.replace("-joints.json", "*.h264"))
    r = {'json': json_file, 'joints': data, 'vids': vids}
    return r

def skip_joint_filters(example):
    if list(example['joints']['from'].keys()) != FILTER_JOINTS_ONLY:
        emit(example['joints']['from'].keys(), 'skipping')
        # emit(example, 'skipping')
        return True
    else:
        return False

def find_examples(dir_):
    f = glob.glob(emit(path.join(dir_, "**", "*.json"), 'path'), recursive=True)
    emit(len(f), 'number of examples')
    r = [x for x in [load_example(x) for x in f] if not skip_joint_filters(x)]
    return r

def save_frames(vid):
    p = emit(vid.split("/"), 'p')
    fn = '_'.join(p[:-1]) + p[-1].replace('.h264', '-%d.png')
    out = path.join(FRAMES_DIR, fn)
    cmd = f'ffmpeg -i {vid} -s {W}x{H} {out}'
    emit(cmd, 'save thumbs')
    os.system(cmd)
    r = glob.glob(out.replace('-%d.png', '-*.png'))
    r.sort(key=lambda x: int(x.split("-")[-1].replace('.png','')))
    emit(r, 'frames')
    if len(r) < 10:
        return [None, None]

    assert len(r) > 10
    first = r[0]
    last = r[-1]
    for x in r:
        if x != first and x != last:
            os.unlink(x)
            pass

    return [first, last]

def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clear_old_frames()
    v = find_examples(VID_DIR)
    X, Y = [ [], [] ]
    r = []
    for x in v:
        emit(x, 'vx')
        joint_dict = x['joints']
        from_ = list(joint_dict['from'].values())
        to_ = list(joint_dict['to'].values())

        for vid in x['vids']:
            emit(vid, 'extracting')
            
            first, last = save_frames(vid)
            
            if not first or not last:
                emit(vid, 'WARNING: no first or last frame')
                continue

            X.append(first); Y.append(from_)
            X.append(last);  Y.append(to_)

    emit(len(X), 'X items')
    emit(len(Y), 'Y items')
    open(DATASET_FILE, 'w').write(json.dumps({'x': X, 'y': Y}))

main()
