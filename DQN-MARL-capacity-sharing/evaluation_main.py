import tensorflow as tf
import csv
from pandas import DataFrame
import pandas as pd
import numpy as np
import os
import tempfile
import zipfile 
import shutil
import io
import statistics as st


from tf_agents.environments import tf_py_environment
from BS import BS
from BS_controller import BS_controller
from environment_5G_multipleBS import environment_5G_multipleBS
from common import *

#This script allows loading policies and evaluating them considering a sample evaluation offered load.
#Requirements: 
#Loads: csv file with the offered load values, SAGBR and MCBR values for tenants 1 and 2. 
#Policies: A policy needs to be uploaded per tenant, which has to be trained previously and saved by PolicySaver. 

def main(): 

  print('Initializing configuration...')
  full_path = os.path.realpath(__file__)
  path, filename = os.path.split(full_path)
  os.chdir(path)

  k_tenants=2 #Number of tenants
  n_BS=5 # Number of BSs
  Nt=65 #Number of PRBs/per BS
  Seff=5 #Average spectral efficiency per cell
  PRB_B=360e3 #PRB bandwdith
  Ct=Nt*Seff*PRB_B #Total capacity a la cell
  Ct_allcells=Ct*n_BS #Total capacity in the system
  pos_actions=[-3,0,3]
  n_rep=5  #Number of repetition per sample
  n_eval = 1 #Number of evaluations

  file_name_evaluation='eval_sample.csv'
  eval_polices=[]
  filenames=[]

  print('Importing policies...')
  #Import policies for T1 and T2
  filenames.append('policy_results_newstrt_a3t3_5BS_NN_100_T0') #T1 --> POLICY TRAINED FOR TENANT 2
  filenames.append('policy_results_newstrt_a3t3_5BS_NN_100_T0') #T2 --> POLICY TRAINED FOR TENANT 1

  #Unzip policies
  for k in range(k_tenants):
    with zipfile.ZipFile(filenames[k]+'.zip', 'r') as zip_ref:
      zip_ref.extractall(filenames[k])
    eval_polices.append(tf.compat.v2.saved_model.load(filenames[k]))

  print('Importing data for evaluation...')
  #Import evaluation loads
  data_eval = pd.read_csv("eval_data_week_basis.csv",sep=',',header=None) #Obtain the whole file (shorter)

  print('Processing input evaluataion data...')
  O_k_n_eval, SAGBR_eval, MCBR_eval=obtain_data_from_dataset(data_eval,n_rep,Ct_allcells, Ct)

  print('Generate objects for the evaluation...')
  bs_controller_eval=BS_controller(k_tenants,n_BS,Nt,Seff,PRB_B,Ct,SAGBR_eval,MCBR_eval,O_k_n_eval)

  #Generate environments for evaluation
  env_tenants_py_eval=[]
  env_tenants_tf_eval=[]
  for k in range(k_tenants):
    env_tenants_py_eval.append(environment_5G_multipleBS(k,bs_controller_eval,pos_actions))

  #Generate tf environment for evaluation
  for k in range(k_tenants):
    env_tenants_tf_eval.append(tf_py_environment.TFPyEnvironment(env_tenants_py_eval[k]))
    env_tenants_tf_eval[k].reset() #Initialise

  print('Starting evaluation...')
  evaluation(k_tenants,bs_controller_eval,env_tenants_tf_eval,eval_polices,file_name_evaluation,None,n_eval) #evaluate

if __name__ == '__main__':
  main()




