import numpy as np
from itertools import chain, islice, repeat
import traceback
import logging
import pickle
import nltk
import sys
import os

logging_level = logging.INFO
logging.basicConfig(level=logging_level)


UNKNOWN_TOKEN = 'UNKNOWN_TOKEN'
data = {}
"""
data can contain the following keys:
sentences: list of sentence strings
tokens: word-tokenized list of sentences
unique_tokens: list of unique tokens sorted by frequency
indices: integer representation of tokens
one_hot: one-hot representation of indices
vocab_size: number of unique tokens
token_to_index: map from token to index space
index_to_token: map from index to token space
max_sentence_length: number of tokens in the longest sentence
raw_data: full text
data_size: number of tokens in data
filename: name of file to read raw data from
tokens_flat: flattened sequence of word tokens
token_to_one_hot: map from tokens to one-hot space
index_to_one_hot: map from indices to one-hot space
"""

current_epoch = 0
position_in_batch = 0


def read(filename, vocab_fraction=0, sentence_tokenized=False):
    """
    Read raw data and add data properties to self.data

    Args:
        filename: String. Name of file to read raw data from
        tokenize: Use NLTK to tokenize (word or sentence), or split into chars
        tokenize_type: if tokenizing, whether to use word or sentence tokenization

    Returns:
        dict: python dictionary containing data properties
    """
    # TODO: change name of variable 'filename' to reflect that it can also be a string of the raw data
    # TODO: add paramter 'is_string' to docstring
    global data

    # load raw data
        raw_data = open(filename, 'r').read()

    # sentence tokenize data
    if not sentence_tokenized:
        sentences = nltk.sent_tokenize(raw_data)

    # word-tokenize each sentence
    tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    # flatten list of tokens
    tokens = list(chain(*tokenized_sentences))
    # get data and full vocab size
    data_size, vocab_size = len(tokens), len(set(tokens))

    if vocab_fraction == 1:  # include all words in vocabulary
        unique_tokens = sorted(list(set(tokens)))
    else:  # remove least common words
        # get word frequencies
        word_freq = nltk.FreqDist(tokens)
        # filter rare words, ignore number of occurences
        unique_tokens = [x[0] for x in word_freq.most_common(int(vocab_fraction * vocab_size))]

    # add UNKNOWN_TOKEN to vocabulary
    unique_tokens.insert(0, UNKNOWN_TOKEN)
    # get final vocab size
    vocab_size = len(unique_tokens)
    data_update = {'filename': filename,
                   'raw_data': raw_data,
                   'sentences': sentences,
                   'tokens': tokenized_sentences,
                   'tokens_flat': tokens,
                   'unique_tokens': unique_tokens,
                   'data_size': data_size,
                   'vocab_size': vocab_size}
    _update_data(data_update)
    return data_update


def _update_data(properties):
    """
    :param kwargs: Dict containing properties to add to data
    :return: None
    """
    global data
    data.update(properties)
    return properties


def tokens_to_indices(tokens, unique_tokens):
    # mapping from tokens to indices
    token_to_index = {w: i for i, w in enumerate(unique_tokens)}
    index_to_token = {i: w for i, w in enumerate(unique_tokens)}
    # replace all invalid tokens with UNKOWN_TOKEN
    for i, sent in enumerate(tokens):
        tokens[i] = [w if w in unique_tokens[:-1] else UNKNOWN_TOKEN for w in sent]
    indices = [[token_to_index[word] for word in sent] for sent in tokens]
    data_update = {'indices': indices,
                   'token_to_index': token_to_index,
                   'index_to_token': index_to_token}
    _update_data(data_update)
    return indices


def one_hot_encode_indices(indices, vocab_size):
    """
    Encode given data (or default data) as one-hot numpyvectors
    :param indices: String. If None, uses raw_data from self.data
    :return: one-hot encoded numpy array
    """
    global data
    index_to_one_hot = dict((index, enc) for index, enc in zip(range(vocab_size), np.eye(vocab_size, dtype=bool)))
    one_hot = [[index_to_one_hot[index] for index in sentence] for sentence in indices]
    max_sentece_length = max([len(sentence) for sentence in indices])
    data_update = {'index_to_one_hot': index_to_one_hot,
                   'one_hot': one_hot,
                   'max_sentence_length': max_sentece_length}
    _update_data(data_update)
    return one_hot


def one_hot_encode_tokens(tokens, vocab_size):
    """
    Encode given data (or default data) as one-hot nested list
    :param tokens (list): nested list of word-tokenized sentences
    :return (list): one-hot encoded list
    """
    global data
    indices = tokens_to_indices(data['tokens'], data['unique_tokens'])
    one_hot = one_hot_encode_indices(indices, vocab_size)
    data_update = {'indices': indices,
                   'one_hot': one_hot}
    _update_data(data_update)
    return one_hot


def one_hot_decode(one_hot_data=None):
    """
    Convert one-hot encoded vectors to vector containing integer indices
    :param one_hot_data:
    :return:
    """
    if one_hot_data is None:
        one_hot_data = self.data['one_hot']
    return np.argmax(one_hot_data, axis=int(len(one_hot_data.shape) != 1))
def save_data(obj_name):
    """
    pirkcle and save object data at <working_dir>\<data_filename>\objname
    Args:
        obj_name (object): object to be saved
    Returns (str):
        full path to saved file
    """
    global data
    # get working directory
    dir = sys.path[0]
    subfolder = os.path.join(data['filename'].split('.')[0] + '_data', 'pickled_data')
    save_folder = os.path.join(dir, subfolder)
    save_file = os.path.join(save_folder, obj_name)

    try:
        os.makedirs(save_folder)
    except:
        pass

    with open(save_file, 'wb') as f:
        pickle.dump(data[obj_name], f)

    return save_file


def load_data(filename):
    """
    Args:
        filename (str): name of key to store loaded data in
    Returns (object):
        object from loaded data
    """
    global data
    dir = sys.path[0]
    subfolder = os.path.join(data['filename'].split('.')[0] + '_data', 'pickled_data')
    save_folder = os.path.join(dir, subfolder)
    save_file = os.path.join(save_folder, filename)

    try:
        with open(save_file, 'rb') as f:
            _update_data({filename: pickle.load(f)})
    except Exception as e:
        logging.error("Unable to open file at {}".format(save_file))
        logging.info(traceback.format_exc())
    return data[filename]


def batch(batch_size):
    global current_epoch
    global position_in_batch
    if current_epoch == position_in_batch == 0:
        pass
        # TODO: create list of 'sections'
    for ndx in range(0, data['vocab_size'], batch_size):
        pass


def main(filename=None, vocab_fraction=1):
    """
    Args:
        filename (str): If not provided, read() method must be called explicitly to add data
    """
    global data
    if filename is not None:
        read(filename=filename, vocab_fraction=vocab_fraction)  # read raw data from file
        one_hot_encode_tokens(data['tokens'], data['vocab_size'])
        return filename

    # TODO: condition: filename == None -- what then?


if __name__ == '__main__':
    data_to_save = ['index_to_token',
                    'token_to_index',
                    'index_to_one_hot',
                    'sentences',
                    'indices',
                    'unique_tokens']

    main('1984.txt', vocab_fraction=0.95)
    for obj_name in data_to_save:
        save_data(obj_name)

    print('All done')