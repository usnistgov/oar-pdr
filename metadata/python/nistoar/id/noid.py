"""
An implementation of the NOID convention for creating identifier strings

NOID stands for Nice Opaque Identifier.  With this convention, identifier 
strings contain only numbers and lower-case letters, excluding vowels and 
the letter 'l'.  This convention is intented to maintain identifier 
opaqueness while avoiding characters that are prone to human transcription 
errors.  NOIDs may optionally include a single trailing "check character"; 
this is essentially a 1-byte check-sum of the identifier.  It allows 
applications to inform users that an unrecognized identifier is actually 
invalid, possibly due to a transcription error.  
"""

import os

