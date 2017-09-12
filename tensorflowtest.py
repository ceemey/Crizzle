import os
import time
import logging
import warnings
import numpy as np
import matplotlib.pyplot as plt
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.utils import plot_model
from keras.models import Sequential, load_model
import read_historical as rh

np.random.seed(0)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)


def normalize(dataset):
    return dataset - dataset.mean()


def normalize_windows(windows):
    norm = []
    for window in windows:
        normed_window = [((float(p) / (float(window[0]+0.00001))) - 1) for p in window]
        norm.append(normed_window)
    return np.array(norm)


def rolling_window(arr, window_size):
    shape = arr.shape[:-1] + (arr.shape[-1] - window_size + 1, window_size)
    strides = arr.strides + (arr.strides[-1],)
    return np.lib.stride_tricks.as_strided(arr, shape=shape, strides=strides)


def plot_windows(array_of_arrays, animate=False):
    plt.ion()
    plt.ylabel('value')
    for window in windows[::sequence_length]:
        plt.plot(window)
        if animate:
            plt.pause(0.0001)
            plt.clf()
        plt.show()
    plt.ioff()
    plt.show()


def build_model(layers):
    """
    :param layers: [data dimensions, sequence length, LSTM layer 2 size, fully connected layer size]
    :return:
    """
    model = Sequential()
    model.add(LSTM(input_shape=(layers[1], layers[0]),
                   output_dim=layers[1],
                   return_sequences=True))
    model.add(Dropout(0.1))
    model.add(LSTM(layers[2], return_sequences=False))
    model.add(Dropout(0.1))
    model.add(Dense(output_dim=layers[3]))
    model.add(Activation('tanh'))
    # model.add(Activation('linear'))

    start = time.clock()
    model.compile(loss='mse', optimizer='rmsprop')
    print('Model successfully built.')
    print('Compilation Time: {}'.format(time.clock() - start))
    plot_model(model, show_shapes=True)
    return model


def predict_next_point(model, inp):
    predicted = model.predict(inp)
    predicted = np.reshape(predicted, (predicted.size,))
    return predicted


def predict_sequence_full(model, inp):
    predicted = []
    for i in inp:
        predicted.append(model.predict(i[None, :, :]))
    return np.array(predicted)


def predict_sequences_multiple(model, inp, window_size, prediction_length):
    prediction_sequences = []
    for i in range(int(len(inp)/prediction_length)):
        # for every window in input data
        frame = inp[i*prediction_length]  # Which window to look at
        predicted = []
        for j in range(prediction_length):
            predicted.append(model.predict(frame[None, :, :])[0, 0])
            frame = frame[1:]
            frame = np.insert(frame, [window_size - 1], predicted[-1], axis=0)
            prediction_sequences.append(predicted)
    return prediction_sequences


def plot_results(predicted_data, true_data):
    fig = plt.figure(facecolor='white')
    ax = fig.add_subplot(111)
    ax.plot(true_data, label='True Data')
    plt.plot(predicted_data, label='Prediction')
    plt.legend()
    plt.show()


def plot_results_multiple(predicted_data, true_data, prediction_len):
    fig = plt.figure(facecolor='white')
    ax = fig.add_subplot(111)
    ax.plot(true_data, label='True Data')
    for i, data in enumerate(predicted_data):
        padding = [None for p in range(i * prediction_len)]
        plt.plot(padding + data, label='Prediction')
        plt.legend()
    plt.show()


model_from_disk = False

end = 100
interval = 0.01
test_fraction = 0.2
sequence_length = 101
epochs = 1
prediction_len = 50
data = normalize(rh.load_historical_data('BTC_ETH', 30))
windows = rh.generate_windows(data, sequence_length)

train, test = np.split(windows, [int((1-test_fraction)*len(windows))])
x_train = train[:, :-1]
x_test = test[:, :-1]
x_train = np.expand_dims(x_train, 2)
x_test = np.expand_dims(x_test, 2)
y_train = train[:, -1]
y_test = test[:, -1]


if __name__ == '__main__':
    print(windows.shape)
    print(train.shape)
    print(test.shape)
    print(x_train.shape)
    print(y_train.shape)
    print(x_test.shape)
    print(y_test.shape)

    if not model_from_disk:
        model = build_model([1, sequence_length-1, 100, 1])
        start = time.time()
        model.fit(x_train, y_train, batch_size=256, nb_epoch=epochs, validation_split=0.1)
        model.save('model.hdf5')
        print('training took {} seconds'.format(time.time() - start))
    else:
        model = load_model('model.hdf5')
        print('Loaded model from disk')

    start = time.time()
    predictions = predict_sequence_full(model, x_test)
    print('prediction took {} seconds'.format(time.time() - start))
    predictions.shape = predictions.shape[0]
    plot_results(predictions, y_test)
