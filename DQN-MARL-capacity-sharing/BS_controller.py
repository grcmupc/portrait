from BS import BS
import numpy as np

class BS_controller():
    LOCAL=0
    GLOBAL=1
    MIXED_A=2
    MIXED_B=3
    MIXED_C=4

    def __init__(self,k_tenants,n_BS,Nt,Seff,PRB_B,Ct,SAGBR,MABR,O_k_n):
        self.k_tenants=k_tenants
        self.n_BS=n_BS

        #BS_configuration
        self.Nt=Nt
        self.Seff=Seff
        self.PRB_B=PRB_B
        self.Ct=Ct
        self.SAGBR=SAGBR
        self.MABR=MABR
        self.initial_share=[self.SAGBR[k][0]/sum([self.SAGBR[i][0] for i in range(len(self.SAGBR))]) for k in range(self.k_tenants)]
        self.reward_factors=[0,0,0.5,0.4]
        self.BS_set=[] 
        self.total_capacity=self.n_BS*self.Ct

        self.O_k_n=O_k_n

        self.initialise_BS()

        self.total_steps=len(self.O_k_n[0]) #Total time steps to perfrom
        self.time_step=0 #number of time steps performed
        self.time_step_chunk=0 #time step in the current chunk of data

        self.reward_history=[[0],[0]]
        self.fi_SLA_history=[[1],[1]]
        self.fi_ut_history=[[0],[0]]
        self.fi_extra_history=[[0],[0]]
        self.total_O_k_history=[[0],[0]]
        self.beta_k_history=[[0],[0]]
        self.Thr_k=[[],[]]#System level throughput (sumation of all BS)
        self.pG_k=[[],[]]
        self.O_k=[[],[]]
        self.O_k_modif=[[],[]]
        self.C_ass_k=[[],[]]
        

        self.run()

    def initialise_BS(self):
        for n in range(self.n_BS): 
            self.BS_set.append(BS(self.k_tenants,n,self.Nt,self.Seff,self.PRB_B,self.initial_share,self.SAGBR,self.MABR,self.O_k_n))

    def reset(self):
        for n in range(self.n_BS):
            self.BS_set[n].reset(self.initial_share)

        self.time_step=0 #number of time steps performed
        self.time_step_chunk=0 #time step in the current chunk of data
        self.reward_history=[[0],[0]]
        self.fi_SLA_history=[[1],[1]]
        self.fi_ut_history=[[0],[0]]
        self.fi_extra_history=[[0],[0]]
        self.total_O_k_history=[[0],[0]]
        self.beta_k_history=[[0],[0]]
        self.Thr_k=[[],[]]#System level throughput (sumation of all BS)
        self.pG_k=[[],[]]
        self.O_k=[[],[]]
        self.O_k_modif=[[],[]]
        self.C_ass_k=[[],[]]

        
        self.run()


        
  
    def get_state(self,tenant):
        pG_k=[]
        share_k=[]
        av_share_k=[]
        av_pg_k=[]
        MCBR=[]    
        
        for n in range(self.n_BS):
            BS_state=self.BS_set[n].get_state(tenant)
            pG_k.append(BS_state[0]) # ocupation
            share_k.append(BS_state[1]) #tenant's share
            av_share_k.append(BS_state[2]) #Share not used by any tenant
            av_pg_k.append(BS_state[3])
            MCBR.append(self.MABR[tenant][self.time_step_chunk]/self.BS_set[n].Ct)
            

        #Last row --> SAGBR(k), SAGBR_others, 0, 0 ,0
        pG_k.append(self.SAGBR[tenant][self.time_step_chunk]/self.total_capacity)
        SAGBR_others=0
        for i in range(self.k_tenants):
            if i!=tenant:
                SAGBR_others+=self.SAGBR[i][self.time_step_chunk]
        share_k.append(SAGBR_others/self.total_capacity)
        av_share_k.append(0)
        av_pg_k.append(0)
        MCBR.append(0)

        return [pG_k,share_k,av_share_k,av_pg_k,MCBR]

    def get_reward(self,tenant):
        fi_extra=1 #In the case of MIXED_C it is computed, for other cases is just one
        

        fi_SLA_tenants=np.ones(self.k_tenants)
        fi_ut=0
        fi_extra=1
        sum_Thr=0

        for k in range(self.k_tenants):
            if self.O_k_modif[k][-1]>0:
                sla_ratio=self.Thr_k[k][-1]/min(self.O_k_modif[k][-1],self.SAGBR[k][self.time_step_chunk])   
                fi_SLA_tenants[k]=min(sla_ratio,1)
                sum_Thr+=self.Thr_k[k][-1]

        fi_SLA_othertenants=1/(self.k_tenants-1)*sum(fi_SLA_tenants[k] for k in range(self.k_tenants) if k!=tenant)
        fi_SLA=fi_SLA_tenants[tenant]

        if self.C_ass_k[tenant][-1]>0:
            fi_ut=self.Thr_k[tenant][-1]/(self.C_ass_k[tenant][-1])

        total_O_k=0
        beta_k=0 #extra capacity not required by other tenants
        for k in range(self.k_tenants):
            total_O_k+=self.O_k_modif[k][-1]
            if k!=tenant:
                beta_k+=max(self.SAGBR[k][self.time_step_chunk]-self.O_k_modif[k][-1],0)


        if total_O_k>self.total_capacity:
            fi_extra=min(self.Thr_k[tenant][-1]/min(self.SAGBR[tenant][self.time_step_chunk]+beta_k,self.O_k_modif[tenant][-1]),1)
        else:
            fi_extra=self.Thr_k[tenant][-1]/self.O_k_modif[tenant][-1]

        reward=(fi_SLA**self.reward_factors[0])*(fi_SLA_othertenants**self.reward_factors[1])*(fi_ut**self.reward_factors[2])*(fi_extra**self.reward_factors[3])
        self.reward_history[tenant].append(reward)
        self.fi_SLA_history[tenant].append(fi_SLA)
        self.fi_ut_history[tenant].append(fi_ut)
        self.fi_extra_history[tenant].append(fi_extra)
        self.total_O_k_history[tenant].append(total_O_k)
        self.beta_k_history[tenant].append(beta_k)
        

        return reward


    def set_action(self,actions,tenant):
        for n in range(self.n_BS):
            self.BS_set[n].set_action(actions[n],tenant)
            self.BS_set[n].inform_system_thr(self.Thr_k[tenant][-1],tenant)

    def run(self): 
        Thr=np.zeros(self.k_tenants)
        pG=np.zeros(self.k_tenants)
        Oreal_k=np.zeros(self.k_tenants)
        Omodif_k=np.zeros(self.k_tenants)
        C_ass=np.zeros(self.k_tenants)

        for n in range(self.n_BS):
            self.BS_set[n].run()

            #Gather throughput and occupation
            for k in range(self.k_tenants):
                results=self.BS_set[n].get_performance(k)
                Thr[k]+=results[0]
                pG[k]+=results[1]
                Oreal_k[k]+=results[2]
                Omodif_k[k]+=results[3]
                C_ass[k]+=results[4]
        
        #Store performance data- Required for reward computation
        for k in range(self.k_tenants):
            self.Thr_k[k].append(Thr[k])
            self.pG_k[k].append(pG[k])
            self.O_k[k].append(Oreal_k[k])
            self.O_k_modif[k].append(Omodif_k[k])
            self.C_ass_k[k].append(C_ass[k])
        

        self.time_step+=1
        self.time_step_chunk+=1


    def import_data_chunk(self, O_chunk_k_n, SAGBR_chunk, MCBR_chunk):
        self.O_k_n=O_chunk_k_n
        self.SAGBR=SAGBR_chunk
        self.MABR=MCBR_chunk
        self.time_step_chunk=0

        for n in range(self.n_BS):
            self.BS_set[n].import_data_chunk_BS(O_chunk_k_n,SAGBR_chunk,MCBR_chunk)
        

        

            
