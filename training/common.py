from __future__ import absolute_import, division, print_function

import base64
#import IPython
import matplotlib
import matplotlib.pyplot as plt
#import PIL.Image
#import pyvirtualdisplay

import tensorflow as tf
import csv
from pandas import DataFrame
import pandas as pd
import numpy as np
import os
import tempfile
import zipfile
import shutil
import statistics as st

from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import dynamic_step_driver
from tf_agents.environments import tf_py_environment
from tf_agents.eval import metric_utils
from tf_agents.metrics import tf_metrics
from tf_agents.networks import q_network
from tf_agents.policies import random_tf_policy
from tf_agents.replay_buffers import tf_uniform_replay_buffer
from tf_agents.trajectories import trajectory
from tf_agents.utils import common
from environment_5G_multipleBS import environment_5G_multipleBS
from tf_agents.trajectories import time_step as ts
from tf_agents.trajectories import policy_step
from tf_agents.policies import policy_saver

from BS import BS
from BS_controller import BS_controller

tf.compat.v1.enable_v2_behavior()

tf.version.VERSION


#Function that collect a single step of an agent
def collect_step(env, policy, buffer):
  #Obtain previous time step 
  time_step = env.current_time_step()
  #Obtain last performed action and put it in policystep format
  last_action=policy_step.PolicyStep(tf.constant(np.array([env.pyenv.envs[0].last_action]))) 
  #Obtain new action to send to the environment
  action_new = policy.action(time_step)
  #Obtain state and reward after the last action and send new action to the environment 
  next_time_step = env.step(action_new.action)
  #Construct trajectory from last experience
  traj = trajectory.from_transition(time_step, last_action, next_time_step)
  
  # Add trajectory to the replay buffer
  buffer.add_batch(traj)

#Function that collect a single step of an agent
def collect_step_MA(envs, polices, buffers, bs_controller):
  for k in range(bs_controller.k_tenants):
    collect_step(envs[k],polices[k],buffers[k])
  bs_controller.run()

#Function that collects multiple steps of all agents
def collect_data_MA(envs, polices, buffers, bs_controller, steps):
  for _ in range(steps):
    collect_step_MA(envs, polices, buffers, bs_controller)

def evaluation(k_tenants,bs_controller_eval,env_tenants_tf_eval,polices,file_name,file_name_conv, n_eval):
  for ev in range(n_eval): #evaluate 10 times
    print('Starting Evaluation...')
    #Reset evaluation environment
    for k in range(k_tenants):
      env_tenants_tf_eval[k].reset() #Initialise

    for i in range(bs_controller_eval.total_steps-1):
      if i%50==0:
        print('Evaluation Step: ',i)
      for k in range(k_tenants):
        time_step = env_tenants_tf_eval[k].current_time_step()
        action_new = polices[k].action(time_step)
        env_tenants_tf_eval[k].step(action_new.action)
      bs_controller_eval.run()

    export_results(file_name+'_'+str(ev)+'.csv',bs_controller_eval)
    export_convergence_results(bs_controller_eval,file_name_conv)
    print('Finished Evaluation...')

def export_results(file_name,bs_contr):
  print('Generating output file...')

  data={}
  rows_data=bs_contr.total_steps
  #System_level parameters
  data['O_k T1']=bs_contr.O_k[0]
  data['O_k T2']=bs_contr.O_k[1]

  data['O_k_modif T1']=bs_contr.O_k_modif[0]
  data['O_k_modif T2']=bs_contr.O_k_modif[1]

  data['SThr T1']=bs_contr.Thr_k[0]
  data['SThr T2']=bs_contr.Thr_k[1]

  data['Cass_k T1']=bs_contr.C_ass_k[0]
  data['Cass_k T2']=bs_contr.C_ass_k[1]

  data['p_k T1']=bs_contr.pG_k[0]
  data['p_k T2']=bs_contr.pG_k[1]

  data['Reward T1']=bs_contr.reward_history[0]
  data['Reward T2']=bs_contr.reward_history[1]

  data['fi_SLA T1']=bs_contr.fi_SLA_history[0]
  data['fi_SLA T2']=bs_contr.fi_SLA_history[1]

  data['fi_ut T1']=bs_contr.fi_ut_history[0]
  data['fi_ut T2']=bs_contr.fi_ut_history[1]

  data['fi_extra T1']=bs_contr.fi_extra_history[0]
  data['fi_extra T2']=bs_contr.fi_extra_history[1]

  data['Total O comp T1']=bs_contr.total_O_k_history[0]
  data['Total O comp T2']=bs_contr.total_O_k_history[1]
  
  data['Beta T1']=bs_contr.beta_k_history[0]
  data['Beta T2']=bs_contr.beta_k_history[1]

  #Parameter configuration
  data['SAGBR_k T1']=bs_contr.BS_set[0].SAGBR[0] 
  data['SAGBR_k T2']=bs_contr.BS_set[0].SAGBR[1]
  data['MABR_k T1']=bs_contr.MABR[0]
  data['MABR_k T2']=bs_contr.MABR[1]
  data['SLA_rw_factor']=[bs_contr.reward_factors[0] for k in range(rows_data)]
  data['ut_rw_factor']=[bs_contr.reward_factors[1] for k in range(rows_data)]
  data['Cells Ct']=[bs_contr.Ct for k in range(rows_data)]
  data['Total Capacity']=[bs_contr.total_capacity for k in range(rows_data)]

  #Cell_level parameters
  for bs in range(bs_contr.n_BS):
    bs_name='BS'+str(bs)

    data['O_k_n T1'+bs_name]=bs_contr.BS_set[bs].O_k[0]
    data['O_k_n T2'+bs_name]=bs_contr.BS_set[bs].O_k[1]

    data['Action T1'+bs_name]=bs_contr.BS_set[bs].action_history[0]
    data['Action T2'+bs_name]=bs_contr.BS_set[bs].action_history[1]

    data['Share T1'+bs_name]=bs_contr.BS_set[bs].share_history[0][1:]
    data['Share T2'+bs_name]=bs_contr.BS_set[bs].share_history[1][1:]

    data['CThr T1'+bs_name]=bs_contr.BS_set[bs].Thr_k[0]
    data['CThr T2'+bs_name]=bs_contr.BS_set[bs].Thr_k[1]

    data['p_k_n T1'+bs_name]=bs_contr.BS_set[bs].pG_k[0]
    data['p_k_n T2'+bs_name]=bs_contr.BS_set[bs].pG_k[1]



  df_exp=DataFrame(data,columns=[*data])
  df_exp.to_csv(file_name, index=None, header=True, sep=',',mode='w',encoding='utf-8-sig')

def create_zip_file(dirname, base_filename):
  return shutil.make_archive(base_filename, 'zip', dirname)

#Function that appends a new row in the convergence csv file with average values of the evaluation
#Do not move to another script, needs the file name from this script and Ct_allcells
def export_convergence_results(bs_contr,file_name_conv):
  new_row=[]
  utilisation=[]
  for k in range(bs_contr.k_tenants):
    new_row.append(st.mean(bs_contr.reward_history[k]))
    #new_row.append(st.mean(bs_contr.fi_SLA_history[k]))
    new_row.append(st.mean(bs_contr.fi_ut_history[k]))
    new_row.append(st.mean(bs_contr.fi_extra_history[k]))
    utilisation.append(st.mean(bs_contr.Thr_k[k]))
  new_row.append(sum(utilisation)/bs_contr.total_capacity)    

  #Open the file in append mode
  with open(file_name_conv, 'a+', newline='') as write_obj:
    csv_writer=csv.writer(write_obj)
    csv_writer.writerow(new_row)

#Function to obtain data from csv file and process it
def obtain_data_from_dataset(df_data,n_rep, Ct_allcells, Ct):

  #Obtain data from each column
  dataT1=df_data.values.T[0].tolist()#Offered load Tenant 1
  dataT2=df_data.values.T[1].tolist()#Offered load Tenant 2
  SAGBR_perc_T1=df_data.values.T[2].tolist()#SAGBR Tenant 1
  SAGBR_perc_T2=df_data.values.T[3].tolist()#SAGBR Tenant 2
  MCBR_perc_T1=df_data.values.T[4].tolist()#SAGBR Tenant 1
  MCBR_perc_T2=df_data.values.T[5].tolist()#SAGBR Tenant 2

  O_k_T1=[]
  O_k_T2=[]
  SAGBR_k_T1=[]
  SAGBR_k_T2=[]
  MCBR_k_T1=[]
  MCBR_k_T2=[]

  #Process data
  for i in range(len(dataT1)): 
    for _ in range(n_rep):
      O_k_T1.append(dataT1[i]*Ct)
      O_k_T2.append(dataT2[i]*Ct)
      SAGBR_k_T1.append(SAGBR_perc_T1[i]*Ct_allcells)
      SAGBR_k_T2.append(SAGBR_perc_T2[i]*Ct_allcells)
      MCBR_k_T1.append(MCBR_perc_T1[i]*Ct)
      MCBR_k_T2.append(MCBR_perc_T2[i]*Ct)
  O_k_n=[O_k_T1,O_k_T2]
  SAGBR=[SAGBR_k_T1,SAGBR_k_T2]
  MCBR=[MCBR_k_T1,MCBR_k_T2]

  return O_k_n, SAGBR, MCBR