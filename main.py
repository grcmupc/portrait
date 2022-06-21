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
from common import *

tf.compat.v1.enable_v2_behavior()

tf.version.VERSION

def main(): 

  full_path = os.path.realpath(__file__)
  path, filename = os.path.split(full_path)
  os.chdir(path)

  #HYPERPARAMETERS DQN
  num_iterations = 20000 # @param {type:"integer"}

  initial_collect_steps = 5000  # @param {type:"integer"} 
  collect_steps_per_iteration = 1  # @param {type:"integer"}
  replay_buffer_max_length = 10000000  # @param {type:"integer"}

  max_steps=2e6


  batch_size = 512  # @param {type:"integer"}
  learning_rate = 1e-4  # @param {type:"number"}
  log_interval = 10  # @param {type:"integer"}

  n_eval = 1  # @param {type:"integer"}
  eval_interval = 100  # @param {type:"integer"}

  fc_layer_params = (100,) #neural network params

  dir_act = os.getcwd()

  #5G scenario parameters

  k_tenants=2 #Number of tenants
  n_BS=5 # Number of BSs
  Nt=65 #Number of PRBs/per BS
  Seff=5 #Average spectral efficiency per cell
  PRB_B=360e3 #PRB bandwdith
  Ct=Nt*Seff*PRB_B #Total capacity a la cell
  Ct_allcells=Ct*n_BS #Total capacity in the system
  #SAGBR=[Ct_allcells*0.6, Ct_allcells*0.4]
  #MABR=np.multiply([0.8,0.8],Ct)
  pos_actions=[-3,0,3]
  n_rep=5  #Number of repetition per sample
  chunk_size=5000 #Number of samples read in each chunk. 

  output_name='results'

  O_k_T1_train=[]
  O_k_T2_train=[]
  SAGBR_k_T1_train=[]
  SAGBR_k_T2_train=[]
  MCBR_k_T1_train=[]
  MCBR_k_T2_train=[]

  print('Loading Training dataset...')

  #Import traffic from csv for training
  data_train = pd.read_csv("load_training_with_SAGBR_MCBR_long_v3.csv",sep=';',header=None, chunksize=chunk_size) #Obtain data in chunks
  data_train_firstchunk=next(data_train)

  O_k_n_train, SAGBR_train, MCBR_train=obtain_data_from_dataset(data_train_firstchunk,n_rep,Ct_allcells, Ct)

  print('Loading Evaluation dataset...')

  #Import traffic from csv for evaluation final
  data_eval = pd.read_csv("load_eval6_journal_SAGBR_MCBR.csv",sep=';',header=None) #Obtain the whole file (shorter)

  O_k_n_eval, SAGBR_eval, MCBR_eval=obtain_data_from_dataset(data_eval,n_rep,Ct_allcells, Ct)

  #Create folder to store output results
  os.mkdir(output_name)
  path='./'+output_name+'/'


  #Create csv file for convergence evaluation
  file_name_conv=path+'convergence_'+output_name+'.csv'
  convg_data={}
  for k in range(k_tenants):
    convg_data['Avg Reward T'+str(k+1)]=[]
    #convg_data['Avg fi_SLA T'+str(k+1)]=[]
    convg_data['Avg fi_ut T'+str(k+1)]=[]
    convg_data['Avg fi_extra T'+str(k+1)]=[]
  convg_data['Avg system_utilisation']=[]
  df_exp=DataFrame(convg_data,columns=[*convg_data])
  df_exp.to_csv(file_name_conv, index=None, header=True, sep=',',mode='w',encoding='utf-8-sig')


  #INITIALIZATION of environment and agents

  print('Creating objects for training...')

  #BS controller for training
  bs_controller=BS_controller(k_tenants,n_BS,Nt,Seff,PRB_B,Ct,SAGBR_train,MCBR_train,O_k_n_train)

  #Environments for traininig
  env_tenants_py=[]
  env_tenants_tf=[]
  q_network_tenants=[]
  optimizer_tenants=[]
  train_step_counter_tenants=[]
  agents_tenants=[]
  tf_policy_savers=[]
  policy_dirs=[]
  random_policy_tenants=[]
  replay_buffer_tenants=[]


  print('Generating environments...')
  for k in range(k_tenants):
    env_tenants_py.append(environment_5G_multipleBS(k,bs_controller,pos_actions))

  #Generate tf environment for training
  for k in range(k_tenants):
    env_tenants_tf.append(tf_py_environment.TFPyEnvironment(env_tenants_py[k]))
    env_tenants_tf[k].reset() #Initialise

  #BS controller for evaluation
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

  print('Creating agents, polices and reply buffers...')
  #Create the agent,random policy and replay buffer for each of the tenants
  for k in range(k_tenants):

    #Neural network
    q_network_tenants.append(q_network.QNetwork(
        env_tenants_tf[k].observation_spec(),
        env_tenants_tf[k].action_spec(),
        fc_layer_params=fc_layer_params))

    optimizer_tenants.append(tf.compat.v1.train.AdamOptimizer(learning_rate=learning_rate))

    train_step_counter_tenants.append(tf.Variable(0))

    agents_tenants.append(dqn_agent.DqnAgent(
        env_tenants_tf[k].time_step_spec(),
        env_tenants_tf[k].action_spec(),
        q_network=q_network_tenants[k],
        optimizer=optimizer_tenants[k],
        td_errors_loss_fn=common.element_wise_squared_loss,
        train_step_counter=train_step_counter_tenants[k]))
    agents_tenants[-1].initialize() #Initialise last agent

    random_policy_tenants.append(random_tf_policy.RandomTFPolicy(env_tenants_tf[k].time_step_spec(),
                                                  env_tenants_tf[k].action_spec()))

    replay_buffer_tenants.append(tf_uniform_replay_buffer.TFUniformReplayBuffer(
        data_spec=agents_tenants[k].collect_data_spec,
        batch_size=env_tenants_tf[k].batch_size,
        max_length=replay_buffer_max_length))

    policy_dirs.append(os.path.join(dir_act, 'policy_'+output_name+'_T'+str(k)))
    tf_policy_savers.append(policy_saver.PolicySaver(agents_tenants[-1].policy))
    tf_policy_savers[-1].save(policy_dirs[-1])


  print("Collecting initial data...")

  collect_data_MA(env_tenants_tf, random_policy_tenants, replay_buffer_tenants, bs_controller, steps=initial_collect_steps)


  # Reset the train step
  for k in range(k_tenants):
    agents_tenants[k].train_step_counter.assign(0)

  #Initial evaluation
  evaluation_num=0
  eval_polices=[]
  for k in range(k_tenants):
    eval_polices.append(agents_tenants[k].policy) #Generate greedy policy to evaluate

  file_name=path+output_name+'_eval_'+str(evaluation_num)
  evaluation(k_tenants,bs_controller_eval,env_tenants_tf_eval,eval_polices,file_name,file_name_conv,n_eval) #evaluate
  evaluation_num+=1

  dataset=[]
  iterator=[]
  chunk_number=1
  for k in range(k_tenants):
    dataset.append(replay_buffer_tenants[k].as_dataset(
    num_parallel_calls=3,
    sample_batch_size=batch_size, 
    num_steps=2).prefetch(3))

    iterator.append(iter(dataset[-1]))
  '''
    for _ in range(batch_size):
      experience, unused_info = next(iterator)
      train_loss = agents_tenants[k].train(experience).loss
    step = agents_tenants[k].train_step_counter.numpy()'''


  print("Regular operation and training...")
  for it in range(bs_controller.time_step,int(max_steps)):
    if it%log_interval==0:
      print('Iteration: ',it)

    #keep reading chunks from file
    if bs_controller.time_step%(chunk_size*n_rep)==0: 
      data_train_chunk=next(data_train)
      O_k_n_train, SAGBR_train, MCBR_train=obtain_data_from_dataset(data_train_chunk,n_rep,Ct_allcells, Ct)
      bs_controller.import_data_chunk(O_k_n_train,SAGBR_train,MCBR_train)
      chunk_number+=1
      print('Chunk '+str(chunk_number)+' imported...')

    #Generate collecting polices for the iteration 
    collecting_polices=[]
    for k in range(k_tenants):
      collecting_polices.append(agents_tenants[k].collect_policy)

    # Collect a few steps using collect_policy and save to the replay buffer.
    for _ in range(collect_steps_per_iteration):
      collect_step_MA(env_tenants_tf, collecting_polices, replay_buffer_tenants, bs_controller)

    # Sample a batch of data from the buffer and update the agent's network.
    for k in range(k_tenants):
      experience, unused_info = next(iterator[k])
      train_loss = agents_tenants[k].train(experience).loss
      step = agents_tenants[k].train_step_counter.numpy()

    if it % eval_interval == 0: #Eval every eval_interval iterations
      eval_polices=[]
      for k in range(k_tenants):
        eval_polices.append(agents_tenants[k].policy) #Generate greedy policy to evaluate

        tf_policy_savers[k].save(policy_dirs[k])
        policy_zip_filename = create_zip_file(policy_dirs[k], os.path.join(path, 'policy_'+output_name+'_T'+str(k)+'_eval_'+str(evaluation_num)))    

      file_name=path+output_name+'_eval_'+str(evaluation_num)
      evaluation(k_tenants,bs_controller_eval,env_tenants_tf_eval,eval_polices,file_name,file_name_conv,n_eval)
      evaluation_num+=1
      
  #Export final evaluation
  eval_polices=[]
  for k in range(k_tenants):
    eval_polices.append(agents_tenants[k].policy) #Generate greedy policy to evaluate
    tf_policy_savers[k].save(policy_dirs[k])
    policy_zip_filename = create_zip_file(policy_dirs[k], os.path.join(path, 'policy_'+output_name+'_T'+str(k)))

  file_name=path+output_name+'_eval_'+str(evaluation_num)
  evaluation(k_tenants,bs_controller_eval,env_tenants_tf_eval,eval_polices,file_name,file_name_conv,n_eval)


if __name__ == '__main__':
  main()
