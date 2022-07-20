#! /usr/bin/env python

import os, warnings
warnings.simplefilter("ignore", DeprecationWarning)
from ncclient import manager
import xml.etree.ElementTree as ET

full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
os.chdir(path)

def NETCONF_edit_config(host, port, user, password, v1, v2):

  snippet ='''<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><RRMPolicyRatio xmlns="urn:3gpp:sa5:_3gpp-nr-nrm-rrmpolicy"><id>1</id><attributes><rRMPolicyDedicatedRatio>%d</rRMPolicyDedicatedRatio></attributes></RRMPolicyRatio><RRMPolicyRatio xmlns="urn:3gpp:sa5:_3gpp-nr-nrm-rrmpolicy"><id>2</id><attributes><rRMPolicyDedicatedRatio>%d</rRMPolicyDedicatedRatio></attributes></RRMPolicyRatio></config>''' % (v1,v2)
  
  with manager.connect(host=host, port=port, username=user, password=password, hostkey_verify=False) as m:
    assert(":validate" in m.server_capabilities)
    m.edit_config(target='running', config=snippet, format = 'xml',test_option="set")

if __name__ == '__main__':
    host='192.168.0.2'
    port='830'
    usr='usr'
    pw='pw'

    rRMPolicyDedicatedRatio_Tenant1=57
    rRMPolicyDedicatedRatio_Tenant2=42

    NETCONF_edit_config(host, port, usr, pw, rRMPolicyDedicatedRatio_Tenant1,rRMPolicyDedicatedRatio_Tenant2)