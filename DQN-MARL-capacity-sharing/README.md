## DQN-MARL Capacity sharing solution

This folder contains the code for the training and evaluation of the DQN-MARL capacity sharing solution. It contains the following: 

- **training.py:** Main function for performing the training in python. 
- **evaluation.py:** Main function for performing the evaluation of trained policies. 
- **environment_5G_multipleBS.py:** Python environment based on py_environment.PyEnvironment (required for interacting with DQN agents). 
- **BS_controller.py:** BS_controller class. 
- **BS.py:** BS class. 
- **common.py:** Python script with different functions for supporting the main operation.

Example data to run the scripts are included in the subfolder **/data**, including: 
- Training data in csv file to perform the training (training.py). 
- Evaluation data in csv file to perform the evaluation (evaluation.py). This is also required by training.py if evaluation is performed during training. 
- Saved policies by PolicySaver to held the evaluation (evaluation.py).



