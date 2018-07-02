import datetime as dt
import numpy as np
import pandas as pd
import math
import random
import copy
from statistics import mean
from collections import namedtuple
import matplotlib.pyplot as plt
from py_vollib.black_scholes.implied_volatility import black_scholes, implied_volatility

# Paul Packages
##from paul_resources import InformationTable, tprint, rprint
from data.finance import InformationTable
from utility.general import tprint, rprint
from utility.decorators import my_time_decorator
"""
-Option: NamedTuple
    -Params:
        -Option_Type: 'str'
        -Strike: 'float'
        -Expiry: 'Datetime'

-OptionPrice: Function
    -Params:
        -Option: 'NamedTuple'
        -Distribution: 'Object'
    -Returns->
        -'Float'
        -Content: Option Price 
"""

Option = namedtuple('Option', ['Option_Type', 'Strike', 'Expiry'])

def OptionPrice(Option, Distribution):
    if Option.Option_Type == 'Call':
        return sum([state.Prob*max(state.Relative_Price - Option.Strike, 0) for state in Distribution.distribution_df.itertuples()])

    if Option.Option_Type == 'Put':
        return sum([state.Prob*max(Option.Strike - state.Relative_Price, 0) for state in Distribution.distribution_df.itertuples()])

#@my_time_decorator
def OptionPriceMC(Option, MC_Results):
    if Option.Option_Type == 'Call':
        return np.mean(np.maximum(MC_Results - Option.Strike, np.zeros(len(MC_Results))))
        return np.average(np.maximum(MC_Results - Option.Strike, np.zeros(len(MC_Results))))
    
    if Option.Option_Type == 'Put':
        return np.average(np.maximum(Option.Strike - MC_Results, np.zeros(len(MC_Results))))

def get_time_to_expiry(expiry: 'dt.date', ref_date = dt.date.today()):
    if isinstance(expiry, dt.datetime):
        expiry = expiry.date()
    return  max((expiry - ref_date).days/365, 0)

#@my_time_decorator
def get_implied_volatility(Option,
                           option_price,
                           underlying_price = None,
                           interest_rate = None,
                           reference_date = None):

    if underlying_price is None:
        underlying_price = 1

    if interest_rate is None:
        interest_rate = 0

    if reference_date is None:
        reference_date = dt.date.today()
    
    price = option_price
    S = underlying_price
    K = Option.Strike
    r = interest_rate
    flag = Option.Option_Type.lower()[0]
    t = get_time_to_expiry(Option.Expiry)
    
    if S <= .05:
        print('Stock price is below 5 cents. Check stock price')
        return 0
    
    # If the option price is below the specified threshold, return volatility of 0
    if price < .01:
        return 0

    # If the intrinsic value is below the specified threshold, return volatility of 0
    if flag == 'c':
        #print('S', S)
        #print('K', K)
        #print('Instrinsic Value', max(S - K), 0)
        #print('Price', price)

        if price - max((S - K), 0) < .01:
            return 0
    elif flag == 'p':
        if price - max((K - S), 0) < .01:
            return 0
    else:
        raise ValueError


    #print('Type: {}, S: {:.2f}, K: {:.2f}, price: {:.2f}'.format(flag, S, K, price))
    return implied_volatility(price, S, K, t, r, flag)

def get_option_price(Option,
                     implied_vol,
                     underlying_price = None,
                     interest_rate = None,
                     reference_date = None):
    
    if underlying_price is None:
        underlying_price = 1

    if interest_rate is None:
        interest_rate = 0

    if reference_date is None:
        reference_date = dt.date.today()
    
    S = underlying_price
    K = Option.Strike
    r = interest_rate
    flag = Option.Option_Type.lower()[0]
    t = get_time_to_expiry(Option.Expiry)
    sigma = implied_vol

    return black_scholes(flag, S, K, t, r, sigma)
