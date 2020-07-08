"""
A package for pushing notification messages to people through various channels.

The package's client interface allows components to submit a message to be 
pushed out to configured recipients, usually as a way to alert real persons 
of a failure that requires attention.  The primary channel for pushing 
notifications is email: one can configure a list of addresses that an 
notification will be sent to.  This package, however, provides an API to send 
notifications through multiple channels.  From the client's perspective, 
notifications are sent to a named "target" representing a logical role (like 
an operator or a curator or a webmaster).  
"""
from .base import Notice, ChannelService, NotificationTarget, NotificationError
from .service import NotificationService
from . import archive
from . import email
