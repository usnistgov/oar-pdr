"""
Utilities for managing semantic version strings that will be assigned to OAR documents 
when they are released (e.g. published).  This module implements the version convention 
used by the OAR framework.  

The centerpiece of this module is the :py:class:`Version` class which allow a version string to be 
compared for sorting or to be incremented.  
"""
import re, typing

__all__ = [ "Version", "OARVersion", "cmp_versions", "cmp_oar_versions" ]

_ver_delim = re.compile(r"[\._]")
_numeric_ver = re.compile(r"^\d+([\._]\d+)*")
_proper_ver = re.compile(_numeric_ver.pattern+'$')

class Version(object):
    """
    a version class that can facilitate comparisons
    """

    def _toint(self, field):
        try:
            return int(field)
        except ValueError:
            return field

    def __init__(self, vers):
        """
        convert a version string to a Version instance
        """
        self._vs = vers
        self.fields = [self._toint(n) for n in _ver_delim.split(self._vs)]

    def __str__(self):
        return self._vs

    def __eq__(self, other):
        if not isinstance(other, Version):
            other = Version(other)
        return self.fields == other.fields

    def __lt__(self, other):
        if not isinstance(other, Version):
            other = Version(other)
        return self.fields < other.fields

    def __le__(self, other):
        if not isinstance(other, Version):
            other = Version(other)
        return self < other or self == other

    def __ge__(self, other):
        return not (self < other)
    def __gt__(self, other):
        return not self.__le__(other)
    def __ne__(self, other):
        return not (self == other)

    @classmethod
    def is_proper_version(cls, vers):
        """
        return true if the given version string is of the form M.M.M... where
        each M is any non-negative number.   
        """
        return _proper_ver.match(vers) is not None

def cmp_versions(ver1, ver2):
    """
    compare two version strings for their order.
    :return int:  -1 if v1 < v2, 0 if v1 = v2, and +1 if v1 > v2
    """
    a = Version(ver1)
    b = Version(ver2)
    if a < b:
        return -1
    elif a == b:
        return 0
    return +1

OARVersion = typing.NewType("OARVersion", Version)

class OARVersion(Version):
    """
    a Version class that supports OAR document version label conventions.

    The OAR document version conventions are:
      * contains at least 3 numeric fields
      * an increment in the third field (from the left) represents a
        change in only the document's metadata or similar inconsequential
        change.
      * an increment in the second field represents a consequential change
        which may include a change in the attached data products.
      * an increment in the first field represenets a major shift in the 
        scope or aim of the document.  Such an increment is usually a choice 
        of the document's authors (as it implies intent) as opposed to 
        some automatically applied based on specific technical criteria.
      * a version whose last field is followed by a '+' (and additional 
        optional characters) indicate that the document is in draft form 
        and whose version to be applied at publication time has not yet been 
        set.  The version to the left of the '+' is the version of the 
        previously published version that the draft is derived from.  

    This class provides support for the above conventions for incrementing the version.  
    If simple comparison is all that is needed, then the lighterweight :py:class:`Version`
    should be used instead.  
    """

    def __init__(self, vers):
        self._sfx = ''
        m = _numeric_ver.match(vers)
        if m:
            self._sfx = vers[m.end():]
            vers = vers[:m.end()]
        super(OARVersion, self).__init__(vers)

    @property
    def suffix(self):
        return self._sfx

    def is_draft(self):
        """
        return True if this version represents 
        """
        return False if not self._sfx else self._sfx[0] == '+'

    def __eq__(self, other):
        if not isinstance(other, OARVersion):
            other = OARVersion(str(other))

        if self.suffix != other.suffix:
            return False
        return super(OARVersion, self).__eq__(other)

    def __lt__(self, other):
        if not isinstance(other, OARVersion):
            other = OARVersion(str(other))

        if self.fields == other.fields:
            if other.suffix and self.is_draft() and not other.is_draft():
                return True
            elif self.suffix and not self.is_draft() and other.is_draft():
                return False
            return self.suffix < other.suffix

        return self.fields < other.fields

    def _set(self, *flds, **kw):
        suffix=kw.get('suffix', '')
        vers = '.'.join([str(f) for f in flds]) + suffix
        new = OARVersion(vers)
        self._vs = new._vs
        self.fields = new.fields
        self._sfx = new.suffix

    def __str__(self):
        return self._vs + self._sfx

    def increment_field(self, pos):
        """
        increment the field of the version at a given position.  If this version has a suffix
        indicative of a draft (see :py:meth:`is_draft`), the suffix will be dropped. 
        :param int pos:  the 0-origin position of the field to increment.  The value can be negative to
                         change field positions relative to the end (i.e. -1 increments the last field).
                         If the ``pos`` indicates a position beyond the current number of fields, the 
                         version fields will be padded with zeros up to that position before incrementing.
        :returns:  self, allowing for chaining with, say, :py:meth:`drop_suffix`.
                   :rtype: OARVersion
        :raises IndexError: if ``pos`` is less than -1 times the number of fields in the version
        """
        origpos = pos
        if pos < 0:
            pos = len(self.fields) + pos
        if pos < 0:
            raise IndexError(origpos)
        if pos >= len(self.fields):
            for i in range(len(self.fields), pos+1):
                self.fields.append(0)

        self.fields[pos] += 1
        for i in range(pos+1, len(self.fields)):
            self.fields[i] = 0
        self._vs = '.'.join([str(f) for f in self.fields])
        if self.is_draft():
            self.drop_suffix()

        return self

    def trivial_incr(self):
        """
        increment the third field of the version representing a metadata or other trivial change
        in the document it is assinged to.
        :returns:  self, allowing for chaining with, say, :py:meth:`drop_suffix`.
                   :rtype: OARVersion
        """
        return self.increment_field(2)
        
    def minor_incr(self):
        """
        increment the third field of the version representing a data or other minor change
        in the document it is assinged to.
        :returns:  self, allowing for chaining with, say, :py:meth:`drop_suffix`.
                   :rtype: OARVersion
        """
        return self.increment_field(1)

    def major_incr(self):
        """
        increment the third field of the version representing a major change
        in the document it is assinged to.
        :returns:  self, allowing for chaining with, say, :py:meth:`drop_suffix`.
                   :rtype: OARVersion
        """
        return self.increment_field(0)

    def drop_suffix(self):
        """
        remove the suffix from this version
        :returns:  self, allowing for chaining with, say, :py:meth:`incrment_field`.
                   :rtype: OARVersion
        """
        self._sfx = ''
        return self

def cmp_oar_versions(ver1, ver2):
    """
    compare two version strings for their order using the OAR document version conventions
    :return int:  -1 if v1 < v2, 0 if v1 = v2, and +1 if v1 > v2
    """
    a = OARVersion(ver1)
    b = OARVersion(ver2)
    if a < b:
        return -1
    elif a == b:
        return 0
    return +1

    
