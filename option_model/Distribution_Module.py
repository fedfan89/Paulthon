import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# Standard Packages
import pandas as pd
import math
import numpy as np
import random
from statistics import mean
import logging
from py_vollib.black_scholes.implied_volatility import black_scholes, implied_volatility

# Paul General Formulas
from utility.general import to_pickle_and_CSV
from utility.graphing import get_histogram_from_array
from utility.decorators import my_time_decorator

# Logging Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s:%(message)s')

file_handler = logging.FileHandler('mc_transform.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# logging.disable(logging.CRITICAL)

class Distribution(object):
    """
    Distribution object-- DataFrame wrapped as an object to provide additional attributes and methods.
        -mean_move (sqrt)
        -average move (plain average)
        -straddle
        -method to return MonteCarlo simulation of size n iterations
    """

    def __init__(self, distribution_df):
        """
        DataFrame({Index: 'States', Columns: ['Prob', 'Pct_Move', 'Relative_Price']}") -> 'Distribution Object'

        Row Index:
            - 'States' -- Future scenarios

        Columns:
            - Prob  -- Probability of each scenario
            - Pct_Move -- Percentage Move in each scenario
            - Relative_Price -- Relative Price in each scenario
        """
        self.distribution_df = distribution_df

    @property
    def average_move(self):
        return sum([state.Prob * state.Pct_Move for state in self.distribution_df.itertuples()])

    @property
    def straddle(self):
        return sum([state.Prob * abs(state.Pct_Move) for state in self.distribution_df.itertuples()])

    @property
    def mean_move(self):
        return math.sqrt(sum([state.Prob * state.Pct_Move ** 2 for state in self.distribution_df.itertuples()]))

    # @my_time_decorator
    def mc_simulation(self, iterations=10 ** 5):
        relative_prices = self.distribution_df.loc[:, 'Relative_Price'].values.tolist()
        weights = self.distribution_df.loc[:, 'Prob'].values.tolist()

        # @my_time_decorator
        def random_generator():
            results = random.choices(relative_prices, weights=weights, k=iterations)
            return results

        results = random_generator()
        # print('MC Results Type:', type(results))
        results = np.array(results)
        return results

    def get_histogram(self, iterations=10 ** 6, bins=10 ** 2):
        simulation_results = self.mc_simulation(iterations=iterations)
        get_histogram_from_array(simulation_results, bins=bins)

    def __add__(self, other):
        i = 1
        new_states = []
        new_probs = []
        new_pct_moves = []
        new_relative_prices = []

        for self_state in self.distribution_df.itertuples():
            for other_state in other.distribution_df.itertuples():
                index = i
                # new_state = "{}; {}".format(self_state.Index, other_state.Index)
                new_prob = self_state.Prob * other_state.Prob
                new_relative_price = self_state.Relative_Price * other_state.Relative_Price
                new_pct_move = new_relative_price - 1

                new_states.append(i)
                new_probs.append(new_prob)
                new_relative_prices.append(new_relative_price)
                new_pct_moves.append(new_pct_move)

                i += 1

        new_distribution_info = {'State': new_states,
                                 'Prob': new_probs,
                                 'Pct_Move': new_pct_moves,
                                 'Relative_Price': new_relative_prices}

        # return distribution_info_to_distribution(new_distribution_info)
        new_distribution_df = pd.DataFrame(new_distribution_info).set_index('State').loc[:,
                              ['Prob', 'Pct_Move', 'Relative_Price']]
        return Distribution(new_distribution_df)

    def __mul__(self, other):
        states = [state.Index for state in self.distribution_df.itertuples()]
        probs = [state.Prob for state in self.distribution_df.itertuples()]
        new_pct_moves = []
        new_relative_prices = []

        for state in self.distribution_df.itertuples():
            new_pct_move = state.Pct_Move * other
            new_relative_price = new_pct_move + 1

            new_pct_moves.append(new_pct_move)
            new_relative_prices.append(new_relative_price)

        new_distribution_info = {'State': states,
                                 'Prob': probs,
                                 'Pct_Move': new_pct_moves,
                                 'Relative_Price': new_relative_prices}

        new_distribution_df = pd.DataFrame(new_distribution_info).set_index('State').loc[:,
                              ['Prob', 'Pct_Move', 'Relative_Price']]
        return Distribution(new_distribution_df)


class Distribution_MultiIndex(Distribution):
    def __init__(self, df):
        self.input_df = df
        self.positive_scenario = df.loc[['Positive']]
        self.negative_scenario = df.loc[['Negative']]
        self.new = self.positive_scenario.append(self.negative_scenario)
        self.core_scenarios = df.index.levels[0].tolist()
        self.all_states = df.loc[['Positive', 'Negative']].index.tolist()

    @property
    def core_scenario_dfs(self):
        return [self.input_df.loc[i] for i in self.core_scenarios]

    @property
    def positive_scenario_states(self):
        return self.positive_scenario.index.tolist()

    @property
    def negative_scenario_states(self):
        return self.negative_scenario.index.tolist()

    @property
    def positive_scenario_wgt_move(self):
        probs = self.positive_scenario.loc[:, 'Relative_Prob'].values.tolist()
        pct_moves = self.positive_scenario.loc[:, 'Pct_Move'].values.tolist()
        return sum([prob * pct_move for prob, pct_move in zip(probs, pct_moves)])

    @property
    def negative_scenario_wgt_move(self):
        probs = self.negative_scenario.loc[:, 'Relative_Prob'].values.tolist()
        pct_moves = self.negative_scenario.loc[:, 'Pct_Move'].values.tolist()
        return sum([prob * pct_move for prob, pct_move in zip(probs, pct_moves)])

    @property
    def prob_success(self):
        return -self.negative_scenario_wgt_move / (self.positive_scenario_wgt_move - self.negative_scenario_wgt_move)

    def set_positive_scenario_substate_prob(self, state, new_relative_prob):
        all_states = self.positive_scenario_states
        unchanged_states = [i for i in all_states if i[1] != state]

        old_relative_prob = self.positive_scenario.loc[('Positive', state), 'Relative_Prob']
        old_total_prob_other_states = 1 - old_relative_prob
        new_total_prob_other_states = 1 - new_relative_prob
        adjustment_mult = new_total_prob_other_states / old_total_prob_other_states

        # Set New Probabilities
        self.positive_scenario.loc[('Positive', state), 'Relative_Prob'] = new_relative_prob
        for i in unchanged_states:
            self.positive_scenario.loc[('Positive', i[1]), 'Relative_Prob'] *= adjustment_mult

    def set_negative_scenario_substate_prob(self, state, new_relative_prob):
        all_states = self.negative_scenario_states
        unchanged_states = [i for i in all_states if i[1] != state]

        old_relative_prob = self.negative_scenario.loc[('Negative', state), 'Relative_Prob']
        old_total_prob_other_states = 1 - old_relative_prob
        new_total_prob_other_states = 1 - new_relative_prob
        adjustment_mult = new_total_prob_other_states / old_total_prob_other_states

        # Set New Probabilities
        self.negative_scenario.loc[('Negative', state), 'Relative_Prob'] = new_relative_prob
        for i in unchanged_states:
            self.negative_scenario.loc[('Negative', i[1]), 'Relative_Prob'] *= adjustment_mult

    def set_substate_prob(self, state, new_relative_prob):
        if state[0] == 'Positive':
            all_states = self.positive_scenario_states
            unchanged_states = [i for i in all_states if i != state]

            old_relative_prob = self.positive_scenario.loc[state, 'Relative_Prob']
            old_total_prob_other_states = 1 - old_relative_prob
            new_total_prob_other_states = 1 - new_relative_prob
            adjustment_mult = new_total_prob_other_states / old_total_prob_other_states

            # Set New Probabilities
            self.positive_scenario.loc[state, 'Relative_Prob'] = new_relative_prob
            for i in unchanged_states:
                self.positive_scenario.loc[i, 'Relative_Prob'] *= adjustment_mult
        elif state[0] == 'Negative':
            all_states = self.negative_scenario_states
            unchanged_states = [i for i in all_states if i != state]

            old_relative_prob = self.negative_scenario.loc[state, 'Relative_Prob']
            old_total_prob_other_states = 1 - old_relative_prob
            new_total_prob_other_states = 1 - new_relative_prob
            adjustment_mult = new_total_prob_other_states / old_total_prob_other_states

            # Set New Probabilities
            self.negative_scenario.loc[state, 'Relative_Prob'] = new_relative_prob
            for i in unchanged_states:
                self.negative_scenario.loc[i, 'Relative_Prob'] *= adjustment_mult
        else:
            raise ValueError

        self.calc_absolute_probs()

    def calc_absolute_probs(self):
        for state in self.positive_scenario_states:
            self.positive_scenario.loc[state, 'Prob'] = self.positive_scenario.loc[
                                                            state, 'Relative_Prob'] * self.prob_success
        for state in self.negative_scenario_states:
            self.negative_scenario.loc[state, 'Prob'] = self.negative_scenario.loc[state, 'Relative_Prob'] * (
                        1 - self.prob_success)

    def set_prob_success(self, new_prob_success):
        for state in self.positive_scenario_states:
            self.positive_scenario.loc[state, 'Prob'] = self.positive_scenario.loc[
                                                            state, 'Relative_Prob'] * new_prob_success
        for state in self.negative_scenario_states:
            self.negative_scenario.loc[state, 'Prob'] = self.negative_scenario.loc[state, 'Relative_Prob'] * (
                        1 - new_prob_success)

        center_shift = sum([state.Prob * state.Pct_Move for state in self.distribution_df.itertuples()])
        for state in self.positive_scenario_states:
            self.positive_scenario.loc[state, 'Pct_Move'] += -center_shift
            self.positive_scenario.loc[state, 'Relative_Price'] = self.positive_scenario.loc[state, 'Pct_Move'] + 1
        for state in self.negative_scenario_states:
            self.negative_scenario.loc[state, 'Pct_Move'] += -center_shift
            self.negative_scenario.loc[state, 'Relative_Price'] = self.negative_scenario.loc[state, 'Pct_Move'] + 1

    @property
    def distribution_df(self):
        return self.positive_scenario.append(self.negative_scenario)


# --------------------------------------Functions in the Distribution_Module---------------------------------#
def float_to_distribution(move_input: 'float', csv_file):
    distribution_df = pd.read_csv(csv_file).set_index('State')
    mean_move = Distribution(distribution_df).mean_move

    # Old Way Using Pct Returns 
    # distribution_df.loc[:, 'Pct_Move'] *= (move_input/mean_move)
    # print(distribution_df)
    # distribution_df.loc[:, 'Relative_Price'] = distribution_df.loc[:, 'Pct_Move'] + 1

    # New Way Using Natural Log Returns
    distribution_df.loc[:, 'Relative_Price'] = np.exp(distribution_df.loc[:, 'Pct_Move'] * move_input / mean_move)
    distribution_df.loc[:, 'Pct_Move'] = distribution_df.loc[:, 'Relative_Price'] - 1
    average_relative_price = Distribution(
        distribution_df).average_move + 1  # Normalize the Event Distribution (off due to natural log math?)
    # print('Average Relative Price:', average_relative_price)
    distribution_df.loc[:, 'Relative_Price'] *= (1 / average_relative_price)
    # print('HERE---------', distribution_df.loc[:, 'Relative_Price'])
    distribution_df.loc[:, 'Pct_Move'] = distribution_df.loc[:, 'Relative_Price'] - 1
    # print('HERE---------', distribution_df.loc[:, 'Pct_Move'])
    # print(distribution_df)

    # new_dist = Distribution(distribution_df)
    # print(new_dist.mean_move, new_dist.average_move, new_dist.straddle)
    dist = Distribution(distribution_df)
    # print('Average Move:', dist.average_move)
    return dist


def float_to_event_distribution(move_input: 'float'):
    return float_to_distribution(move_input, '/Users/paulwainer/Paulthon/Events/Distributions/Event.csv')


def float_to_volbeta_distribution(move_input: 'float'):
    return float_to_distribution(move_input, '/Users/paulwainer/Paulthon/Events/Distributions/VolbetaDistribution.csv')


def float_to_bs_distribution(move_input: 'float'):
    return float_to_distribution(move_input, '/Users/paulwainer/Paulthon/Events/Distributions/BlackScholes.csv')


def distribution_info_to_distribution(distribution_info):
    distribution_df = pd.DataFrame(distribution_info).set_index('State').loc[:, ['Prob', 'Pct_Move', 'Relative_Price']]
    return Distribution(distribution_df)


def mc_distribution_to_distribution(mc_distribution,
                                    bins=10 ** 4 + 1,
                                    to_file=False,
                                    file_name=None):
    mean_mc_price = np.mean(mc_distribution)

    counts, binEdges = np.histogram(mc_distribution, bins)
    binCenters = .5 * (binEdges[1:] + binEdges[:-1])

    probs = [i / sum(counts) for i in counts]
    # relative_moves = [binCenter / mean_mc_price for binCenter in binCenters]
    relative_moves = [binCenter / 1.0 for binCenter in binCenters]
    pct_moves = [relative_move - 1 for relative_move in relative_moves]

    distribution_info = {'State': np.array(range(len(counts))),
                         'Prob': probs,
                         'Pct_Move': pct_moves,
                         'Relative_Price': relative_moves}

    if to_file is True:
        distribution_df = distribution_info_to_distribution(distribution_info).distribution_df
        # distribution_df.to_csv(file_name)
        to_pickle_and_CSV(distribution_df, file_name)

    logger.info("Iterations: {:,}".format(sum(counts)))
    logger.info("Total Prob: {:.2f}".format(sum(probs)))
    logger.info("Mean Stock Price: {}".format(mean_mc_price))

    return distribution_info_to_distribution(distribution_info)


def float_to_histogram(move_input: 'float'):
    bs_distribution_original = float_to_bs_distribution(.3)
    # logger.info("Original: {:.2f}".format(bs_distribution_original.mean_move))
    mc_distribution = bs_distribution_original.mc_simulation(10 ** 6)
    bs_distribution_created = mc_distribution_to_distribution(mc_distribution)
    # logger.info("Created: {.2f}".format(bs_distribution_created.mean_move))


def get_no_event_distribution():
    no_event_info = {'State': ['No_Event'],
                     'Prob': [1.0],
                     'Pct_Move': [0],
                     'Relative_Price': [1.0]}

    no_event_df = pd.DataFrame(no_event_info).set_index('State').loc[:, ['Prob', 'Pct_Move', 'Relative_Price']]
    return Distribution(no_event_df)


if __name__ == '__main__':
    bs_distribution_original = float_to_bs_distribution(.3)
    print("Original: {:.2f}".format(bs_distribution_original.mean_move))
    mc_distribution = bs_distribution_original.mc_simulation(10 ** 6)
    bs_distribution_created = mc_distribution_to_distribution(mc_distribution)
    print("Created: {:.2f}".format(bs_distribution_created.mean_move))
