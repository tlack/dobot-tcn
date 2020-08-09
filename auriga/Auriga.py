import serial

DEBUG = True
MAX_WAIT_ITERS = 1000

def dbg(txt):
    if DEBUG:
        print('!! Auriga: ', txt)

class Auriga:

    def __init__(self, port):
        self.ser = serial.Serial(port,
                                 baudrate=115200,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS)
        is_open = self.ser.isOpen()

    def _send_expect(self, cmd, resp_code):
        self.ser.write((cmd+"\n").encode('ascii'))
        n = 0
        while n < MAX_WAIT_ITERS:
            s = self.ser.readline().decode('ascii').replace("\r\n","")
            dbg('_send_wait(): '+s)
            parts = s.split(" ")
            if parts[0] == "CMD": # echo back commands
                continue
            if parts[0] == resp_code:
                return parts
        return None

    def pose(self):
        ret = self._send_expect("G", "J")
        if ret is None:
            return None
        if ret[0] == "J":
            joints = ret[1:]
            keys = [str(x) for x in joints[::2]]
            vals = [int(x) for x in joints[1::2]]
            return dict(zip(keys, vals))
        return None

    def move(self, joint, goal, speed=100):
        o = self._send_expect(f"J {joint} {goal} {speed}", "P1")
        dbg('move() '+(" ".join(o)))

    def close(self):
        self.ser.close()




