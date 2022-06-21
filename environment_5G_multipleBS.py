from tf_agents.specs import array_spec
from tf_agents.environments import py_environment
from tf_agents.trajectories import time_step as ts
from tf_agents.environments import tf_py_environment
import numpy as np
import tensorflow as tf
#import matlab.engine as matlab_engine
from BS import BS
from BS_controller import BS_controller
from itertools import product

'''
Simple 5G scenario considering multiple base stations. Then, each agent is associated to a Tenant. 
The environment available to each tenant is an instance of BS_controller class. 
The specifications of the environment seen by each tenant is: 
Actions: combinantions of actions {10,0,-10} for each BS --> number of combinations is 3^n_BS
Observation: [pG,sharek,share_ava] for each cell --> 3*n_BS 
'''

class environment_5G_multipleBS(py_environment.PyEnvironment):

    def __init__(self,tenant_id,bs_controller,pos_actions):

        self.tenant_id=tenant_id
        self.bs_controller=bs_controller

        self.possible_actions_cell=pos_actions
        self.n_BS=self.bs_controller.n_BS

        self.possible_actions=[val for val in product(self.possible_actions_cell,repeat=self.n_BS)]
        self.n_actions=len(self.possible_actions)
        
        #Set format of actions. Possible actions of an agent considering
        self._action_spec = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int64, minimum=0, maximum=self.n_actions-1, name='action')
        self._observation_spec = array_spec.BoundedArraySpec(
            shape=(5,self.n_BS+1), dtype=np.float32, minimum=0, name='observation')
            #For each state defined by the <pg, share_k, share_ava, 1-sum(pg), MCBR(n)> for each BS
            #Last row, SAGBR(k) and sum(SAGBR(k') for k'=!k)
        
        self.last_action=0
        self._state=self.bs_controller.get_state(self.tenant_id)
        self._episode_ended=False       

    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec

    def _reset(self):
        self.bs_controller.reset()
        self._state = self.bs_controller.get_state(self.tenant_id)
        self.last_action=0
        self._episode_ended = False
        return ts.restart(np.array(self._state, dtype=np.float32))

    def _step(self, action):   
        
        if self._episode_ended:
            # The last action ended the episode. Ignore the current action and start
            # a new episode.
            return self.reset()

        # Obtain state after action
        self._state=self.bs_controller.get_state(self.tenant_id)
        # Obtain reward after last action
        self.reward=self.bs_controller.get_reward(self.tenant_id)

        # Construct step to return
        if self._episode_ended:
            next_step=ts.termination(np.array(self._state, dtype=np.float32), self.reward)
        else:
            next_step=ts.transition(np.array(self._state, dtype=np.float32), reward=self.reward, discount=0.9)
        
        if isinstance(action,np.ndarray):
            action=action.take(0)

        #Translate action
        action_trans=self.possible_actions[action]
 
        # Apply new action
        self.bs_controller.set_action(action_trans, self.tenant_id)
        self.last_action=action

        # Return last experience turple
        return next_step

#Testing environment
'''k_tenants=2
n_BS=2

bs_controller=BS_controller(k_tenants,n_BS)
env_T1=environment_5G_multipleBS(0,bs_controller)
env_tf=tf_py_environment.TFPyEnvironment(env_T1)
print('Reset')
env_tf.reset()
print('step1')
time_step=env_tf.step(0)
bs_controller.run()
print('step2')
time_step=env_tf.step(1)
print('done')'''

