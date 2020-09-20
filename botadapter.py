from auriga import Auriga
from pydobot import pydobot

def sanitize_joints(goal, ranges):
    out = {}
    for k, v in goal.items():
        if not k in ranges:
            out[k] = v
            continue
        rng = ranges[k]
        if v < rng[0]:
            out[k] = rng[0]
        elif v > rng[1]:
            out[k] = rng[1]
        else:
            out[k] = v
    return out

class BotAdapter:
    _pose = {}
    def start(self, port):
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
    JOINT_RANGE = {}
    def start(self, port):
        self.device = pydobot.Dobot(port=port, verbose=True)
        self._pose = self._getpose()
        self._home = self._pose;
    def _getpose(self):
        # TODO gripper
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        return {'x': x, 'y': y, 'z': z, 'r':j1, '1': j1, '2':j2, '3':j3, '4':j4};
    def joint_ranges(self):
        return self.JOINT_RANGE
    def pose(self):
        self._pose = self._getpose()
        return self._pose
    def home(self):
        self.move_wait(self._home)
    def move_wait(self, joints):
        self.device.move_to(joints['x'], joints['y'], joints['z'], joints['r'], wait=True)
    def movable_joints(self):
        return ['x', 'y', 'z', 'r']
    def sanitize(self, goal):
        return sanitize_joints(goal, self.JOINT_RANGE)
    def close(self):
        self.device.close()

class AurigaAdapter(BotAdapter):
    JOINT_RANGE = {'1': (-60, 60), '2': (-60, 60)}
    def start(self, port):
        self.device = Auriga.Auriga(port)
        self._pose = self._getpose()
        self._home = self._pose
    def _getpose(self):
        return self.device.pose()
    def joint_ranges(self):
        return self.JOINT_RANGE
    def close(self):
        self.device.close()
    def pose(self):
        self._pose = self._getpose()
        return self._pose
    def home(self):
        self.move_wait(self._home)
    def sanitize(self, goal):
        return sanitize_joints(goal, self.JOINT_RANGE)
    def move_wait(self, joints):
        goal = {x: joints[x] for x in self._pose.keys()}
        for k, v in goal.items():
            self.device.move(k, v) # XXX does this wait?
    def movable_joints(self):
        return list(self._pose.keys())

