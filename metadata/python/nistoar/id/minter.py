"""
module for minting identifier strings

This module is expected to be replaced with a Java implementation.
"""

import os, abc
import pynoid as noid

class IDMinter(object):
    """
    An abstract class for creating of identifier strings.  
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def mint(self, data=None):
        """
        return an available identifier string.  
     
        It is an implementation detail as to what portion of the eventual 
        identifier this string will represent, e.g. whether it includes a 
        namespace.  

        :param data dict:  any data to associate with the identifier.  It's
                           implementation's choice to whether to support the 
                           this parameter as well as what data to expect and 
                           support.  If associating data with the identifier
                           is not supported, this parameter should be ignored.
        """
        return None

    @abc.abstractmethod
    def issued(self, id):
        """
        return true if the given identifier string is a recognized one that 
        has been previously issued.
        """
        return False

    def datafor(self, id):
        """
        return the data associated with the given ID.  None is returned if 
        no data was associated with the ID when it was minted (or data 
        association is not supported).  
        """
        return False

class IDRegistry(object):
    """
    An abstract class for storing identifier strings that have been issued
    already.

    This class is expected to be used within a IDMinter implementation.  New
    IDs are reserved from further use by calling registerID().  The IDMinter 
    can then called issued() with a proposed ID string to determine if it has 
    already been issued.  
    """

    @abc.abstractmethod
    def registerID(self, id, data=None):
        """
        register the given ID to reserve it from further use.  

        An implementation chooses whether to support the storage of data along
        with the identifier as well as what data to expect.

        :param id str:     the ID to be reserved
        :param data dict:  any data to store with the identifier.
        :raises ValueError:  if the id has already exists in storage.
        """
        raise RuntimeError("ID Registration not implemented")

    @abc.abstractmethod
    def registered(self, id):
        """
        return true if the given ID has already been registered

        :param id str:  the identifier string to check
        """
        return None

class NoidMinter(IDMinter):
    """
    A IDMinter that creates NOID-compliant identifiers

    NOID stands for Nice Opaque Identifier.  With this convention, identifier 
    strings contain only numbers and lower-case letters, excluding vowels and 
    the letter 'l'.  This convention is intented to maintain identifier 
    opaqueness while avoiding characters that are prone to human transcription 
    errors.  NOIDs may optionally include a single trailing "check character"; 
    this is essentially a 1-byte check-sum of the identifier.  It allows 
    applications to inform users that an unrecognized identifier is actually 
    invalid, possibly due to a transcription error.  

    This implementation uses pynoid to mint noid identifiers.
    """


    def __init__(self, template='zeeek', count=1, registry=None):
        """
        Create the minter

        IDs issued by this minter have a form specified by a template that 
        is defined by the pynoid module.  In general, a template has the 
        following form, expressed as a regular expression:

           (.+\.)?[zrs]?[de]+k?

        The template breaks down into the following components:

           (.+\.) -- This portion represents an optional prefix, minus the 
                     '.' delimiter, that all emitted IDs will start with.  
           [de]+  -- This portion is the core of the pattern and is represented 
                     by a sequence of 'd' and 'e' characters; the total number 
                     specifies the minimal number of characters that will appear 
                     after the optional prefix.  'd' means only a numerical digit
                     will appear in that position; 'e' means that either a digit
                     or a letter can appear.  
           [zrs]? -- The sequence of d/e characters can be preceded by a 'z', 
                     'r', or 's' character.  If this character is a 'z',
                     then the number of characters will appear after the prefix 
                     will be expanded as needed.  Without this 'z', the minter
                     would eventually run out of IDs.  The expanded digits will
                     be of the type given by the first 'd' or 'e' character.  
           k?     -- If the template ends with a 'k' character, the emitted ID
                     will be appended with an extra "check character" (see 
                     description in the class documentation).  

        :param template str:   a pynoid compliant mask; see explanation above
        :param count int:      the sequence number to start with; when no 
                               registry is used (and the default is provided)
                               it is assumed that identifiers have already been 
                               issued for sequence numbers less than this value.
        :param registry IDRegistry:  The registry to use for keeping track of 
                               previously issued IDs.
        """
        self.mask = template
        self.nextn = count
        self.registry = registry
        if not self.registry:
            self.registry = self.seqreg(self.nextn-1, self.mask)

    def mint(self, data=None):
        """
        return an available identifier string.  
     
        Whether the data parameter is supported depends on the support 
        provided by the IDRegistry instance provided at construction.  
        The default registry (used if no registry was provided) does not 
        support the data parameter; if provided, it will be ignored.  

        :param data dict:  any data to associate with the identifier.  (See
                           note above about its support.)
        """
        out = noid.mint(self.mask, self.nextn)
        self.nextn += 1
        while self.issued(out):
            out = noid.mint(self.mask, self.nextn)
            self.nextn += 1
        self.registry.registerID(out, data)
        return out
        
    def issued(self, id):
        return self.registry.registered(id)

    class seqreg(IDRegistry):
        """
        a default IDRegistry that assumes all issued IDs have an associated 
        sequence number smaller than or equal to a maximum value.
        """
        def __init__(self, initn, mask):
            self.n = initn
            self.mask = mask
        def registerID(self, id, data=None):
            n = self.seqFor(id)
            if self.n < n:
                self.n = n
        def registered(self, id):
            return self.seqFor(id) <= self.n
        def seqFor(self, id):
            """
            return the sequence number corresponding to the given ID
            """
            # start by stripping down the mask (and id) to its e-d spec
            mask = self.mask
            if mask[-1] == 'k':
                mask = mask[:-1]
                id = id[:-1]
            if '.' in mask:
                pref,mask = mask.split('.',1)
                if id.startswith(pref):
                    id = id[len(pref):]
            if mask[0] in ['z', 'r', 's']:
                mask = mask[1:]
            if len(mask) < len(id):
                mask = (mask[0] * (len(id)-len(mask))) + mask

            n = 0
            tot = 1
            for i in range(len(id)):
                try: p = noid.XDIGIT.index(id[-1-i])
                except: raise noid.ValidationError("Not a legal ID: "+id)
                n += tot * p
                tot*= ((mask[-1-i]=='d' and len(noid.DIGIT)) or len(noid.XDIGIT))
            return n
                


    
