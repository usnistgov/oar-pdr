"""
functions for evaluating the health of the distribution cache
"""
import time
from collections import Sequence, Mapping

def unchecked_volumes(volumes, hourssince=24):
    """
    Given a list of dictionaries, each describing the status of a cache volume, return a filtered 
    list containing files that haven't been checked in a time longer that a given window.
    :param list    volumes:  a list of volume descriptions, including a "checked" property that 
                             gives the oldest integrity check time for the files in the volume, 
                             in epoch seconds.
    :param float hourssince: the amount of time (in fractional hours) that must have passed since 
                             the oldest check time for a volume to be included in the output list.
    """
    lim = time.time()*1000 - hourssince * 3600000
    return [v for v in volumes if v.get('filecount',0) > 0 and v.get('checked', 0) < lim]

def check_for_unchecked_volumes(chkres, srvresp, **kw):
    """
    a wrapper for :py:function:`unchecked_volumes` for use as a service check plug-in.  
    """
    if not chkres.data:
        chkres.ok = False
        chkres.message = "Missing JSON output"
        return chkres
    if not isinstance(chkres.data, Sequence):
        chkres.ok = False
        chkres.message = "Unexpected JSON output: not an array"
        return chkres

    unchecked = [v.get('name', '?') for v in unchecked_volumes(chkres.data, kw.get('hourssince', 24))]
    if len(unchecked) > 0:
        chkres.ok = False
        chkres.message = "Volumes have files unchecked in the last %d hours: %s" % \
                         (kw.get('hourssince', 24), ", ".join(unchecked))
    else:
        chkres.ok = True

    return chkres

def check_for_ds_version(chkres, srvresp, **kw):
    """
    a service check plug-in that tests the output of the distribution service's version endpoint.
    This is provided primarily for purposes of testing the plug-in feature of the service checker.
    """
    if not chkres.data:
        chkres.ok = False
        chkres.message = "Missing JSON output"
        return chkres
    if not isinstance(chkres.data, Mapping):
        chkres.ok = False
        chkres.message = "Unexpected JSON output: not an object"
        return chkres

    if chkres.data.get('serviceName') != "oar-dist-service":
        chkres.ok = False
        chkres.message = "Unexpected service name: " + str(chkres.data.get('serviceName'))
    elif 'version' in kw and chkres.data.get('version') != kw['version']:
        chkres.ok = False
        chkres.message = "Expected service version %s but got %s" % \
                         (str(kw['version']), str(chkres.data.get('version')))
        
    return chkres
