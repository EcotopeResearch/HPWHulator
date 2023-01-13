# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 14:27:43 2022
SCL Simulations

@author: madison
"""
import os
import numpy as np
import pandas as pd
from Simulator import Simulator, plotStorageLoadSim2
from cfg import HRLIST_to_MINLIST, rhoCp

#Import inputs csv
df = pd.read_excel('C:\\Users\\madison\\Documents\\GitHub\\HPWHulator\\SCL_Sim_Inputs.xlsx')
df = df.iloc[1:]
df = df.reset_index(drop = True)

def runSimulation():
    
    results = []
    shed_heating_time = []
    percent_shed_met = []
    
    for row in df.itertuples():
        
        #hot water usage
        D_hw = row.usage_curve.split(',')
        D_hw = [float(s.replace(' ', '')) for s in D_hw]
        
        #load shift controls
        controls = row.controls_array.split(',')
        controls = [s.replace(' ', '') for s in controls]
    
        loadshift = np.array([0 if i == 'S' else 1 for i in controls])
    
        aq_normal = 0.4 if np.isnan(row.aqFrac_normalOp) else row.aqFrac_normalOp
        aq_loadUp = 0.2 if np.isnan(row.aqFrac_loadUp) else row.aqFrac_loadUp
        aq_shed = 0.8 if np.isnan(row.aqFrac_shed) else row.aqFrac_shed
    
        aq = np.array([aq_normal if i == 'N' else aq_loadUp if i == 'L' else aq_shed for i in controls])
        
        capacity_normal = row.capacity_normOp
        capacity_loadUp = row.capacity_loadUp
    
        capacity = np.array([capacity_loadUp if i == 'L' else capacity_normal for i in controls])
    
        #hot water gen rate and vtrig
        Tsupply = 120 if np.isnan(row.T_supply) else row.T_supply
        Tcity = 50 if np.isnan(row.T_cw) else row.T_cw
        Tstorage = 150 if np.isnan(row.T_storage) else row.T_storage
        defrost_factor = 1 if np.isnan(row.defrost_factor) else row.defrost_factor
        V0 = row.V0
    
        Vtrig = V0 * (1- aq)
    
        G_hw = 1000 * capacity / rhoCp / (Tsupply - Tcity) \
               * defrost_factor #* loadshift
         
        #convert all quantities from hour list to minute list
        D_hw = np.array(HRLIST_to_MINLIST(D_hw)) / 60
        G_hw = np.array(HRLIST_to_MINLIST(G_hw)) / 60
        Vtrig = np.array(HRLIST_to_MINLIST(Vtrig))
        loadshift = HRLIST_to_MINLIST(loadshift)
        
        #instantiate simulator object
        sim = Simulator(G_hw = G_hw,
                    D_hw = D_hw,
                    V0 = V0,
                    Vtrig = Vtrig,
                    Tcw = Tcity,
                    Tstorage = Tstorage,
                    Tsupply = Tsupply,
                    schematic = "swingtank",
                    swing_V0 = 80,
                    swing_Ttrig = 121,
                    Qrecirc_W = 2700,
                    Swing_Elem_kW = 5)
    
    
        fig, V, total_shed_heating = plotStorageLoadSim2(sim, capacity_normal, capacity_loadUp, loadshift)
        fig.write_html('C:\\Users\\madison\\Documents\\GitHub\\HPWHulator\\SCL_plots\\' + str(row.run_name) + '.html')
        
        
        #find lowest storage volume
        #min_vol = 0 if min(V) <= min(Vtrig) else 1
        #results.append(min_vol)
    
        shed_heating_time.append(total_shed_heating)
        
        percent_captured = 1 - (total_shed_heating / sum(loadshift))
        percent_shed_met.append(percent_captured)
        
        result = 1 if total_shed_heating == 0 else 0
        results.append(result)
    
    return results, shed_heating_time, percent_shed_met
    
results, shed_heating_time, percent_shed_met = runSimulation()

results = pd.Series(results)
df['results'] = results
df['heating_min_shed'] = shed_heating_time
df['percent_shed_met'] = percent_shed_met

out_path = 'C:\\Users\\madison\\Documents\\GitHub\\HPWHulator\\SCL_Results.xlsx'
writer = pd.ExcelWriter(out_path , engine='xlsxwriter')
df.to_excel(writer, sheet_name='Results')
writer.save()