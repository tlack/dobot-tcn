# dobot-tcn

This is an attempt to utilize a time contrastive network to control a robotic arm.

It supports the Dobot Magician and custom Makeblock Auriga / MS-12a configurations.

This experiment is an attempt to replicate
[Time Contrastive Networks: Self-Supervised Learning from Multiview Observation](https://sermanet.github.io/tcn/).


## status

DATA: 
Generalized data recording subsystem works. There are two different variants, one of which records a video, the other just still frames.
Use the stills, bro. See [my other repo](https://github.com/tlack/dobot-tcn-training-data/) for samples of training data.

TRAINING: 
There are two failed direct image regression (picture of robot -> joint positions of robot) attempts here. Others may
have luck with that approach. 

I seem to be having better luck with a contrastive model, a hacky manual version of which can be seen here:
[on Google Colab](https://colab.research.google.com/drive/18axcd2EtWSp9H5PnxqJe6arKzTMDBgNC?usp=sharing) or [YT](https://www.youtube.com/watch?v=f2J2HG72fd8). Needs a lot of work.

IMITATION:
The last step is to use this trained model and a system like [PPO](https://openai.com/blog/openai-baselines-ppo/) to 
actually control a robot with a given video, or, the horror, a live stream. 

This part hasn't been started.

## prereq

1. A robotic arm. We support: 
   - Dobot Magician
	 - Makeblock Auriga with MS-12a Smart Sensors
	 - Dynamixel XL (soon!)
2. PiCamera x2 or more
3. Python3.7+
4. ffmpeg

## what's here

### picamera_webserver.py

This is a simple Flask web app to interact with a Raspberry Pi PiCamera. 

Edit settings on first line and run.

Stores videos in `data/picamera-webserver`.

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

### pydobot/

This is my fork of the regular Pydobot code.

### auriga/

Support for Makeblock Auriga motor controller board with ATmel Mega2650, along with
their MS-12a Smart Servos.

#### auriga/Makeblock-Auriga-SmartServoMS12a-FIRMWARE

This is an Arduino sketch that provides new firmware for your Auriga. This new firmware
is a highly optimized ASCII protocol that allows you to control your bot over serial
from your Raspberry Pi. 

Note that Makeblock provides some connectivity with their standard firmware but the
protocol isn't well documented.

**Load this on your Auriga first** before continuing to the Python stage.

#### auriga/Auriga.py

This is a PySerial-based wrapper that speaks to the firmware and provides a
super simple class wrapper.

### jointrecording.py

This is the main script that enables us to begin data collection on the Dobot Magician.

Open the file. You will notice a list of camera nodes at the top. Edit to match your cameras and run.

Data is stored under `data/jointrecording/`. It names each one after an experiment name you enter.

Here is how it works:

* Initialize robot.

* Prompt for experiment name (enter for same name as last time)

* Create folder `data/jointrecording/[experiment_name]-[timestamp]`. This is called the data dir.

* For N_EXAMPLES as N..

* * Record current robot position including joints - this is called a pose.

* * Instruct all cameras to begin recording.

* * Select new location to move to - this is called a goal. Only one axis will be tweaked at a time. The number of repetitions per axis is in AXIS_REPS. The amount of change in each value is in SWEEP_RANGE.

* * Move to goal.

* * Record new pose.

* * Stop all cameras

* * Log to pose to `[datadir]/[N]-[timestamp]-joints.json`

* * Receive videos from all cameras and store each to `[datadir]/[N]-[timestamp]-[camera_name].h264`

* * Return to original pose

This should be useful for training, but I'm not there yet.

### 2upvideo.sh

This takes two matching videos and joins them into a single side-by-side video.

If called with a folder, it will perform this operation for all experiment videos in the folder.

In folder mode, It will attempt to create a single montage called ALL.h264 at the end. This sometimes fails.

