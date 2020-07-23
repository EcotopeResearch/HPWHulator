

# Functions to gather data from JSON
import os

import json
from scipy.stats import lognorm

class hpwhDataFetch():
    
    
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'hpwhdata.json')) as json_file:
            self.dataDict = json.load(json_file)
    
    def getLoadshape(self):
        return self.dataDict['loadshapes']['Stream']
    
    def getGPDPP(self, key):
        try: 
            return self.dataDict['gpdpp'][key]
        except KeyError:
            raise KeyError("Mapping key not found for gpdpp, valid keys are ashLow, ashMed, ecoMark, CA")
            
    def getRPepperBR(self, key):
        try: 
            return self.dataDict['rpeople'][key]
        except KeyError:
            raise KeyError("Mapping key not found for ratio of people per bedroom, valid keys are CA, ASHSTD, ASHLOW")
    
    # x in this are the quantiles. this should not be a user input. it should come from the dataDict. 
    def getCDF(self, x, cdf_shift = 0):
        params = self.dataDict['gpdppfit']
        #cdf = list(zip(x, lognorm.cdf(x, params[0], params[1] + cdf_shift, params[2])))
        cdf = lognorm.cdf(x, params[0], params[1] + cdf_shift, params[2])
        return(cdf)
    
new_datafetch = hpwhDataFetch()
print(new_datafetch.getCDF(x=))
