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

ts_labo = []
for i,frequency in enumerate(freq):
    ts_labo.append(2.01*np.power(freq[i],-1/2))

def perform_acoustic_calculations(temp_file_path):
    # Load the serialized data
    msg=0
    with open(temp_file_path, "rb") as file:
        objects = pickle.load(file)

# print('test')
    # print(objects)

    # Access the individual objects
    floor = objects['materialf1']
    ceiling = objects['materialc1']
    separative = objects['material1']
    opening_sep = objects['openings1']
    lining_sep_em = objects['linings2']
    lining_sep_rec = objects['linings1']
    lining_wall_em = objects['liningw2']
    lining_wall_rec = objects['liningw1']
    lining_ceil_em = objects['liningc2']
    lining_ceil_rec = objects['liningc1']
    lining_floor_em = objects['liningf2']
    lining_floor_rec = objects['liningf1']
    wall_int = objects['materialw1']
    wall_facade = objects['materialfa']
    lining_facade_em = objects['liningfa2']
    lining_facade_rec = objects['liningfa1']
    l = objects['l']
    L = objects['L']
    h = objects['h']
    L2 = objects['L2']
    l_ops = objects['l_ops']
    h_ops = objects['h_ops']
    h_plenum = objects['h_plenum']
      
    room1 = Room(l,L,h) #reception room
    room2 = Room(l,L2,h) #emission room

        
    #Calculation inputs 
    
    s_floor_em = L2*l
    s_floor_rec =L*l
    s_int_em = L2*h
    s_int_rec = L*h
    s_sep = l*h
    s_opening = 0
    
    
    c = 10*np.log10(0.032*room1.calc_volume())

    ######## INSULATION BETWEEN ROOMS
    
    #Junction calculations
    
    def junction(mat1, mat2, t): #t = type de jonction, homogène, mixte, légère ou cas particulier pour séparative en double ossature
        
        M = np.log10(mat1.ms/mat2.ms) # mat1 : perpendicular material / mat2 : continuous material
        Mbis = np.log10(mat2.ms/mat1.ms) 
        K11 = []
        K12 = []
        #K22 = []
        
        for i in freq: 
            if t == 'h':
                K11.append(6.7+14.1*M+5.7*np.power(M,2))
                K12.append(6.7+5.7*np.power(M,2))
                #K22 = [0]*21
       
            if t == 'm':
                # K11.append(7.5+20*np.power(M,2)-3.3*np.log10(i/500))
                K11.append(4.7-14.1*Mbis+5.7*np.power(Mbis,2))
                K12.append(7.5+10*np.power(Mbis,2)+3.3*np.log10(i/500))
                #K22.append(4.7-14.1*M+5.7*np.power(M,2)) 
            
            if t == 'l':
                K11.append(max(10,10+20*(M)-3.3*np.log10(i/500)))
                K12.append(10+10*np.abs(M)-3.3*np.log10(i/500))
                #K22.append(max(10,10-20*M-3.3*np.log10(i/500)))
            
            if t == 'd':
                K11.append(20+max(10,10+20*(M)-3.3*np.log10(i/500)))
                K12.append(30+10*np.abs(M)-3.3*np.log10(i/500))                  
        
        return M, K11, K12 
          
    def Dvij(mat1,mat2,t,lj,l,h,L,L2): 
        
        dv11 = []
        dv12 = []
        dv21 = []
        #dv22 = []
    
       
        for idx, i in enumerate(freq):
            dv11.append(max(0,junction(mat1,mat2,t)[1][idx]-10*np.log10(lj/np.power(lj*L2*mat2.aeq[idx]*lj*L*mat2.aeq[idx],0.5))))
            dv12.append(max(0,junction(mat1,mat2,t)[2][idx]-10*np.log10(lj/np.power(lj*L2*mat2.aeq[idx]*h*l*mat1.aeq[idx],0.5))))
            dv21.append(max(0,junction(mat1,mat2,t)[2][idx]-10*np.log10(lj/np.power(lj*L*mat1.aeq[idx]*h*l*mat2.aeq[idx],0.5))))
            #dv22.append(max(0,junction(mat1,mat2)[3][idx]-10*np.log10(l/np.power(s1*mat1.eq_abs_length()[idx]*s2*mat2.eq_abs_length()[idx],0.5))))

        return dv11, dv12, dv21

    if lining_sep_em == None:
        dr_sep_em = [0]*21
    elif lining_sep_em != 'None' and (separative.name in lining_sep_em.name) is True:
        dr_sep_em = lining_sep_em.d_sri
    else:
        msg = 1

    if lining_sep_rec == None:
        dr_sep_rec = [0]*21        
    elif lining_sep_rec != 'None' and (separative.name in lining_sep_rec.name) is True:
        dr_sep_rec = lining_sep_rec.d_sri
    else: 
        msg = 1
        
    if lining_wall_em == None:
        dr_wall_em = [0]*21    
    elif lining_wall_em != 'None' and (wall_int.name in lining_wall_em.name) is True:
        dr_wall_em = lining_wall_em.d_sri
    else: 
        msg = 1

    if lining_wall_rec == None:
        dr_wall_rec = [0]*21    
    elif lining_wall_rec != 'None' and (wall_int.name in lining_wall_rec.name) is True:
        dr_wall_rec = lining_wall_rec.d_sri
    else: 
        msg = 1
       
    if lining_facade_em == None :
        dr_fac_em = [0]*21        
    elif lining_facade_em != 'None' and (wall_facade.name in lining_facade_em.name) is True:
        dr_fac_em = lining_facade_em.d_sri
    else: 
        msg = 1

    if lining_facade_rec == None :
        dr_fac_rec = [0]*21    
    elif lining_facade_rec != 'None' and (wall_facade.name in lining_facade_rec.name) is True:
        dr_fac_rec = lining_facade_rec.d_sri
    else: 
        msg = 1    
    
    if lining_floor_em == None:
        dr_floor_em = [0]*21
    else:
        dr_floor_em = lining_floor_em.d_sri
    
    if lining_floor_rec == None:
        dr_floor_rec = [0]*21
    else: 
        dr_floor_rec = lining_floor_rec.d_sri
    
    if lining_ceil_em == None:
        dr_ceil_em = [0]*21
    else: 
        dr_ceil_em = lining_ceil_em.d_sri
    
    if lining_ceil_rec == None:
        dr_ceil_rec = [0]*21
    else:
        dr_ceil_rec = lining_ceil_rec.d_sri
        dr_ceil_rec = [0]*21
       
    #direct
    
    for i in range(len(freq)):
        # print(separative.sri[i] - 10*np.log10(separative.ts[i]/ts_labo[i]))
        # print(separative.ts[i])
        if msg == 1:
            print("Erreur de définition doublage, calcul stoppé")
            # break
        else:
            if opening_sep == None:
                tau_opening_sep.append(0)
                tau_sep.append((h*L/10)*np.power(10,(-separative.sri[i]+10*np.log10(separative.ts_situ[i]/separative.ts_labo[i])-dr_sep_em[i]-dr_sep_rec[i])/10))
            else:
                tau_opening_sep.append((l_ops*h_ops/10)*(np.power(10,-opening_sep.sri[i]/10))) #Opening
                tau_sep.append((((h*L)-(l_ops*h_ops))/10)*np.power(10,-(separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))-dr_sep_em[i]-dr_sep_rec[i]/10))#Facade wall 
                
            DnT_direct.append(round(-10*np.log10(tau_opening_sep[i]+tau_sep[i]) + 10*np.log10(0.032*room1.calc_volume()),1))

        #lateraL ; floor
            
            if separative.cat == 1:
                t = 'h'
            if (separative.cat == 2 or separative.cat == 3) :
                t = 'm'
        
            Dn1_df.append(Dvij(separative,floor,t,l,l,h,L,L2)[2][i] + (dr_sep_em[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2 
                          + dr_floor_rec[i] + (floor.sri[i]-10*np.log10(floor.ts_situ[i]/floor.ts_labo[i]))/2) - 10*np.log10((np.power(s_floor_rec*s_sep,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume()))
            Dn1_ff.append(Dvij(separative,floor,t,l,l,h,L,L2)[0][i] + (dr_floor_em[i] + (floor.sri[i] - 10*np.log10(floor.ts_situ[i]/floor.ts_labo[i]))/2 
                          + dr_floor_rec[i] + (floor.sri[i]-10*np.log10(floor.ts_situ[i]/floor.ts_labo[i]))/2) - 10*np.log10((np.power(s_floor_em*s_floor_rec,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume()))
            Dn1_fd.append(Dvij(separative,floor,t,l,l,h,L,L2)[1][i] + (dr_floor_em[i] + (floor.sri[i]-10*np.log10(floor.ts_situ[i]/floor.ts_labo[i]))/2 
                          + dr_sep_rec[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2) - 10*np.log10((np.power(s_floor_em*s_sep,0.5))/10)
                          + 10*np.log10(0.032*room1.calc_volume()))
        
            DnT1.append(round(-10*np.log10(np.power(10,-Dn1_df[i]/10)+np.power(10,-Dn1_ff[i]/10)+np.power(10,-Dn1_fd[i]/10)),1))
            
        #lateral2 ; wall_int
            
            if separative.cat == 2 and ((wall_int.cat == 2) or (wall_int.cat == 3)):
                t = 'l'
            if separative.cat == 3 and ((wall_int.cat == 2) or (wall_int.cat == 3)):
                t = 'd'
                # print(t)
            if separative.cat == 2 and wall_int.cat == 1:
                t = 'm'
            if separative.cat == 1 and wall_int.cat == 1:
                t = 'h'
         
            Dn2_df.append(Dvij(separative,wall_int,t,h,l,h,L,L2)[2][i] + (dr_sep_em[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2
                          + dr_wall_rec[i] + (wall_int.sri[i] - 10*np.log10(wall_int.ts_situ[i]/wall_int.ts_labo[i]))/2) - 10*np.log10((np.power(s_sep*s_int_rec,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume()))
            Dn2_ff.append(Dvij(separative,wall_int,t,h,l,h,L,L2)[0][i] + (dr_wall_em[i] + (wall_int.sri[i] - 10*np.log10(wall_int.ts_situ[i]/wall_int.ts_labo[i]))/2 
                          + dr_wall_rec[i] + (wall_int.sri[i] - 10*np.log10(wall_int.ts_situ[i]/wall_int.ts_labo[i]))/2)-10*np.log10((np.power(s_int_em*s_int_rec,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume()))
            Dn2_fd.append(Dvij(separative,wall_int,t,h,l,h,L,L2)[1][i] + (dr_wall_em[i] + (wall_int.sri[i] - 10*np.log10(wall_int.ts_situ[i]/wall_int.ts_labo[i]))/2 
                          + dr_sep_rec[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2)-10*np.log10((np.power(s_int_em*s_sep,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume())) 
        
            DnT2.append(round(-10*np.log10(np.power(10,-Dn2_df[i]/10)+np.power(10,-Dn2_ff[i]/10)+np.power(10,-Dn2_fd[i]/10)),1))
        
        #lateral3 ; ceiling
            
            if ceiling.cat != 4:
                if separative.cat == 1:
                    t = 'h'
                if (separative.cat == 2 or separative.cat == 3):
                    t = 'm'
            
                Dn3_df.append(Dvij(separative,floor,t,l,l,h,L,L2)[2][i] + (dr_sep_em[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2 
                              + dr_ceil_rec[i] + (ceiling.sri[i] - 10*np.log10(ceiling.ts_situ[i]/ceiling.ts_labo[i]))/2) - 10*np.log10((np.power(s_floor_rec*s_sep,0.5))/10) 
                              + 10*np.log10(0.032*room1.calc_volume()))
                Dn3_ff.append(Dvij(separative,floor,t,l,l,h,L,L2)[0][i] + (dr_ceil_em[i] + (ceiling.sri[i] - 10*np.log10(ceiling.ts_situ[i]/ceiling.ts_labo[i]))/2 
                              + dr_ceil_rec[i] + (ceiling.sri[i] - 10*np.log10(ceiling.ts_situ[i]/ceiling.ts_labo[i]))/2) - 10*np.log10((np.power(s_floor_em*s_floor_rec,0.5))/10) 
                              + 10*np.log10(0.032*room1.calc_volume()))
                Dn3_fd.append(Dvij(separative,floor,t,l,l,h,L,L2)[1][i] + (dr_ceil_em[i] + (ceiling.sri[i] - 10*np.log10(ceiling.ts_situ[i]/ceiling.ts_labo[i]))/2 
                              + dr_sep_rec[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2) - 10*np.log10((np.power(s_floor_em*s_sep,0.5))/10) 
                              + 10*np.log10(0.032*room1.calc_volume()))
            
                DnT3.append(round(-10*np.log10(np.power(10,-Dn3_df[i]/10)+np.power(10,-Dn3_ff[i]/10)+np.power(10,-Dn3_fd[i]/10)),1))
            
            if ceiling.cat == 4:
                DnT3.append(round((ceiling.sri[i] + 10*np.log10(h_plenum*l/(0.68*4.2)) + 10*np.log10(22.5*22.5/(l*L*l*L2)) + 10*np.log10(0.032*room1.calc_volume())),1))
            
        #lateral4 ; wall_facade
        
            if separative.cat == 1:
                t = 'h'
            if (separative.cat == 2 or separative.cat == 3):
                t = 'm'
         
           
            Dn4_df.append(Dvij(separative,wall_facade,t,h,l,h,L,L2)[2][i] + (dr_sep_em[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2 
                          + dr_fac_rec[i] + (wall_facade.sri[i] - 10*np.log10(wall_facade.ts_situ[i]/wall_facade.ts_labo[i]))/2) - 10*np.log10((np.power(s_int_rec*s_sep,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume()))
            Dn4_ff.append(Dvij(separative,wall_facade,t,h,l,h,L,L2)[0][i] + (dr_fac_em[i] + (wall_facade.sri[i] - 10*np.log10(wall_facade.ts_situ[i]/wall_facade.ts_labo[i]))/2 
                          + dr_fac_rec[i] + (wall_facade.sri[i] - 10*np.log10(wall_facade.ts_situ[i]/wall_facade.ts_labo[i]))/2 - 10*np.log10((np.power(s_int_rec*s_int_em,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume())))
            Dn4_fd.append(Dvij(separative,wall_facade,t,h,l,h,L,L2)[1][i] + (dr_fac_em[i] + (wall_facade.sri[i] - 10*np.log10(wall_facade.ts_situ[i]/wall_facade.ts_labo[i]))/2 
                          + dr_sep_rec[i] + (separative.sri[i] - 10*np.log10(separative.ts_situ[i]/separative.ts_labo[i]))/2 - 10*np.log10((np.power(s_int_em*s_sep,0.5))/10) 
                          + 10*np.log10(0.032*room1.calc_volume())))
            
            DnT4.append(round(-10*np.log10(np.power(10,-Dn4_df[i]/10)+np.power(10,-Dn4_ff[i]/10)+np.power(10,-Dn4_fd[i]/10)),1))
            
        #Global
        
            DnT.append(round(-10*np.log10(np.power(10,-DnT_direct[i]/10)+np.power(10,-DnT1[i]/10)+np.power(10,-DnT2[i]/10)+np.power(10,-DnT3[i]/10)+np.power(10,-DnT4[i]/10)),1))
    
                
    # # Tracé du spectre
    # fig, ax = plt.subplots(figsize=(6,10))
    # ax.plot(freq, DnT)
    # ax.set_xscale("log") 
    # ax.set_xticks(freq)
    # ax.set_xticklabels(freq, rotation=45)
    # ax.set_ylim(ymin=0)
    # ax.set_title('DnT')
    # ax.grid()
# 
    if len(DnT) == 21:
        dnt_global = building.rw(DnT[3:19])
        dnt_direct = building.rw(DnT_direct[3:19])
        dnt_floor = building.rw(DnT1[3:19])
        dnt_facade = building.rw(DnT4[3:19])
        dnt_ceiling = building.rw(DnT3[3:19])
        dnt_walls = building.rw(DnT2[3:19])

    
    print ('DnT,w (C;Ctr) = %d(-%d;-%d)' % (dnt_global,dnt_global - building.rw_c(DnT[3:19]),dnt_global - building.rw_ctr(DnT[3:19])))
    print (DnT)
    print ('DnT_direct (C;Ctr) = %d(-%d;-%d)' % (dnt_direct,dnt_direct - building.rw_c(DnT_direct[3:19]),dnt_direct - building.rw_ctr(DnT_direct[3:19])))
    print (DnT_direct)
    print ('DnT_floor (C;Ctr) = %d(-%d;-%d)' % (dnt_floor,dnt_floor - building.rw_c(DnT1[3:19]),dnt_floor - building.rw_ctr(DnT1[3:19])))
    print (DnT1)
    print ('DnT_walls (C;Ctr) = %d(-%d;-%d)' % (dnt_walls,dnt_walls - building.rw_c(DnT2[3:19]),dnt_walls - building.rw_ctr(DnT2[3:19])))
    print (DnT2)    
    print ('DnT_ceiling (C;Ctr) = %d(-%d;-%d)' % (dnt_ceiling,dnt_ceiling - building.rw_c(DnT3[3:19]),dnt_ceiling - building.rw_ctr(DnT3[3:19])))
    print (DnT3)
    print ('DnT_facade (C;Ctr) = %d(-%d;-%d)' % (dnt_facade,dnt_facade - building.rw_c(DnT4[3:19]),dnt_facade - building.rw_ctr(DnT4[3:19])))
    print (DnT4)
    print(Dn2_df)

    # print(results)
if __name__ == "__main__":
    temp_file_path = sys.argv[1]
    results = perform_acoustic_calculations(temp_file_path)
    