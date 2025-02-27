# -*- coding: utf-8 -*-
"""
Created on Thu Nov  9 09:58:36 2023

@author: M3309200
"""
from initial_data import *
from session_state_init import *
import pandas as pd
import pyvista as pv
import numpy as np
import streamlit as st
import subprocess
import os
import pickle
import tempfile
# import ast
# import json
from streamlit import session_state
from stpyvista import stpyvista
from streamlit_extras.row import row
from streamlit_extras.grid import grid
import matplotlib.pyplot as plt
from matplotlib import ticker
from acoustics import building
import warnings
# from tkinter import Tk, filedialog
# import openpyxl

freq = [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
warnings.filterwarnings("ignore", message="missing ScriptRunContext")

# Set page configuration
st.set_page_config(
    page_title="Building acoustic indicators calculation tool",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
    
)
pv.global_theme.show_scalar_bar = True
pv.OFF_SCREEN = True

## Initialize a plotter object
plotter = pv.Plotter(window_size=[600, 400])
plotter.background_color = (0.9, 0.9, 0.9)

# Set the CSS style to adjust the width of the plotter
st.markdown(
    """
    <style>
        .css-1aumxhk {
            max-width: 50%;
        }
        .font {
            font-size:30px;} 
    </style>
    """,
    unsafe_allow_html=True
)

# =============================================================================
# Functions
# =============================================================================

@st.cache_data
def load_file(file):
    df = pd.read_excel(file, sheet_name=None, header=None)
    return df

def plot3droom(cx, cy, cz, l, L, h, face_colors=None, face_labels=None, plotter=None):
    """
    Draw a 3D room and label its faces with customizable face colors.

    Parameters:
    - cx, cy, cz: Coordinates of the corner of the room.
    - l, L, h: Dimensions of the room (length, width, height).
    - face_colors: Dictionary with face indices as keys and RGB colors (tuples) as values.
        Default indices:
        - 0: Bottom
        - 1: Top
        - 2: Left
        - 3: Right
        - 4: Front
        - 5: Back
        If face_colors is not provided, all faces will default to white.
    - face_labels: Dictionary with face indices as keys and labels as values (optional).
    - plotter: PyVista plotter instance.
    """
    if plotter is None:
        raise ValueError("A PyVista plotter instance must be provided.")

    # Define vertices of the cuboid
    vertices = np.array([
        [cx, cy, cz],
        [cx, cy + L, cz],
        [cx + l, cy + L, cz],
        [cx + l, cy, cz],
        [cx, cy, cz + h],
        [cx, cy + L, cz + h],
        [cx + l, cy + L, cz + h],
        [cx + l, cy, cz + h],
    ])

    # Define faces of the cuboid
    faces = np.hstack([
        [4, 0, 1, 2, 3],  # Bottom
        [4, 4, 5, 6, 7],  # Top
        [4, 0, 4, 7, 3],  # Left
        [4, 1, 5, 6, 2],  # Right
        [4, 0, 4, 5, 1],  # Front
        [4, 3, 7, 6, 2],  # Back
    ])

    # Default to white for all faces if no colors are provided
    if face_colors is None:
        face_colors = {i: (255, 255, 255) for i in range(6)}

    # Ensure all faces have a defined color
    for i in range(6):
        face_colors.setdefault(i, (255, 255, 255))

    # Create the room as a mesh
    mesh = pv.PolyData(vertices, faces)

    # Assign colors to each face
    face_colors_array = np.array([face_colors[i] for i in range(6)], dtype=np.uint8)
    mesh.cell_data['colors'] = face_colors_array

    # Add the mesh to the plotter
    plotter.add_mesh(mesh, scalars='colors', rgb=True, show_edges=True)

    # If face labels are provided, add text labels to the faces
    if face_labels:
        face_centers = [
            np.mean(vertices[[0, 1, 2, 3]], axis=0),  # Bottom
            np.mean(vertices[[4, 5, 6, 7]], axis=0),  # Top
            np.mean(vertices[[0, 4, 7, 3]], axis=0),  # Left
            np.mean(vertices[[1, 5, 6, 2]], axis=0),  # Right
            np.mean(vertices[[0, 1, 5, 4]], axis=0),  # Front
            np.mean(vertices[[3, 2, 6, 7]], axis=0),  # Back
        ]


def draw_performance(selected_options):
    
    if selected_options is not None:
        fig, ax = plt.subplots()
        for selection in selected_options:
            if selected_options == selected_materials or selected_options == selected_openings:
                sri_values = eval(selection).sri  # Ensure `eval` points to correct Material object with `sri` list
                ax.plot(freq, sri_values, label=selection)
                # Text output for performance stats
                rw_value = building.rw(sri_values[3:19])
                rw_c = round(building.rw_c(sri_values[3:19]))
                rw_ctr = round(building.rw_ctr(sri_values[3:19]))
                st.text(f"{selection} : Rw(C;Ctr) = {rw_value}(-{rw_value - rw_c};-{rw_value - rw_ctr}) dB")
            
            elif selected_options == selected_linings:
                matching_material = None
                for material_name in st.session_state.materials:
                    if material_name in selection:
                        matching_material = material_name      
                dr_values = eval(selection).d_sri
                sri_values = eval(matching_material).sri
                sri_dr_values = []
                for i in range(len(freq)):
                    sri_dr_values.append(dr_values[i]+sri_values[i])           
                ax.plot(freq,sri_dr_values, label=selection + ' + ' + matching_material)
                ax.plot(freq, sri_values, label = matching_material)
                ax.plot(freq, dr_values, label='ΔR ' + selection)
                rw_value = building.rw(sri_values[3:19])
                rw_c = round(building.rw_c(sri_values[3:19]))
                rw_ctr = round(building.rw_ctr(sri_values[3:19]))
                drw_value = building.rw(dr_values[3:19])
                drw_c = round(building.rw_c(dr_values[3:19]))
                drw_ctr = round(building.rw_ctr(dr_values[3:19]))                
                glob_rw_value = building.rw(sri_dr_values[3:19])
                glob_rw_c = round(building.rw_c(sri_dr_values[3:19]))
                glob_rw_ctr = round(building.rw_ctr(sri_dr_values[3:19]))
                st.text(f"{matching_material} : Rw(C;Ctr) = {rw_value}(-{rw_value - rw_c};-{rw_value - rw_ctr}) dB")                
                st.text(f"{selection + ' / ' + matching_material} : ΔRw(C;Ctr) = {glob_rw_value}(-{glob_rw_value - glob_rw_c};-{glob_rw_value - glob_rw_ctr}) dB") 
                st.text(f"{selection} : Δ(Rw+C) = {glob_rw_c-rw_c} dB | Δ(Rw+Ctr) = {glob_rw_ctr-rw_ctr} dB") 
                
            elif selected_options == selected_air_inlets or selected_options == selected_roller_shutter_boxes: 
                sri_values = eval(selection).n_sri  # Ensure `eval` points to correct Material object with `sri` list
                ax.plot(freq, sri_values, label=selection)
                # Text output for performance stats
                rw_value = building.rw(sri_values[3:19])
                rw_c = round(building.rw_c(sri_values[3:19]))
                rw_ctr = round(building.rw_ctr(sri_values[3:19]))
                st.text(f"{selection} : Dn,e,w(C;Ctr) = {rw_value}(-{rw_value - rw_c};-{rw_value - rw_ctr})")
    
        ax.set_xscale('log')
        if ax.get_legend_handles_labels()[0]:
            ax.legend()
        ax.set_xticks(freq)
        ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x)}"))
        ax.set_xlim(min(freq), max(freq))
        ax.tick_params(axis='x', rotation=90)
        ax.tick_params(axis='x', which='minor', bottom=False)
        ax.grid(which='major', linestyle="--", linewidth=0.5)
        ax.grid(which='minor', linestyle='', linewidth=0)
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Sound reduction index (dB)')
        ax.set_title('Performance for selected materials')
        st.pyplot(fig)
        return fig    
        
# =============================================================================
# Import and reading of material library external uploaded file
# =============================================================================

material_library = st.sidebar.file_uploader("Material library", type=['xls', 'xlsx'], accept_multiple_files=False)

if material_library is not None:
    if 'material_library' not in st.session_state or st.session_state['material_library_name'] != material_library.name:
        # Load the new file
        st.session_state['material_library'] = load_file(material_library)
        st.session_state['material_library_name'] = material_library.name  # Track file name to detect changes

    # Access the loaded file from session_state
    df = st.session_state['material_library']
    
    # Extract 'Materials' sheet
    materials_sheet = df.get('Materials', None)
    num_rows = materials_sheet.shape[0]
    num_cols = materials_sheet.shape[1]
    
    # Materials data
    st.session_state.materials = []

    for i in range(1, materials_sheet.shape[1]):
        material_name = materials_sheet.iloc[0, i]
        st.session_state.materials.append(material_name)
        sri = [materials_sheet.iloc[j+4, i] for j in range(21)]
        ts_labo, ts_situ, aeq = [], [], []
        for j, frequency in enumerate(freq):
            if materials_sheet.iloc[2, i] == 1:
                ts_labo.append(2.2/((0.011*(1+(0.25*materials_sheet.iloc[3, i]/np.power(freq[j],1/2))))*freq[j]))
                ts_situ.append(2.2/((np.power(10,(-12-3.3*np.log10(freq[j]/100))/10))*freq[j]))
                aeq.append(2.2*np.pi*np.pi*(np.power((1000/freq[j]),0.5))/(340*(ts_situ[j])))
            elif materials_sheet.iloc[2, i] == 2 or materials_sheet.iloc[2, i] == 3:
                ts_labo.append(2.01*np.power(freq[j],-0.5))
                ts_situ.append(2.01*np.power(freq[j],-0.5))
                aeq.append(2.2*np.pi*np.pi*(np.power((1000/freq[j]),0.5))/(340*ts_situ[j]))

        globals()[material_name] = Material(material_name,materials_sheet.iloc[1, i],int(materials_sheet.iloc[2, i]),materials_sheet.iloc[3, i],sri, ts_labo, ts_situ, aeq)    
   
    # Openings data
    openings_sheet = df['Openings']
    st.session_state.openings= []
    for i in range(1, openings_sheet.shape[1]):
        opening_name = openings_sheet.iloc[0, i]
        if pd.isna(opening_name):
            opening_name = 'None'
        else:
            opening_name = str(opening_name)
        st.session_state.openings.append(opening_name)
        sri= [openings_sheet.iloc[j, i] for j in range(3, openings_sheet.shape[0])]
        globals()[opening_name] = Opening(opening_name, openings_sheet.iloc[1, i], openings_sheet.iloc[2, i], sri)
    # st.write(st.session_state.openings)
    # Linings data
    linings_sheet = df['Linings']
    st.session_state.linings = []
    for i in range(1, linings_sheet.shape[1]):
        lining_name = linings_sheet.iloc[0, i]
        if pd.isna(lining_name):
            lining_name = 'None'
        else:
            lining_name = str(lining_name)
        st.session_state.linings.append(lining_name)
        d_sri = [linings_sheet.iloc[j, i] for j in range(2, linings_sheet.shape[0])]
        globals()[lining_name] = Lining(lining_name, linings_sheet.iloc[1, i], d_sri)

    # Air inlets data
    air_inlets_sheet = df['Air_inlets']
    st.session_state.air_inlets = []
    for i in range(1, air_inlets_sheet.shape[1]):
        air_inlet_name = air_inlets_sheet.iloc[0, i]
        if pd.isna(air_inlet_name):
            air_inlet_name = 'None'
        else:
            air_inlet_name = str(air_inlet_name)
        st.session_state.air_inlets.append(air_inlet_name)
        n_sri = [air_inlets_sheet.iloc[j, i] for j in range(1, air_inlets_sheet.shape[0])]
        globals()[air_inlet_name] = Air_inlet(air_inlet_name, n_sri)

    # Roller shutter boxes data
    roller_shutter_boxes_sheet = df['Roller_shutter_boxes']
    st.session_state.roller_shutter_boxes = []
    for i in range(1, roller_shutter_boxes_sheet.shape[1]):
        roller_shutter_box_name = roller_shutter_boxes_sheet.iloc[0, i]
        if pd.isna(roller_shutter_box_name):
            roller_shutter_box_name = 'None'
        else:
            roller_shutter_box_name = str(roller_shutter_box_name)
        st.session_state.roller_shutter_boxes.append(roller_shutter_box_name)
        n_sri = [roller_shutter_boxes_sheet.iloc[j, i] for j in range(1, roller_shutter_boxes_sheet.shape[0])]
        globals()[roller_shutter_box_name] = Roller_shutter_box(roller_shutter_box_name, n_sri)


# =============================================================================
# Geometry definition and drawing
# =============================================================================

if material_library is not None:

    # Plot Room Dimensions Input
    st.sidebar.write("Room")
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        st.session_state.l = st.number_input("Length l", value=float(st.session_state.get('l', 0.0)), format="%.2f")
    with col2:
        st.session_state.L = st.number_input("Width L", value=float(st.session_state.get('L', 0.0)), format="%.2f")
    with col3:
        st.session_state.h = st.number_input("Height h", value=float(st.session_state.get('h', 0.0)), format="%.2f")
    
           
    face_colors = {
        0: (255, 0, 0),    # Bottom - Red
        1: (0, 255, 0),    # Top - Green
        2: (0, 255, 255),  # Back - Cyan
        3: (255, 255, 0),  # Right - Yellow
        4: (255, 0, 255),  # Front - Magenta
        5: (0, 0, 255),    # Left - Blue
    }
    
    # Define labels for faces
    face_labels = {
        0: "Bottom",
        1: "Top",
        2: "Left",
        3: "Right",
        4: "Front",
        5: "Back",
        }
    center_col1, center_col2 = st.columns([0.4,0.6])
   
    #Drawing rooms
    with center_col1:
        st.session_state.project_name = st.text_input("Project name")
        #Plot Reception room = Room
        if st.session_state.l != 0 and st.session_state.L != 0 and st.session_state.h != 0:
            # plot3droom(0,0,0,st.session_state.l, st.session_state.L, st.session_state.h, 85, 240, 158,'Room')
            # mesh_room = plot3droom(cx=0, cy=0, cz=0, l=st.session_state.l, L=st.session_state.L, h=st.session_state.h,color_r=85, color_g=240, color_b=158,face_colors=facecolors,face_labels=face_labels, leg='Room',plotter=plotter)
            mesh_room = plot3droom(cx=0, cy=0, cz=0, l=st.session_state.l, L=st.session_state.L, h=st.session_state.h,face_colors=face_colors,face_labels=face_labels,plotter=plotter)

        room_choice = st.sidebar.radio("Emission room choice",["Adjacent","Exterior"])#,"Up","Down"])
        
        #Plot Adjacent
        if room_choice == "Adjacent" and material_library is not None:
            col1, col2 = st.sidebar.columns(2)
            with col2:
                st.session_state.L2 = st.number_input("L2", value = st.session_state.L2,step=1.,format="%.2f")
            if st.session_state.L2 != 0:
                # plot3droom(0,-st.session_state.L2,0,st.session_state.l,st.session_state.L2, st.session_state.h, 118,118,118,'Room1')
                # mesh_adjacent = plot3droom(cx=0,cy=-st.session_state.L2,cz=0,l=st.session_state.l,L=st.session_state.L2, h=st.session_state.h, color_r=118,color_g=118,color_b=118,face_colors=facecolors,face_labels=face_labels,plotter=plotter, leg='Room1')
                mesh_adjacent = plot3droom(cx=0,cy=-st.session_state.L2,cz=0,l=st.session_state.l,L=st.session_state.L2, h=st.session_state.h,face_colors=face_colors,face_labels=face_labels,plotter=plotter)          
                st.write(":blue[Facade] :green[Ceiling] :violet[Walls] :red[Floor]")
        #Plot Facade
        if room_choice == "Exterior":
            # if st.session_state.L2 != 0:
                # mesh_exterior = plot3droom(cx=st.session_state.l,cy=0,cz=0,l=0,L=st.session_state.L, h=st.session_state.h, color_r=0,color_g=0,color_b=255,plotter=plotter, leg='Facade1'
            mesh_exterior = plot3droom(cx=st.session_state.l,cy=0,cz=0,l=0,L=st.session_state.L, h=st.session_state.h, face_colors=face_colors,face_labels=face_labels,plotter=plotter)
            st.write(":blue[Facade] ")
     
         ## Final touches
        plotter.view_isometric()
            
        ## Send to streamlit
        stpyvista(plotter, horizontal_align='left')
        plotter.show()

if material_library is not None:
    with center_col1:
        st.write("Performances visualizer")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Materials", "Linings", "Openings", "Air inlets","Roller shutter boxes"])
        
        with tab1:
            # rcol1, rcol2, rcol3 = st.columns(3)
            # with rcol1:
            selected_materials = st.multiselect("Select Materials", st.session_state.materials, default=st.session_state['selected_materials'])
            st.session_state['selected_materials'] = selected_materials
            if selected_materials is not None:
                draw_performance(selected_materials)

        with tab2:
            # rcol1, rcol2, rcol3 = st.columns(3)
            # with rcol1:
            selected_linings = st.multiselect("Select Linings", st.session_state.linings, default=st.session_state['selected_linings'])
            st.session_state['selected_linings'] = selected_linings
            if selected_linings is not None:
                draw_performance(selected_linings)
                
        with tab3:
            selected_openings = st.multiselect("Select Openings", st.session_state.openings, default=st.session_state['selected_openings'])
            st.session_state['selected_openings'] = selected_openings
            if selected_openings is not None:
                draw_performance(selected_openings)

        with tab4:
            selected_air_inlets = st.multiselect("Select Air inlets", st.session_state.air_inlets, default=st.session_state['selected_air_inlets'])
            st.session_state['selected_air_inlets'] = selected_air_inlets
            if selected_air_inlets is not None:
                draw_performance(selected_air_inlets)
                
        with tab5:
            selected_roller_shutter_boxes = st.multiselect("Select Roller shutter boxes", st.session_state.roller_shutter_boxes, default=st.session_state['selected_roller_shutter_boxes'])
            st.session_state['selected_roller_shutter_boxes'] = selected_roller_shutter_boxes
            if selected_roller_shutter_boxes is not None:
                draw_performance(selected_roller_shutter_boxes)
                
    with center_col2:
                
        if room_choice == "Exterior":
           
            st.write('Facade')
            grid3 = grid([1],[1],[2, 3,3],[1],[1],vertical_align="bottom")
            materialfa = grid3.selectbox('Facade',st.session_state.materials, key = "materialfa")
            liningfa1 = grid3.selectbox('Doubling',st.session_state.linings, key = "liningfa1")
            openingfa = grid3.selectbox('Openings',st.session_state.openings, key = "openingfa")
            l_opfa = grid3.number_input("l", value = st.session_state.l_opfa, format="%.2f", key = "l_opfa")
            h_opfa = grid3.number_input("h", value = st.session_state.h_opfa, format="%.2f",  key = "h_opfa")
            inletfa = grid3.selectbox('Air inlet',st.session_state.air_inlets, key = "inletfa")
            rollerfa = grid3.selectbox('Roller shutter box',st.session_state.roller_shutter_boxes, key = "rollerfa")
        
        else:
            st.write('Reception room')
            grid1 = grid([2,2,2,2,1,1],[2,3,3],[2,3,3],[2,3,3],vertical_align="bottom")
            grid1.write("Separative wall")
            material1 = grid1.selectbox('Separative',st.session_state.materials, key = "material1")
            linings1 = grid1.selectbox('Doubling',st.session_state.linings, key="linings1")
            openings1 = grid1.selectbox('Openings',st.session_state.openings, key = "openings1")
            l_ops = grid1.number_input("l", value=st.session_state.l_ops, format="%.2f", key='l_ops')
            h_ops = grid1.number_input("h", value=st.session_state.h_ops, format="%.2f", key="h_ops")
            grid1.write("Room walls")
            materialw1 = grid1.selectbox('Material',st.session_state.materials, key = "materialw1")
            liningw1 = grid1.selectbox('Doubling',st.session_state.linings, key = "liningw1")
            grid1.write("Room facade")
            materialfa = grid1.selectbox('Material',st.session_state.materials, key = "materialfa")
            liningfa1 = grid1.selectbox('Doubling',st.session_state.linings, key = "liningfa1")
            grid1.write("Room floor")
            materialf1 = grid1.selectbox('Material',st.session_state.materials, key = "materialf1")
            liningf1 = grid1.selectbox('Screed',st.session_state.linings, key = "liningf1")
            grid1.write("Room ceiling")
            materialc1 = grid1.selectbox('Material',st.session_state.materials, key = "materialc1")
            if eval(materialc1).cat == 4:
                h_plenum = grid1.number_input("h_plenum", value=st.session_state.h_plenum, format="%.2f", key='h_plenum')
                liningc1 = 'None'
            else:
                liningc1 = grid1.selectbox('Doubling',st.session_state.linings, key = "liningc1")
                h_plenum = 0
            st.markdown("<hr style='border: 1px solid grey;'/>", unsafe_allow_html=True)
                  
            if room_choice == "Adjacent":
                st.write('Adjacent- Emission room')
                grid2 = grid([2,2,2,2],[2,3,3],[2,3,3],[2,3,3],[2,3,3],vertical_align="bottom")
                grid2.write("Room2 - adjacent")
                grid2.write(material1)
                linings2 = grid2.selectbox('Doubling',st.session_state.linings, key="linings2")
                grid2.write(openings1)
                grid2.write("Room2 walls")
                grid2.write(materialw1)
                liningw2 = grid2.selectbox('Doubling',st.session_state.linings, key="liningw2")
                grid2.write("Room2 facade")
                grid2.write(materialfa)
                liningfa2 = grid2.selectbox('Doubling',st.session_state.linings, key = "liningfa2")
                grid2.write("Room2 floor")
                grid2.write(materialf1)
                liningf2 = grid2.selectbox('Doubling',st.session_state.linings, key="liningf2")
                grid2.write("Room2 ceiling")
                grid2.write(materialc1)
                liningc2 = grid2.selectbox('Doubling',st.session_state.linings, key="liningc2")
                st.markdown("<hr style='border: 1px solid grey;'/>", unsafe_allow_html=True)
  
        if st.button("Calculation"):
            st.session_state.numeric_values = []
            # st.session_state.results = []  
            # st.write(l_ops)
            if room_choice == "Adjacent":
                st.session_state.results_adj = [] 
                
                objects = {'material1': eval(material1),
                           'linings1': eval(linings1),
                           'openings1': eval(openings1),
                           'materialw1': eval(materialw1),
                           'liningw1': eval(liningw1), 
                           'materialf1': eval(materialf1),
                           'materialfa': eval(materialfa),
                           'liningf1': eval(liningf1),
                           'liningfa1': eval(liningfa1),
                           'liningfa2': eval(liningfa2),
                           'materialc1': eval(materialc1), 
                           'liningc1': eval(liningc1), 
                           'linings2': eval(linings2), 
                           'liningw2': eval(liningw2),
                           'liningf2': eval(liningf2),
                           'liningc2': eval(liningc2),
                           'l': st.session_state.l, 
                           'L': st.session_state.L,
                           'h': st.session_state.h ,
                           'L2': st.session_state.L2,
                           'l_ops': st.session_state.l_ops,
                           'h_ops': st.session_state.h_ops,
                          'h_plenum': st.session_state.h_plenum}
                
                # Serialize the objects to a temporary file
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    pickle.dump(objects, temp_file)
                    temp_file_path = temp_file.name
                # Pass the file path to the subprocess
                try:
                    # Run subprocess and capture JSON output
                    result = subprocess.run(["python", "DnT_calculation.py", temp_file_path],capture_output=True, text=True)
                    print("Subprocess stdout:", result.stdout)
                    print("Subprocess stderr:", result.stderr)
                
                finally:
                    # Clean up the temporary file
                    os.remove(temp_file_path)
                
                stdout_output_str = str(result.stdout)
                                      
                # Split the string into words
                clean = stdout_output_str.replace(',','')
                clean = clean.replace('[','')
                clean = clean.replace(']','')
                results_adj = clean.split()
                results_adj = [float(num) if num.replace('.', '', 1).isdigit() or (num.startswith('-') and num[1:].replace('.', '', 1).isdigit()) else num for num in results_adj]

                #Store results in session_state
                st.session_state.results_adj = results_adj
                
            if room_choice == "Exterior":
                st.session_state.results_ext = [] 
                objects = {'materialfa': eval(materialfa),
                           'liningfa1': eval(liningfa1),
                           'openingfa': eval(openingfa),
                           'inletfa': eval(inletfa),
                           'rollerfa': eval(rollerfa),
                           'l_opfa': st.session_state.l_opfa,
                           'h_opfa': st.session_state.h_opfa,
                           'l': st.session_state.l, 
                           'L': st.session_state.L,
                           'h': st.session_state.h ,
                           'L2': st.session_state.L2}    
                
                # Serialize the objects to a temporary file
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    pickle.dump(objects, temp_file)
                    temp_file_path = temp_file.name
                # Pass the file path to the subprocess
                try:
                    # Run subprocess and capture JSON output
                    result = subprocess.run(["python", "DnT_calculation_facade.py", temp_file_path],capture_output=True, text=True)
                    print("Subprocess stdout:", result.stdout)
                    print("Subprocess stderr:", result.stderr)
                
                finally:
                    # Clean up the temporary file
                    os.remove(temp_file_path)

                stdout_output_str = str(result.stdout)
                      
                # Split the string into words
                clean = stdout_output_str.replace(',','')
                clean = clean.replace('[','')
                clean = clean.replace(']','')
                results_ext = clean.split()
                results_ext = [(num) if num.replace('.', '', 1).isdigit() or (num.startswith('-') and num[1:].replace('.', '', 1).isdigit()) else num for num in results_ext]

                #Store results in session_state
                st.session_state.results_ext = results_ext
                
        result_col1, result_col2 = st.columns(2)
        if room_choice == 'Adjacent':
            if st.session_state.results_adj != []: 
                with result_col1: 
                        st.text(f"Results: DnT,w(C,Ctr) = {st.session_state.results_adj[3]}")
                        df_results = {'Frequency': freq+['DnT,w(C,Ctr)'], 'DnT_global':st.session_state.results_adj[4:25]+st.session_state.results_adj[3:4],
                                      "DnT_direct": st.session_state.results_adj[29:50]+st.session_state.results_adj[28:29], "DnT_floor": st.session_state.results_adj[54:75]+st.session_state.results_adj[53:54],
                                      "DnT_walls": st.session_state.results_adj[79:100]+st.session_state.results_adj[78:79], "DnT_ceiling": st.session_state.results_adj[104:125]+st.session_state.results_adj[103:104],
                                      "DnT_facade": st.session_state.results_adj[129:150]+st.session_state.results_adj[128:129]}
                        dataframe_results = pd.DataFrame(df_results)
                        # st.dataframe(styled_dataframe)
                        st.table(df_results)
                
               
                with result_col2:     
                        for i in range(4,25):
                            st.session_state.numeric_values.append(st.session_state.results_adj[i])
                        fig_result, ax_result = plt.subplots(figsize=(4,6))
                        ax_result.set_xscale('log')
                        ax_result.set_xticks(freq)
                        ax_result.get_xaxis().set_major_formatter(plt.ScalarFormatter())
                        ax_result.get_xaxis().set_tick_params(which='minor', size=0)
                        ax_result.get_xaxis().set_tick_params(which='minor', width=0) 
                        ax_result.tick_params(axis='x', rotation=90)
                        ax_result.plot(freq, st.session_state.results_adj[4:25], label = "DnT")
                        ax_result.plot(freq, st.session_state.results_adj[29:50], label = "DnT_direct")
                        ax_result.plot(freq, st.session_state.results_adj[54:75], label = "DnT_floor")
                        ax_result.plot(freq, st.session_state.results_adj[79:100], label = "DnT_walls")
                        ax_result.plot(freq, st.session_state.results_adj[104:125], label = "DnT_ceiling")
                        ax_result.plot(freq, st.session_state.results_adj[129:150], label = "DnT_facade")
                        ax_result.set_xlabel('Frequency (Hz)')
                        ax_result.set_ylabel('Airborne sound insulation (dB)')
                        ax_result.set_title('Calculation result')
                        ax_result.legend()
                        ax_result.grid(which = "major")
                        st.pyplot(fig_result)
            
        if room_choice == "Exterior":
            if st.session_state.results_ext != []: 
                with result_col1: 
                    st.text(f"Results: D_2m_nT,w(C,Ctr) = {st.session_state.results_ext[3]}")
                    # st.text(st.session_state.results)
                    df_results = {'Frequency': freq+['D_2m_nT,w(C,Ctr)'], 'D_2m_nT':st.session_state.results_ext[4:25]+st.session_state.results_ext[3:4]}
                    dataframe_results = pd.DataFrame(df_results)
                    st.table(df_results)
                        
                with result_col2:  
                    for i in range(4,25):
                        st.session_state.numeric_values.append(st.session_state.results_ext[i])
                    fig_result, ax_result = plt.subplots(figsize=(4,6))
                    plt.figure(figsize=(10,6))
                    ax_result.set_xscale('log')
                    ax_result.set_xticks(freq)
                    ax_result.get_xaxis().set_major_formatter(plt.ScalarFormatter())
                    ax_result.get_xaxis().set_tick_params(which='minor', size=0)
                    ax_result.get_xaxis().set_tick_params(which='minor', width=0) 
                    ax_result.tick_params(axis='x', rotation=90)
                    ax_result.plot(freq, st.session_state.results_ext[4:25], label = "D_2m_nT")
                    ax_result.set_xlabel('Frequency (Hz)')
                    ax_result.set_ylabel('Facade sound insulation (dB)')
                    ax_result.set_title('Calculation result')
                    ax_result.legend()
                    ax_result.grid(which = "major")
                    st.pyplot(fig_result)                
     
        title = st.text_input('Calculation name', value="")
        if st.button("save"):
            list_name = title
            st.session_state.user_dnt[list_name] = st.session_state.numeric_values[0:21]
            st.text('saved');
    
            
    # Prompt user for file name
    form = st.form(key="user_form")
    file_name = form.text_input("File name:", value="default_file_name")


    if room_choice == "Exterior":
        dict_settings = {"Project name": [st.session_state.project_name], "Calculation type": room_choice,
                "l": float(st.session_state.l), "L": float(st.session_state.L), 'h': float(st.session_state.h), 
                "Room facade": materialfa, "Reception room facade doubling": liningfa1,
                "Opening": openingfa, "Opening length": st.session_state.l_opfa, "Opening height": st.session_state.h_opfa,
                "Air inlet": inletfa, "Roller shutter box": rollerfa}
    if room_choice == "Adjacent":
        dict_settings = {"Project name": st.session_state.project_name, "Calculation type": room_choice, 
                 "l": float(st.session_state.l), "L": float(st.session_state.L), 'h': float(st.session_state.h), 'L2': float(st.session_state.L2),
                 "Separative": [material1], "Reception room separative doubling": linings1, "Separative opening": openings1, "Opening length": st.session_state.l_ops, "Opening height": st.session_state.h_ops,
                 "Room walls": materialw1 ,"Reception room wall doubling": liningw1,
                 "Room facade": materialfa, "Reception room facade doubling": liningfa1,
                 "Room floor": materialf1, "Reception room floor doubling": liningf1,
                 "Room ceiling": materialc1, "Reception room ceiling doubling": liningc1,
                 "Emission room separative doubling": linings2, "Emission room wall doubling": liningw2,
                 "Emission room facade doubling": liningfa2, "Emission room floor doubling": liningf2,
                 "Emission room ceiling doubling": liningc2}
    
    # Prompt user for folder path
    folder_path = form.text_input("Enter the full folder path to save the file:")
    
    # Function to export data to an Excel file
    @st.cache_data
    def export_to_excel(file_name, folder_path):
        if not file_name:
            st.warning("Please enter a valid file name.")
            return
    
        if not folder_path:
            st.warning("Please specify a valid folder path.")
            return
    
        # Ensure the folder path exists
        if not os.path.exists(folder_path):
            st.warning("The specified folder does not exist.")
            return
    
        # Construct full file path
        full_file_path = os.path.join(folder_path, f"{file_name}.xlsx")
    
        try:
            # Write data to the Excel file
            with pd.ExcelWriter(full_file_path, engine="openpyxl") as writer:
                df = pd.DataFrame(dict_settings)
                df.T.to_excel(writer, sheet_name='Settings')
                dataframe_results.to_excel(writer, sheet_name ='Results', index=False)
            
            st.success(f"Excel file has been successfully saved to: {full_file_path}")
    
        except Exception as e:
            st.error(f"An error occurred while exporting the Excel file: {e}")
            
    if form .form_submit_button('Export settings and results'):
        export_to_excel(file_name, folder_path)
