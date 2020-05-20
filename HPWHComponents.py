# -*- coding: utf-8 -*-
"""
HPWHComponents
@author: paul
"""
import numpy as np;
from cfg import rhoCp, W_TO_BTUHR


##############################################################################
## Components of a HPWH system given below:
##############################################################################
class PrimarySystem_SP:
    """ Sizes the primary single pass system"""
   
    def __init__(self, totalHWLoad, loadShapeNorm, nPeople,
                 incomingT_F, supplyT_F, storageT_F,
                 defrostFactor, percentUseable,
                 compRuntime_hr):
        """Initialize the sizer object with the inputs"""
        self.totalHWLoad    = totalHWLoad;
        self.loadShapeNorm  = loadShapeNorm;
        self.nPeople        = nPeople;
        
        self.incomingT_F      = incomingT_F;
        self.storageT_F       = storageT_F;
        self.supplyT_F        = supplyT_F;
    
        self.defrostFactor  = defrostFactor;
        self.percentUseable = percentUseable;
        self.compRuntime_hr    = compRuntime_hr;

        # Outputs
        self.PCap              = 0.; #kBTU/Hr
        self.PVol_G_atStorageT = 0.; # Gallons
        self.runningVol_G      = 0.; # Gallons
        self.cyclingVol_G      = 0.; # Gallons
        self.aquaFract         = 0.; #Fraction
        
    def getPeakIndices(self,diff1):
          """Returns an array that gives the indices when the array diff goes from positive to negative"""
          diff1 = np.array(diff1);
          return np.where(np.diff(np.sign(diff1))<0)[0]+1;
          
    def primaryHeatHrs2kBTUHR(self, heathours):
        """Returns the heating capacity in kBTU/hr for the heating hours given by, heathours"""
        if isinstance(heathours, np.ndarray):
            if any(heathours > 24) or any(heathours <= 0):
                raise Exception("Heat hours is not within 1 - 24 hours")
        else:
            if heathours > 24 or heathours <= 0:
                raise Exception("Heat hours is not within 1 - 24 hours")
                
        heatCap = self.totalHWLoad / heathours * rhoCp * \
            (self.storageT_F - self.incomingT_F) / self.defrostFactor /1000.;
        return heatCap;
    
    def sizePrimaryTankVolume(self, heatHrs):
        """Sizes the primary HPWH plant with the new methodology"""
        diffN = 1/heatHrs - np.append(self.loadShapeNorm,self.loadShapeNorm);         
        diffInd = self.getPeakIndices(diffN[0:23]); #Days repeat so just get first day!
        
        # Get the running volume #############################################
        runVolTemp = 0;
        if len(diffInd) == 0:
            raise Exception("The heating rate is greater than the peak volume the system is oversized!")
        else:
            for peakInd in diffInd:
                diffCum = np.cumsum(diffN[peakInd:]); #Get the rest of the day from the start of the peak
                runVolTemp = max(runVolTemp, -min(diffCum[diffCum<0.])); #Minimum value less than 0 or 0.
        self.runningVol_G = runVolTemp * self.totalHWLoad;
        
        # Get the Cycling Volume #############################################
        averageGPDPP    = 17.; # Hard coded average draw rate
        avg_runtime     = 1.; # Hard coded average runtime for HPWH
        self.cyclingVol_G = avg_runtime * (self.totalHWLoad / heatHrs - averageGPDPP/24. * self.nPeople); # (generation rate - average background draw)
        
        # Get the total volume ###############################################
        totalVol = ( self.runningVol_G + self.cyclingVol_G ) / self.percentUseable;
        
        # Get the aquastat fraction from independently solved for cycling vol
        # and running vol.
        self.aquaFract =  1 - self.runningVol_G / totalVol;

        # Return the temperature adjusted total volume #######################
        return totalVol * (self.supplyT_F - self.incomingT_F) / \
            (self.storageT_F - self.incomingT_F);
            
    def primaryCurve(self):
        """"Size the primary system curve"""
        heatHours = np.linspace(self.compRuntime_hr, 1/max(self.loadShapeNorm)*1.001, 10);
        volN = np.zeros(len(heatHours))
        for ii in range(0,len(heatHours)): 
            volN[ii] = self.sizePrimaryTankVolume(heatHours[ii]);
        return [volN, self.primaryHeatHrs2kBTUHR(heatHours)]
         
    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.PVol_G_atStorageT = self.sizePrimaryTankVolume(self.compRuntime_hr);
        self.PCap = self.primaryHeatHrs2kBTUHR(self.compRuntime_hr);
     
    def getSizingResults(self):
        """Returns the results of the primary sizer"""
        if self.PVol_G_atStorageT == 0. or self.PCap == 0. or self.aquaFract == 0.:
            raise Exception("The system hasn't been sized yet!")
        
        return [ self.PVol_G_atStorageT,  self.PCap, self.aquaFract ];
    
##############################################################################
class PrimarySystem_MP_NR:    
    """ Sizes primary multipass HPWH system with NO recirculation loop """
    def __init__(self, totalHWLoad, loadShapeNorm, 
                 incomingT_F, supplyT_F, storageT_F,
                 defrostFactor, percentUseable, aquaFract,
                 compRuntime_hr):
        pass

##############################################################################
class PrimarySystem_MP_R:
    """ Sizes primary multipass HPWH system WITH a recirculation loop """
    
    def __init__(self):
        """Initialize the sizer object with 0's for the inputs"""
        pass
    
##############################################################################
class TempMaint:
    """ Sizes a temperature maintenance tank  """ 
    
    def __init__(self, nApt, Wapt, UAFudge, offTime_hr, TMRuntime_hr, setpointTM_F, TMonTemp_F):
        # Inputs from primary system
        self.nApt       = nApt; 
        
        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt; # W/ apartment
        self.UAFudge    = UAFudge;
        self.offTime_hr  = offTime_hr; # Hour
        self.TMRuntime_hr  = TMRuntime_hr;
        self.setpointTM_F = setpointTM_F;
        self.TMonTemp_F    = TMonTemp_F;
        # Outputs:
        self.TMCap = 0; #kBTU/Hr
        self.TMVol_G_atStorageT = 0; # Gallons
        
    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.TMVol_G_atStorageT =  (self.Wapt + self.UAFudge) * self.nApt / rhoCp * \
            W_TO_BTUHR * self.offTime_hr / (self.setpointTM_F - self.TMonTemp_F);
            
        self.TMCap =  rhoCp * self.TMVol_G_atStorageT * (self.setpointTM_F - self.TMonTemp_F) * \
            (1./self.TMRuntime_hr + 1./self.offTime_hr);
        return [ self.TMVol_G_atStorageT, self.TMCap ];
##############################################################################
class SwingTank:
    """ Sizes a swing tank  """    

    def __init__(self, nApt, storageT_F, Wapt, UAFudge, offTime_hr, TMonTemp_F):
        # Inputs from primary system
        self.nApt       = nApt; 
        self.storageT_F   = storageT_F; # deg F
        
        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt; # W/ apartment
        self.UAFudge    = UAFudge;
        self.offTime_hr    = offTime_hr; # Hour
        self.TMonTemp_F   = TMonTemp_F; # deg F

        # Outputs:
        self.TMCap      = 0; #kBTU/Hr
        self.TMVol_G_atStorageT      = 0; # Gallons

        if self.Wapt == 0:
            raise Exception("Swing tank initialized with 0 W per apt heat loss")
            
    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.TMVol_G_atStorageT = (self.Wapt + self.UAFudge) * self.nApt / rhoCp * \
            W_TO_BTUHR * self.offTime_hr / (self.storageT_F - self.TMonTemp_F);
            
        self.TMCap = (self.Wapt + self.UAFudge) * self.nApt * W_TO_BTUHR / 1000.;  
        return [ self.TMVol_G_atStorageT, self.TMCap ];
         
##############################################################################
class TrimTank:       
    """ Sizes a trim tank for use in a multipass HPWH system """
    
    def __init__(self):
        """Initialize the sizer object with 0's for the inputs"""

        
##############################################################################
##############################################################################
