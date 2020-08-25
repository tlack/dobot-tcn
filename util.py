import datetime
import sys

def emit(x, t):
    sys.stderr.write(repr(t)+":"+repr(x)+"\n\n")
    return x

def noemit(x, t):
    return x

def pluck(vals, keys):
    if type(vals) == type([]):
        if type(keys) == type([]):
            rr = []
            for x in vals:
                r = []
                for y in keys:
                    r.append(x[y])
                rr.append(r)
            return rr
        else:
            rr = []
            for x in vals:
                rr.append(x[keys])
            return rr
    if type(vals) == type({}):
        if type(keys) != type([]):
            return vals[keys]
        else:
            return [vals[x] for x in keys]


def pretty(float_vec):
    if type(float_vec) == type({}):
        float_vec = float_vec.values()
    # emit(float_vec,'pretty')
    def pad(x): 
        n = 8
        while len(x) < n: 
            x = " "+x
        return x
    return ','.join([pad(str('%0.4f' % x)) for x in float_vec])

def timestamp():
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
