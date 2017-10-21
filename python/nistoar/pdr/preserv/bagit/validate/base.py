"""
This module provides the base validator class
"""
from abc import ABCMeta, abstractmethod, abstractproperty

class Validator(object):
    """
    a class for validating a bag encapsulated in a directory.
    """
    __metaclass__ = ABCMeta
    
    def __init__(self, config=None):
        """
        Initialize the validator
        """
        if config is None:
            config = {}
        self.cfg = config

    @abstractmethod
    def validate(self, bag, types='ewr'):
        """
        run the embeded tests, returning a list of errors.  If the returned
        list is empty, then the bag is considered validated.  

        :param bag NISTBag:  an NISTBag instance wrapping the bag directory
        :return list of ValidationError objects:  the errors that were detected.
        """
        return []

issue_types = [ "error", "warning", "recommendation" ]
ERROR = issue_types[0]
WARN  = issue_types[1]
REC   = issue_types[2]

class ValidationIssue(object):
    """
    an object capturing issues detected by a validator.  It contains attributes 
    describing the type of error, identity of the recommendation that was 
    violated, and a prose description of the violation.
    """
    ERROR = issue_types[0]
    WARN  = issue_types[1]
    REC   = issue_types[2]
    
    def __init__(self, profile, idlabel='', issuetype=ERROR, message=''):
        self._prof = profile
        self._lab = idlabel
        self._msg = message
        self.type = issuetype

    @property
    def profile(self):
        """
        The name (and version) of the BagIt profile that this error references
        """
        return self._prof
    @profile.setter
    def profile(self, name):
        self._prof = name

    @property
    def label(self):
        """
        A label that identifies the recommendation within the profile that 
        was violated.  
        """
        return self._lab
    @label.setter
    def label(self, value):
        self._lab = value

    @property
    def type(self):
        """
        return the issue type, one of ERROR, WARN, or REC
        """
        return self._type
    @type.setter
    def type(self, issuetype):
        if issuetype not in issue_types:
            raise ValueError("ValidationIssue: not a recognized issue type: "+
                             issuetype)
        self._type = issuetype

    @property
    def message(self):
        """
        the explanation of what went wrong
        """
        return self._msg
    @message.setter
    def message(self, text):
        self._msg = text

    def __str__(self):
        return "{0}: {1} {2}: {3}".format(self.type.upper(), self.profile, 
                                          self.label, self.message)

    def to_tuple(self):
        """
        return a tuple containing the issue data
        """
        return (self.type, self.profile, self.label, self.message)

    @classmethod
    def from_tuple(cls, data):
        return ValidationIssue(data[1], data[2], data[0], data[3])

class AggregatedValidator(Validator):
    """
    a Validator class that combines several validators together
    """
    def __init__(self, *validators):
        super(AggregatedValidator, self).__init__()
        self._vals = list(validators)

    def validate(self, bag):
        out = []
        for v in self._vals:
            out.extend(v.validate(bag))
        return out


class ValidatorBase(Validator):
    """
    a base class for Validator implementations.  

    This validator will recognizes all methods that begin with "test_" as
    test that can return a list of errors.  The method should accept a 
    NISTBag instance as its first argument.  
    """
    profile = None
    
    def __init__(self, config):
        super(ValidatorBase, self).__init__(config)

    def the_test_methods(self):
        """
        returns an ordered list of the method names that should be executed
        as validation tests.  This implementation will look for 'run_tests'
        and 'skip_tests' in the configuration to see if a reduced list should
        be returned.  
        """
        tests = self.all_test_methods()

        if self.cfg:
            if "include_tests" in self.cfg:
                filter = set(self.cfg['include_tests'])
                tests = [t for t in tests if t in filter]
            elif "skip_tests" in self.cfg:
                filter = set(self.cfg['skip_tests'])
                tests = [t for t in tests if t not in filter]

        return tests

    def all_test_methods(self):
        """
        returns an ordered list of names of all the possible methods that 
        can be executed as validation tests.

        This default implementation returns all methods whose name begins 
        with "test_" in arbitrary order.  Subclasses should override this 
        method if a particular order is desired or some other mechanism is 
        needed to identify tests.  
        """
        return [name for name in dir(self) if name.startswith('test_')]

    def validate(self, bag):
        out = []
        for test in self.test_methods():
            try:
                out.extend( getattr(self, test)(bag) )
            except Exception, ex:
                out.extend( ValidationIssue(self.profile, ERROR, test,
                                     "test method, {0}, raised an exception: {1}"
                                            .format(test, str(ex))) )
        return out

    def _list_payload_files(self, bag):
        out = set()
        for root, subdirs, files in os.walk(os.path.join(bag.dir, "data")):
            root = root[len(bag.dir)+1:]
            out.update([os.path.join(root, f) for f in files])
        return out

    def _err(self, label, message):
        return _VIE(self.profile, label, message) 
    def _warn(self, label, message):
        return _VIW(self.profile, label, message) 
    def _rec(self, label, message):
        return _VIR(self.profile, label, message) 

# These are convenience subclasses of ValidationIssue that allows for
# briefer instantiations

class _VIE(ValidationIssue):
    def __init__(self, profile, label, message):
        super(_VIE, self).__init__(profile, label, ValidationIssue.ERROR, 
                                   message)
class _VIW(ValidationIssue):
    def __init__(self, profile, label, message):
        super(_VIW, self).__init__(profile, label, ValidationIssue.WARN, 
                                   message)
class _VIR(ValidationIssue):
    def __init__(self, profile, label, message):
        super(_VIR, self).__init__(profile, label, ValidationIssue.REC, 
                                   message)

