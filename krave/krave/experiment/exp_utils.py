import decimal
import numpy as np

def get_precision(dt):
    d = decimal.Decimal(str(dt))
    DecimalDigit = -d.as_tuple().exponent
    return DecimalDigit

# get the index of time within the reward pdf
def get_time_index(reward_time_array, target_time_stamp):
    FindIndex = np.where(reward_time_array == target_time_stamp)
    IndexArray = FindIndex[0]
    index = IndexArray[0]
    return index