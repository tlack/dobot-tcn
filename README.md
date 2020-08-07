# dobot-tcn

This is an attempt to utilize a time contrastive network
to control a Dobot Magician robotic arm

## status

Building data set: Moves Dobot randomly while recording from two perspectives

## prereq

1. Dobot Magician
2. PiCamera x2 or more
3. Python3.7+
4. ffmpeg

## what's here

### remote_picamera_webserver.py

This is a simple Flask web app to interact with a Raspberry Pi PiCamera. 

Edit settings on first line and run.

Stores videos in `data/remote-camera-webserver`.

The API presents these endpoints:

`http://0.0.0.0:5858/` - **index**
Returns listing of known videos

`http://0.0.0.0:5858/start?fname=test.h264` - **start**
Start recording to named video file

`http://0.0.0.0:5858/start?fname=test.h264` - **stop**
Stop recording - file name optional.

`http://0.0.0.0:5858/send?fname=test.h264` - **send video**
Retrieve contents of video. Returned as Base64 string inside JSON structure:
```{"fn": "test.h264", "data": "...enormous string...", "size": 123123}```

Run one copy of this script on each PiCamera node.

### jointrecording.py

This is the main script that enables us to begin data collection on the Dobot Magician.

Open the file. You will notice a list of camera nodes at the top. Edit to match your cameras and run.

Data is stored under `data/jointrecording/`. It names each one after an experiment name you enter.

Here is how it works:

* Initialize robot.

* Prompt for experiment name (enter for same name as last time)

* Create folder `data/jointrecording/[experiment_name]-[timestamp]`. This is called the data dir.

* For N_EXAMPLES as N..

** Record current robot position including joints - this is called a pose.

** Instruct all cameras to begin recording.

** Select new location to move to - this is called a goal. Only one axis will be tweaked at a time. The number of repetitions per axis is in AXIS_REPS. The amount of change in each value is in SWEEP_RANGE.

** Move to goal.

** Record new pose.

** Stop all cameras

** Log to pose to `[datadir]/[N]-[timestamp]-joints.json`

** Receive videos from all cameras and store each to `[datadir]/[N]-[timestamp]-[camera_name].h264`

** Return to original pose

This should be useful for training, but I'm not there yet.

### 2upvideo.sh

This takes two matching videos and joins them into a single side-by-side video.

If called with a folder, it will perform this operation for all experiment videos in the folder.

In folder mode, It will attempt to create a single montage called ALL.h264 at the end. This sometimes fails.

