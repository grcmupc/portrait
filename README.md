# DQN-MARL Capacity sharing solution

##WARNING: THIS IS A PRELIMINARY DRAFT - THE COMPLETE VERSION WILL BE AVAILABLE AT THE END OF JULY 2022

Welcome to the Gihub repository of the DQN-MARL capacity sharing solution, a solution for dynamically distributing the capacity in multiple RAN nodes among multiple tenants, each of them provided with a RAN slice. The capacity sharing is performed so that the traffic demands and Service Level Agreement (SLA) of the different tenant are satisfied and the resources in the different RAN nodes are efficiently used. 

Current development of the solution focuses on a Proof of Concept (PoC) of this solution, which is included in the [PORTRAIT project](https://portrait.upc.edu/). 

## Reference
A detailed description of the operation of the DQN-MARL capacity sharing solution has been published in our paper:
*   [A Multi-Agent Reinforcement Learning Approach for Capacity Sharing in Multi-Tenant Scenarios](https://ieeexplore.ieee.org/abstract/document/9497684)


## Contents

- [DQN-MARL-capacity-sharing](DQN-MARL-capacity-sharing): Includes the Python code for training and evaluating the solution. 
- [O1](O1): Includes the implementation of the O1 interface the inference of the DQN-MARL capacity sharing solution.
- [Tutorials](Tutorials): Tutorials on the major components of the solution are available. 


## Contributors
The solution has been designed and developed by Mobile Communications Research Group (GRCM) of the Department of Signal Theory and Communications (TSC) of Universitat Politècnica de Catalunya (UPC). Within the group, we would like to recognize the following individuals for their code contributions, discussions, and other work to make the DQN-MARL capacity sharing library:
- Irene Vilà
- Jordi Pérez-Romero
- Oriol Sallent
- Anna Umbert

## Citations
If you use this code, please cite it as:
```
@misc{DQN-MARL-capacity-sharing,
  title = {DQN-MARL capacity sharing solution},
  author = {Irene Vilà, Jordi-Pérez Romero, Oriol Sallent, Anna Umbert},
  howpublished = {\url{https://github.com/grcmupc/portrait}},
  url = "https://github.com/grcmupc/portrait",
  year = 2022,
  note = "[Online; accessed 16-May-2022]"
}
```
