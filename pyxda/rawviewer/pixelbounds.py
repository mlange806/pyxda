import numpy as np

#Takes in image data and returns percent
#of pixels lower than value
def perc_lower_than(value, data):
    data = data.ravel()
    amount = np.count_nonzero(data < value)
    perc = amount/float(np.size(data))
    return perc
    
#Takes in image data and returns percent
#of pixels greater than value
def perc_greater_than(value, data):
    amount = np.count_nonzero(data > value)
    perc = amount/float(np.size(data))
    return perc