## O-DU elements for O1 testing

This folder includes the O-DU elements used for testing the NETCONF and SFTP clients of the DQN-MARL capacity sharing solution, which are the following ones: 
- ***NETCONF server container***: This is a Docker container of a NETCONF server available at https://docs.onap.org/projects/onap-integration/en/latest/simulators/nf_simulator.html that is part of the ONAP NF simulator.
- ***SFTP server container***: This is a Docker container of a SFTP server available at https://github.com/atmoz/sftp. 

#### Deployment
The deployment of these containers can be performed by running the **docker-compose.yml** script included here. 

#### NETCONF server initialization:
This folder includes the following YANG modules that need to be included in the NETCONF server to support the configuration of the *rRMPolicyDedicatedRatio per S-NSSAI*: 
- _3gpp-nr-nrm-rrmpolicy.yang
- _3gpp-common-yang-types.yang
- _3gpp-5g-common-yang-types.yang

The following files are required for initializing the NETCONF server: 
- example-models-configuration.ini: Initialization file configuration for NETCONF server that includes _3gpp-nr-nrm-rrmpolicy.yang 
- _3gpp-nr-nrm-rrmpolicy.xml: Initial *rRMPolicyDedicatedRatio per S-NSSAI* configuration values for the module _3gpp-nr-nrm-rrmpolicy.yang. 

#### PM files:
Need to be generaed by considering the XML schema *measData.xsd* included here. 
