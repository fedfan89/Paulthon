"""
formula for black scholes distribution:
S_t = S_o*exp(r*t - vol^2/2 + z*vol*sqrt(t)"""

import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from decorators import my_time_decorator
from option_model.Distribution_Module import mc_distribution_to_distribution


@my_time_decorator
def create_rand_nums(iterations: 'int' = 10**5) -> 'np_array':
    """ Return a numpy array of normally distributed random numbers"""
    return np.array([random.normalvariate(0,1) for i in range(iterations)])

#run simulation using a previously cretaed array of random numbers as the input
@my_time_decorator
def bs_simulation(rand_nums: 'np_array') -> 'np_array':
    stock, r, t, vol = 100, 0, 1.0, .10
    stock_futures = stock*np.e**(r*t - (vol**2)*(t/2) + rand_nums*vol*np.sqrt(t))
    return stock_futures

rand_nums = create_rand_nums(10**7)
stock_futures = bs_simulation(rand_nums)
print("HELLO SUSAN", [list_average(l) for l in [rand_nums, stock_futures]])

distribution = mc_distribution_to_distribution(stock_futures, 10**4+1, to_csv = True, csv_file_name = 'BlackScholes.csv')
print("HELLO JANE", distribution.mean_move, distribution.average_move)
get_mc_histogram(distribution.mc_simulation(10**6))

############################# Graph Component ##########################3
stock = 100
bins = [float(i) for i in np.arange(stock*-.1, stock*3, stock*.02)]
plt.hist(stock_futures, bins, histtype='bar', rwidth=0.8, color='purple')

plt.xlabel('St. Dev. Moves')
plt.ylabel('Relative Frequency')
plt.title('Beautiful Probabilitiy Distribution\nSmooth and Pretty!\n{:,d} Iterations'.format(len(stock_futures)))
plt.legend()
plt.show()

#@my_time_decorator
def create_stock_path(nodes = 252, volbeta=.2, pprint = False):
    """Make One Stock Path where local volatility varies based on volbeta"""
    stock_prices = [100]
    pct_moves = [0]
    vols = [.12]
    vol_changes = [0]
    iteration_labels = [0]

    relative_stock_change_cutoff = .05
    vol_change_cutoff = .1

    for i in range(1,nodes):
        r = 0
        t = 1/252
        stock_price = stock_prices[i-1]
        vol = vols[i-1]
        rand_num = float(random.normalvariate(0,1))

        relative_stock_price = np.e**(r*t - (vol**2)*(t/2) + rand_num*vol*np.sqrt(t))
        if relative_stock_price < relative_stock_change_cutoff - 1 or relative_stock_price > relative_stock_change_cutoff + 1:
            print("Relative_Stock_Price:", round(relative_stock_price, 2), round(vol, 2), i)
        relative_stock_price = min(max(relative_stock_change_cutoff-1, relative_stock_price), relative_stock_change_cutoff+1)
        new_stock_price = stock_price*relative_stock_price
        #print('New Stock Price:', new_stock_price)
        stock_prices.append(new_stock_price)
        
        if stock_price == 0:
            print(stock_prices)
            break
        pct_move = np.log(new_stock_price/stock_price)
        pct_moves.append(pct_move)

        vol_mult = min(max(vol_change_cutoff-1, np.e**(-pct_move*volbeta)), vol_change_cutoff +1)
        new_vol = vol*vol_mult
        
        #rprint(new_stock_price, pct_move, vol_mult, vol, new_vol)
        vols.append(new_vol)

        vol_change = new_vol - vols[i-1]
        vol_changes.append(vol_change)
    
        iteration_labels.append(i)
    
    if pprint is True:
        stock_path_info = {'Stock_Price': stock_prices,
                           'Pct_Move': pct_moves,
                           'Vol': vols,
                           'Vol_Change': vol_changes,
                           'Iteration': iteration_labels}
        
        stock_path_df = pd.DataFrame(stock_path_info)
        stock_path_df.set_index('Iteration', inplace=True)
        stock_path_df = stock_path_df.loc[:, ['Stock_Price', 'Pct_Move', 'Vol', 'Vol_Change']]
        print(stock_path_df.round(3).to_string())
    return stock_prices[-1]

@my_time_decorator
def run_volbeta_simulation(iterations = 10**4, volbeta = .2):
    stock_prices = []
    for iteration in range(iterations):
        stock_price = create_stock_path(nodes=252, volbeta = volbeta)
        stock_prices.append(stock_price)
    return stock_prices

volbeta = 1.5
create_stock_path(pprint=True, volbeta = volbeta)
stock_futures = run_volbeta_simulation(iterations = 10**5, volbeta = volbeta)
total_returns = [np.log(stock_future/100) for stock_future in stock_futures]
vol = np.nanstd(total_returns)
print("Vol:", vol)



########################## Vol Beta Histogram #########################333
stock = 100
bins = [float(i) for i in np.arange(stock*.5, stock*1.75, stock*.025)]
plt.hist(stock_futures, bins, histtype='bar', rwidth=0.8, color='purple')

plt.xlabel('Stock Prices')
plt.ylabel('Relative Frequency')
plt.title('Beautiful Probabilitiy Distribution\nSmooth and Pretty!\n{:,d} Iterations'.format(len(stock_futures)))
plt.legend()
plt.show()




