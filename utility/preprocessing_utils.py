"""

@Author:

@Date: 17/05/2019

"""

import string
from functools import reduce
from collections import OrderedDict

import math
import numpy as np
from nltk import word_tokenize
import six
from skimage.util import view_as_windows

special_words = [
    "-lrb-",
    "-rrb-",
    "i.e.",
    "``",
    "\'\'",
    "lrb",
    "rrb"
]


def punctuation_filtering(line):
    """
    Filters given sentences by removing punctuation
    """

    table = str.maketrans('', '', string.punctuation)
    trans = [w.translate(table) for w in line.split()]

    return ' '.join([w for w in trans if w != ''])


def convert_to_unicode(text):
    """Converts `text` to Unicode (if it's not already), assuming utf-8 input."""
    if six.PY3:
        if isinstance(text, str):
            return text
        elif isinstance(text, bytes):
            return text.decode("utf-8", "ignore")
        else:
            raise ValueError("Unsupported string type: %s" % (type(text)))
    elif six.PY2:
        if isinstance(text, str):
            return text.decode("utf-8", "ignore")
        elif isinstance(text, unicode):
            return text
        else:
            raise ValueError("Unsupported string type: %s" % (type(text)))
    else:
        raise ValueError("Not running on Python2 or Python 3?")


def remove_special_words(line):
    """
    Removes any pre-defined special word
    """

    words = word_tokenize(line)
    filtered = []
    for w in words:
        if w not in special_words:
            filtered.append(w)

    line = ' '.join(filtered)
    return line


def number_replacing_with_constant(line):
    """
    Replaces any number with a fixed special token
    """

    words = word_tokenize(line)
    filtered = []
    for w in words:
        try:
            int(w)
            filtered.append('SPECIALNUMBER')
        except ValueError:
            filtered.append(w)
            continue

    line = ' '.join(filtered)
    return line
    # return re.sub('[0-9][0-9.,-]*', 'SPECIALNUMBER', line)


def sentence_to_lower(line):
    return line.lower()


filter_methods = OrderedDict(
    [
        ('convert_to_unicode', convert_to_unicode),
        ('sentence_to_lower', sentence_to_lower),
        ('punctuation_filtering', punctuation_filtering),
        ('number_replacing_with_constant', number_replacing_with_constant),
        ('remove_special_words', remove_special_words),
    ]
)


def filter_line(line, function_names=None):
    """
    General filtering proxy function that applies a sub-set of the supported
    filtering methods to given sentences.
    """

    if function_names is None:
        function_names = list(filter_methods.keys())

    functions = [filter_methods[name] for name in function_names]
    return reduce(lambda r, f: f(r), functions, line.strip().lower())


def windowing(x, y, window_dim):
    if type(x) is not np.ndarray:
        x = np.asarray(x)
    if type(y) is not np.ndarray:
        y = np.asarray(y)

    grouped_x = view_as_windows(x, window_shape=window_dim, step=1)

    y = y[:grouped_x.shape[0]]

    return grouped_x, y


def group_data_including(x, y, window_dim):
    x = np.asarray(x)
    y = np.asarray(y)

    grouped_x = []

    if window_dim == 1:
        x = [[sentence] for sentence in x]
        return x, y

    for idx, sentence in enumerate(x):

        context_left = int(math.floor(window_dim / 2))
        context_right = window_dim - context_left - 1

        context = []

        # First sentences
        if idx < context_left:
            context_right += context_left - idx
            context_left = idx

        # Last sentences
        if len(x) - idx - 1 < context_right:
            context_left += context_right - (len(x) - idx - 1)
            context_right = len(x) - idx - 1

        left_sentences = x[idx - context_left:idx]
        context.extend(left_sentences)
        context.append(sentence)
        right_sentences = x[idx + 1: idx + context_right + 1]
        context.extend(right_sentences)

        grouped_x.append(context)

    return grouped_x, y


def group_data_excluding(x, y, window_dim):
    x = np.asarray(x)
    y = np.asarray(y)

    grouped_x = []

    for idx, sentence in enumerate(x):

        context_left = int(math.ceil(window_dim / 2))
        context_right = window_dim - context_left

        # Initial sentences
        if idx < context_left:
            context_right += context_left - idx
            context_left = idx

        # Last sentences
        if len(x) - idx - 1 < context_right:
            context_left += context_right - (len(x) - idx - 1)
            context_right = len(x) - idx - 1

        if idx != 0 and idx != len(x) - 1:
            left_sentences = x[idx - context_left: idx]
            right_sentences = x[idx + 1: idx + context_right + 1]
            context = []
            context.extend(left_sentences)
            context.extend(right_sentences)
        elif idx == 0:
            context = x[1: context_right + 1].tolist()
        else:
            context = x[idx - context_left: idx].tolist()

        grouped_x.append(context)

    return grouped_x, y


def compute_jaccard_similarity(sent1, sent2, lemmatizer=None):
    """
    Hp: text has already been parsed.
    """

    sent1_words = set(sent1.split(' '))
    sent2_words = set(sent2.split(' '))

    if lemmatizer is not None:
        sent1_words = set(map(lambda word: lemmatizer.lemmatize(word), sent1_words))
        sent1_words = set(map(lambda word: lemmatizer.lemmatize(word), sent1_words))

    intersection = sent1_words.intersection(sent2_words)
    union = sent1_words.union(sent2_words)

    return float(len(intersection)) / len(union)
