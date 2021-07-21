"""
    HPWHulator
    Copyright (C) 2020  Ecotope Inc.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import numpy as np

from cfg import rhoCp, W_TO_BTUHR, HRLIST_to_MINLIST, mixVolume, \
                pCompMinimumRunTime, tmCompMinimumRunTime
from Simulator import Simulator

##############################################################################
## Components of a HPWH system given below:
##############################################################################
class PrimarySystem_SP:
    """
    Class containing attributes and methods to describe and size the primary
    heat pump and storage for single pass systems.

    Attributes
    ----------
    totalHWLoad : float
        Total hot water load [btu/hr]
    loadShapeNorm : numpy array
        A one dimensional array with length 24 that describes the hot water
        usage for each hour of the day as a fraction of the total daily load.
    nPeople: integer
        Number of residents.
    incomingT_F : float
        Incoming city water temperature (design temperature in winter). [°F]
    storageT_F: float
        Storage temperature of the primary hot water storage tanks. [°F]
    supplyT_F : float
        Supply hot water temperature to occupants, typically 120°F. [°F]
    percentUsable : float
        Percent of primary hot water storage that is usable due to sufficient
        thermal stratification.
    aquaFract: float
        The fraction of the total hieght of the primary hot water tanks at
        which the Aquastat is located.
    compRuntime_hr : float
        Hour per day central heat pump equipment can run, duty cycle [hrs/day]
    defrostFactor: float
        A factor that reduces heating capacity at low temperatures based on
        need for defrost cycles to remove ice from evaporator coils.
    PCap_kBTUhr : float
        Primary heat pump water heater capacity [kBtu]
    PVol_G_atStorageT : float
        Primary storage tank volume [gals]
    aquaFract : float
        Fractional hieght of the aquastat in the tank.
    SwingTank : swingtank
        The swing tank object associated with the primary system if there is
        one.
    swingTankLoad_W : float
        Extra load in Watts that is added to the primary system.
    fractDHW : float
        Fraction describing the decreased total volume to be met for load
        shift based on the total number of days to meet.
    LSconstrained : boolean
        If the load shift requirement for the recommended system is larger
        than the system without load shift recommended.
    """

    def __init__(self, totalHWLoad, loadShapeNorm, nPeople,
                 incomingT_F, supplyT_F, storageT_F,
                 percentUseable, compRuntime_hr, aquaFract,
                 defrostFactor, swingTank=None):

        #Initialize the sizer object with the inputs
        self.totalHWLoad = totalHWLoad
        if not isinstance(loadShapeNorm, np.ndarray):
            self.loadShapeNorm = np.array(loadShapeNorm)
        else:
            self.loadShapeNorm = loadShapeNorm
        self.nPeople = nPeople

        self.incomingT_F = incomingT_F
        self.storageT_F = storageT_F
        self.supplyT_F = supplyT_F

        self.defrostFactor = defrostFactor
        self.percentUseable = percentUseable
        self.compRuntime_hr = compRuntime_hr
        self.aquaFract = aquaFract #Fraction

        self.swingTank = swingTank

        # Internal variables
        self.effSwingFract = 1.

        self.maxDayRun_hr = compRuntime_hr
        self.LS_on_off = np.ones(24)
        self.loadShift = False
        self.fractDHW = 1.
        self.LSconstrained = False
        self.avgLoadShape = None
         
        # Outputs
        self.PCap_kBTUhr = 0. #kBTU/Hr
        self.PVol_G_atStorageT = 0. # Gallons

    def setLoadShift(self, schedule, fractDHW, avgLoadShape):
        """
        Sets the load shifting schedule from input schedule

        Parameters
        ----------
        schedule : array_like
            List or array of 0's and 1's for don't run and run.

        fractDHW : float
            Fraction of DHW load corresponding to percent of days to be
            shifted in a load shift scenario

        """
        # Coerce to 0s and 1s
        self.LS_on_off = np.where(schedule > 0, 1, 0)
        self.fractDHW = fractDHW
        self.loadShift = True
        #Check if need to increase sizing to meet lower runtimes for load shift
        self.maxDayRun_hr = min(self.compRuntime_hr, sum(self.LS_on_off))
         
        self.avgLoadShape = np.array(avgLoadShape)
        
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

    def primaryHeatHrs2kBTUHR(self, heathours, effSwingVolFract=1):
        """
        Converts from hours of heating in a day to heating capacity.

        Parameters
        ----------
        heathours : float or numpy.ndarray
            The number of hours primary heating equipment can run.

        effSwingVolFract : float or numpy.ndarray
            The fractional adjustment to the total hot water load for the
            primary system. Only used in a swing tank system.

        Returns
        -------
        heatCap
            The heating capacity in [btu/hr].
        """
        self._checkHeatHours(heathours)
        if self.swingTank:
            heatCap = self.totalHWLoad * effSwingVolFract / heathours * rhoCp * \
                (self.storageT_F - self.incomingT_F) / self.defrostFactor /1000.
        else:
            heatCap = self.totalHWLoad / heathours * rhoCp * \
                (self.supplyT_F - self.incomingT_F) / self.defrostFactor /1000.
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
        # Fraction used for adjusting swing tank volume.
        effMixFract = 1.
        # If the system is sized for load shift days or the load shift
        # requirement is less than required
        largerLS = False

        # Running vol
        if self.swingTank:
            runningVol_G, effMixFract = self.__calcRunningVolSwingTank(heatHrs,np.ones(24))
        else:
            runningVol_G = self.__calcRunningVol(heatHrs, np.ones(24))

        # If doing load shift, solve for the runningVol_G and take the larger volume
        if self.loadShift:
            LSrunningVol_G = 0
            LSeffMixFract = 0
            if self.swingTank:
                LSrunningVol_G, LSeffMixFract = self.__calcRunningVolSwingTank(heatHrs, self.LS_on_off, self.avgLoadShape)
            else:
                LSrunningVol_G = self.__calcRunningVol(heatHrs, self.LS_on_off, self.avgLoadShape)
            LSrunningVol_G *= self.fractDHW

            # Get total volume from max of primary method or load shift method
            if LSrunningVol_G > runningVol_G:
                runningVol_G = LSrunningVol_G
                effMixFract = LSeffMixFract
                largerLS = True

        if self.swingTank: # For a swing tank the storage volume is found at the appropriate temperature in __calcRunningVol
            totalVolMax = runningVol_G / (1-self.aquaFract)
        else: # If the swing tank is not being used
            totalVolMax = mixVolume(runningVol_G, self.storageT_F, self.incomingT_F, self.supplyT_F) / (1-self.aquaFract)

        # Check the Cycling Volume ############################################
        cyclingVol_G = totalVolMax * (self.aquaFract - (1 - self.percentUseable))
        minRunVol_G = pCompMinimumRunTime * (self.totalHWLoad * effMixFract / heatHrs) # (generation rate - no usage)

        if minRunVol_G > cyclingVol_G:
            min_AF = minRunVol_G / totalVolMax + (1 - self.percentUseable)
            if min_AF < 1:
                raise ValueError("01", "The aquastat fraction is too low in the storge system recommend increasing the maximum run hours in the day or increasing to a minimum of: ", round(min_AF,3))
            raise ValueError("02", "The minimum aquastat fraction is greater than 1. This is due to the storage efficency and/or the maximum run hours in the day may be too low. Try increasing these values, we reccomend 0.8 and 16 hours for these variables respectively." )

        # Return the temperature adjusted total volume ########################
        return totalVolMax, effMixFract, largerLS

    def __calcRunningVol(self, heatHrs, onOffArr, loadShapeN = None):
        """
        Function to find the running volume for the hot water storage tank, which
        is needed for calculating the total volume for primary sizing and in the event of load shift sizing
        represents the entire volume.

        Parameters
        ----------
        heatHrs : float
            The number of hours primary heating equipment can run in a day.
        onOffArr : ndarray
            array of 1/0's where 1's allow heat pump to run and 0's dissallow. of length 24.
            
        loadShape : ndarray
            defaults to memember design load shape.
        
        Raises
        ------
        Exception: Error if oversizeing system.

        Returns
        -------
        runV_G : float
            The running volume in gallons

        """
        if loadShapeN is None:
            loadShapeN = self.loadShapeNorm
            
        genrate = np.tile(onOffArr,2) / heatHrs #hourly
        diffN = genrate - np.tile(loadShapeN,2) #hourly
        diffInd = getPeakIndices(diffN[0:24]) #Days repeat so just get first day!

        diffN *= self.totalHWLoad
        # Get the running volume ##############################################
        if len(diffInd) == 0:
            raise Exception("ERROR ID 03","The heating rate is greater than the peak volume the system is oversized! Try increasing the hours the heat pump runs in a day", )
        runV_G = 0
        for peakInd in diffInd:
            #Get the rest of the day from the start of the peak
            diffCum = np.cumsum(diffN[peakInd:])  #hourly
            runV_G = max(runV_G, -min(diffCum[diffCum<0.])) #Minimum value less than 0 or 0.

        return runV_G

    def __calcRunningVolSwingTank(self, heatHrs, onOffArr, loadShapeN=None):
        """
        Function to find the running volume for the hot water storage tank, which
        is needed for calculating the total volume for primary sizing and in the event of load shift sizing
        represents the entire volume.

        Parameters
        ----------
        heatHrs : float
            The number of hours primary heating equipment can run in a day.
        onOffArr : ndarray
            array of 1/0's where 1's allow heat pump to run and 0's dissallow. of length 24.

        Raises
        ------
        Exception: Error if oversizeing system.

        Returns
        -------
        runV_G : float
            The running volume in gallons

        """
        if loadShapeN is None:
            loadShapeN = self.loadShapeNorm
                    
        genrate = np.tile(onOffArr,2) / heatHrs #hourly
        diffN   = genrate - np.tile(loadShapeN,2) #hourly
        diffInd = getPeakIndices(diffN[0:24]) #Days repeat so just get first day!
                
        # Get the running volume ##############################################
        if len(diffInd) == 0:
            raise Exception("ERROR ID 03","The heating rate is greater than the peak volume the system is oversized! Try increasing the hours the heat pump runs in a day",)

        # Watch out for cases swing cases where the heating is to close to the initial peak value so also check the hour afterwards too.
        diffInd = np.append(diffInd, diffInd+1)
        runV_G = 0
        for peakInd in diffInd:
            hw_out = np.tile(loadShapeN, 2)
            hw_out = np.array(HRLIST_to_MINLIST(hw_out[peakInd:peakInd+24])) \
                / 60 * self.totalHWLoad # to minute

            # Simulate the swing tank assuming it hits the peak just above the supply temperature.
            hpwhsim = Simulator([0]*len(hw_out), hw_out, 10, 1,
                                Tcw=self.incomingT_F,
                                Tstorage=self.storageT_F,
                                Tsupply=self.supplyT_F,
                                schematic="swingtank",
                                swing_V0=int(self.swingTank.TMVol_G.split()[-1]), # -1 grabs the last element of list
                                swing_Ttrig=self.supplyT_F,
                                Qrecirc_W=self.swingTank.Wapt*self.swingTank.nApt,
                                Swing_Elem_kW=self.swingTank.TMCap_kBTUhr/W_TO_BTUHR )
            #Get the volume removed for the primary adjusted by the swing tank
            [_, _, hw_out_from_swing] = hpwhsim.simJustSwing(self.supplyT_F + 0.1)

            # Get the effective adjusted hot water demand on the primary system at the storage temperature.
            temp_eff_HW_mix_faction = sum(hw_out_from_swing)/self.totalHWLoad #/2 because the sim goes for two days
            genrate_min = np.array(HRLIST_to_MINLIST(genrate[peakInd:peakInd+24])) \
                / 60 * self.totalHWLoad * temp_eff_HW_mix_faction # to minute

            # Get the new difference in generation and demand
            diffN = genrate_min - hw_out_from_swing
            # Get the rest of the day from the start of the peak
            diffCum = np.cumsum(diffN)

            # from plotly.graph_objs import Figure, Scatter
            # fig = Figure()
            # fig.add_trace(Scatter(y=swingT, mode='lines', name='SwingT'))
            # fig.add_trace(Scatter(y=hw_out_from_swing, mode='lines', name='hw_out_from_swing, fract='+str(temp_eff_HW_mix_faction)))
            # fig.add_trace(Scatter(y=hw_out, mode='lines', name='hw_out'))
            # fig.add_trace(Scatter(y=diffCum, mode='lines', name='diffCum'))
            # fig.add_trace(Scatter(y=genrate_min, mode='lines', name='genrate'))
            # fig.show()

            new_runV_G = -min(diffCum[diffCum<0.])
            
            if runV_G < new_runV_G:
                runV_G = new_runV_G #Minimum value less than 0 or 0.
                eff_HW_mix_faction = temp_eff_HW_mix_faction

        return runV_G, eff_HW_mix_faction


    def primaryCurve(self):
        """
        Sizes the primary system curve. Will catch the point at which the aquatstat
        fraction is too small for system and cuts the return arrays to match cutoff point.

        Returns
        -------
        volN : array
            Array of volume in the tank at each hour.

        primaryHeatHrs2kBTUHR : array
            Array of heating capacity in kBTU/hr
            
        heatHours : array
            Array of running hours per day corresponding to primaryHeatHrs2kBTUHR
            
        recIndex : int
            The index of the recommended heating rate. 
        """
        # Define the heating hours we'll check
        delta = -0.25
        maxHeatHours = 1/(max(self.loadShapeNorm))*1.001   
        
        arr1 = np.arange(24, self.maxDayRun_hr, delta)
        recIndex = len(arr1)
        heatHours = np.concatenate((arr1, np.arange(self.maxDayRun_hr, maxHeatHours, delta)))
        
        volN = np.zeros(len(heatHours))
        effMixFract = np.ones(len(heatHours))
        for ii in range(0,len(heatHours)):
            try:
                volN[ii], effMixFract[ii], _ = self.sizePrimaryTankVolume(heatHours[ii])
            except ValueError:
                break
        # Cut to the point the aquastat fraction was too small
        volN        = volN[:ii]
        heatHours   = heatHours[:ii]
        effMixFract = effMixFract[:ii]

        return [volN, self.primaryHeatHrs2kBTUHR(heatHours, effMixFract), heatHours, recIndex]

    def sizeVol_Cap(self):
        """
        Calculates the minimum primary volume and heating capacity for the primary system: PVol_G_atStorageT and PCap_kBTUhr
        """
        self.PVol_G_atStorageT, self.effSwingFract, self.LSconstrained = self.sizePrimaryTankVolume(self.maxDayRun_hr)
        self.PCap_kBTUhr = self.primaryHeatHrs2kBTUHR(self.maxDayRun_hr, self.effSwingFract )

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

        return [self.PVol_G_atStorageT, self.PCap_kBTUhr]


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
    TMVol_G_atStorageT
        Volume of parrallel loop tank.
    """

    def __init__(self, nApt, Wapt, safetyTM, setpointTM_F, TMonTemp_F, offTime_hr):
        # Inputs from primary system
        self.nApt = nApt
        # Inputs for temperature maintenance sizing
        self.Wapt = Wapt # W/ apartment

        self.safetyTM = safetyTM # Safety factor

        self.setpointTM_F = setpointTM_F
        self.TMonTemp_F = TMonTemp_F
        self.offTime_hr = offTime_hr # Hour
        # Outputs:
        self.TMCap_kBTUhr = 0 #kBTU/Hr
        self.TMVol_G = 0 # Gallons

    def sizeVol_Cap(self):
        """
        Sizes the volume in gallons and heat capactiy in kBTU/h

        Returns:
        ----------
        TMVol_G : float
            Dedicated loop tank volume.
        TMCap_kBTUhr : float
            Calculated temperature maintenance equipment capacity in kBTU/h.

        Raises:
        -------
        Exceptions : If the system is sized too small and
        """

        self.TMVol_G  =  self.Wapt * self.nApt / rhoCp * \
            W_TO_BTUHR * self.offTime_hr / (self.setpointTM_F - self.TMonTemp_F)

        self.TMCap_kBTUhr = self.safetyTM * self.Wapt * self.nApt * W_TO_BTUHR/1000


    def getSizingResults(self):
        """
        Returns sizing results as array

        Returns
        -------
        list
            self.TMVol_G, self.TMCap_kBTUhr
        """
        return [self.TMVol_G, self.TMCap_kBTUhr]

    def tempMaintCurve(self, runtime=tmCompMinimumRunTime):
        """
        Returns the sizing curve for a parallel loop tank

        Returns
        -------
        list
            volN_G, capacity
        """

        volN_G = np.linspace(0 , round(self.TMVol_G*4/100)*100, 100)
        capacity = rhoCp * volN_G / runtime * (self.setpointTM_F - self.TMonTemp_F) + \
                    self.nApt * self.Wapt  * W_TO_BTUHR #0.66 comes from the lower limit of the distrubution losses.
        capacity /= 1000.

        keep = capacity >= self.TMCap_kBTUhr

        return [volN_G[keep], capacity[keep]]


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
    sizingTable_EMASHRAE = ["80", "80", "80", "120 - 300", "120 - 300"]
    sizingTable_CA = ["80", "96", "168", "288", "480"]

    #swingLoadToPrimary_Wapt = 50.

    def __init__(self, nApt, Wapt, safetyTM):
        # Inputs from primary system
        self.nApt = nApt
        # Inputs for temperature maintenance sizing
        self.Wapt = Wapt #W/ apartment
        self.safetyTM = safetyTM # Safety factor


        # Outputs:
        self.TMCap_kBTUhr = 0 #kBTU/Hr
        self.TMVol_G = 0 # Gallons

        if self.Wapt == 0:
            raise Exception("Swing tank initialized with 0 W per apt heat loss")

    def __str__(self):
        return f'a swing tank object'

    def sizeVol_Cap(self, CA = False):
        """
        Sizes the volume in gallons and heat capactiy in kBTU/hr

        Returns
        -------
        TMVol_G
            Calculated swing tank volume.
        TMCap_kBTUhr
            Calculated temperature maintenance equipment capacity.
        """
        ind = [idx for idx, val in enumerate(self.Table_Napts) if val <= self.nApt][-1]

        if CA:
            self.TMVol_G = self.sizingTable_CA[ind]
        else:
            self.TMVol_G = self.sizingTable_EMASHRAE[ind]

        self.TMCap_kBTUhr = self.safetyTM * self.Wapt * self.nApt * W_TO_BTUHR / 1000.

    def getSizingResults(self):
        """
        Returns sizing results as array

        Returns
        -------
        list
            self.TMVol_G, self.TMCap_kBTUhr
        """
        return [self.TMVol_G, self.TMCap_kBTUhr]


    def getSizingTable(self, CA=True):
        """
        Returns sizing table for a swing tank

        Returns
        -------
        list
            self.Table_Napts, self.Table
        """
        if CA:
            return list(zip(self.Table_Napts, self.sizingTable_CA))
        return list(zip(self.Table_Napts, self.sizingTable_EMASHRAE))


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
    diff1[diff1==0] = .0001 #Got to catch this error in the algorithm. Damn 0s.
    return np.where(np.diff(np.sign(diff1))<0)[0]
