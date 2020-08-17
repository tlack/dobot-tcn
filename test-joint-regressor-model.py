MODEL_DIR="data/trained-models/"
VID_DIR="data/joint-videos/"

FRAMES_DIR="data/test-trained-model-frames/"

MIN_FRAMES = 50
OFS = [10, 20, -20, -10]

W = 224
H = 224

# what type of robot's data are we looking at here?
FILTER_JOINTS_ONLY=['x', 'y', 'z', 'r', '1', '2', '3', '4']

# some of my training data was a list, not a dict - these are the labels that
# we'll apply to the joint observations in that case
LABEL_OLD_JOINTS=['x', 'y', 'z', 'r', '1', '2', '3', '4'];

import glob
import json
from os import makedirs, path, stat, system, unlink
import random
import re
import time

import cv2
import keras
import numpy

from util import emit, noemit, pretty, timestamp

def clear_old_frames():
    xx = glob.glob(FRAMES_DIR+"/*png")
    for x in xx:
        unlink(x)

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
        # emit(example['joints']['from'].keys(), 'skipping')
        # emit(example, 'skipping')
        return True
    else:
        return False

def find_examples(dir_):
    f = glob.glob(emit(path.join(dir_, "**", "*.json"), 'path'), recursive=True)
    emit(len(f), 'number of examples')
    r = [x for x in [load_example(x) for x in f] if not skip_joint_filters(x)]
    random.shuffle(r)
    return r

def extract_frames(vid):
    p = emit(vid.split("/"), 'p')
    fn = '_'.join(p[:-1]) + p[-1].replace('.h264', '-%d.png')
    out = path.join(FRAMES_DIR, fn)
    cmd = f'ffmpeg -i {vid} -s {W}x{H} {out}'
    emit(cmd, 'save thumbs')
    system(cmd)
    r = glob.glob(out.replace('-%d.png', '-*.png'))
    r.sort(key=lambda x: int(x.split("-")[-1].replace('.png','')))
    emit(r, 'frames')
    if len(r) < MIN_FRAMES:
        return [None, None]
    keepers = {x: r[x] for x in OFS}
    for x in r:
        if not x in keepers.values():
            unlink(x)
    return keepers

def test_frame(model, ofs, frame_fname, joints, maxes):
    img = cv2.imread(frame_fname)
    if img is not None:
        img = cv2.resize(img, (W, H)) / 255.0
        print('img mean', numpy.mean(img))
        print('img center mean', numpy.mean(img[50:150, 50:150]))
        # print(img[0:10])
        # cv2.imshow('review image', img)
        t1 = time.time()
        pred = model.predict(numpy.array([img]))[0]
        for i, p in enumerate(pred):
            pred[i] = p * maxes[i]
        t2 = time.time()
        from_ = joints['from']
        to_ = joints['to']
        print(f'')
        print(f'-----------------')
        print(f'FRAME     : {ofs}')
        print(f'time      : {t2-t1}')
        print(f'image     : {frame_fname}')
        print(f'range from: {pretty(from_)}')
        print(f'range to  : {pretty(to_)}')
        print(f'prediction: {pretty(pred)}')
        breakpoint()

def test_video(model, vid_fname, joints, maxes):
    frames = extract_frames(vid_fname)
    print('got frames', frames)
    for ofs, fn in frames.items():
        test_frame(model, ofs, fn, joints, maxes)

def pick_model():
    models = glob.glob(path.join(MODEL_DIR, "*.h5"))
    for i, m in enumerate(models):
        sz = stat(m).st_size // 1024 // 1024
        print(f'#{i}: {m} ({sz}mb)')
    # mi = int(input('Enter model # to load: '))
    mi = 2
    model_fname = models[mi]
    print(f'Loading #{mi} {model_fname}..')
    model = keras.models.load_model(model_fname)
    max_fn = path.join(MODEL_DIR, 'jointmax.json')
    # get max values for joint value scaling
    maxes = json.loads(open(max_fn).read())
    print(f'Got joint scaling values {maxes}')
    return [maxes, model]

def main():
    makedirs(FRAMES_DIR, exist_ok=True)
    [maxes, model] = pick_model()
    examples = find_examples(VID_DIR)
    for x in examples:
        for v in x['vids']:
            test_video(model, v, x['joints'], maxes)
            clear_old_frames()
            break

main()
