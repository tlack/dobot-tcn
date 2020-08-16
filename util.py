import sys

def emit(x, t):
    sys.stderr.write(repr(t)+":"+repr(x)+"\n\n")
    return x

def noemit(x, t):
    return x

def timestamp():
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
