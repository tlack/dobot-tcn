DATASET_FILE='data/training-frames.json'
MODEL_OUTPUT_FNAME = 'data/train-joint-regressor-{FC_TXT}-{EPOCHS}-{start_time}-{last_loss}.h5'
W = 224
H = 224
CHAN = 3 #rgb
BATCH = 16
EPOCHS = 2
DROPOUT = 0.1
FC = [W * 2, H, H // 4]
FC_TXT = ','.join([str(x) for x in FC])

import json

import cv2
from keras.layers import Dense, Activation, Flatten, Dropout
from keras.models import Sequential, Model
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import SGD, Adam
from keras.callbacks import ModelCheckpoint
from keras.applications.resnet50 import ResNet50, preprocess_input
from sklearn.model_selection import train_test_split
import numpy

from util import emit, noemit, timestamp

def prep():
    d = json.loads(open(DATASET_FILE).read())
    X = []
    Y = []

    n_joints = len(d['y'][0])
    emit(n_joints, 'n_joints')

    maxes = []
    for i in range(n_joints):
        j_vals = [yy[i] for yy in d['y']]
        m = numpy.max(j_vals)
        emit(m, ('max', i))
        maxes.append(m)

    for x, y in zip(d['x'], d['y']):
        img = cv2.imread(x)
        if img is not None:
            x = cv2.resize(img, (W, H)) / 255.0
            for i, yy in enumerate(y):
                y[i] = y[i] / maxes[i]
            X.append(x)
            Y.append(y)

    emit(len(X), 'len X')
    emit(len(Y), 'len Y')

    assert len(X) == len(Y)

    Xn = numpy.array(X)
    Yn = numpy.array(Y)

    Xs = Xn.shape
    Ys = Yn.shape
    emit(Xs, 'shape X')
    emit(Ys, 'shape X')

    assert Xs[0] == len(X)
    assert Xs[1] == H
    assert Xs[2] == W
    assert Xs[3] == CHAN
    assert Ys[0] == len(Y)
    assert Ys[1] == n_joints

    return [n_joints, Xn, Yn, Xs, Ys]

def model(n_joints):
    base = ResNet50(weights='imagenet',
        include_top=False,
        input_shape=(H, W, CHAN))
    for layer in base.layers:
        layer.trainable = False
    x = Flatten()(base.output)
    for l in FC:
        x = Dense(l, activation='relu')(x) # XXX relu?
        x = Dropout(DROPOUT)(x)
    y = Dense(n_joints, activation='linear')(x) # XXX linear?
    model = Model(inputs=base.input, outputs=y)
    opt = Adam(lr=1e-3, decay=1e-3 / 200)
    model.compile(loss="mean_absolute_percentage_error", optimizer=opt)
    return model

def main():
    start_time = timestamp()
    last_loss = '(loss)';
    model_fname = MODEL_OUTPUT_FNAME.format_map({**globals(), **locals()})
    emit(model_fname, 'output file')

    [y_size, Xn, Yn, Xs, Ys] = prep()
    X_tr, X_te, Y_tr, Y_te = train_test_split(Xn, Yn, test_size=0.15)

    emit((X_tr.shape, X_te.shape), 'tr/te')

    net = model(y_size)

    o = net.fit(X_tr, Y_tr, epochs=EPOCHS, validation_data=(X_te, Y_te), batch_size=BATCH)
    emit(o, 'model.fit')

    last_loss = o.history['loss'][-1]
    model_fname = MODEL_OUTPUT_FNAME.format_map({**globals(), **locals()})
    o.model.save(model_fname)

main()

