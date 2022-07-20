## O1 interface implementation

This folder contains the code elements required to enable the DQN-MARL Capacity sharing solution to interact through the O1 interface during the inference stage. During this stage the DQN-MARL capacity sharing requires to perform the following operations: 

1. *Obtain Performance Measurements (PM) from the O-DU of each of the cells.* This is supported by establishing a SFTP connection between the DQN-MARL capacity sharing solution with each O-DU, where the DQN-MARL capacity sharing solution acts as SFTP client that obtains PM files from the SFTP server at each O-DU. 
2. *Configure the rRRMPolicyDedicatedRatio per S-NSSAI  attributes of each of the cells* (i.e., assigned capacity to each tenant in each cell) This is performed by establishing a  NETCONF connection between the DQN-MARL capacity sharing solution with each O-DU.  In this case, the DQN-MARL capacity sharing solution acts as NETCONF client that sends "edit-config" requirments to the NETCONF server deployed in each O-DU, which includes the 3GPP YANG model for RRMPolicyRatio Objects. 

To support this, the following scripts are included in this folder: 
- **SFTP_client.py**: SFTP client python code for obtaining PM files from the SFTP server at the O-DU. 
- **NETCONF_client_edit_config.py**: NETCONF client python code for performing the "edit-config" operation to configure rRRMPolicyDedicatedRatio per S-NSSAI attributes at the O-DU. 

Additionally, the following subfolders are included:

**/Sample_data/** includes sample NETCONF xml configurations of the *rRRMPolicyDedicatedRatio per S-NSSAI* and PM files. 

**/Testing/** includes the O-DU simulator used for testing the SFTP and NETCONF client codes.  


