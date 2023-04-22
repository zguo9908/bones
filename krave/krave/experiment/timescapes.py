

import numpy as np
from scipy.stats import expon


def lin_over_ex(x, cumulative=10, x_peak=1):
    b = 1 / x_peak
    a = b ** 2 * cumulative
    density = (a * x) / np.exp(b * x)
    return density


# This is the simple exponential decreasing
def exp_decreasing_old(x, cumulative, starting):
    a = starting
    b = a / cumulative
    density = a / np.exp(b * x)
    return density


def fixed_single(x, wait_time):
    if x > wait_time:
        reward = 1
    else:
        reward = 0
    return reward

def exp_decreasing(time_array, min_delay, scale):
    reward_pdf = expon.pdf(time_array, min_delay, scale)
    reward_cdf = expon.cdf(time_array, min_delay, scale)
    return reward_pdf, reward_cdf

