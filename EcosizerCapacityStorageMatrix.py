# -*- coding: utf-8 -*-
"""
Size & Capacity Matrix
Created on Wed Jan 11 11:53:00 2023

@author: madison
"""
from HPWHsizer import HPWHsizer
import numpy as np
import pandas as pd


#Ecosizer run for 4 scenarios get combinations of storage and capacity from sizing results
#market rate, low income * 2 3-hr sheds, 1 peak price reduction

def sizeSystem(gpdpp, loadShapeNorm, compRuntime_hr, loadshift):

    hpwh = HPWHsizer()
    hpwh.initPrimaryByPeople(nPeople = 100, # FILL THIS IN FOR BAYVIEW
                             nApt = 100, #FILL THIS IN FOR BAYVIEW
                             gpdpp = gpdpp,#FILL THIS IN FOR BAYVIEW
                             loadShapeNorm = loadShapeNorm,
                             supplyT_F = 120,
                             incomingT_F = 50, 
                             storageT_F = 150,
                             compRuntime_hr = compRuntime_hr,
                             percentUseable = 0.9,
                             aquaFract = 0.4,
                             schematic = 'swingtank')
    hpwh.initTempMaint(Wapt = 100,
                       setpointTM_F = 135,
                       TMonTemp_F = 125)

    #set loadshift
    hpwh.setLoadShiftforPrimary(loadshift)
    
    hpwh.build_size()
    
    return hpwh.primarySystem.primaryCurve

#low income 3 hour sheds
gpdpp = 25
loadShapeNorm = 'stream'
compRuntime_hr = 18
loadshift = [1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,1,1,1]
lowIncome_3hr = sizeSystem(gpdpp, loadShapeNorm, compRuntime_hr, loadshift)