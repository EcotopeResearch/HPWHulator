

# Functions to gather data from JSON

import json
from scipy.stats import lognorm

class hpwhDataFetch():
    
    with open('hpwhdata.json') as json_file:
        dataDict = json.load(json_file)
    
    
    def __init__(self):
        pass
    
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
    
    def getCDF(self, x, cdf_shift = 0):
        params = self.dataDict['gpdppfit']
        #cdf = list(zip(x, lognorm.cdf(x, params[0], params[1] + cdf_shift, params[2])))
        cdf = lognorm.cdf(x, params[0], params[1] + cdf_shift, params[2])
        return(cdf)
    