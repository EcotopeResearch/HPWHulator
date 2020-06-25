 # -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 16:01:38 2020

@author: adria
"""

import numpy as np
from cfg import rhoCp, TONS_TOKBTUHR

class ASHRAEsizer:
    # Create the ASHRAE medium sizing look-up table
    ashraeMediumLU = np.array([[5, 0.7], [15, 1.7], [30, 2.9], [60, 4.8], \
                                   [120, 8.0], [180, 11.0], [1440, 49.0]])
        
    # Create the ASHRAE low sizing look-up table
    ashraeLowLU = np.array([[5, 0.4], [15, 1.0], [30, 1.7], [60, 2.8], \
                                [120, 4.5], [180, 6.1], [1440, 20.0]])
        
    def __init__(self, nPeople, gpdpp,
                 incomingT_F, supplyT_F, storageT_F,
                 defrostFactor, percentUseable,
                 compRuntime_hr):
        """Initialize the ASHRAE sizer object with 0's for the inputs"""
        self.nPeople        = nPeople # Nnumber of people
        self.gpdpp          = gpdpp # Gallons per day per person

        self.supplyT_F        = supplyT_F # The supply temperature to the occupants
        self.incomingT_F      = incomingT_F # The incoming cold water temperature for the city
        self.storageT_F       = storageT_F # The primary hot water storage temperature 
       
        self.defrostFactor  = defrostFactor
        self.percentUseable = percentUseable
        self.compRuntime_hr = compRuntime_hr 

        self.peakFlowTable      = None
        self.PCap               = 0. #kBTU/Hr
        self.PVol_G_atStorageT  = 0. # Gallons
        
        self.extrapolated = False
        
        self.__checkInputs()
        self.__getASHRAEtable()
        [self.primaryVolArr, self.accurateRecoveryTonsArr] =self.sizePrimaryCurveAshrae(self.peakFlowTable)
        
    def __checkInputs(self):
        """Checks inputs are all valid"""
        if self.percentUseable > 1 or self.percentUseable < 0: # Check to make sure the percent is stored as anumber 0 to 1.
            raise Exception('\nERROR: Invalid input given for percentUseable.\n')    
        if self.gpdpp > 49: # or self.gpdpp < 20:
            raise Exception('\nERROR: Please ensure your gallons per day per person is less than 49.\n')
                            
    def __getASHRAEtable(self):
        """Sizes the primary HPWH plant with the ASHRAE methodology"""

        # Create a peakFlowTable - 
        # use the ASHRAE table if gpdpp is a match to the low or medium gpdpp
        # otherwise calculate userValues based on their input gpdpp
        if self.gpdpp == 20:
            peakFlowTable = self.ashraeLowLU
        elif self.gpdpp == 49:
            peakFlowTable = self.ashraeMediumLU
        #otherwise calculate the peak flow volumes for user-inputted gpdpp 
        else:
            yIncrement = (self.gpdpp - self.ashraeLowLU[6,1]) / (self.ashraeMediumLU[6,1] - self.ashraeLowLU[6,1])
            userValues = np.zeros_like(self.ashraeLowLU)
            #add the time intervals
            peakTimes = (5, 15, 30, 60, 120, 180, 1440)
            for ii in range(len(self.ashraeLowLU)):
                userValues[ii,1] = (self.ashraeMediumLU[ii,1] - self.ashraeLowLU[ii,1]) * yIncrement + self.ashraeLowLU[ii,1]
                userValues[ii,0] = peakTimes[ii]
            peakFlowTable = userValues

            if self.gpdpp < 20:
                self.extrapolated = True

        self.peakFlowTable = peakFlowTable;
        
    def sizePrimaryCurveAshrae(self, flowTable):
        """"Sizes the primary system curve using ASHRAE sizing"""

        # Create a diff peakFlowTable for recovery calculations
        # This takes the difference between the peakTimes and the gallons per Person for the peakFlowTable
        diffPeakFlowTable = np.diff(flowTable, axis = 0)
        #duplicate the last row
        diffPeakFlowTable = np.insert(diffPeakFlowTable, len(diffPeakFlowTable)-1, diffPeakFlowTable[len(diffPeakFlowTable)-1], axis=0)
        
        peakVolume = flowTable[:,1] * self.nPeople
       
        primaryVol = peakVolume / self.percentUseable * (self.supplyT_F - self.incomingT_F) / \
                (self.storageT_F - self.incomingT_F)
        
        accurateRecoveryTons = 60 * rhoCp * self.nPeople * \
                        (diffPeakFlowTable[:len(diffPeakFlowTable),1]) /  \
                        (diffPeakFlowTable[:len(diffPeakFlowTable),0]) *  \
                        (self.storageT_F - self.incomingT_F) / self.defrostFactor / 12000
             
        return [primaryVol, accurateRecoveryTons]
        
    def primaryCurve(self):
        """Function to return the sized ASHRAE curves for the interpolated gpdpp"""
        return [self.primaryVolArr, self.accurateRecoveryTonsArr * TONS_TOKBTUHR]
                
    def getLowCurve(self):
        """Function to return ASHRAE Low"""
        [vol_g, cap_tons] = self.sizePrimaryCurveAshrae(flowTable = self.ashraeLowLU)
        return [vol_g, cap_tons * TONS_TOKBTUHR]
        
    def getMediumCurve(self):
        """Function to return ASHRAE Low"""
        [vol_g, cap_tons] =  self.sizePrimaryCurveAshrae(flowTable = self.ashraeMediumLU)
        return [vol_g, cap_tons * TONS_TOKBTUHR]

        
    def tonsRecoveryForMaxDaily(self):
        """"Calculates the system heat capacity for a given compressor run time"""
        
        # Define the range of recovery hours
        recoveryHours = np.array([1,2,4,8,12,16,24])
        
        simpleTons = np.amax(self.peakFlowTable[6,1])*self.nPeople*rhoCp*(self.supplyT_F-self.incomingT_F)/12000/recoveryHours
     
        # Heat capacity determined by defined run time
        heatCap = np.interp(self.compRuntime_hr, recoveryHours, simpleTons)
        return heatCap 
    
    def minimumStorageVol(self,  heatCap):
        """"Calculates the minimum storage volume"""
        minStorage_gal = np.interp(heatCap, 
                                   self.primaryVolArr, 
                                   self.accurateRecoveryTonsArr)
        return minStorage_gal
    
    def sizeVol_Cap(self):
        """Sizes the system"""
        self.PCap = self.tonsRecoveryForMaxDaily() * TONS_TOKBTUHR;
        self.PVol_G_atStorageT = self.minimumStorageVol(self.PCap / TONS_TOKBTUHR)