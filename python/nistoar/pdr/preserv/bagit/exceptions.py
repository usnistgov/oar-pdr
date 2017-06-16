"""
"""
from ...exceptions import PDRException

class BagItException(PDRException):
    """
    an exception occuring while interacting with a BagIt bag
    """
    def __init__(self, msg, bagname=None, cause=None, sys=None):
        """
        create the exception

        :param msg     str: the description of the error; this will be used 
                            as the full error message (it will not be altered).
        :param bagname str: the name of the bag in question
        :param cause Exception:  a caught exception that represents the 
                            underlying cause of the problem.  
        :param sys SystemInfo:  the system class the produced the exception
        """
        super(PDRException, self).__init__(msg, cause, sys)
        self.bagname = bagname

class BadBagRequest(BagItException):
    """
    an exception resulting from a request that is inconsistant with the 
    current state of a BagIt bag.  
    """
    pass

class BagProfileError(BagItException):
    """
    an exception indicating that the current state of the bag being accessed 
    is inconsistent with the NIST BagIt Profile.
    """
    pass

class BagSerializationError(BagItException):
    """
    an exception resulting from a failure serializing or unserializing
    a bag.
    """
    pass

