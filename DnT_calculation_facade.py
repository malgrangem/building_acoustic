# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 09:50:34 2022

@author: M3309200
"""

from initial_data import*
from initial_data import Room
from SGSF_acoubox import materials, openings, air_inlets, linings, roller_shutter_boxes
import numpy as np
import matplotlib.pyplot as plt
from acoustics import building
import sys
import pickle
import json
import warnings

warnings.filterwarnings("ignore", message="missing ScriptRunContext")

freq = [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
msg=0


def perform_acoustic_calculations(temp_file_path):
    # Load the serialized data
    msg=0
    with open(temp_file_path, "rb") as file:
        objects = pickle.load(file)

    wall_facade = objects['materialfa']
    lining_facade_rec = objects['liningfa1']
    opening_facade = objects['openingfa']
    air_inlet = objects['inletfa']
    roller_shutter_box = objects['rollerfa']
    l_opfa = objects['l_opfa']
    h_opfa = objects['h_opfa']
    l = objects['l']
    L = objects['L']
    h = objects['h']

######### GLOBAL PARAMETERS
    tau_wall_facade = [] 
    tau_opening_facade = []
    tau_air_inlet = []
    tau_shutter = []


    room1 = Room(l,L,h) #reception room

    c = 10*np.log10(0.032*room1.calc_volume())

######## FACADE CALCULATION
        
    if lining_facade_rec != None and (wall_facade.name in lining_facade_rec.name) is True:
        dr_fac_rec = lining_facade_rec.d_sri
    elif lining_facade_rec == None :
        dr_fac_rec = [0]*21
    else: 
        msg = 1
    
    for i in range(len(freq)): 
    
        if opening_facade is None:
            tau_opening_facade = [0]*21
            tau_wall_facade.append((h*L/10)*np.power(10,(-wall_facade.sri[i]-dr_fac_rec[i])/10)) #Facade wall without window
        else:
            tau_opening_facade.append((h_opfa*l_opfa/10)*(np.power(10,-opening_facade.sri[i]/10))) #Opening
            tau_wall_facade.append((((h*L)-(h_opfa*l_opfa))/10)*np.power(10,-wall_facade.sri[i]-dr_fac_rec[i]/10))#Facade wall 
        
        if air_inlet is None:
            tau_air_inlet = [0]*21
        else:
            tau_air_inlet.append(np.power(10,-air_inlet.n_sri[i]/10))
            
        if roller_shutter_box is None:
            tau_shutter = [0]*21
        else: tau_shutter.append((l_opfa/1.4)*np.power(10,-roller_shutter_box.n_sri[i]/10))
        
        D_2m_nT.append(round(-10*np.log10(tau_wall_facade[i]+tau_opening_facade[i]+tau_air_inlet[i]+tau_shutter[i]) + 10*np.log10(0.032*l*L*h),1))
    
    d_2m_nt = building.rw(D_2m_nT[3:19])
    
    print ('D2m,nT,w (C;Ctr) = %d(-%d;-%d)' % (d_2m_nt,d_2m_nt - building.rw_c(D_2m_nT[3:19]),d_2m_nt - building.rw_ctr(D_2m_nT[3:19])))
    print (D_2m_nT)

       
if __name__ == "__main__":
    temp_file_path = sys.argv[1]
    results = perform_acoustic_calculations(temp_file_path)
