# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 14:28:32 2024

@author: M3309200
"""
import streamlit as st
from streamlit import session_state


# Library initialization

if 'materials' not in st.session_state:
    st.session_state.materials = []
    
if 'imported_settings' not in st.session_state:
    st.session_state.imported_settings = {}

if 'imported_settings_name' not in st.session_state:
    st.session_state['imported_settings_name'] = []

if 'room_choice' not in st.session_state:
    st.session_state['room_choice'] = "Adjacent"

if 'selected_materials' not in st.session_state:
    st.session_state.selected_materials = []

if 'selected_linings' not in st.session_state:
    st.session_state.selected_linings = []
    
if 'selected_openings' not in st.session_state:
    st.session_state.selected_openings = []
    
if 'selected_air_inlets' not in st.session_state:
    st.session_state.selected_air_inlets = []
        
if 'selected_roller_shutter_boxes' not in st.session_state:
    st.session_state.selected_roller_shutter_boxes = []
    
if 'selected_sources' not in st.session_state:
    st.session_state.selected_sources = []

if 'sources' not in st.session_state:
    st.session_state.sources = []

if 'NR_curves' not in st.session_state:
    st.session_state.NR_curves = []
    
# Dimensions initialization

if 'l' not in st.session_state:
    st.session_state.l = 0.00

if 'L' not in st.session_state:
    st.session_state.L = 0.00
    
if 'h' not in st.session_state:
    st.session_state.h = 0.00
    
if 'L1' not in st.session_state:
    st.session_state['L1'] = 0.00

if 'L2' not in st.session_state:
    st.session_state['L2'] = 0.00
    
if 'l_ops' not in st.session_state:
    st.session_state['l_ops'] = 0.00

if 'h_ops' not in st.session_state:
    st.session_state['h_ops'] = 0.00

if 'l_opfa' not in st.session_state:
    st.session_state['l_opfa'] = 0.00

if 'h_opfa' not in st.session_state:
    st.session_state['h_opfa'] = 0.00

if 'h_plenum' not in st.session_state:
    st.session_state['h_plenum'] = 0.00

# Systems initialization

if 'project_name' not in st.session_state:
    st.session_state['project_name'] = ''
    
if 'numeric_values' not in st.session_state:
    st.session_state['numeric_values'] = []
    
if 'results_adj' not in st.session_state:
    st.session_state['results_adj'] = []

if 'results_ext' not in st.session_state:
    st.session_state['results_ext'] = []

if 'user_dnt' not in st.session_state:
    st.session_state['user_dnt'] = {}
    
if "user_rt" not in st.session_state:
    st.session_state.user_rt = {"Default_RT_0.5": [0.5] * 21, "Default_RT_1": [1] * 21}
    
if 'dict_results' not in st.session_state:
    st.session_state['dict_results'] = {}

