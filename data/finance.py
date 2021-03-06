import datetime as dt
import pandas as pd
import pickle

"""
Symbols:
    Symbol Excludes
    Symbols
    SP500Symbols
    HealthcareSymbols

Prices
    PriceTable
    ETF_PriceTable

SectorInfo
    InformationTable
        
Betas
    SPY_Betas_Raw
    SPY_Betas_Scrubbed
    Best_Betas

Distributions
    VolBeta

EventParams
    TakeoutParams

Distributions
    VolBeta
"""


# Prices
PriceTable = pickle.load(open('/Users/paulwainer/Paulthon/DataFiles/StockPrices/stock_prices.pkl', 'rb'))

# Sector Info
InformationTable = pd.read_csv('/Users/paulwainer/Paulthon/DataFiles/SectorInfo/information_table.csv')
InformationTable.rename(columns = {'Last Close': 'Price', 'Ticker': 'Stock', 'Market Cap ': 'Market Cap'}, inplace=True)
InformationTable.set_index('Stock', inplace=True)

# Distributions
VolBeta = pd.read_csv('/Users/paulwainer/Paulthon/Events/Distributions/VolbetaDistribution.csv')
#EarningsEvents = pickle.load(open('EarningsEvents.pkl', 'rb')) # Can't include here because of circular imports.

# Event Params
TakeoutParams = pd.read_csv('/Users/paulwainer/Paulthon/Events/Parameters/TakeoutParams.csv').set_index('Stock')
TakeoutBuckets = pd.read_csv('/Users/paulwainer/Paulthon/Events/Parameters/TakeoutBuckets.csv').set_index('Rank')

# Betas
BestBetas = pickle.load(open('/Users/paulwainer/Paulthon/DataFiles/Betas/best_betas.pkl', 'rb'))
Best_Betas = pickle.load(open('/Users/paulwainer/Paulthon/DataFiles/Betas/Best_Betas.pkl', 'rb'))
SPY_Betas_Raw = pickle.load(open('/Users/paulwainer/Paulthon/DataFiles/Betas/SPY_Betas_Raw.pkl', 'rb'))
SPY_Betas_Scrubbed = pickle.load(open('/Users/paulwainer/Paulthon/DataFiles/Betas/SPY_Betas_Scrubbed.pkl', 'rb'))
ETF_Betas_to_SPY = pickle.load(open('/Users/paulwainer/Paulthon/DataFiles/Betas/ETF_betas.pkl', 'rb'))
