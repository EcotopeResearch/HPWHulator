# -*- coding: utf-8 -*-
"""
SCL Regression
Created on Mon Jan  9 15:36:29 2023

@author: madison
"""

import numpy as np
import pandas as pd
from itertools import product



#Storage volumes
LUcapacityFactor = 1.1
loadshift = 'N, N, N, N, L, L, S, S, S, S, L, L, L, L, L, L, L, S, S, S, S, N, N, N'
volumes = np.arange(200, 1001, 30)
capacities = np.arange(50, 301, 10)

path = 'C:\\Users\\madison\\Documents\\GitHub\\HPWH-Sizing-Tool---Research\\metered_data\\'
filename = 'bayview_volume.csv'
vol_df = pd.read_csv(path + filename).set_index('time stamp').drop(columns = 'Unnamed: 0')
vol_df.index = pd.to_datetime(vol_df.index)

filename = 'bayview_peakyness.csv'
peak_df = pd.read_csv(path + filename).set_index('dates').drop(columns = 'Unnamed: 0')
peak_df.index = pd.to_datetime(peak_df.index)

#merge and clean up
df = vol_df.merge(peak_df, left_on = vol_df.index, right_on = peak_df.index, how = 'left')
df = df.rename(columns = {'key_0':'timestamp', 'value_x':'Flow','value_y':'dailyVol'})
df.index = df['timestamp']
df = df.drop(columns = ['timestamp', 'timestep_sum_x', 'timestep_sum_y'])
df = df.ffill().round(2)

#extract usage data and group days together 
allFlow = []
usageList = []
normList = []

for date in df['dates'].unique(): #each day
    dayFlow = []
    
    temp_df = df.loc[df['dates'] == date]
    totalUsage = temp_df.iloc[0]['dailyVol']
    peakNorm = temp_df.iloc[0]['peak_norm']
    
    for hour in range(24): #each hour of day
        flow = temp_df.iloc[hour]['Flow']
        dayFlow.append(flow)
        
    allFlow.append(dayFlow)
    usageList.append(totalUsage)
    normList.append(peakNorm)
    
dfList = [allFlow, usageList, normList]
df = pd.DataFrame(dfList).transpose()
df.columns = ['Loadshape', 'totalUsage', 'peakNorm']
df = df.dropna()

#randomly select 20 rows 
df = df.sample(n = 20)
df['Loadshape'] = df['Loadshape'].astype(str)
df['totalUsage'] = df['totalUsage'].astype(str)
df['peakNorm'] = df['peakNorm'].astype(str)
df['allInfo'] = df['Loadshape'] + '$' + df['totalUsage'] + '$' + df['peakNorm'] 

#put all parameters together
combinations = pd.DataFrame(list(product(df['allInfo'], volumes, capacities)))
combinations.columns = ['allInfo', 'storageVol', 'capacity']

#allInfo = combinations['allInfo'].str.split('$', expand = True) 
#allInfo.columns = ['loadshape', 'totalUsage', 'peakNorm']
#combinations2 = pd.concat([combinations, allInfo])

combinations['loadshape'] = combinations['allInfo'].str.split('$', expand = True)[0] 
combinations['loadshape'] = combinations['loadshape'].str.replace('[','')
combinations['loadshape'] = combinations['loadshape'].str.replace(']','')
combinations['totalUsage'] = combinations['allInfo'].str.split('$', expand = True)[1]
combinations['peakNorm'] = combinations['allInfo'].str.split('$', expand = True)[2]
combinations['capacityLU'] = combinations['capacity'].astype(float) * LUcapacityFactor

#setup nicely for excel table
combinations['runName'] = 'bayview' + combinations.index.astype(str)
combinations.index = combinations['runName']
combinations = combinations.drop(columns = ['allInfo', 'runName'])
combinations['loadshift'] = loadshift
combinations = combinations[['loadshape', 'loadshift', 'capacity', 'capacityLU', 'storageVol', 'totalUsage', 'peakNorm']]

#export csv that can be used for inputs
out_path = 'C:\\Users\\madison\\Documents\\GitHub\\HPWHulator\\SCL_RegressionInputs.xlsx'
writer = pd.ExcelWriter(out_path , engine='xlsxwriter')
combinations.to_excel(writer, sheet_name='RegInputs')
writer.save()






