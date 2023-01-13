## DQN-MARL Capacity sharing solution

This folder contains the code for the training and evaluation of the DQN-MARL capacity sharing solution, including the following python scripts: 

- **training.py:** Main function for performing the training in python. 
- **evaluation.py:** Main function for performing the evaluation of trained policies. 
- **environment_5G_multipleBS.py:** Python environment based on py_environment.PyEnvironment. 
- **BS_controller.py:** BS_controller class. 
- **BS.py:** BS class. 
- **common.py:** Python script with different functions for supporting the training and evaluation operations.

Note: the developed code relies on the TF-Agents library. 

**/sample_data** includes example data to conduct the training and evaluation of the model: 
- Training data in csv file to perform the training (training_main.py). (*To be uploaded*). 
- Evaluation data in csv file to perform the evaluation (evaluation_main.py). This is also required by training.py if evaluation is performed during training.

**/sample_policies** includes example policies already learnt to test the evaluation_main.py script. 
- Saved policies by PolicySaver format of TF-Agents to held the evaluation (evaluation.py).
