import pandas as pd
import pickle
from functools import reduce
import logging


# Nice way to convert dict of lists to one list
def dict_of_lists_to_unique_list(dictionary):
    """Take a Dictory of keys that map to lists and combine the lists to one list"""
    final_list = []
    for key in dictionary.keys():
        final_list.extend(dictionary[key])
    final_list = sorted(list(set(final_list)))
    return final_list

def largest_abs_value_in_dataframe(dataframe):
    max_number = dataframe.max().item()
    min_number = dataframe.min().item()
    return max(abs(max_number), abs(min_number))

# File Saving Utility Functions
def to_pickle(content, file_name):
    pickle_file = open('{}.pkl'.format(file_name), 'wb')
    pickle.dump(content, pickle_file, pickle.HIGHEST_PROTOCOL)
    pickle_file.close()

def to_pickle_and_CSV(content, file_name):
    to_pickle(content, file_name)
    content.to_csv("{}.csv".format(file_name))

# Logging Utility Function
def setup_standard_logger(file_name):
    # Logging Setup
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s;%(levelname)s;%(message)s', "%m/%d/%Y %H:%M")

    file_handler = logging.FileHandler('{}.log'.format(file_name))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger

# DataFrame Utility Functions
def merge_dfs_horizontally(dfs: 'list of dfs', suffixes=('_x', '_y')):
    dfs = [df for df in dfs if df is not None]

    if len(dfs) == 1:
        return dfs[0]
    else:
        return reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True, suffixes=suffixes), dfs)

def concat_dfs_horizontally(dfs: 'list of dfs'):
    dfs = [df for df in dfs if df is not None]

    if len(dfs) == 1:
        return dfs[0]
    else:
        return reduce(lambda x, y: pd.concat(dfs, axis=1))

def outer_join_dfs_horizontally(dfs: 'list of dfs'):
    dfs = [df for df in dfs if df is not None]

    if len(dfs) == 1:
        return dfs[0]
    else:
        return reduce(lambda x, y: x.join(y, how='outer'), dfs)

def append_dfs_vertically(dfs: 'list of dfs'):
    if len(dfs) == 1:
        return dfs[0]
    else:
        return reduce(lambda x, y: x.append(y), dfs)

# Printing Utility Functions
def tprint(*args):
    print("TPrint Here--------")
    for arg in args:
        print("Type: ", type(arg), "\n", "Obj: ", arg, sep='')

def rprint(*args):
    print("RPrint Here--", end="")
    for arg in args:
        if args.index(arg) == len(args)-1:
            e = " \n"
        else:
            e = ", "
        if type(arg) is not str:
            print(round(arg, 3), end = e)
        else:
            print(arg, end = e)

def lprint(*args):
    print("LPrint Here--------")
    for arg in args:
        print("Len: ", len(arg), "\n", sep='')
