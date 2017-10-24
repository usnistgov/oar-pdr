"""
This module provides the base validator class
"""
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import Sequence, OrderedDict

ERROR = 1
WARN  = 2
REC   = 4
ALL   = 7
PROB  = 3
issuetypes = [ ERROR, WARN, REC ]

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
    def validate(self, bag, want=ALL, results=None):
        """
        run the embeded tests, returning a list of errors.  If the returned
        list is empty, then the bag is considered validated.  

        :param bag NISTBag:  an NISTBag instance wrapping the bag directory
        :param want    int:  bit-wise and-ed codes indicating which types of 
                             test results are desired.  A validator may (but 
                             is not required to) use this value to skip 
                             execution of certain tests.
        :param results ValidationResults: a ValidationResults to add result
                             information to; if provided, this instance will 
                             be the one returned by this method.
        :return ValidationResults:  the results of applying requested validation
                             tests
        """
        return ValidationResults(bag.name, want)

class ValidationResults(object):
    """
    a container for collecting results from validation tests
    """
    def __init__(self, bagname, want=ALL):
        """
        initialize an empty set of results for a particular bag

        :param bagname str:   the name of the bag being validated
        :param want    int:   the desired types of tests to collect.  This 
                              controls the result of ok().
        """
        self.bagname = bagname
        self.want    = want

        self.results = {
            ERROR: [],
            WARN:  [],
            REC:   []
        }

    def applied(self, issuetype=ALL):
        """
        return a list of the validation tests that were applied of the
        requested types:
        :param issuetype int:  an bit-wise and-ing of the desired issue types
                               (default: ALL)
        """
        out = []
        if ERROR & ALL:
            out += self.results[ERROR]
        if WARN & ALL:
            out += self.results[WARN]
        if REC & ALL:
            out += self.results[REC]
        return out

    def count_applied(self, issuetype=ALL):
        """
        return the number of validation tests of requested types that were 
        applied to the named bag.
        """
        return len(applied(issuetype))

    def failed(self, issuetype=ALL):
        """
        return the validation tests of the requested types which failed when
        applied to the named bag.
        """
        return [issue for issue in self.applied(issuetype) if issue.failed()]
    
    def count_failed(self, issuetype=ALL):
        """
        return the number of validation tests of requested types which failed
        when applied to the named bag.
        """
        return len(self.failed(issuetype))

    def passed(self, issuetype=ALL):
        """
        return the validation tests of the requested types which passed when
        applied to the named bag.
        """
        return [issue for issue in self.applied(issuetype) if issue.passed()]
    
    def count_passed(self, issuetype=ALL):
        """
        return the number of validation tests of requested types which passed
        when applied to the named bag.
        """
        return len(self.passed(issuetype))

    def ok(self):
        """
        return True if none of the validation tests of the types specified by 
        the constructor's want parameter failed.
        """
        return self.count_failed(self.want) == 0

    def _add_issue(self, issue, type, passed, comments=None):
        """
        add an issue to this result.  The issue will be updated with its 
        type set to type and its status set to passed (True) or failed (False).

        :param issue   ValidationIssue:  the issue to add
        :param type    int:              the issue type code (ERROR, WARN, 
                                         or REC)
        :param passed  bool:             either True or False, indicating whether
                                         the issue test passed or failed
        :param comments str or list of str:  one or more comments to add to the 
                                         issue instance.
        """
        issue.type = type
        issue._passed = bool(passed)

        if comments:
            if isinstance(comments, (str, unicode)) or \
               not isinstance(comments, Sequence):
                comments = [ comments ]
            for comm in comments:
                issue.add_comment(comm)
        
        self.results[type].append(issue)

    def _err(self, issue, passed, comments=None):
        """
        add an issue to this result.  The issue will be updated with its 
        type set to ERROR and its status set to passed (True) or failed (False).

        :param issue   ValidationIssue:  the issue to add
        :param passed  bool:             either True or False, indicating whether
                                         the issue test passed or failed
        :param comments str or list of str:  one or more comments to add to the 
                                         issue instance.
        """
        self._add_issue(issue, ERROR, passed, comments)

    def _warn(self, issue, passed, comments=None):
        """
        add an issue to this result.  The issue will be updated with its 
        type set to WARN and its status set to passed (True) or failed (False).
        """
        self._add_issue(issue, WARN, passed, comments)

    def _rec(self, issue, passed, comments=None):
        """
        add an issue to this result.  The issue will be updated with its 
        type set to REC and its status set to passed (True) or failed (False).
        """
        self._add_issue(issue, REC, passed, comments)


type_labels = { ERROR: "error", WARN: "warning", REC: "recommendation" }
ERROR_LAB = type_labels[ERROR]
WARN_LAB  = type_labels[WARN]
REC_LAB   = type_labels[REC]

class ValidationIssue(object):
    """
    an object capturing issues detected by a validator.  It contains attributes 
    describing the type of error, identity of the recommendation that was 
    violated, and a prose description of the violation.
    """
    ERROR = issuetypes[0]
    WARN  = issuetypes[1]
    REC   = issuetypes[2]
    
    def __init__(self, profile, profver, idlabel='', issuetype=ERROR,
                 spec='', passed=True, comments=None):
        if comments and not isinstance(comments, Sequence):
            comments = [ comments ]

        self._prof = profile
        self._pver = profver
        self._lab = idlabel
        self._spec = spec
        self.type = issuetype
        self._passed = passed
        self._comm = []
        if comments:
            self._comm.extend([str(c) for c in comments])

    @property
    def profile(self):
        """
        The name of the BagIt profile that this issue references
        """
        return self._prof
    @profile.setter
    def profile(self, name):
        self._prof = name

    @property
    def profile_version(self):
        """
        The version of the nameed BagIt profile that this issue references
        """
        return self._pver
    @profile_version.setter
    def profile_version(self, version):
        self._pver = version

    @property
    def label(self):
        """
        A label that identifies the recommendation within the profile that 
        was tested.  
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
        if issuetype not in issuetypes:
            raise ValueError("ValidationIssue: not a recognized issue type: "+
                             issuetype)
        self._type = issuetype

    @property
    def specification(self):
        """
        the explanation of the requirement or recommendation that the test
        checks for
        """
        return self._spec
    @specification.setter
    def specification(self, text):
        self._spec = text

    def add_comment(self, text):
        """
        attach a comment to this issue.  The comment typically provides some 
        context-specific information about how a issue failed (e.g. by 
        specifying a line number)
        """
        self._comm.append(str(text))

    @property
    def comments(self):
        """
        return a tuple of strings giving comments about the issue that are
        context-specific to its application
        """
        return tuple(self._comm)

    def passed(self):
        """
        return True if this test is marked as having passed.
        """
        return self._passed

    def failed(self):
        """
        return True if this test is marked as having passed.
        """
        return not self.passed()

    def __str__(self):
        status = (self.passed() and "PASSED") or type_labels[self._type].upper()
        out = "{0}: {1} {2} {3}: {4}".format(status, self.profile, 
                                             self.profile_version,
                                             self.label, self.specification)
        if self._comm and self._comm[0]:
            out += " ({0})".format(self._comm[0])
        return out

    def to_tuple(self):
        """
        return a tuple containing the issue data
        """
        return (self.type, self.profile, self.profile_version, self.label, 
                self.specification, self._passed, self._comm)

    def to_json_obj(self):
        """
        return an OrderedDict that can be encoded into a JSON object node
        which contains the data in this ValidationIssue.
        """
        return OrderedDict([
            ("type", type_labels[self.type]),
            ("profile_name", self.profile),
            ("profile_version", self.profile_version),
            ("label", self.label),
            ("spec", self.message),
            ("comments", self.comments)
        ])

    @classmethod
    def from_tuple(cls, data):
        return ValidationIssue(data[1], data[2], data[3], data[0], 
                               data[4], data[5], data[6])

class AggregatedValidator(Validator):
    """
    a Validator class that combines several validators together
    """
    def __init__(self, *validators):
        super(AggregatedValidator, self).__init__()
        self._vals = list(validators)

    def validate(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        for v in self._vals:
            v.validate(bag, want, out)
        return out


class ValidatorBase(Validator):
    """
    a base class for Validator implementations.  

    This validator will recognizes all methods that begin with "test_" as
    test that can return a list of errors.  The method should accept a 
    NISTBag instance as its first argument.  
    """
    profile = (None, None)
    
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

    def validate(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        for test in self.the_test_methods():
            try:
                getattr(self, test)(bag, want, out) 
            except Exception, ex:
                out._err( ValidationIssue(self.profile[0], self.profile[1],
                                          "validator failure", ERROR, 
                                     "test method, {0}, raised an exception: {1}"
                                            .format(test, str(ex)), False),
                          False )
        return out

    def _list_payload_files(self, bag):
        out = set()
        for root, subdirs, files in os.walk(os.path.join(bag.dir, "data")):
            root = root[len(bag.dir)+1:]
            out.update([os.path.join(root, f) for f in files])
        return out

    def _issue(self, label, message):
        """
        return a new ValidationIssue instance that is part of this validator's
        profile.  The issue type will be set to ERROR and its status, to passed.
        """
        return ValidationIssue(self.profile[0], self.profile[1], label, ERROR,
                               message, True)


