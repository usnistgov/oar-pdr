"""
A module that provides NERDm metadata to the pre-publication landing page 
service.  It is designed to operate on SIP work areas such as MIDAS-managed
data directories used for publishing.
"""
from copy import deepcopy
from nistoar.pdr.exceptions import ConfigurationException

def extract_mdserv_config(config):
    """
    from a common configuration shared with the preservation service, 
    extract the bits needed by the metadata service.   
    """
    if 'sip_type' not in config:
        # this is the old-style configuration, return it unchangesd
        return config

    if 'midas' not in config['sip_type']:
        raise ConfigurationException("ppmdserver config: 'midas' missing as an "+
                                     "sip_type")
    out = deepcopy(config)
    del out['sip_type']
    midas = config['sip_type']['midas']
    out.update(midas.get('common', {}))
    out.update(midas.get('mdserv', {}))

    return out


