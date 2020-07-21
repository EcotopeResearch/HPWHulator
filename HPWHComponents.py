# -*- coding: utf-8 -*-
"""
HPWHComponents
@author: paul
"""
import numpy as np
from cfg import rhoCp, W_TO_BTUHR, Wapt75, Wapt25, TMSafetyFactor


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
    nPeople: integer
        Number of residents.
    incomingT_F : float
        Incoming city water temperature (design temperature in winter). [°F]
    storageT_F: float
        Storage temperature of the primary hot water storage tanks. [°F]
    supplyT_F : float
        Supply hot water temperature to occupants, typically 120°F. [°F]
     percentUsable : float
        Percent of primary hot water storage that is usable due to sufficient thermal stratification.
    aquaFract: float
        The fraction of the total hieght of the primary hot water tanks at which the Aquastat is located.
    compRuntime_hr : float
        Hour per day central heat pump equipment can run, duty cycle [hrs/day]
    defrostFactor: float
        A factor that reduces heating capacity at low temperatures based on need for defrost cycles to remove ice from evaporator coils.
    swingTankLoad_W : float
        An addition of extra laod from the distrubution system when using the swing tank. 
    PCap_kBTUhr : float
        Primary heat pump water heater capacity [kBtu]
    PVol_G_atStorageT : float
        Primary storage tank volume [gals]
    aquaFract : float
        Fractional hieght of the aquastat in the tank.
    swingTankLoad_W : float
        Extra load in Watts that is added to the primary system.
        
    """

    def __init__(self, totalHWLoad, loadShapeNorm, nPeople,
                 incomingT_F, supplyT_F, storageT_F,
                 percentUseable, compRuntime_hr, aquaFract,
                 defrostFactor, swingTankLoad_W = 0):

        #Initialize the sizer object with the inputs
        self.totalHWLoad    = totalHWLoad
        if not isinstance(loadShapeNorm, np.ndarray):
            self.loadShapeNorm  = np.array(loadShapeNorm)
        else:
            self.loadShapeNorm  = loadShapeNorm
        self.nPeople        = nPeople

        self.incomingT_F      = incomingT_F
        self.storageT_F       = storageT_F
        self.supplyT_F        = supplyT_F

        self.defrostFactor      = defrostFactor
        self.percentUseable     = percentUseable
        self.compRuntime_hr     = compRuntime_hr
        self.aquaFract          = aquaFract #Fraction

        self.extraLoad_GPH = W_TO_BTUHR * swingTankLoad_W / rhoCp / \
            (self.storageT_F - self.incomingT_F)

        # Internal variables
        self.maxDayRun_hr = compRuntime_hr
        self.LS_on_off = np.ones(24)
        self.loadShift = False;

        # Outputs
        self.PCap_kBTUhr              = 0. #kBTU/Hr
        self.PVol_G_atStorageT = 0. # Gallons

    def setLoadShift(self, schedule):
        """
        Sets the load shifting schedule from input schedule

        Parameters
        ----------            
        schedule : array_like
            List or array of 0's and 1's for don't run and run.

        """
        # Coerce to 0s and 1s
        self.LS_on_off = np.where(schedule > 0, 1, 0)
        self.loadShift = True
        # Check if need to increase sizing to meet lower runtimes in a day for load shifting.
        self.maxDayRun_hr = min(self.compRuntime_hr,sum(self.LS_on_off))

    def _checkHeatHours(self, heathours):
        """
        Quick check to see if heating hours is a valid number between 1 and 24

        Parameters
        ----------
        heathours (float or numpy.ndarray)
            The number of hours primary heating equipment can run.
        """
        if isinstance(heathours, np.ndarray):
            if any(heathours > 24) or any(heathours <= 0):
                raise Exception("Heat hours is not within 1 - 24 hours")
        else:
            if heathours > 24 or heathours <= 0:
                raise Exception("Heat hours is not within 1 - 24 hours")

    def primaryHeatHrs2kBTUHR(self, heathours):
        """
        Converts from hours of heating in a day to heating capacity.

        Parameters
        ----------
        heathours  (float or numpy.ndarray)
            The number of hours primary heating equipment can run.

        Returns
        -------
        heatCap
            The heating capacity in [btu/hr].
        """
        self._checkHeatHours(heathours)
        heatCap = (self.totalHWLoad + 24*self.extraLoad_GPH) / heathours * rhoCp * \
            (self.storageT_F - self.incomingT_F) / self.defrostFactor /1000.
        return heatCap

    def sizePrimaryTankVolume(self, heatHrs):
        """
        Calculates the primary storage using the Ecotope sizing methodology

        Parameters
        ----------
        heatHrs : float
            The number of hours primary heating equipment can run in a day.

        Returns
        -------
        totalVolMax : float
            The total storage volume in gallons adjusted to the storage tempreature
        """
        self._checkHeatHours(heatHrs)

        # Running vol
        runningVol_G = self.__calcRunningVol(heatHrs,np.ones(24))

        # If doing load shift, solve for the runningVol_G and take the larger volume
        LSrunningVol_G = 0
        if self.loadShift:
            LSrunningVol_G = self.__calcRunningVol(heatHrs,self.LS_on_off)

        # Get total volume from max of primary method or load shift method
        totalVolMax = max(runningVol_G, LSrunningVol_G)

        # If the swing tank is not being used
        if self.extraLoad_GPH == 0:
            totalVolMax = self.__SUPPLYV_TO_STORAGEV(totalVolMax) / (1-self.aquaFract)

        # Check the Cycling Volume ##############################################
        cyclingVol_G    = totalVolMax * (self.aquaFract - (1 - self.percentUseable))
        min_runtime_hr  = 10/60. # Hard coded minimum run time for water heater in hours
        minRunVol_G     = min_runtime_hr * (self.totalHWLoad / heatHrs) # (generation rate - no usage)

        if minRunVol_G > cyclingVol_G:
            min_AF = minRunVol_G / totalVolMax + (1 - self.percentUseable)
            if min_AF < 1:
                raise ValueError ("The aquastat fraction is too low in the storge system recommend increasing to a minimum of: %.3f or increasing the maximum run hours in the day" % round(min_AF,3))
            else:
                raise ValueError ("The minimum aquastat fraction is greater than 1. This is due to the storage efficency and/or the maximum run hours in the day may be too low. Try increasing these values, we reccomend 0.8 and 16 hours for these variables respectively." )

            
        # Return the temperature adjusted total volume ########################
        return totalVolMax

    def __calcRunningVol(self, heatHrs, onOffArr):
        """
        Function to find the running volume for the hot water storage tank, which
        is needed for calculating the total volume for primary sizing and in the event of load shift sizing
        represents the entire volume.

        Parameters
        ----------
            heatHrs (float): The number of hours primary heating equipment can run in a day.
            onOffArr (np.array): array of 1/0's where 1's allow heat pump to run and 0's dissallow. of length 24.

        Raises
        ------
            Exception: Error if oversizeing system.

        Returns
        -------
            runV_G : float 
            The running volume in gallons

        """
        diffN   = (np.tile(onOffArr,2) + self.extraLoad_GPH/self.totalHWLoad) / heatHrs - np.tile(self.loadShapeNorm,2)
        diffInd = getPeakIndices(diffN[0:23]) #Days repeat so just get first day!

        # Get the running volume ##############################################
        if len(diffInd) == 0:
            raise Exception("The heating rate is greater than the peak volume the system is oversized! Try increasing the hours the heat pump runs in a day")
        else:
            runVolTemp = 0
            for peakInd in diffInd:
                diffCum = np.cumsum(diffN[peakInd:]) #Get the rest of the day from the start of the peak
                runVolTemp = max(runVolTemp, -min(diffCum[diffCum<0.])) #Minimum value less than 0 or 0.
        runV_G = runVolTemp * self.totalHWLoad

        return runV_G

    def __SUPPLYV_TO_STORAGEV(self, vol):
        """
        Converts the volume of water at the supply temperature to an equivalent volume at the storage temperature

        Parameters
        ----------
        vol : float
            Volume at the supply temperature.

        Returns
        -------
        float
            Volume at storage temperature.

        """
        return mixVolume(vol, self.storageT_F, self.incomingT_F, self.supplyT_F)

    def __STORAGEV_TO_SUPPLYV(self, vol):
        """
        Converts the volume of water at the storage temperature to an equivalent volume at the supply temperature

        Parameters
        ----------
        vol : float
            Volume at the storage temperature.

        Returns
        -------
        float
            Volume at supply temperature.

        """
        return mixVolume(vol, self.supplyT_F,  self.incomingT_F, self.storageT_F)


    def primaryCurve(self):
        """
        Sizes the primary system curve. Will catch the point at which the aquatstat
        fraction is too small for system and cuts the return arrays to match cutoff point.

        Returns
        -------
        volN
            Array of volume in the tank at each hour.

        array
            Array of heat input...
        """

        maxHeatHours = 1/(max(self.loadShapeNorm) - self.extraLoad_GPH/self.totalHWLoad)*1.001
        heatHours = np.linspace(self.compRuntime_hr, maxHeatHours,30)
        volN = np.zeros(len(heatHours))
        for ii in range(0,len(heatHours)):
            try:
                volN[ii] = self.sizePrimaryTankVolume(heatHours[ii])
            except ValueError:
                break
        # Cut to the point the aquastat fraction was too small
        volN        = volN[:ii]
        heatHours   = heatHours[:ii]

        return [volN, self.primaryHeatHrs2kBTUHR(heatHours)]

    def sizeVol_Cap(self):
        """
        Calculates the minimum primary volume and heating capacity for the primary system: PVol_G_atStorageT and PCap_kBTUhr
        """
        self.PVol_G_atStorageT = self.sizePrimaryTankVolume(self.maxDayRun_hr)
        self.PCap_kBTUhr = self.primaryHeatHrs2kBTUHR(self.maxDayRun_hr)

    def getSizingResults(self):
        """
        Returns the minimum primary volume and heating capacity sizing results 

        Returns
        -------
        list
            self.PVol_G_atStorageT, self.PCap_kBTUhr
        """
        if self.PVol_G_atStorageT == 0. or self.PCap_kBTUhr == 0.:
            raise Exception("The system hasn't been sized yet! Run sizeVol_Cap() first")

        return [ self.PVol_G_atStorageT,  self.PCap_kBTUhr ]

    def runStorage_Load_Sim(self, capacity = None, volume = None, hourly = False):
        """
        Returns sizing storage depletion and load results for water volumes at the supply temperature

        Parameters
        ----------
        capacity (float) : The primary heating capacity in kBTUhr to use for the simulation, default is the sized system
        volume (float) : The primary storage volume in gallons to  to use for the simulation, default is the sized system

        Returns
        -------
        list [ V, G_hw, D_hw, run ]
        V - Volume of HW in the tank with time
        G_hw - The generation of HW with time
        D_hw - The hot water demand with time
        run - The actual output in gallons of the HPWH with time
        """
        if not capacity:
            if self.PCap_kBTUhr:
                capacity =  self.PCap_kBTUhr
            else:
                raise Exception("The system hasn't been sized yet! Either specify capacity AND volume or size the system.")

        if not volume:
            if self.PVol_G_atStorageT:
                volume =  self.PVol_G_atStorageT
            else:
                raise Exception("The system hasn't been sized yet! Either specify capacity AND volume or size the system.")

        heathours = (self.totalHWLoad + 24*self.extraLoad_GPH) / capacity * rhoCp * \
            (self.storageT_F - self.incomingT_F) / self.defrostFactor /1000.


        G_hw = self.totalHWLoad/heathours * np.tile(self.LS_on_off,3)
        D_hw = self.totalHWLoad * np.tile(self.loadShapeNorm,3)

        if not hourly:
            G_hw = np.array(HRLIST_to_MINLIST(G_hw)) / 60
            D_hw = np.array(HRLIST_to_MINLIST(D_hw)) / 60
            
        #Init the "simulation"
        N = len(G_hw)
        V0 = self.__STORAGEV_TO_SUPPLYV(volume) * self.percentUseable
        Vtrig = self.__STORAGEV_TO_SUPPLYV(volume) * (1 - self.aquaFract)
        run = [0] * (N)
        V = [V0] + [0] * (N - 1)
        heating = False

        #Run the "simulation"
        for ii in range(1,N):

            if heating:
                V[ii] = V[ii-1] + G_hw[ii] - D_hw[ii] # If heating, generate HW and lose HW
                run[ii] = G_hw[ii]

            else:  # Else not heating,
                V[ii] = V[ii-1] - D_hw[ii] # So lose HW
                if V[ii] < Vtrig: # If should heat
                    time_missed = (Vtrig - V[ii])/D_hw[ii] #Volume below turn on / rate of draw gives time below tigger
                    V[ii] += G_hw[ii]*time_missed # Start heating
                    run[ii] = G_hw[ii]*time_missed
                    heating = True

            if V[ii] > V0: # If full
                time_over = (V[ii] - V0)/(G_hw[ii]-D_hw[ii]) # Volume over generated / rate of generation gives time above full
                V[ii] = V0 - D_hw[ii]*time_over # Make full with miss volume
                run[ii] = G_hw[ii] * (1-time_over)
                heating = False # Stop heating

        return [ roundList(V,3), roundList(G_hw,3), roundList(D_hw,3), roundList(run,3) ]


##############################################################################
class ParallelLoopTank:
    """
    Class containing attributes and methods to describe and size the parrallel loop tank arrangement. Unlike a swing tank, a parrallel loop tank \
    will have equipment to provide heat for periods of low or no hot water use.

    Attributes
    ----------
    nApt: integer
        The number of apartments. Use with Qdot_apt to determine total recirculation losses.
    Wapt:  float
        Watts of heat lost in through recirculation piping system. Used with N_apt to determine total recirculation losses.
    offTime_hr: integer
        Maximum hours per day the temperature maintenance equipment can run.
    TMRuntime_hr: float
        Run time required for temperature maintenance equipment to meet setpoint.
    setpointTM_F: float
        Temperature maintenance tank setpoint.
    TMonTemp_F: float
        Temperature at which temperature maintenance equipment will engauge.
    TMCap_kBTUhr
        Temperature maintenance equipment capacity.
    TMVol_G
        Volume of parrallel loop tank.
    """
    minimumRunTime  = 10./60.

    def __init__(self, nApt, Wapt, setpointTM_F, TMonTemp_F):
        # Inputs from primary system
        self.nApt       = nApt
        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt # W/ apartment

        self.setpointTM_F = setpointTM_F
        self.TMonTemp_F    = TMonTemp_F
        # Outputs:
        self.TMCap_kBTUhr = 0 #kBTU/Hr
        self.TMVol_G = 0 # Gallons

    def sizeVol_Cap(self):
        """
        Sizes the volume in gallons and heat capactiy in kBTU/h

        Calculates:
        TMVol_G
            Dedicated loop tank volume.
        TMCap_kBTUhr
            Calculated temperature maintenance equipment capacity in kBTU/h.
        """

        self.TMCap_kBTUhr = self.nApt * self.Wapt * Wapt75 * TMSafetyFactor * W_TO_BTUHR/ 1000.
        self.TMVol_G = (1000.*self.TMCap_kBTUhr - self.nApt * self.Wapt * Wapt25 * W_TO_BTUHR ) * \
                        self.minimumRunTime/(self.setpointTM_F - self.TMonTemp_F)/rhoCp



    def getSizingResults(self):
        """
        Returns sizing results as array

        Returns
        -------
        list
            self.TMVol_G, self.TMCap_kBTUhr
        """
        return [ self.TMVol_G, self.TMCap_kBTUhr ]

    def tempMaintCurve(self, runtime = None):
        """
        Returns the sizing curve for a parallel loop tank

        Returns
        -------
        list
            volN_G, capacity
        """
        if runtime is None:
            runtime = self.minimumRunTime

        volN_G = np.linspace(self.TMVol_G , 1000, 30)
        capacity = rhoCp * volN_G / runtime * (self.setpointTM_F - self.TMonTemp_F) + \
                    self.nApt * self.Wapt * Wapt25 * W_TO_BTUHR
        capacity /= 1000.

        keep = capacity >= self.TMCap_kBTUhr

        return [ volN_G[keep], capacity[keep] ]


##############################################################################

class SwingTank:
    """
    Class containing attributes and methods to describe and size the swing tank. Unlike a temperature maintenance tank, the swing tank is sized so
    the primary system heat adds heat to cover about up to 70% of the reciculation losses.

    Attributes
    ----------
    nApt : integer
        The number of apartments. Use with Qdot_apt to determine total recirculation losses.
    Wapt :  float
        Watts of heat lost in through recirculation piping system. Used with N_apt to determine total recirculation losses.
    TMCap_kBTUhr :  float
        The required capacity of temperature maintenance equipment.
    TMVol_G :  float
        The volume of the swing tank required to ride out the low use period.
    """
    Table_Napts = [0, 12, 24, 48, 96]
    sizingTable_MEASHRAE = ["80", "80", "80", "120 - 300", "120 - 300"]
    sizingTable_CA = ["80", "96", "168", "288", "480"]

    swingLoadToPrimary_Wapt = 50.

    def __init__(self, nApt, Wapt):
        # Inputs from primary system
        self.nApt       = nApt
        # Inputs for temperature maintenance sizing
        self.Wapt       = Wapt #W/ apartment

        self.swingLoadToPrimary_W = self.swingLoadToPrimary_Wapt * self.nApt

        # Outputs:
        self.TMCap_kBTUhr                   = 0 #kBTU/Hr
        self.TMVol_G      = 0 # Gallons

        if self.Wapt == 0:
            raise Exception("Swing tank initialized with 0 W per apt heat loss")

    def sizeVol_Cap(self, CA = False):
        """
        Sizes the volume in gallons and heat capactiy in kBTU/hr

        Calculates:
        TMVol_G
            Calculated swing tank volume.
        TMCap_kBTUhr
            Calculated temperature maintenance equipment capacity.
        """
        ind = [idx for idx, val in enumerate(self.Table_Napts) if val <= self.nApt][-1]

        if CA:
            self.TMVol_G = self.sizingTable_CA[ind]
        else:
            self.TMVol_G = self.sizingTable_MEASHRAE[ind]

        self.TMCap_kBTUhr = TMSafetyFactor * Wapt75 * self.Wapt * self.nApt * W_TO_BTUHR / 1000.

    def getSizingResults(self):
        """
        Returns sizing results as array

        Returns
        -------
        list
            self.TMVol_G, self.TMCap_kBTUhr
        """
        return [ self.TMVol_G, self.TMCap_kBTUhr ]

    def getSwingLoadOnPrimary_W(self):
        """
        Returns the load in watts that the primary system handles from the reciruclation loop losses.
        Returns
        -------
        float
            self.swingLoadToPrimary_W
        """
        return self.swingLoadToPrimary_W

    def getSizingTable(self, CA = True):
        if CA:
            return list(zip(self.Table_Napts, self.sizingTable_CA))
        else:
            return list(zip(self.Table_Napts, self.sizingTable_MEASHRAE))


##############################################################################
##############################################################################
##############################################################################

def getPeakIndices(diff1):
    """
    Finds the points of an array where the values go from positive to negative

    Parameters
    ----------
    diff1 : array_like
        A 1 dimensional array.

    Returns
    -------
    ndarray
        Array of indices in which input array changes from positive to negative
    """
    if not isinstance(diff1, np.ndarray):
        diff1 = np.array(diff1)
    diff1 = np.insert(diff1, 0, 0)
    return np.where(np.diff(np.sign(diff1))<0)[0]

def roundList(a_list, n=3):
    """
    Rounds elements in a python list

    Parameters
    ----------
    a_list : float 
        list to round values of.
    n : int
        optional, default = 3. Number of digits to round elements to.

    Returns
    -------
    list
        rounded values.

    """
    return [round(num, n) for num in a_list]

def HRLIST_to_MINLIST(a_list):
    """
    Repeats each element of a_list 60 times to go from hourly to minute. 
    Still may need other unit conversions to get data from per hour to per minute

    Parameters
    ----------
    a_list : list
        A list in of values per hour.

    Returns
    -------
    out_list : list 
        A list in of values per minute created by repeating values per hour 60 times.

    """
    out_list = []
    for num in a_list:
        out_list += [num]*60
    return out_list


def mixVolume(vol, hotT, coldT, outT):
    """
    Adjusts the volume of water such that the hotT water and outT water have the 
    same amount of energy, meaning different volumes.

    Parameters
    ----------
    vol : float
        The reference volume to convert.
    hotT : float
        The hot water temperature used for mixing.
    coldT : float 
        The cold water tempeature used for mixing.
    outT : float 
        The out water temperature from mixing.

    Returns
    -------
    float
        Temperature adjusted volume.

    """
    fraction = (outT - coldT) / (hotT - coldT)
    
    return vol * fraction
