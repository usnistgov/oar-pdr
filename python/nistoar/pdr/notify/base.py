"""
This module proivdes the base interface and infrastructure for the notification 
service.
"""
from datetime import datetime
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import Mapping, OrderedDict
import json

class NotificationTarget(object):
    """
    a base class for a destination to send notifications to.
    """
    __metaclass__ = ABCMeta

    def __init__(self, service, config=None, name=None, fullname=None):
        """
        initialize the target.  This implementation sets the name and fullname
        which are normally extracted from the given configuration.  Values 
        provided for these as arguments are default values that are used if 
        not set in the configuration.

        :param service ChannelService: the service to associate with this 
                         destination.  The implementation will check to ensure
                         that the service is of the right type for this target.
        :param config dict:  a configuration that can include 'name' and 
                         'fullname' properties (with the same meaning as 
                         below) as well as implementation specific properties.
        :param name str: the unique label that can be used to identify this 
                         target
        :param fullname str: a human-friendly name to use for identifying the 
                         target of the notification.  This can be a person's 
                         name, but more often it is a name for a functional 
                         group.
        """
        if config is None:
            config = {}
        if not isinstance(config, Mapping):
            raise TypeError("configuration must be a dictionary-like object")
        self._cfg = config
        self.service = service
        self.name = self._cfg.get('name', name)
        self.fullname = self._cfg.get('fullname', fullname)

    @abstractmethod
    def send_notice(self, notice):
        """
        send the given notice to this notification target.

        :param notice Notice:  the notification to send to the target
        """
        pass

class ChannelService(object):
    """
    a base class for a service that can send notifications to 
    NotificationTargets of its type.
    """
    __metaclass__ = ABCMeta

    def __init__(self, config):
        """
        initialize the service with a configuration
        """
        if not config:
            config = {}
        self.cfg = config

class Notice(object):
    """
    a notification message that should be sent to one or more targets.  
    """

    def __init__(self, type, title, desc=None, origin=None, issued=None, 
                 **mdata):
        """
        create the Notice with metadata.  The extra keywords can be arbitrary 
        data that can be added to the out-going message.  

        The information that is actually included in the delivered 
        notification is dependent on the NotificationChannel used.  Some 
        mechanisms may keep the content short and opt to include only minimal 
        information.

        :param type str:   a label indicating the type or severity of the 
                           notification.
        :param title str:  a brief title or subject for the notification
        :parma desc str or list of str:  a longer description of the 
                           reason for the notification.
        :param origin str: the name of the software component that is issuing 
                           the notification.
        :param issued str: a formatted date/time string to include; if not 
                           provided, one will be set from the current time.
        :param mdata dict: arbitrary metadata to (optionally) include
        """
        self.type = type
        self.title = title
        self.description = desc
        self.origin = origin
        if not issued:
            issued = self.now()
        self._issued = issued
        self._md = mdata.copy()

    @property
    def issued(self):
        return self._issued

    @property
    def metadata(self):
        return self._md

    def now(self):
        """
        Return a formatted time-stamp representing the current time
        """
        return datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

    def to_json(self, pretty=True):
        """
        export this notice into a JSON object
        """
        out = OrderedDict([
            ("type", self.type),
            ("title", self.title),
            ("issued", self.issued)
        ])
        if self.description:
            out['description'] = self.description
        if self.origin:
            out['origin'] = self.origin
        if self.origin:
            out['metadata'] = self.metadata

        return json.dumps(out)

    @classmethod
    def from_json(cls, data):
        """
        turn the JSON data into a Notice object
        """
        if isinstance(data, (str, unicode)):
            data = json.loads(data)
        elif hasattr(data, 'read'):
            data = json.load(data)
        if not isinstance(data, Mapping):
            raise TypeError("Notice.from_json(): arg is not JSON data")

        mdata = data.get("metadata", {})
        return Notice(data.get('type'), data.get('title'),
                      data.get('description'), data.get('origin'),
                      data.get('issued'), **mdata)
            
