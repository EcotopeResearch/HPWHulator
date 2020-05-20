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
                 incomingT, supplyT, storageT,
                 defrostFactor, percentUseable,
                 compRuntime):
        """Initialize the sizer object with the inputs"""
        self.totalHWLoad    = totalHWLoad;
        self.loadShapeNorm  = loadShapeNorm;
        self.nPeople        = nPeople;
        
        self.incomingT      = incomingT;
        self.storageT       = storageT;
        self.supplyT        = supplyT;
    
        self.defrostFactor  = defrostFactor;
        self.percentUseable = percentUseable;
        self.compRuntime    = compRuntime;

        # Outputs
        self.PCap           = 0.; #kBTU/Hr
        self.PVol           = 0.; # Gallons
        self.runningVol     = 0.; # Gallons
        self.cyclingVol     = 0.; # Gallons
        self.aquaFract      = 0.; #Fraction
        
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
            (self.storageT - self.incomingT) / self.defrostFactor /1000.;
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
        self.runningVol = runVolTemp * self.totalHWLoad;
        
        # Get the Cycling Volume #############################################
        averageGPDPP    = 17.; # Hard coded average draw rate
        avg_runtime     = 1.; # Hard coded average runtime for HPWH
        self.cyclingVol = avg_runtime * (self.totalHWLoad / heatHrs - averageGPDPP/24. * self.nPeople); # (generation rate - average background draw)
        
        # Get the total volume ###############################################
        totalVol = ( self.runningVol + self.cyclingVol ) / self.percentUseable;
        
        # Get the aquastat fraction from independently solved for cycling vol
        # and running vol.
        self.aquaFract =  1 - self.runningVol / totalVol;

        # Return the temperature adjusted total volume #######################
        return totalVol * (self.supplyT - self.incomingT) / \
            (self.storageT - self.incomingT);
            
    def primaryCurve(self):
        """"Size the primary system curve"""
        heatHours = np.linspace(self.compRuntime, 1/max(self.loadShapeNorm)*1.001, 10);
        volN = np.zeros(len(heatHours))
        for ii in range(0,len(heatHours)): 
            volN[ii] = self.sizePrimaryTankVolume(heatHours[ii]);
        return [volN, self.primaryHeatHrs2kBTUHR(heatHours)]
         
    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.PVol = self.sizePrimaryTankVolume(self.compRuntime);
        self.PCap = self.primaryHeatHrs2kBTUHR(self.compRuntime);
     

    def getSizingResults(self):
        """Returns the results of the primary sizer"""
        if self.PVol == 0. or self.PCap == 0. or self.aquaFract == 0.:
            raise Exception("The heating rate is greater than the peak volume the system is oversized!")
        
        return [ self.PVol,  self.PCap, self.aquaFract ];
        
    
##############################################################################
class PrimarySystem_MP_NR:    
    """ Sizes primary multipass HPWH system with NO recirculation loop """
    def __init__(self, totalHWLoad, loadShapeNorm, 
                 incomingT, supplyT, storageT,
                 defrostFactor, percentUseable, aquaFract,
                 compRuntime):
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
    
    def __init__(self, nApt, Wapt, UAFudge, offTime, TMRuntime, setpointTM, TMonTemp):
        # Inputs from primary system
        self.nApt       = nApt; 
        
        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt; # W/ apartment
        self.UAFudge    = UAFudge;
        self.offTime  = offTime; # Hour
        self.TMRuntime  = TMRuntime;
        self.setpointTM = setpointTM;
        self.TMonTemp    = TMonTemp;
        # Outputs:
        self.TMCap = 0; #kBTU/Hr
        self.TMVol = 0; # Gallons
        
    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.TMVol =  (self.Wapt + self.UAFudge) * self.nApt / rhoCp * \
            W_TO_BTUHR * self.offTime / (self.setpointTM - self.TMonTemp);
            
        self.TMCap =  rhoCp * self.TMVol * (self.setpointTM - self.TMonTemp) * \
            (1./self.TMRuntime + 1./self.offTime);
        return [ self.TMVol, self.TMCap ];
##############################################################################
class SwingTank:
    """ Sizes a swing tank  """    

    def __init__(self, nApt, storageT, Wapt, UAFudge, offTime, TMonTemp):
        # Inputs from primary system
        self.nApt       = nApt; 
        self.storageT   = storageT; # deg F
        
        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt; # W/ apartment
        self.UAFudge    = UAFudge;
        self.offTime    = offTime; # Hour
        self.TMonTemp   = TMonTemp; # deg F

        # Outputs:
        self.TMCap      = 0; #kBTU/Hr
        self.TMVol      = 0; # Gallons
    
        if self.Wapt == 0:
            raise Exception("Swing tank initialized with 0 W per apt heat loss")
            
    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.TMVol = (self.Wapt + self.UAFudge) * self.nApt / rhoCp * \
            W_TO_BTUHR * self.offTime / (self.storageT - self.TMonTemp);
            
        self.TMCap = (self.Wapt + self.UAFudge) * self.nApt * W_TO_BTUHR / 1000.;  
        return [ self.TMVol, self.TMCap ];
         
##############################################################################
class TrimTank:       
    """ Sizes a trim tank for use in a multipass HPWH system """
    
    def __init__(self):
        """Initialize the sizer object with 0's for the inputs"""

        
##############################################################################
##############################################################################