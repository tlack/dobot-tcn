DATASET_FILE='data/training-frames.json'
W = 224
H = 224
CHAN = 3 #rgb
BATCH = 8
FC = [W * 1.5, H * 1.5, W+H]

import json

from keras.applications.resnet50 import ResNet50, preprocess_input

from util import emit, noemit

def prep():
    d = json.loads(open(DATASET_FILE).read())
    X = []
    Y = []

    n_joints = len(d['y'][0])
    emit(n_joints, 'n_joints')

    maxes = []
    for i in range(len(d['y'][0])):
        m = numpy.max(d['y'][i])
        emit(m, ('max', i))
        maxes.push(m)

    for x, y in zip(d['x'], d['y']):
        x = cv2.resize(cv2.imread(x), (W, H)) / 255.0
        for i in y:
            y[i] = y[i] / maxes[i]
        X.push(x)
        Y.push(y)

    emit(len(X), 'len X')
    emit(len(Y), 'len Y')

    assert len(X) == len(Y)

    Xn = numpy.array(X)
    Yn = numpy.array(Y)

    Xs = X.shape()
    Ys = Y.shape()
    emit(Xs, 'shape X')
    emit(Ys, 'shape X')

    assert Xs[0] == len(X)
    assert Xs[1] == H
    assert Xs[2] == W
    assert Xs[3] == DEPTH
    assert Ys[0] == len(Y)
    assert Ys[1] == n_joints

    return [n_joints, Xn, Yn, Xs, Ys]

def model(n_joints):
    base = ResNet50(weights='imagenet',
        include_top=False,
        input_shape=(HEIGHT, WIDTH, CHAN))
    for layer in base.layers:
        layer.trainable = False
    x = Flatten()(base.output)
    for l in FC:
        x = Dense(l, activation='relu')(x) # XXX relu?
        x = Dropout(DROPOUT)(x)
    y = Dense(n_joints, activation='linear')(x) # XXX linear?
    model = Model(inputs=base_model.input, outputs=y)
    opt = Adam(lr=1e-3, decay=1e-3 / 200)
    model.compile(loss="mean_absolute_percentage_error", optimizer=opt)
    return model

def main():

    [y_size, Xn, Yn, Xs, Ys] = prep()
    net = model(y_size)
    breakpoint()
    o = model.fit(Xn, Yn, epochs=2, batch_size=BATCH)
    emit(o, 'model.fit')

