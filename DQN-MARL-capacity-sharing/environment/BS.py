import numpy as np

class BS():

    def __init__(self,k_tenants,BS_id,Nt,Seff,PRB_B,initial_share,SAGBR,MABR,O_k_n):
        self.k_tenants=k_tenants
        self.BS_id=BS_id
        self.Nt=Nt
        self.Seff=Seff
        self.PRB_B=PRB_B
        self.Ct=self.Nt*self.Seff*self.PRB_B
        self.share=initial_share
        self.MABR=MABR 
        self.SAGBR=SAGBR       
        self.O_k=O_k_n
        
        self.Thr_k=[[],[]]
        self.pG_k=[[],[]]
        self.time_step=0 #number of time steps performed
        self.time_step_chunk=0
        self.total_steps=len(self.O_k[0])
        #self.reward_factors=[0.3,0.2,0.5]

        self.SThr=[[],[]]

        #Params to evaluate
        
        self.action_history=[[0],[0]] #It is considered that the first action is 0
        self.share_history=[[0.6],[0.4]]

        
    def reset(self,share):
        self.time_step=0
        self.time_step_chunk=0
        self.share=share
        self.Thr_k=[[],[]]
        self.pG_k=[[],[]]
        self.action_history=[[0],[0]]
        self.share_history=[[0.6],[0.4]]

    def print_BS_configuration(self):
        print('CELL CONFIGURATION')
        print('Share ratios: ',self.share)
        print('Total PRBs: ', self.Nt)
        print('Average Seff: ', self.Seff)
        print('PRB Bandwidth: ', self.PRB_B)
        print('Total Capacity: ', self.Ct)


    #Get the current state
    def get_state(self,tenant):   
          
        total_pG=0
        for i in range(self.k_tenants):
            total_pG+=self.pG_k[i][-1]

        return [self.pG_k[tenant][-1],self.share[tenant],max(1-sum(self.share),0),max(1-total_pG,0)]

    #Provide return parameters [Cthr, pg_k,Ok_real, Ok_modif, C_ass_n]
    def get_performance(self,tenant):
        return [self.Thr_k[tenant][-1],self.pG_k[tenant][-1],self.O_k[tenant][self.time_step_chunk-1],min(self.O_k[tenant][self.time_step_chunk-1],self.MABR[tenant][self.time_step_chunk-1]),self.Ct*self.share[tenant]]

    #Configure a new action
    def set_action(self,action,tenant):
        self.action_history[tenant].append(action)

    def inform_system_thr(self,SThr,tenant):
        self.SThr[tenant]=SThr
        

    def apply_actions(self):
        #Compute expected share with last actions
        expected_share=np.zeros(self.k_tenants)
        last_action=np.zeros(self.k_tenants) #used to identify
        for k in range(self.k_tenants):
            expected_share[k]=self.share[k]+self.action_history[k][-1]/100
            last_action[k]=self.action_history[k][-1]
            if expected_share[k]>self.MABR[k][self.time_step_chunk]/self.Ct:
                expected_share[k]=self.MABR[k][self.time_step_chunk]/self.Ct
                last_action[k]=0
            elif expected_share[k]<0:
                expected_share[k]=0
                last_action[k]=0

        #Check if conflict
        if sum(expected_share)<=1: #No conflict
            self.share=expected_share
        else: #conflict: summation of share is larger than 1
            #If there are no enough resources, those tenants above SAGBR cannot increase their PRBs
            tenants_no_increase = [item.tolist() for item in np.where(np.array(last_action)<=0)][0] #Index of tenants that do not increase
            tenants_increase=[item.tolist() for item in np.where(np.array(last_action)>0)][0] #Index tenants that want to increase

            for k in tenants_no_increase: #Apply actions of tenants that do not ask to increase
                self.share[k]=expected_share[k]

            traffic_below=0
            for k in tenants_increase: #detect if there are tenants with traffic below SAGBR
                if self.SThr[k]<self.SAGBR[k][self.time_step_chunk]:
                    traffic_below=1

            for k in tenants_increase:
                if self.SThr[k]>self.SAGBR[k][self.time_step_chunk] and traffic_below==1: #those that are above SAGBR need to decrease if there is some that is below
                    last_action[k]=-self.action_history[k][-1]
                    expected_share[k]=self.share[k]+last_action[k]/100
                    self.share[k]=expected_share[k]
                    
            tenants_increase=[item.tolist() for item in np.where(np.array(last_action)>0)][0] #Index tenants that want to increase (update)

            if sum(self.share)<1: #If the result applying -10 and 0 actions give 1, do anything. Else:
                denom=sum([self.SAGBR[k][self.time_step_chunk] for k in tenants_increase])
                Av_share=1-sum(self.share)
                #actions_tenants_increase=[self.action_history[k][-1] for k in tenants_increase]
                action_sharing=np.zeros(self.k_tenants)
                for k in tenants_increase: 
                    action_sharing[k]=(self.SAGBR[k][self.time_step_chunk]/denom) 
                    #In case of SAC (self.action_history[k][-1]/sum(actions_tenants_increase))
                    self.share[k]=self.share[k]+Av_share*action_sharing[k]/100 #Share according to last SLA
            
        for k in range(self.k_tenants):
            self.share_history[k].append(self.share[k])



    #Execute the environment for a step
    def run(self): 

        #Apply actions set by agents in the environment
        self.apply_actions()
        
        #Obtain current slice throughput and occupation
        total_thr=0
        for k in range(self.k_tenants):
            if self.O_k[k][self.time_step_chunk]<self.share[k]*self.Ct:
                self.Thr_k[k].append(self.O_k[k][self.time_step_chunk])
                
            else:
                self.Thr_k[k].append(self.share[k]*self.Ct)
                
            total_thr+=self.Thr_k[k][-1]
        
        #Case when the total provided throughput is higher than the available reduce it proportionally
        '''if total_thr>self.Ct:
            excess=total_thr-self.Ct
            for k in range(self.k_tenants):
                self.Thr_k[k][-1]-=excess*self.Thr_k[k][-1]/total_thr'''
        
        #Compute occupation 
        for k in range(self.k_tenants):
            self.pG_k[k].append(self.Thr_k[k][-1]/self.Ct)
                     
        self.time_step+=1
        self.time_step_chunk+=1

    def import_data_chunk_BS(self, O_chunk_k_n, SAGBR_chunk, MCBR_chunk):
        self.O_k_n=O_chunk_k_n
        self.SAGBR=SAGBR_chunk
        self.MABR=MCBR_chunk
        self.time_step_chunk=0



'''
#Test functions:
bs=BS(2)
bs.print_BS_configuration()
state1_T1=bs.get_state(0)
state1_T2=bs.get_state(1)
bs.set_action(10,0)
bs.set_action(-20,1)
bs.run()
reward_T1=bs.get_reward(0)
reward_T2=bs.get_reward(1)
state2_T1=bs.get_state(0)
state2_T2=bs.get_state(1)
print('finished')
print(bs.k_tenants)'''
