import sys

def emit(x, t):
    sys.stderr.write(repr(t)+":"+repr(x)+"\n\n")
    return x

def noemit(x, t):
    return x

