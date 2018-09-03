"""
This distrib submodule provides a client interface to the part of the PDR 
Distribution Service that provides access to preservation bags. 
"""
import os
from .client import RESTServiceClient

class BagDistribClient(object):
    """
    a client for getting bags and information about bags that are available 
    for data collection with a given (AIP) ID.

    The PDR's preservation archive stores its data in BagIt bags which are 
    organized by their _archive information package_ (AIP) identifier.  This 
    class is designed to use the PDR's distribution service to retrieve 
    information about the available bags as well as the bags themselves.  

    The data in an PDR AIP are stored in one or more serialized bags using the 
    multibag profile.  This set of bags can encapsulate one or more versions of 
    the AIP.  Each version has its own "head" bag which lists all the other 
    bags that include data for that version.  The head bag also contains the 
    complete metadata for that version.
    """

    def __init__(self, aipid, svcclient):
        """
        create a client that accesses information about an archive 
        information package (AIP) with the given id

        :param str aipid:   the identifier for the desired AIP
        :param svcclient:   if str, it is the URL to the Distribution 
                            service endpoint; otherwise, it can be an 
                            an instance of generic client to the REST service
        :type svcclient:    ServiceClient or str 
        """
        if not aipid:
            raise ValueError("BagClient: aipid must be non-empty str")
        if isinstance(svcclient, (str, unicode)):
            svcclient = RESTServiceClient(str(svcclient))
        self.id = aipid
        self.svc = svcclient
        self.op = "/".join([self.id, "_bags"])

    def list_versions(self):
        """
        return a list of all available versions for our AIP

        This accesses the following resource from the service: <base>/<aipid>/_v
        """
        rurl = "/".join([self.op,"_v"])
        return self.svc.get_json(rurl)

    def list_all(self):
        """
        return a list of all available bags for our AIP
        :rtype: list of str giving the available bag names
        """
        return [f['name'] for f in self.describe_all()]

    def describe_all(self):
        """
        return a list of descriptions of available bags for our AIP.  Each 
        item in the list is a dictionary containing the following properties:
        :prop str name:  the name of the bag
        :prop str size:  the size of the serialized bag file in bytes
        :prop str hash:  the checksum hash of the file
        :prop str hashtype:  the algorithm used to calculate the hash (e.g. 
                         'sha256')
        """
        return self.svc.get_json(self.op)

    def list_for_version(self, version=None):
        """
        return a list of all available bags for a given version of the AIP
        :param str version:   the desired version.  If not provided, the 
                              list will be for the latest version.
        """
        return [f['name'] for f in self.describe_for_version(version)]

    def describe_for_version(self, version=None):
        """
        return a list of descriptions of all bags available for a given version 
        of the AIP

        This accesses the following resource from the service: 
        <base>/<aipid>/_v/<version>

        :param str version:   the desired version.  If not provided, the 
                              list will be for the latest version.
        """
        if not version:
            version = "latest"
        rurl = "/".join([self.op,"_v",version])
        return self.svc.get_json(rurl)

    def describe_head_for_version(self, version=None):
        """
        return a list of the available head bags for a given version of the AIP.
        Each head bag in the returned list represents a different serialized 
        form or format of the head bag's contents.  

        This accesses the following resource from the service: 
        <base>/<aipid>/_v/<version>/head

        :param str version:   the desired version.  If not provided, the 
                              name for the latest version will be returned.
        """
        if not version:
            version = "latest"
        rurl = "/".join([self.op,"_v",version,"head"])
        return self.svc.get_json(rurl)

    def head_for_version(self, version=None):
        """
        return a list of the available head bags for a given version of the AIP.
        Each head bag in the returned list represents a different serialized 
        form or format of the head bag's contents.  

        :param str version:   the desired version.  If not provided, the 
                              name for the latest version will be returned.
        """
        return [f['name'] for f in self.describe_head_for_version(version)]
    
    def stream_bag(self, bagname):
        """
        return an open file-like object for reading the serialized bag with 
        the given name.

        This accesses the following resource from the service: 
        <base>/<aipid>/<bagfilename>

        :param str bagname:  the name of the bag as given by any of the listing
                             methods in this client.  
        """
        rurl = "/".join([self.op, bagname])
        return self.svc.get_stream(rurl)

    def save_bag(self, bagname, outdir):
        """
        save the serialized bag to a specified output directory.  The output 
        filename will match the given bagname

        This accesses the following resource from the service: 
        <base>/<aipid>/<bagfilename>

        :param str bagname:  the name of the bag as given by any of the listing
                             methods in this client.  
        :param dir str:  the directory to save the serialized bag to
        """
        rurl = "/".join([self.op, bagname])
        self.svc.retrieve_file(rurl, os.path.join(outdir, bagname))

