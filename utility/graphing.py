import numpy as np
import matplotlib.pyplot as plt
import pylab
from scipy.interpolate import interp1d


def get_histogram_from_array(results: 'array of numbers', bins=10 ** 2,
                             title='Monte Carlo Simulation\n Simulated Distribution'):

    plt.hist(results, bins, histtype='bar', rwidth=1.0, color='blue', label='Rel. Frequency')
    plt.title(title)
    plt.xlabel('Relative Price')
    plt.ylabel('Relative Frequency')
    plt.legend()
    plt.show()


def show_mc_distributions_as_line_chart(mc_distributions, labels=None):
    i = 0
    for mc_distribution in mc_distributions:
        min_cutoff = np.percentile(mc_distribution, 0)
        max_cutoff = np.percentile(mc_distribution, 100)
        print(min_cutoff)
        print(max_cutoff)
        # mc_distribution = [i for i in mc_distribution if (i > min_cutoff) and (i < max_cutoff)]

        # print('Percentiles', (np.percentile(mc_distribution, .1), np.percentile(mc_distribution, .9)))
        # print('Min_Max', (np.min(mc_distribution), np.max(mc_distribution)))

        bin_min = np.percentile(mc_distributions[-1], .25)
        bin_max = np.percentile(mc_distributions[-1], 99.75)
        y, binEdges = np.histogram(mc_distribution, bins=np.arange(bin_min, bin_max, .00875))

        bincenters = .5 * (binEdges[1:] + binEdges[:-1])

        xnew = np.linspace(bin_min + .01, bin_max - .01, num=10 ** 3, endpoint=True)

        # p = np.polyfit(bincenters, y, 3)
        # y_p = np.polyval(p, xnew)
        f = interp1d(bincenters, y, kind='cubic')
        # f = UnivariateSpline(bincenters, y, s=1)
        # f = UnivariateSpline(xnew, y, s=1)
        # pylab.plot(xnew, f(xnew), '-', label = "Events {}".format(i))

        if labels == None:
            label = "Distribution {}".format(i + 1)
        else:
            label = labels[i]
        pylab.plot(bincenters, y, '-', label=label)
        i += 1
    pylab.legend()
    pylab.show()
