import pandas as pd
import pprint
from pprint import pprint
import statsmodels.formula.api as sm
import matplotlib.pyplot as plt
import statsmodels.api as sm
from ols import OLS
from ols2 import OLS as MainOLS

from utility.decorators import my_time_decorator
from utility.general import tprint
from data.finance import PriceTable
from utility.finance import daily_returns

from scrubbing_processes import stock_ceiling_scrub_process, index_floor_scrub_process, best_fit_scrub_process

class ScrubParams(object):
    """Three Parameters for Scrubbing Process:
        - Stock Cutoff: Scrub all moves that are larger (absolute value) than the stock cutoff
        - Index Cutoff: Scrub all moves where the index move is smaller (absolute value) than the stock cutoff)
        - Percentile Cutoff: With the remaining data points, keep the n-percentile data points with the best fit on the OLS Regression fit.
        """
    def __init__(self,
                 stock_cutoff=5,
                 index_cutoff=0,
                 percentile_cutoff=100):
        
        self.stock_cutoff = stock_cutoff
        self.index_cutoff = index_cutoff
        self.percentile_cutoff = percentile_cutoff

    def __repr__(self):
        return "ScrubParams(Stock Cutoff: {:2f}, Index Cutoff: {:2f}, Percentile Cutoff: {:2f})".format(self.stock_cutoff, self.index_cutoff, self.percentile_cutoff)

class Beta(object):
    def __init__(self,
                 stock: 'str',
                 index: 'str',
                 lookback: 'int',
                 scrub_params: 'obj'):
        """The Beta object takes as parameters the stock, index, lookback, and scrubparams object"""
        self.stock = stock
        self.index = index
        self.lookback = lookback
        self.scrub_params = scrub_params
        
        self.price_table = PriceTable.head(self.lookback)[[self.stock, self.index]]
        self.daily_returns = daily_returns(self.price_table)
        self.num_data_points = self.daily_returns.shape[0]
    
    @property
    def initial_scrub(self):
        """Eliminate data points where the stock moved greater (absolute value) than the specified stock cutoff.
           This process imposes a celing for the magnitude of stock moves included in the sample."""
        return stock_ceiling_scrub_process(returns_df_to_scrub=self.daily_returns,
                                          stock_to_drive_scrubbing=self.stock,
                                          stock_move_ceiling=self.scrub_params.stock_cutoff)
    
    @property
    def second_scrub(self):
        """Eliminate data points where the index moved less than the index cutoff. Only keep data points above the floor."""
        return index_floor_scrub_process(returns_df_to_scrub=self.initial_scrub,
                                         index_to_drive_scrubbing=self.index,
                                         index_move_floor=self.scrub_params.index_cutoff)
    
    @property
    def third_scrub(self):
        """Keep the n percentile data points that have the best fit based on OLS regression"""
        return best_fit_scrub_process(returns_df_to_scrub=self.second_scrub,
                                      stock=self.stock,
                                      index=self.index,
                                      percentile_cutoff=self.scrub_params.percentile_cutoff)
    
    scrubbed_returns_cache = {}
    @property
    def scrubbed_returns(self):
        if self.stock in Beta.scrubbed_returns_cache:
            return Beta.scrubbed_returns_cache[self.stock]
        else:
            Beta.scrubbed_returns_cache[self.stock] = self.third_scrub
            return Beta.scrubbed_returns_cache[self.stock]

    @property
    def num_days_in_calculation(self):
        return self.scrubbed_returns.shape[0]
    
    @property
    def percent_days_in_calculation(self):
        return (self.num_days_in_calculation)/self.num_data_points

    @property
    def OLS_model_results(self):
        stock_returns = self.scrubbed_returns[self.stock]
        index_returns = self.scrubbed_returns[self.index]
        
        ols_model = sm.OLS(stock_returns, index_returns, missing='drop')
        ols_results = ols_model.fit()
        return ols_results
    
    @property
    def rsquared(self):
        return self.OLS_model_results.rsquared

    @property
    def degrees_of_freedom(self):
        return self.OLS_model_results.df_resid
    
    
    
    # These calculations use my own OLS class as opposed to the smmodule. The degrees are freedom differ by one (not sure how to affect this parameter with the open-source model.
    @property
    def OLS_object(self):
        stock_returns = list(self.scrubbed_returns[self.stock])
        index_returns = list(self.scrubbed_returns[self.index])
        dates = list(self.scrubbed_returns.index.values)
        return MainOLS(list(zip(index_returns, stock_returns, dates)))

    @property
    def beta(self):
        return self.OLS_model_results.params[self.index]

    @property
    def beta1(self):
        return self.OLS_object.beta1
    
    @property
    def corr(self):
        return self.OLS_object.corr
    
    @property
    def scrub_type(self):
        if self.scrub_params.stock_cutoff >= 1.0 and self.scrub_params.index_cutoff == 0 and self.scrub_params.percentile_cutoff == 1.0:
            return "Raw Returns"
        elif self.scrub_params.index_cutoff == 0 and self.scrub_params.percentile_cutoff == 1.0:
            return "Initial Scrub"
        elif self.scrub_params.percentile_cutoff == 1.0:
            return "Second Scrub"
        else:
            return "Third Scrub"

    def describe(self):
        """Scrub Type: Beta, Corr., n"""
        pprint("{}-> Beta: {:.2f}, Corr.: {:.2f}, n = {:.0f}".format(self.scrub_type, self.beta1, self.corr, self.degrees_of_freedom))
    

    @my_time_decorator
    def show_scrub_trajectory(self):
        """Beta at Each Stage of the Scrubbing Process: Raw_Returns, Initial_Scrub, Second_Scrub, Third_Scrub"""
        print("{} (Index: {}), n = {}, {}".format(self.stock, self.index, self.lookback, self.scrub_params))
        
        raw_returns = ScrubParams(1.0, 0.0, 1.0)
        initial_scrub = ScrubParams(self.scrub_params.stock_cutoff, 0.0, 1.0)
        second_scrub = ScrubParams(self.scrub_params.stock_cutoff, self.scrub_params.index_cutoff, 1.0)
        third_scrub = ScrubParams(self.scrub_params.stock_cutoff, self.scrub_params.index_cutoff, self.scrub_params.percentile_cutoff)

        scrub_params_list= [raw_returns, initial_scrub, second_scrub, third_scrub]
        
        for param_set in scrub_params_list:
            Beta.scrubbed_returns_cache = {}
            Beta(self.stock, self.index, self.lookback, param_set).describe()

class StockLineSimple(object):
    def __init__(self, stock: 'str', lookback: 'int', base=None):
        self.stock = stock
        self.lookback = lookback
        
        if base is None:
            self.base = self.stock
        else:
            self.base = base

        self.price_table = PriceTable.head(self.lookback)[[self.stock]]
        self.daily_returns = daily_returns(self.price_table).head(self.lookback)

    @property
    def stock_base_price(self):
        return self.price_table.tail(1)[self.stock].iloc[0]
        
    @property   
    def base_price(self):
        if self.base == self.stock:
            return self.price_table.tail(1)[self.stock].iloc[0]
        elif type(self.base) is str:
            return PriceTable.head(self.lookback).tail(1)[self.base].iloc[0]
        elif type(self.base) == float or type(self.base == int):
            return self.base
        else:
            raise ValueError
    
    @property
    def prices_df(self):
        mult = self.base_price / self.stock_base_price
        return self.price_table.iloc[::-1] * mult
    
    @property
    def total_return(self):
        return self.prices_df.tail(1).iloc[0, 0] / self.prices_df.head(1).iloc[0,0] - 1

    @property
    def stock_line_name(self):
        if self.stock == self.base:
            return "{}".format(self.stock)
        else:
            return "{} (Base: {})".format(self.stock, self.base)  
    
    def stock_line(self, color, name = None):
        if name is None:
            name = self.stock_line_name
        return (self.prices_df, color, name)

class StockLineBetaAdjusted(StockLineSimple):
    def __init__(self, stock: 'str', lookback: 'int', beta: 'float', index: 'str', base = None):
        super().__init__(stock, lookback, base)
        self.beta = beta
        self.index = index
    
    @property
    def adjusted_returns_df_column_name(self):
        return "{}_Adj.".format(self.stock)
    
    @property
    def adjusted_returns_scrubbed_df_column_name(self):
        return "{}_Adj_Scrubbed".format(self.stock)
    
    @property   
    def adjusted_returns(self):
        index_prices = PriceTable.head(self.lookback).loc[:, [self.index]]
        index_returns = daily_returns(index_prices)
        
        adj_returns = (1 + self.daily_returns[self.stock]) / (1 + index_returns[self.index]*self.beta) - 1
        adj_returns.name = self.adjusted_returns_df_column_name
        return adj_returns.to_frame()


    def adjusted_returns_scrubbed(self, stock_cutoff = .075):
        adjusted_returns_scrubbed_df =  self.adjusted_returns[abs(self.adjusted_returns[self.adjusted_returns_df_column_name]) <= stock_cutoff]
        adjusted_returns_scrubbed_df.columns = [self.adjusted_returns_scrubbed_df_column_name]
        return adjusted_returns_scrubbed_df
    
    @property
    def prices_df(self):
        dates = list(reversed(self.adjusted_returns.index.values))
        returns = list(reversed(self.adjusted_returns.iloc[:,0].tolist()))
        prices = [self.base_price]
        for i in range(1, len(dates)):
            daily_move = returns[i]
            prices.append((1 + daily_move)*prices[i-1])
        prices_df = pd.DataFrame({'Dates': dates, 'Adj_Prices': prices}).set_index('Dates')
        return prices_df

    @property
    def chart_name(self):
        return "{}; Index: {}, Beta: {:.2}".format(self.stock, self.index, self.beta)


class StockChart(object):
    def __init__(self, stock_lines: 'list of stock lines'):
        self.stock_lines = stock_lines

    def run(self):
        fig = plt.figure()
        ax1 = plt.subplot2grid((1,1), (0,0)) #ax1 is a subplot, ax2 would be a second subplot
        ax1.grid(True, color='gray', linestyle='-', linewidth=.5)
        
        for stock_line in self.stock_lines:
            prices_df = stock_line[0]
            c = stock_line[1]
            l = stock_line[2]
            x = prices_df.index.tolist()
            y = prices_df.iloc[:, 0].tolist()
            ax1.plot(x, y, color = c, label = l)
        
        
        plt.title("Stock Chart\nPut More Information Here")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.xticks(rotation=45)
        plt.style.use('ggplot')
        plt.legend()
        plt.subplots_adjust(left=.09, bottom=.12, right =.94, top=.9, wspace=.2, hspace=0)
        
        plt.show()
