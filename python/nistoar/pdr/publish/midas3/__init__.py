"""
A module that provides the MIDAS-to-PDR publishing service (pubserver), Mark III version.  
It is designed to operate on SIP work areas created and managed by MIDAS for publishing.
The publishing service provides an API for pushing updated POD records that describe inputs
for building a Submission Information Package (SIP) according to the "midas3" conventions:
the SIP is a so-called "metadata bag" with an associated (external) data directory.  This 
service can also act as an intermediary that temporarily transfers update control from MIDAS
to the PDR customization service.  Finally, this service can initiate preservation process by
converting SIPs to AIPs and sending them to long term storage.  

This module deprecates the pre-publication landing page service (mdserv) which conforms to the 
"midas" (Mark I) convention.  
"""
from copy import deepcopy
from nistoar.pdr.exceptions import ConfigurationException

from ..mdserv import extract_mdserv_config

def extract_sip_config(config, siptype='midas3', service='pubserv'):
    """
    from a common configuration shared with the preservation service, 
    extract the bits needed by the metadata service.   
    """
    if 'sip_type' not in config:
        # this is the old-style configuration, return it unchangesd
        return config

    if siptype not in config['sip_type']:
        raise ConfigurationException("ppmdserver config: "+siptype+" missing as an "+
                                     "sip_type")
    out = deepcopy(config)
    del out['sip_type']
    midas = config['sip_type'][siptype]
    out.update(midas.get('common', {}))
    out.update(midas.get(service, {}))

    return out
