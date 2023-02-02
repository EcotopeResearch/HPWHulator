# -*- coding: utf-8 -*-
"""
SCL Sim Plots
Created on Thu Jan 19 21:40:35 2023

@author: madison
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

df = pd.read_excel('C:\\Users\\madison\\Documents\\GitHub\\HPWHulator\\SCL_Results.xlsx')

#extract info from run name
df['gpdpp'] = df['run_name'].str.split('_', expand = True)[3]
df['runCategory'] = df['run_name'].str.split('_', expand = True)[0] + df['run_name'].str.split('_', expand = True)[1]

#plot capcacity/storage versus gpdpp

#market 3hr
market_3hr = df.loc[df['runCategory'] == 'market3hr']
market_peakRed = df.loc[df['runCategory'] == 'marketpeakRed']
lowIncome_3hr = df.loc[df['runCategory'] == 'lowIncome3hr']
lowIncome_peakRed = df.loc[df['runCategory'] == 'lowIncomepeakRed']

def plotSimResults(df, title):
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = df['capacity_loadUp'],
        y = df['gpdpp'].astype('float'),
        mode = 'markers',
        #name = ,
        marker = dict(color = df['percent_shed_met'],
            colorscale = px.colors.diverging.Portland,
            showscale = True)))
    
    fig.update_layout(
        title = title,
        xaxis_title = 'Capacity [kWh] and Storage [gal]',
        yaxis_title = 'Gallons per day per Person')
    
    return fig

Market3hrPlot = plotSimResults(market_3hr, 'Market Rate: Two 3-Hour Shed Periods')
Market3hrPlot.write_html('Z:\\SCL_matrix_inputs\\Market3hr.html')

MarketPeakRedPlot = plotSimResults(market_peakRed, 'Market Rate: Shed During Utility Peak')
MarketPeakRedPlot.write_html('Z:\\SCL_matrix_inputs\\MarketPeakRed.html')

LowIncome3hrPlot = plotSimResults(lowIncome_3hr, 'Low Income Rate: Two 3-Hour Shed Periods')
LowIncome3hrPlot.write_html('Z:\\SCL_matrix_inputs\\LowIncome3hr.html')

LowIncomePeakRedPlot = plotSimResults(lowIncome_peakRed, 'Low Income Rate: Shed During Utility Peak')
LowIncomePeakRedPlot.write_html('Z:\\SCL_matrix_inputs\\LowIncomePeakRed.html')
