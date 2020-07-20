 # -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 16:01:38 2020

@author: adria
"""

import numpy as np
from cfg import rhoCp, TONS_TO_KBTUHR
from HPWHComponents import mixVolume

class ASHRAEsizer:
    """
    Class containing attributes and methods to describe and size the parrallel loop tank arrangement. Unlike a swing tank, a parrallel loop tank \
    will have equipment to provide heat for periods of low or no hot water use.

    Attributes
    ----------
    ashraeMediumLU : array_like
        The medium table derived from ASHRAE to deretrime hot water usage
    ashraeLowLU :  array_like
        The low table derived from ASHRAE to deretrime hot water usage
    nPeople : float 
        The number of people in estimated to live in the project.
    gpdpp : float
        The volume of water in gallons at 120F each person uses per dat.[°F]
    incomingT_F : float 
        The incoming city water temperature on the design day. [°F]
    supplyT_F : float
        The hot water supply temperature to the occupants.[°F]
    storageT_F : float 
        The hot water storage temperature. [°F]
    defrostFactor : float 
        A multipier used to account for defrost in the final heating capacity.
    percentUseable : float
        The fraction of the storage volume that can be filled with hot water.
    compRuntime_hr : float
        The number of hours the compressor will run on the design day. [Hr]
    peakFlowTable : array_like
        A array to describe the peak hot water flow events from 5 minutes to 24 hours, found from interpolating/extrapolating between the ASHRAE Low and Medium tables
    PCap_KBTUHR : float
        The primary heating capacity for the sized system using the ASHRAE "more accurate" method [kBTU/hr]
    PVol_G_atStorageT   : float
        The storage volume in gallons at the storage temperature for the sized system using the ASHRAE "more accurate" method [gallons]
    primaryVolArr_atStorageT : array_like
        An array of possible storage volumes found using the using the ASHRAE "more accurate" method corresponding to heating capacitys in accurateRecoveryTonsArr [gallons]
    accurateRecoveryTonsArr : array_like
        An array of possible heating capacitys found using the using the ASHRAE "more accurate" method corresponding to storage volumes in primaryVolArr_atStorageT  [kBTU/hr]

    Methods
    -------
    sizePrimaryCurveAshrae(flowTable) 
        General function to size the water heating system based on a flow table, ASHRAE low, medium, or an interpolated table based on the input for gpdpp
    primaryCurve()
        Function to return the sized ASHRAE curve for the linear interpolated/extrapolated gallons per day per person from the ASHRAE Low and Medium Cruves
    getMediumCurve()
        Returns the ASHRAE medium sizing curve
    getLowCurve()
        Returns the ASHRAE low sizing curve
    tonsRecoveryForMaxDaily()
        Calculates the system heating capacity for a given compressor run time by interpolating from the ASHRAE curve
    sizeVol_Cap()
        Sizes the system following the ASHRAE "more accurate" methodolgy and returns the heating capacity and tons. 
    
    Examples
    --------
    An example usage to find the recommended size following the ASHRAE method is:

    >>> from ashraesizer import ASHRAEsizer
    >>> a = ASHRAEsizer(100, 20, 50, 120, 150, 1, 0.8, 16)
    >>> a.sizeVol_Cap()
    >>> [73.09343125000001, 25.060605000000002]
    
    """
  
    # Create the ASHRAE medium sizing look-up table
    ashraeMediumLU = np.array([[5, 0.7], [15, 1.7], [30, 2.9], [60, 4.8], \
                                   [120, 8.0], [180, 11.0], [1440, 49.0]])
        
    # Create the ASHRAE low sizing look-up table
    ashraeLowLU = np.array([[5, 0.4], [15, 1.0], [30, 1.7], [60, 2.8], \
                                [120, 4.5], [180, 6.1], [1440, 20.0]])
        
    def __init__(self, nPeople, gpdpp, incomingT_F, supplyT_F, storageT_F,defrostFactor, percentUseable,compRuntime_hr):
        """
        Initialize the ASHRAE sizer object. An object to handle the sizing of \
        heat pump water heaters using the "more accurate" method in the ASHRAE handbook

        Parameters
        ----------
            nPeople : float 
                The number of people in estimated to live in the project.
            gpdpp : float
                The volume of water in gallons at 120F each person uses per dat.
            incomingT_F : float 
                The incoming city water temperature on the design day. [°F]
            supplyT_F : float
                The hot water supply temperature to the occupants. [°F]
            storageT_F : float 
                The hot water storage temperature. [°F]
            defrostFactor : float 
                A multipier used to account for defrost in the final heating capacity.
            percentUseable : float
                The fraction of the storage volume that can be filled with hot water.
            compRuntime_hr : float
                The number of hours the compressor will run on the design day. [Hr]
        """
        self.nPeople        = nPeople # Nnumber of people
        self.gpdpp          = gpdpp # Gallons per day per person

        self.supplyT_F        = supplyT_F # The supply temperature to the occupants
        self.incomingT_F      = incomingT_F # The incoming cold water temperature for the city
        self.storageT_F       = storageT_F # The primary hot water storage temperature 
       
        self.defrostFactor  = defrostFactor
        self.percentUseable = percentUseable
        self.compRuntime_hr = compRuntime_hr 

        self.peakFlowTable      = None
        self.PCap_KBTUHR        = 0. #kBTU/Hr
        self.PVol_G_atStorageT  = 0. # Gallons
                
        self.__getASHRAEtable()
        [self.primaryVolArr_atStorageT, self.accurateRecoveryTonsArr] =self.sizePrimaryCurveAshrae(self.peakFlowTable)
       
    def __getASHRAEtable(self):
        """
        Private function to linearly interpolate/extrapolate the hot water use table from ASHRAE data and set the self.peakFlowTable 
        """
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

        self.peakFlowTable = peakFlowTable;
        
    def sizePrimaryCurveAshrae(self, flowTable):
        """
        General function to size the water heating system based on a flow table, ASHRAE low, medium, or an interpolated table based on the input for gpdpp
        Parameters
        ----------:
        flowTable : array_like
            A array of pairs describing volume flow at increasing lengths of time.

        Returns
        -------
        [primaryVol, accurateRecoveryTons] : list 
            Returns a list of pairs for the sizing the primary HPWH following the ASHRAE "more accurate" method
        """
        
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
        """
        Function to return the sized ASHRAE curve for the linear interpolated/extrapolated \
        gallons per day per person from the ASHRAE Low and Medium Cruves

        Returns
        -------:
            list: [primaryVolArr_atStorageT, accurateRecoveryKBTUHr]. A list of the 
            primary storage options in gallons at the storage temperature with the 
            corresponding list of heating capacity options in kBTU/hr

        """
        return [self.primaryVolArr_atStorageT, self.accurateRecoveryTonsArr * TONS_TO_KBTUHR]
                
    def getLowCurve(self):
        """
        Get the sizing curve for the ASHRAE LOW table following the ASHRAE "more accurate" method

        Returns
        -------:
        [vol_g, cap_kbtuhr] : list
            Sized volume in gallons at storage temperature and heating capactiy in kBTU/hr

        """        
        [vol_g, cap_tons] = self.sizePrimaryCurveAshrae(flowTable = self.ashraeLowLU)
        return [vol_g, cap_tons * TONS_TO_KBTUHR]
        
    def getMediumCurve(self):
        """
        Get the sizing curve for the ASHRAE MEDIUM table following the ASHRAE "more accurate" method

        Returns
        -------:
        [vol_g, cap_kbtuhr] : list 
                Sized volume in gallons at storage temperature and heating capactiy in kBTU/hr

        """
        [vol_g, cap_tons] =  self.sizePrimaryCurveAshrae(flowTable = self.ashraeMediumLU)
        return [vol_g, cap_tons * TONS_TO_KBTUHR]

        
    def tonsRecoveryForMaxDaily(self):
        """
        Calculates the system heating capacity for a given compressor run time by interpolating from the ASHRAE curve

        Returns
        -------
        heatCap : float 
            The heating capacity in tons.

        """
        
        # Define the range of recovery hours
        recoveryHours = np.array([1,2,4,8,12,16,24])
        
        simpleTons = np.amax(self.peakFlowTable[6,1])*self.nPeople*rhoCp*(self.supplyT_F-self.incomingT_F)/12000/recoveryHours
     
        # Heat capacity determined by defined run time
        heatCap = np.interp(self.compRuntime_hr, recoveryHours, simpleTons)
        return heatCap 
    
    def __minimumStorageVol(self,  heatCap_Ton):
        """
        Calculates the minimum storage volume at the storage temperature from the associated heating capacity input

        Parameters
        ----------
        heatCap_Ton : float 
            The heating capacity in Tons.

        Returns
        -------
        minStorage_gal : float 
            The minimum storage volume in .

        """
        minStorage_gal = np.interp(heatCap_Ton, 
                                   self.primaryVolArr_atStorageT, 
                                   self.accurateRecoveryTonsArr)
        return minStorage_gal
    
    def sizeVol_Cap(self):
        """
        Function sizes the system following the ASHRAE "more accurate" methodolgy

        Returns
        -------:
            list: [PCap_KBTUHR, PVol_G_atStorageT]. The primary heating capacity on the design day in kBTU/hr and the primary volume at the storage temperature.

        """
 
        self.PCap_KBTUHR = self.tonsRecoveryForMaxDaily() * TONS_TO_KBTUHR;
        self.PVol_G_atStorageT = self.__minimumStorageVol(self.PCap_KBTUHR / TONS_TO_KBTUHR)
        
        return  [self.PCap_KBTUHR, self.PVol_G_atStorageT]
