

# Functions to gather data from JSON

import json

import pandas as pd
import numpy as np
from scipy.stats import lognorm


class hpwhDataFetch():
    
    dataDict = json.load("hpwhdata")
    
    
    def __init__(self, *args, **kwargs):
        pass



    def getCDF(self, x, cdf_shift = 0):
        params = self.dataDict['gpdppfit']
        #cdf = list(zip(x, lognorm.cdf(x, params[0], params[1] + cdf_shift, params[2])))
        cdf = lognorm.cdf(x, params[0], params[1] + cdf_shift, params[2])
        return(cdf)
    
    def getLoadshape(self):
        return self.dataDict['loadshapes']['Stream']
    
    
    def getGPDPP(self, key):
        try: 
            return self.dataDict['gpdpp'][key]
        except KeyError:
            raise KeyError("Mapping key not found, valid keys are ashLow, ashMed, EcoMark, Ca")
    