# -*- coding: utf-8 -*-
"""
HPWHComponents
@author: paul
"""
import numpy as np
from cfg import rhoCp, W_TO_BTUHR


##############################################################################
## Components of a HPWH system given below:
##############################################################################
class PrimarySystem_SP:
    """
    Class containing attributes and methods to describe and size the primary heat pump and storage for single pass systems.

    Attributes
    ----------
    totalHWLoad : float
        Total hot water load [btu/hr]
    loadShapeNorm : numpy array
        A one dimensional array with length 24 that describes the hot water usage for each hour of the day as a fraction of the total daily load.
    nPeople

    incomingT_F : float
        Incoming city water temperature (design temperature in winter). [°F]
    T_supply: float
        Supply hot water temperature, typically 120°F. [°F]
    storageT_F: float
        Storage temperature of the primary hot water storage tanks. [°F]
    supplyT_F

    defrostFactor: float
        A factor that reduces heating capacity at low temperatures based on need for defrost cycles to remove ice from evaporator coils. [units?]
    percentUsable: integer
        Percent of primary hot water storage that is usable due to sufficient thermal stratification. [more detail is probably needed here]
    aquaFract: float
        The fraction of the total hieght of the primary hot water tanks at which the Aquastat is located. [more detail, what is typical or default]
    compRuntime_hr: float
        Hour per day central heat pump equipment can run, duty cycle [hrs/day]

    PCap
        Primary heat pump water heater capacity [kBtu]
    PVol_G_atStorageT
        Primary storage tank volume [gals]
    runningVol_G
        Primary storage tank running volume [gals]
    cyclingVol_G
        Cycling volume [gals]
    aquaFract
        Fractional hieght of the aquastat in the tank.
    """

    def __init__(self, totalHWLoad, loadShapeNorm, nPeople,
                 incomingT_F, supplyT_F, storageT_F,
                 defrostFactor, percentUseable,
                 compRuntime_hr):

        #Initialize the sizer object with the inputs
        self.totalHWLoad    = totalHWLoad
        self.loadShapeNorm  = loadShapeNorm
        self.nPeople        = nPeople

        self.incomingT_F      = incomingT_F
        self.storageT_F       = storageT_F
        self.supplyT_F        = supplyT_F

        self.defrostFactor  = defrostFactor
        self.percentUseable = percentUseable
        self.compRuntime_hr    = compRuntime_hr

        # Outputs
        self.PCap              = 0. #kBTU/Hr
        self.PVol_G_atStorageT = 0. # Gallons
        self.runningVol_G      = 0. # Gallons
        self.cyclingVol_G      = 0. # Gallons
        self.aquaFract         = 0. #Fraction

    # this should be a separate function and not be part of the main object.
    def getPeakIndices(self,diff1):
        """
        Finds peak indices of array

        Parameters
        ----------
        diff1
        Any 1 dimensional array

        Returns
        -------
        array
        Array of indices in which input array changes from positive to negative
        """

        diff1 = np.array(diff1)
        return np.where(np.diff(np.sign(diff1))<0)[0]+1

    def primaryHeatHrs2kBTUHR(self, heathours):
        """
        Sizes primary heating equipment.

        Parameters
        ----------
        heathours
            The number of hours primary heating equipment can run.

        Returns
        -------
        heatCap
            The heating capacity in [btu/hr].
        """
        if isinstance(heathours, np.ndarray):
            if any(heathours > 24) or any(heathours <= 0):
                raise Exception("Heat hours is not within 1 - 24 hours")
        else:
            if heathours > 24 or heathours <= 0:
                raise Exception("Heat hours is not within 1 - 24 hours")

        heatCap = self.totalHWLoad / heathours * rhoCp * \
            (self.storageT_F - self.incomingT_F) / self.defrostFactor /1000.
        return heatCap

    # the temperature adjusted primary storage should be an attribute
    # what is the "new sizing methodology", isn't this just our sizing methodology?
    def sizePrimaryTankVolume(self, heatHrs):
        """
        Sizes primary storage

        Parameters
        ----------
        heathours
            The number of hours primary heating equipment can run.

        Returns
        -------
        volume
            A temperature adjusted total volume
        """

        diffN = 1/heatHrs - np.append(self.loadShapeNorm,self.loadShapeNorm)
        diffInd = self.getPeakIndices(diffN[0:23]) #Days repeat so just get first day!

        # Get the running volume #############################################
        runVolTemp = 0
        if len(diffInd) == 0:
            raise Exception("The heating rate is greater than the peak volume the system is oversized!")
        else:
            for peakInd in diffInd:
                diffCum = np.cumsum(diffN[peakInd:]) #Get the rest of the day from the start of the peak
                runVolTemp = max(runVolTemp, -min(diffCum[diffCum<0.])) #Minimum value less than 0 or 0.
        self.runningVol_G = runVolTemp * self.totalHWLoad

        # Get the Cycling Volume #############################################
        averageGPDPP    = 17. # Hard coded average draw rate
        avg_runtime     = 1. # Hard coded average runtime for HPWH
        self.cyclingVol_G = avg_runtime * (self.totalHWLoad / heatHrs - averageGPDPP/24. * self.nPeople) # (generation rate - average background draw)

        # Get the total volume ###############################################
        totalVol = ( self.runningVol_G + self.cyclingVol_G ) / self.percentUseable

        # Get the aquastat fraction from independently solved for cycling vol
        # and running vol.
        self.aquaFract =  1 - self.runningVol_G / totalVol

        # Return the temperature adjusted total volume #######################
        return totalVol * (self.supplyT_F - self.incomingT_F) / \
            (self.storageT_F - self.incomingT_F)

    # I am not following this function and need some clarification.
    def primaryCurve(self):
        """"
        Size the primary system curve

        Returns
        -------
        volN
        Array of volume in the tank at each hour.

        array
        Array of heat input...
        """
        heatHours = np.linspace(self.compRuntime_hr, 1/max(self.loadShapeNorm)*1.001, 10)
        volN = np.zeros(len(heatHours))
        for ii in range(0,len(heatHours)):
            volN[ii] = self.sizePrimaryTankVolume(heatHours[ii])
        return [volN, self.primaryHeatHrs2kBTUHR(heatHours)]

    def sizeVol_Cap(self):
        """
        Calculates PVol_G_atStorageT and PCap
        """
        self.PVol_G_atStorageT = self.sizePrimaryTankVolume(self.compRuntime_hr)
        self.PCap = self.primaryHeatHrs2kBTUHR(self.compRuntime_hr)

    def getSizingResults(self):
        """
        Returns sizing results as array

        Returns
        -------
        array
        self.PVol_G_atStorageT, self.PCap, self.aquaFract
        """
        if self.PVol_G_atStorageT == 0. or self.PCap == 0. or self.aquaFract == 0.:
            raise Exception("The system hasn't been sized yet!")

        return [ self.PVol_G_atStorageT,  self.PCap, self.aquaFract ]

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
class ParallelLoopTank:
    """ Sizes a temperature maintenance tank  """

    def __init__(self, nApt, Wapt, UAFudge, offTime_hr, TMRuntime_hr, setpointTM_F, TMonTemp_F):
        # Inputs from primary system
        self.nApt       = nApt

        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt # W/ apartment
        self.UAFudge    = UAFudge
        self.offTime_hr  = offTime_hr # Hour
        self.TMRuntime_hr  = TMRuntime_hr
        self.setpointTM_F = setpointTM_F
        self.TMonTemp_F    = TMonTemp_F
        # Outputs:
        self.TMCap = 0 #kBTU/Hr
        self.TMVol_G_atStorageT = 0 # Gallons

    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.TMVol_G_atStorageT =  (self.Wapt + self.UAFudge) * self.nApt / rhoCp * \
            W_TO_BTUHR * self.offTime_hr / (self.setpointTM_F - self.TMonTemp_F)

        self.TMCap =  rhoCp * self.TMVol_G_atStorageT * (self.setpointTM_F - self.TMonTemp_F) * \
            (1./self.TMRuntime_hr + 1./self.offTime_hr)
        return [ self.TMVol_G_atStorageT, self.TMCap ]
##############################################################################
class SwingTank:
    """ Sizes a swing tank  """

    def __init__(self, nApt, storageT_F, Wapt, UAFudge, offTime_hr, TMonTemp_F):
        # Inputs from primary system
        self.nApt       = nApt
        self.storageT_F   = storageT_F # deg F

        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt # W/ apartment
        self.UAFudge    = UAFudge
        self.offTime_hr    = offTime_hr # Hour
        self.TMonTemp_F   = TMonTemp_F # deg F

        # Outputs:
        self.TMCap      = 0 #kBTU/Hr
        self.TMVol_G_atStorageT      = 0 # Gallons

        if self.Wapt == 0:
            raise Exception("Swing tank initialized with 0 W per apt heat loss")

    def sizeVol_Cap(self):
        """ Sizes the volume in gallons and heat capactiy in BTU/hr"""
        self.TMVol_G_atStorageT = (self.Wapt + self.UAFudge) * self.nApt / rhoCp * \
            W_TO_BTUHR * self.offTime_hr / (self.storageT_F - self.TMonTemp_F)

        self.TMCap = (self.Wapt + self.UAFudge) * self.nApt * W_TO_BTUHR / 1000.
        return [ self.TMVol_G_atStorageT, self.TMCap ]

##############################################################################
class TrimTank:
    """ Sizes a trim tank for use in a multipass HPWH system """

    def __init__(self):
        """Initialize the sizer object with 0's for the inputs"""


##############################################################################
##############################################################################
