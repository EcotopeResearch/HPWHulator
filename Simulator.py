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
    
    MJ's edits:
    First attempt to add loadshift controls to simulator for SCL study. Turn 
    runOnePrimaryStep into a function of Vtrig[i]. 

"""
import numpy as np
from cfg import rhoCp, W_TO_BTUHR, mixVolume, roundList
from plotly.graph_objs import Figure, Scatter
from plotly.offline import plot
from plotly.subplots import make_subplots

###############################################################################
class Simulator:
    """
    Simulator class runs a simplified simulation to check the primary and swing
    tank systems.

    This class will run the primary simulation (schematic = "primary") or
    primary with swing tank simulation (schematic = "swingtank"). Both are run
    on a minute timestep to approximate the available storage volume in the
    primary system and the average tank temperature in the swing tank, if
    applicable.

    The primary system is run assuming the system is perfectly stratified and
    all of the hot water above the
    cold temperature line is at the storage temperature. Each time step some
    hot water is removed and some added according to the inputs.

    The swing tank is run assuming that the swing tank is well mixed and can
    be tracked by the average tank temperature
    and that the system loses the recirculation loop losses as a constant Watts.
    Since the swing tank is in series with the primary system the temperature
    needs to be tracked to inform inputs for primary step, unlike the parallel
    loop tank which is separated from the primary system.

    The swing tank is also assumed to have an 8 °F deadband from the swing
    heating trigger temperature.

    Attributes
    ----------
    G_hw : list
        The primary hot water generation rate in gallons per minute.

    D_hw : list
        The hot water draw rate at the supply temperature.

    V0 : float
        The storage volume of the primary system at the storage temperature.

    Vtrig : float
        The remaining volume of the primary storage volume when heating is
        triggered, note this equals V0*(1 - aquaFract)

    Tcw : float
        The cold makeup water temperature

    Tstorage : float
        The hot water storage temperature

    Tsupply : float
        The hot water supply temperature to occupants.

    schematic : string
        The schematic string, either "primary", "paralleltank", or "swingtank".
        Controls the model run. Defaults to "primary".

    swing_V0 : float
        The storage volume of the swing tank. Is not need unless schematic is
        set to "swingtank". Defaults to None.

    swing_Ttrig : float
        The swing tank tempeature when the swing tank resistance elements turn
        on. Is not need unless schematic is set to "swingtank". Defaults to None.

    Qrecirc_W : float
        The recirculation loop losses in Watts. Is not need unless schematic
        is set to "swingtank". Defaults to None.

    Swing_Elem_kW : float
        The swing tank resistance elements power output in kWatts. Is not need
        unless schematic is set to "swingtank". Defaults to None.

    Examples
    --------
    An example usage to simulate a swing tank system:

    First make sure the hot water draws are in gpm. For examples starting with
    gph for each hour of the day,
    a list can be converted to gpm for each minute oof the day following:

    >>> import numpy as np
    >>> from cfg import HRLIST_to_MINLIST
    >>> D_hw_gph = [ 27, 12, 8, 8, 24, 40, 74, 87, 82, 67, 40, 34, 29, 27,
                    29, 34, 40, 48, 51, 55, 59, 51, 38, 36]

    >>> D_hw_gpm = np.array(HRLIST_to_MINLIST(D_hw_gph)) / 60


    Then the simulator can be imported and initilized, with the desired inputs.


    >>> from HPWHsizer import Simulator
    >>> hpwhsim = Simulator(G_hw = [64]*24*60,
                            D_hw = D_hw_gpm,
                            V0 = 300,
                            Vtrig = 180,
                            Tcw = 50,
                            Tstorage = 150,
                            Tsupply = 120,
                            schematic = "swingtank",
                            swing_V0 = 80,
                            swing_Ttrig = 121,
                            Qrecirc_W = 2700,
                            Swing_Elem_kW = 5 )

    And then in order to find proper for the system in the order of primary
    storage volume, primary heating capacity, temperature maintenance storage
    volume, temperature maintenance heating capacity:

    >>> primaryVol, G_hw, D_hw, primaryGen, swingTemp, swingHeat, hw_outSwing = hpwhsim.simulate()


    """
    pheating = False
    swingheating = False

    def __init__(self, G_hw, D_hw, V0, Vtrig,
                 Tcw, Tstorage, Tsupply,
                 schematic="primary",
                 swing_V0=None,
                 swing_Ttrig=None,
                 Qrecirc_W=None,
                 Swing_Elem_kW=None,
                 ):
        """
        Initialize the simulation to run. Default is the "primary" schematic.

        Parameters
        ----------
        G_hw : list
            The primary hot water generation rate in gallons per minute .

        D_hw : list
            The hot water draw rate at the supply temperature.

        V0 : float
            The storage volume of the primary system at the storage temperature

        Vtrig : list
            The remaining volume of the primary storage volume when heating
            is triggered at each hour to allow for load shift controls. Note
            this equals V0*(1 - aquaFract) for the first timestep.

        Tcw : float
            The cold makeup water temperature

        Tstorage : float
            The hot water storage temperature

        Tsupply : float
            The hot water supply temperature to occupants.

        schematic : string
            The schematic string, either "primary", "paralleltank", or
            "swingtank". Controls the model run. Defaults to "primary".

        swing_V0 : float
            The storage volume of the swing tank. Is not need unless schematic
            is set to "swingtank". Defaults to None.

        swing_Ttrig : float
            The swing tank tempeature when the swing tank resistance elements
            turn on. Is not need unless schematic is set to "swingtank".
            Defaults to None.

        Qrecirc_W : float
            The recirculation loop losses in Watts. Is not need unless
            schematic is set to "swingtank". Defaults to None.

        Swing_Elem_kW : float
            The swing tank resistance elements power output in kWatts. Is not
            need unless schematic is set to "swingtank". Defaults to None.

        """

        self.__checkInputs(G_hw, D_hw, V0, Vtrig)

        self.Tsupply = Tsupply
        self.Tcw = Tcw
        self.Tstorage = Tstorage

        self.N = len(G_hw)
        self.G_hw = G_hw
        self.D_hw = D_hw
        self.prun = [0] * (self.N)

        self.V0 = V0
        self.pV = [V0] + [0] * (self.N - 1)
        self.Vtrig = Vtrig # For the primary system

        self.schematic = schematic

        self.swingT = None
        self.srun = None
        self.hw_outSwing = None

        # If swing tank gather all of the swing tank inputs.
        if self.schematic == "swingtank":
            self.swing_V0 = swing_V0
            self.swing_Ttrig = swing_Ttrig

            self.recircLoss_dT = Qrecirc_W * W_TO_BTUHR / 60 / rhoCp / self.swing_V0  #1/60 to get timestep of 1 minute
            self.element_dT = Swing_Elem_kW * 1000 * W_TO_BTUHR / 60 / rhoCp / self.swing_V0  #1/60 to get timestep of 1 minute
            self.element_deadband_F = 8.

            self.swingT = [self.Tstorage] + [0] * (self.N - 1)
            self.srun = [0] * (self.N)
            self.hw_outSwing = [0] * (self.N)
            self.hw_outSwing[0] = D_hw[0]

    def __checkInputs(self, G_hw, D_hw, V0, Vtrig):
        if len(G_hw) != len(D_hw):
            raise Exception("Hot water generation and domestic hot water use must have the same length, i.e. time")
        if len(G_hw) != len(Vtrig):
            raise Exception("Hot water generation and AQ fraction vector must have the same length, i.e. time")
        if V0 <= Vtrig[0]:
            raise Exception("The initial storage volume can't be less than or equal to the volume to trigger heating.")

    def simulate(self, ls, initPV=None, initST=None):
        """
        Inputs
        ------
        initPV : float
            Primary volume at start of the simulation
        initST : float
            Primary Swing tank at start of the simulation
        """
        total_shed_heating = 0
        if initPV:
            self.pV[0] = initPV
        if initST:
            self.swingT[0] = initST

        # Run the "simulation"
        for ii in range(1, self.N):

            if self.schematic == "swingtank":
                self.hw_outSwing[ii] = mixVolume(self.D_hw[ii], self.swingT[ii-1], self.Tcw, self.Tsupply)

                self.swingT[ii], self.srun[ii] = self.runOneSwingStep(self.swingT[ii-1], self.hw_outSwing[ii])
                #Get the mixed generation
                mixedGHW = mixVolume(self.G_hw[ii], self.Tstorage, self.Tcw, self.Tsupply)
                self.pV[ii], self.prun[ii], shed_heating = self.runOnePrimaryStep(self.pV[ii-1], self.hw_outSwing[ii], mixedGHW, self.Vtrig[ii], ls[ii], ls[ii-1])

            elif self.schematic == "primary" or self.schematic == "paralleltank":
                mixedDHW = mixVolume(self.D_hw[ii], self.Tstorage, self.Tcw, self.Tsupply)
                mixedGHW = mixVolume(self.G_hw[ii], self.Tstorage, self.Tcw, self.Tsupply)
                self.pV[ii], self.prun[ii], shed_heating = self.runOnePrimaryStep(self.pV[ii-1], mixedDHW, mixedGHW, self.Vtrig[ii], ls[ii], ls[ii-1])
                if ii > 1255 and ii < 1265:
                    print(self.pV[ii])
            else:
                raise Exception(self.schematic + " is not a valid schematic")

            total_shed_heating += shed_heating
            
        return [roundList(self.pV, 3),
                roundList(self.G_hw, 3),
                roundList(self.D_hw, 3),
                roundList(self.prun, 3),
                roundList(self.swingT, 3) if self.swingT else None,
                roundList(self.srun, 3) if self.srun else None,
                self.hw_outSwing if self.hw_outSwing else None,
                total_shed_heating]
    

    def simJustSwing(self, initST=None):
        """
        Inputs
        ------

        initST : float
            Primary Swing tank at start of sim
        """
        if initST:
            self.swingT[0] = initST
        # Run the "simulation"

        if self.schematic == "swingtank":
            for ii in range(1, self.N):

                self.hw_outSwing[ii] = mixVolume(self.D_hw[ii], self.swingT[ii-1], self.Tcw, self.Tsupply)
                self.swingT[ii], self.srun[ii] = self.runOneSwingStep(self.swingT[ii-1], self.hw_outSwing[ii])

            return [self.swingT, self.srun, self.hw_outSwing]
        raise Exception("Invalid schematic")

    def runOnePrimaryStep(self, Vcurr, hw_out, hw_in, Vtrig, ls, ls_prev):
        """
        Runs one step on the primary system. This changes the volume of the primary system
        by assuming there is hot water removed at a volume of hw_out and hot water
        generated or added at a volume of hw_in. This is assuming the system is perfectly
        stratified and all of the hot water above the cold temperature is at the storage temperature.

        Parameters
        ----------
        Vcurr : float
            The primary volume at the timestep.
        hw_out : float
            The volume of DHW removed from the primary system, assumed that
            100% of what of what is removed is replaced
        hw_in : float
            The volume of hot water generated in a time step

        Returns
        -------
        Vnew : float
            The new primary volume at the timestep.
        did_run : float
            The volume of hot water generated during the time step.

        """
        
        did_run = 0
        Vnew = 0
        if self.pheating:
            #madison's edit here: if transitioning into shed and Vcurr > Vtrig, turn off heat pump. 
            if ls == 0 and ls_prev == 1 and Vcurr > Vtrig:
                Vnew = Vcurr - hw_out
                self.pheating = False
            else:
                Vnew = Vcurr + hw_in - hw_out # If heating, generate HW and lose HW
                did_run = hw_in

        else:  # Else not heating,
            Vnew = Vcurr - hw_out # So lose HW
            if Vnew < Vtrig: # If should heat
            #ISSUE IS HERE I THINK 
                time_missed = (Vtrig - Vnew)/hw_out # Volume below turn on / rate of draw gives time below tigger
                Vnew += hw_in #* time_missed # Start heating
                did_run = hw_in #* time_missed
                self.pheating = True

        if Vnew > self.V0: # If overflow
            time_over = (Vnew - self.V0) / (hw_in - hw_out) # Volume over generated / rate of generation gives time above full
            Vnew = self.V0 - hw_out * time_over # Make full with missing volume
            did_run = hw_in * (1-time_over)
            self.pheating = False # Stop heating

        #if Vnew < 0:
        #    raise Exception("Primary storage ran out of Volume!")
        #if shed event is not met, count how many minutes 
        shed_heating = 1 if ls == 0 and self.pheating == True else 0
        
        return Vnew, did_run, shed_heating

    def runOneSwingStep(self, Tcurr, hw_out):
        """
        Runs one step on the swing tank step. Since the swing tank is in series
        with the primary system the temperature needs to be tracked to inform
        inputs for primary step. The driving assumptions hereare that the swing
        tank is well mixed and can be tracked by the average tank temperature
        and that the system loses the recirculation loop losses as a constant
        Watts and thus the actual flow rate and return temperature from the
        loop are irrelevant.

        Parameters
        ----------
        Tcurr : float
            The current temperature at the timestep.
        hw_out : float
            The volume of DHW removed from the swing tank system.
        hw_in : float
            The volume of DHW added to the system.

        Returns
        -------
        Tnew : float
            The new swing tank tempeature the timestep assuming the tank is well mixed.
        did_run : int
            Logic if heated during time step (1) or not (0)

        """
        did_run = 0

        # Take out the recirc losses
        Tnew = Tcurr - self.recircLoss_dT

        # Add in heat for a draw
        if hw_out:
            Tnew += hw_out * (self.Tstorage - Tcurr) / self.swing_V0

        # Check if the element is heating
        if self.swingheating:
            Tnew += self.element_dT #If heating, generate HW and lose HW
            did_run = 1

            # Check if the element should turn off
            if Tnew > self.swing_Ttrig + self.element_deadband_F: # If too hot
                time_over = (Tnew - (self.swing_Ttrig + self.element_deadband_F)) / self.element_dT # Temp below turn on / rate of element heating gives time above trigger plus deadband
                Tnew -= self.element_dT * time_over # Make full with miss volume
                did_run = (1-time_over)

                self.swingheating = False
        else:
            if Tnew <= self.swing_Ttrig: # If the element should turn on
                time_missed = (self.swing_Ttrig - Tnew)/self.element_dT # Temp below turn on / rate of element heating gives time below tigger
                Tnew += self.element_dT * time_missed # Start heating

                did_run = time_missed
                self.swingheating = True # Start heating

        if Tnew < self.Tsupply: # Check for errors
            raise Exception("The swing tank dropped below the supply temperature! The system is undersized")


        return Tnew, did_run
    
#add plotting function, copied from HPWHsizer.py
#remove system sized requirement


def plotStorageLoadSim2(simulator_object, normalCapacity, loadUpCapacity, loadshift):
    """
    Returns a plot of the of the simulation for the minimum sized primary
    system as a div or plotly figure. Can plot the minute level simulation

    Parameters
    ----------
    return_as_div 
        A logical on the output, as a div (true) or as a figure (false)

    Returns
    -------
    div/fig

    """
    [V, G_hw, D_hw, run, swingT, srun, hw_out_swing, total_shed_heating] = simulator_object.simulate(ls = loadshift)

    hrind_fromback = 24 # Look at the last 24 hours of the simulation not the whole thing
    run = np.array(run[-(60*hrind_fromback):])*60
    G_hw = np.array(G_hw[-(60*hrind_fromback):])*60
    D_hw = np.array(D_hw[-(60*hrind_fromback):])*60
    V = np.array(V[-(60*hrind_fromback):])
    
    x_data = list(range(len(V)))
    ls_off = [0 if i == 1 else 2000 for i in loadshift]
    
    fig = Figure()
    
    fig.add_trace(Scatter(x=x_data, y=ls_off, name='Load Shift Goal',
                                  mode='lines', line_shape='hv',
                                  opacity=0.5, marker_color='grey',
                                  fill='tonexty'))
                                  
    fig.add_trace(Scatter(x=x_data, y=V, name='Useful Storage Volume at Storage Temperature',
                          mode='lines', line_shape='hv',
                          opacity=0.8, marker_color='green'))
    fig.add_trace(Scatter(x=x_data, y=run, name = "Hot Water Generation at Storage Temperature",
                          mode='lines', line_shape='hv',
                          opacity=0.8, marker_color='red'))
    fig.add_trace(Scatter(x=x_data, y=D_hw, name='Hot Water Demand at Supply Temperature',
                          mode='lines', line_shape='hv',
                          opacity=0.8, marker_color='blue'))
    fig.update_yaxes(range=[0, np.ceil(max(np.append(V,D_hw))/100)*100])

    fig.update_layout(title="<b>Hot Water Simulation</b> <br>" \
                      + '<span style="font-size: 12px;">Primary Capcity: ' + str(normalCapacity) + "kBtu/hr & Load Up Capacity: " + str(loadUpCapacity) + "kBtu/hr<span>",
                      xaxis_title= "Minute of Day",
                      xaxis = dict(tickvals = list(range(0, 1440, 120))),
                      yaxis_title="Gallons or\nGallons per Hour",
                      width=900,
                      height=700)                               

    #print(V[1258:1262], run[1258:1262])
    return fig, V, total_shed_heating

