# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 08:43:47 2022

@author: madison
"""
import numpy as np
from Simulator import Simulator, plotStorageLoadSim2
from cfg import HRLIST_to_MINLIST, rhoCp

D_hw_gph = [27, 12, 8, 8, 24, 40, 74, 87, 82, 67, 40, 34, 29, 27,
            29, 34, 40, 48, 51, 55, 59, 51, 38, 36]

D_hw_gpm = np.array(HRLIST_to_MINLIST(D_hw_gph)) / 60

#0.4 normal operation, 0.8 shed, 0.2 loadup
aq_frac = np.array([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.8, 0.8, 0.8, 0.2, 0.2, 0.2,
           0.2, 0.2, 0.2, 0.2, 0.2, 0.8, 0.8, 0.8, 0.2, 0.2, 0.2, 0.2])

#Ghw vars
primary_capacity = 140000 #should be BTU/hr but cannot get this to work out!! 
defrost_factor = 1 #derates the output power for defrost cycles
LS_array = np.array([1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1]) #for each hour
Tcw = 50
Tsupply = 120

G_hw = primary_capacity / rhoCp / (Tsupply - Tcw) \
       * defrost_factor * LS_array
G_hw = np.array(HRLIST_to_MINLIST(G_hw)) / 60

V0 = 300
Vtrig = 300*(1 - aq_frac)
Vtrig = HRLIST_to_MINLIST(Vtrig)

sim = Simulator(G_hw = G_hw,
                D_hw = D_hw_gpm,
                V0 = V0,
                Vtrig = Vtrig,
                Tcw = 50,
                Tstorage = 150,
                Tsupply = 120,
                schematic = "swingtank",
                swing_V0 = 80,
                swing_Ttrig = 121,
                Qrecirc_W = 2700,
                Swing_Elem_kW = 5)


fig = plotStorageLoadSim2(sim)
fig.write_html('C:\\Users\\madison\\Documents\\GitHub\\HPWHulator\\SCL_plots\\test_plot.html')


[V, G_hw, D_hw, run, swingT, srun, _] = sim.simulate()
