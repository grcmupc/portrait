## DQN-MARL Capacity sharing solution

This folder contains the code for the training and evaluation of the DQN-MARL capacity sharing solution. It contains the following: 

- **training.py:** Main function for performing the training in python. 
- **evaluation.py:** Main function for performing the evaluation of trained policies. (To be uploded)
- **environment_5G_multipleBS.py:** Python environment based on py_environment.PyEnvironment (required for interacting with DQN agents). 
- **BS_controller.py:** BS_controller class. 
- **BS.py:** BS class. 
- **common.py:** Python script with different functions for supporting the main operation.

Example data to training and evaluating the model are included in the folder **/sample_data**: 
- Training data in csv file to perform the training (training.py). 
- Evaluation data in csv file to perform the evaluation (evaluation.py). This is also required by training.py if evaluation is performed during training.

Moreover, **/sample_policies** includes example policies already learnt to test the evaluation.py script. 
- Saved policies by PolicySaver format of TF-Agents to held the evaluation (evaluation.py).



