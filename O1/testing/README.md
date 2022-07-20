## O-DU elements for O1 testing

This folder includes the O-DU elements used for testing the NETCONF and SFTP clients of the DQN-MARL capacity sharing solution, which are the following ones: 
- ***NETCONF server container***: This is a Docker container of a NETCONF server available at https://docs.onap.org/projects/onap-integration/en/latest/simulators/nf_simulator.html that is part of the ONAP NF simulator.
- ***SFTP server container***: This is a Docker container of a SFTP server available at https://github.com/atmoz/sftp. 

The deployment of these containers can be deployed by running the **docker-compose.yml** script included here. 

Additionally, this folder includes the following elements for initializing and loading the YANG files in the NETCONF server: 
- PDTE!!!
