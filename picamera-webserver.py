VID_DIR="data/picamera-webserver/"
CAMERA_OPTIONS={"sensor_mode": 4, "resolution": (640,480), "framerate":30}

import base64
import json
import os
import time

from flask import Flask, jsonify, request
from picamera import PiCamera

try:
    import aiy.toneplayer
    def beep():
        print('beep!')
        moozik = ['C5e','C4e','C5e']
        player = aiy.toneplayer.TonePlayer(22)
except:
    def beep():
        print('starting video..')

def make_fn(fn):
    return os.path.join(VID_DIR, fn+'.h264')

def main(cam):
    app = Flask(__name__)

    @app.route('/')
    def index():
            vids = os.listdir(VID_DIR)
            return jsonify({'vids': vids, 'n': len(vids)})

    @app.route('/start')
    def start():
            global curFn, startTime

            try:
                cam.stop_recording()
            except:
                pass

            fn = request.args.get('fname')
            if not fn: 
                    return jsonify({'err': 'no fname'})
            else:
                    beep()
                    # cam.start_preview()
                    cam.start_recording(make_fn(fn))
                    startTime = time.time()
                    curFn = fn
                    print('curFn', curFn)
                    return jsonify({'started': fn})

    @app.route('/stop')
    def stop():
            global curFn, startTime

            print('curFn', curFn)
            cam.stop_recording()
            # cam.stop_preview()
            sz = os.path.getsize(make_fn(curFn))
            return jsonify({'stopped': curFn, 'duration': time.time() - startTime, 'size': sz})

    @app.route('/send')
    def send():
            fn = request.args.get('fname')
            if not fn: 
                    return jsonify({'err': 'no fname'})
            else:
                    fn2 = make_fn(fn)
                    data = open(fn2, 'rb').read()
                    bdata = base64.b64encode(data)
                    print('bdata', bdata[:16])
                    sz = os.path.getsize(fn2)
                    return jsonify({'fn': fn, 'data': bdata, 'size': sz})

    startTime = None
    curFn = None
    os.makedirs(VID_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port='8585', debug=False)
    print('running')
    
beep()
print('init hw')
# with picamera.PiCamera(sensor_mode=4, resolution=(640,480), framerate=15) as camera, \
with PiCamera(**CAMERA_OPTIONS) as cam:
    main(cam)

