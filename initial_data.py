# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 10:35:03 2023

@author: M3309200
"""

import pyvista as pv
# from stpyvista import stpyvista
import numpy as np
from acoustics.weighting import *
from acoustics.decibel import *
from acoustics.bands import *

## Initialize a plotter object
# plotter = pv.Plotter(window_size=[400,400])
# plotter.add_axes(line_width=5, labels_off=False)
# stpyvista(plotter, horizontal_align='left')
# plotter.view_isometric()
# Sidebar components

#Class initialization

class Room:
    def __init__(self, l, L, h):
        self.l = l
        self.L = L
        self.h = h
    
    def calc_area(self):
        self.area = self.l * self.L
        return self.area
    
    def calc_volume(self):
        self.volume = self.calc_area() * self.h
        return self.volume
    
    def wall_properties(self):
        pass
    
    def vert(self):
        return [self.L,self.h]
    
    def hor(self):
        return[self.L,self.l]
    
    def sep(self):
        return[self.l,self.h]
            
class Material:
    def __init__(self, name, thickness, cat, ms, sri, ts_labo, ts_situ, aeq):
        self.name = name
        self.thickness = thickness
        self.cat = cat
        self.ms = ms
        self.sri = sri
        self.ts_labo = ts_labo
        self.ts_situ = ts_situ
        self.aeq = aeq


    # def structural_time(self):
    #     self.ts = []
    #     self.aeq = []
    #     for i in freq:
    #         if self.cat == 1:
    #             self.ts.append(2.2/(i*(np.power(10,(-12-3.3*np.log10(i/100))/10)))) #formule empirique pour Ts in situ
    #             #self.ts.append(2.2/(i*(0.011*(1+0.25*(self.ms/np.power(i,0.5)))))) #formule 12354 Ts labo
            
    #         if self.cat == 2:
    #             self.ts.append(2.01*np.power(i,-0.5))
              
    #     return self.ts
    
    
    # def eq_abs_length(self):
    #     self.a_eq = []
    #     for idx, i in enumerate(freq):
    #         self.a_eq.append(2.2*np.power(np.pi,2)*np.power(1000/i,0.5)/(340*self.ts[idx]))
    #     return self.a_eq
        
       
class Opening(Material):
    def __init__(self,name,l,h,sri):
        self.name = name
        self.l = l
        self.h = h
        self.sri = sri
        
    def calc_area(self):
        self.area = self.l * self.h
        return self.area

class Lining(Material):
    def __init__(self,name,thickness,d_sri):
        self.name = name
        self.thickness = thickness
        self.d_sri = d_sri
        
class Element():
    def __init__(self,n_sri):
        self.n_sri = n_sri


class Air_inlet(Element):
    def __init__(self,name,n_sri):
        self.name = name
        self.n_sri = n_sri
        
class Roller_shutter_box(Element):
    def __init__(self,name,n_sri):
        self.name = name
        self.n_sri = n_sri

class Source:
    def __init__(self,name,lvl,lvla):
        self.name = name
        self.lvl = lvl
        self.lvla = lvla

## A_weighting octave function

OCTAVE_A_WEIGHTING = np.array([-56.7, -39.4, -26.2, -16.1, -8.6, -3.2, +0.0, +1.2, +1.0, -1.1, -6.6]) 

def a_weighting_oct(first,last):
    oct_bands = octave(16,16000)
    low_index = np.where(oct_bands == first)[0]
    high_index = np.where(oct_bands == last)[0]

    if len(low_index) == 0 or len(high_index) == 0:
        raise ValueError("One or both of the specified frequencies not found in octave bands.")

    low = low_index[0]
    high = high_index[0]
    
    freq_weightings = OCTAVE_A_WEIGHTING

    return freq_weightings[low: high+1]
        
def z2a_oct(levels, first, last):
    """Apply A-weighting to Z-weighted signal, in octave bands.
    """
    return levels + a_weighting_oct(first, last)


def dbaddition(a, b, c):
    """Energetic addition.
    
    :param a: Single level or sequence of levels.
    :param b: Single level or sequence of levels.
    :param c: Single level or sequence of levels.
    
    .. math:: L_{a+b} = 10 \\log_{10}{10^{L_b/10}+10^{L_a/10}+10^{L_c/10}}
    
    Energetically adds b to a to c.
    """
    a = np.asanyarray(a)
    b = np.asanyarray(b)
    c = np.asanyarray(c)
    return 10.0*np.log10(10.0**(a/10.0)+10.0**(b/10.0)+10.0**(c/10.0))

#Data intialization for database files

freq = [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
ts_labo = []
for i,frequency in enumerate(freq):
    ts_labo.append(2.01*np.power(freq[i],-1/2))
selected_materials = []
selected_openings = []
selected_air_inlets = []
selected_roller_shutter_boxes = []
materials = []
openings = []
linings = []
air_inlets = []
roller_shutter_boxes = []
sri = []
d_sri = []
n_sri = []
freq = []
sources = []
selected_sources = []
nr = []
lvl = []
lvla = []

#Data initialization - room dimensions

l = 0.0
L = 0.0
h = 0.0
L1 = 0.0
L2 = 0.0
l2 = 0.0
L3 = 0.0
l4 = 0.0
h5 = 0.0
h6 = 0.0

# LAeq calculation list/dict initialization

lvl_table = []
source_choice = []
lvl_choice = []
lvl_list = []
data_list = []
laeq = []
laeq_glob = []
numeric_values = []
user_dnt = {}
user_rt = {}

#Intérieur

DnT_direct = [] #isolement par la paroi séparative
Dn1_df = [] #isolement latéral 1, transmission direct-flanking (séparatif-sol)
Dn1_ff = [] #isolement latéral 1, transmission flanking-flanking (sol-sol)
Dn1_fd = [] #isolement latéral 1, transmission flanking-direct (sol-séparatif)
DnT1 = [] #isolement latéral1 (jonction entre sol et séparatif)
Dn2_df = [] #isolement latéral 2, transmission direct-flanking (séparatif-mur intérieur)
Dn2_ff = [] #isolement latéral 2, transmission flanking-flanking (mur intérieur-mur intérieur)
Dn2_fd = [] #isolement latéral 2, transmission flanking-direct (mur intérieur-séparatif)
DnT2 = [] #isolement latéral2 (jonction entre mur intérieur et séparatif)
Dn3_df = [] #isolement latéral 3, transmission direct-flanking (séparatif-plafond)
Dn3_ff = [] #isolement latéral 3, transmission flanking-flanking (plafond-plafond)
Dn3_fd = [] #isolement latéral 3, transmission flanking-direct (plafond-séparatif)
DnT3 = [] #isolement latéral3 (jonction entre plafond et séparatif)
Dn4_df = [] #isolement latéral 4, transmission direct-flanking (séparatif-facade)
Dn4_ff = [] #isolement latéral 4, transmission flanking-flanking(facade-facade)
Dn4_fd = [] #isolement latéral 4, transmission flanking-direct (facade-séparatif)
DnT4 = [] #isolement latéral4 (jonction entre facade et séparatif)
DnT = [] #isolement global

# Extérieur
tau_wall_facade = [] 
tau_opening_facade = []
tau_air_inlet = []
tau_shutter = []
tau_opening_sep = []
tau_sep = []
D_2m_nT = []

# LAeq calculation

dict_dnt = {}
dict_rt = {}
dict_results = {}