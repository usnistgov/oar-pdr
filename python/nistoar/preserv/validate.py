"""
This module provides validation and assessment services on a dataset, assessing 
its readiness for bagging.
"""

import os, logging
from warnings import warn
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict, MutableMapping

from .exceptions import ConfigurationWarning, ConfigurationException

logger = logging.getLogger(__name__)

class Validater(object):
    """
    This is an abstract base class that provides the interface for a validation
    operation: the validate() function.  This function returns an assessment 
    of an OrderedDict that enumerates the operations that need to be carried 
    out to make the input dataset compliant in the eyes of this validater.
    """
    __metaclass__ = ABCMeta

    def __init__(self, desc=None):
        """
        initiate the validater with a given description
        """
        self.description = desc or ""

    @abstractmethod
    def validate(self, precursors=None):
        """
        execute the assessment on the data pointed to at construction.

        Implementations must return an Assessment object representing an 
        assessment of what needs to be done to get the data to pass validation.
        See Assessment documentation for details.

        The validater can base its outcome in part based on the results of 
        previously ran validaters.  This can be done by providing a
        dictionary where the keys are named validation operations and the 
        values are their corresponding Assessment objects.

        This implementation returns an empty Assessment indicating success, i.e.
        that no problems have been found.
        """
        return SimpleAssessment(self.description)

class SIPValidater(Validater):
    """
    This class is a base Validater class that will do its work by examining a
    Submission Information Package (SIP) contained in a given directory.  
    """

    def __init__(self, indir, desc=None):
        """
        setup the validater to examine the contents of the given directory 
        as an SIP
        """
        super(SIPValidater, self).__init__(desc)
        self.sipdir = indir


class PreservationValidater(SIPValidater):
    """
    This class applies a suite of validation operations on a Submission 
    Information Package to assess it readiness for bagging and preservation.  
    It returns its assessment in the form of an OrderedDict that enumerates 
    the operations that need to be carried out to make the dataset ready.  

    The assessment object that is an OrderedDict has keys that represent 
    labels representing operations that need to be carried out.  These keys 
    map specifically to classes that can carry out the operations.  The values 
    are dictionaries that represent the configuration on those operations.
    A configuration may be empty or it may contain keys that represent 
    specific subtasks that need to be done.  

    This class is designed to aggregate and encapsulate validation operations
    provided by other modules and classes.
    """
    DEF_DESCRIPTION = "Testing if dataset is ready for preservation"

    def __init__(self, indir, validaters=None, desc=None):
        """
        Create this SIPValidater wrapping the given list of sub-validaters.

        This class will execute validation via each of the given validater
        instances, in order.

        :param validaters OrderedDict:  an ordered set of Validater instances to 
                              delegate validation to.  The dictionary values are
                              Validater instances.  Each key represents the 
                              label for the assessment results from the 
                              validater to use in the overall assesment results
                              returned by this class's validate() function.
        """
        if desc is None:
            desc = self.DEF_DESCRIPTION
        super(PreservationValidater, self).__init__(indir, desc)
        
        if not validaters:
            warn("No specific validaters in place", ConfigurationWarning)
            validaters = OrderedDict()
        self.vd8ers = validaters


    def validate(self):
        """
        execute the assessment on the data pointed to at construction.

        This implementation will cycle through the configured validaters,
        executing them in order.

        
        """
        out = AggregatedAssessment(self.description)
        
        for name, val in self.vd8ers.iteritems():
            if not hasattr(val, 'validate'):
                raise ConfigurationException("Non-validater configured into "+
                                             "PreservationValidater with name, "+
                                             name)

            assmnt = val.validate(precursors=out.delegated())
            if assmnt:
                out.add_delegated(name, assmnt)

        return out
                
class Assessment(MutableMapping):
    """
    a container for results from a validater.

    The valid property indicates whether validation was successful or not.
    The functions, recs(), warnings(), and errors(), each return a list of 
    messages intended for end users regarding changes that can or must be 
    made to make the dataset valid.  The ops property is an OrderedDict()
    that gives as keys names of operations that must be executed in order to be 
    compliant with the validater; the values are each a dictionary used to be
    used configure that operation.  

    This class itself can be (externally) associated with a named operation 
    that can itself be executed to bring the dataset into compliance.  This
    class can be provided as the configuration dictionary to that operation.
    """

    def __init__(self, desc=None):
        """
        initialize an Assessment object
        """
        self.description = desc or ""
        self._cfg = {}

    @abstractproperty
    def valid(self):
        """
        set to True if the validation was successful.  (There may still be
        recommendations or warnings present.)
        """
        raise NotImplementedError

    def recs(self):
        """
        Return a list of recommendations resulting from the validation process.
        The valid property can still be True if there are recommendations.
        """
        return [m for m in self.iter_recs()]

    def warnings(self):
        """
        Return a list of warnings resulting from the validation process.
        The valid property can still be True if there are warnings; however,
        their existence can indicate a problem in need of attention.
        """
        return [m for m in self.iter_warnings()]

    def errors(self):
        """
        Return a list of errors resulting from the validation process.
        If any errors occur, the valid property must be set to False; however,
        the absence of errors does not require that it be True.
        """
        return [m for m in self.iter_errors()]

    def messages(self):
        """
        return a dictionary containing the various messages in this assessment.
        The dictionary returns the following keys which map to a list of strings
        representing the corresponding messages:  'recs', 'warnings', 'errors'.
        """
        return {
            "recs":     self.recs(),
            "warnings": self.warnings(),
            "errors":   self.errors()
        }

    @abstractmethod
    def iter_recs(self):
        "return an iterator that iterates through the recommendations"
        raise NotImplementedError

    @abstractmethod
    def iter_warnings(self):
        "return an iterator that iterates through the warnings"
        raise NotImplementedError

    @abstractmethod
    def iter_errors(self):
        "return an iterator that iterates through the errors"
        raise NotImplementedError

    def __getitem__(self, key):
        return self._cfg.__getitem__(key)
    def __setitem__(self, key, val):
        return self._cfg.__setitem__(key, val)
    def __delitem__(self, key):
        return self._cfg.__delitem__()
    def __len__(self):
        return self._cfg.__len__()
    def __iter__(self):
        return self._cfg.__iter__()
    def __contains__(self, key):
        return self._cfg.__contains__(key)
    

class SimpleAssessment(Assessment):
    """
    An assessment that is not an aggregation of other validation assessments

    If the ops property is set, it will also appear as a dictionary item 
    calls 'ops'.  
    """

    def __init__(self, desc=None, valid=True):
        super(SimpleAssessment, self).__init__(desc)
        self._valid = valid
        self._recs  = []
        self._warns = []
        self._errs  = []

    @property
    def valid(self):
        return self._valid

    def invalidate(self):
        """
        set the valid property to False
        """
        self._valid = False

    @property
    def ops(self):
        """
        an OrderedDict in which the keys are names of operations that can 
        executed to bring the dataset into compliance with the validater.
        Each value is a dictionary that must be used to configure that 
        operation.  The operations must be executed in the order provided
        by the returned OrderedDict.
        """
        if 'ops' not in self:
            self['ops'] = OrderedDict()
        return self.get('ops')

    def add_op(self, name, config={}):
        """
        add a named operation that must be applied to bring the data 
        into a valid state
        """
        self.ops[name] = config

    def iter_recs(self):
        return self._recs.__iter__()

    def iter_warnings(self):
        return self._warns.__iter__()

    def iter_errors(self):
        return self._errs.__iter__()

    def add_rec(self, msg):
        "a recommendation message or a list of messages"
        if not hasattr(msg, '__iter__'):
            msg = [msg]
        self._recs.extend(msg)

    def add_warning(self, msg):
        "a warning message or a list of messages"
        if not hasattr(msg, '__iter__'):
            msg = [msg]
        self._warns.extend(msg)

    def add_error(self, msg):
        "an error message or a list of messages"
        if not hasattr(msg, '__iter__'):
            msg = [msg]
        self._errs.extend(msg)

class AggregatedAssessment(Assessment):
    """
    an Assessment that aggregates data from delegated validaters
    """

    def __init__(self, desc=None):
        super(AggregatedAssessment, self).__init__(desc)

    @property
    def ops(self):
        """
        an OrderedDict in which the keys are names of operations that can 
        executed to bring the dataset into compliance with the validater.
        Each value is a dictionary that must be used to configure that 
        operation.  The operations must be executed in the order provided
        by the returned OrderedDict.
        """
        if 'ops' not in self:
            self['ops'] = OrderedDict()
        return self.get('ops')

    @property
    def delegated(self):
        return OrderedDict([(n,a) for n,a in self.ops.iteritems()
                                  if isinstance(a, Assessment) ])
        

    def add_delegated(self, name, assess):
        """
        associate an delegated assesment with an operation name
        """
        self.ops[name] = assess

    @property
    def valid(self):
        return all([a.valid for n,a in self.delegated.iteritems()])

    def iter_recs(self):
        for a in self.ops.itervalues():
            if isinstance(a, Assessment):
                for msg in a.iter_recs():
                    yield msg

    def iter_warnings(self):
        for a in self.ops.itervalues():
            if isinstance(a, Assessment):
                for msg in a.iter_warnings():
                    yield msg

    def iter_errors(self):
        for a in self.ops.itervalues():
            if isinstance(a, Assessment):
                for msg in a.iter_errors():
                    yield msg

