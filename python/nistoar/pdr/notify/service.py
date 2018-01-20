"""
A module for sending out notifications
"""
import logging, os, importlib
from copy import copy as copyobj

from .base import NotificationTarget, ChannelService, Notice
from .email import Mailer, EmailTarget
from .archive import Archiver, ArchiveTarget
from ..exceptions import ConfigurationException

log = logging.getLogger("Notify")

_channel_cls = {
    "email":   Mailer,
    "archive": Archiver
}
_target_cls = {
    "email":   EmailTarget,
    "archive": ArchiveTarget
}

class TargetManager(object):
    """
    a class that interprets channel and target configuration to set up 
    and manage targets for sending notifications.  This class is used by the 
    NotificationService to retrieve fully configured instances of 
    NotificationTargets to send notifications to.

    This class is used primarily internally to the NotificationService class;
    however, this class can be used to dynamically register new channels and 
    targets.
    """

    def __init__(self, channelscfg=None,
                 channelcls=_channel_cls, targetcls=_target_cls):
        """
        set up the manager with an initial set of ChannelServices.

        :param channelscfg dict or list of dict:  the configuration for a 
             single ChannelService or a list of ChannelService configurations.
        :param channelcls dict: a mapping of names to ChannelService class 
             objects that can be used to instantiate ChannelService instances.
        :param targetcls dict: a mapping of names to NotificationTarget class 
             objects that can be used to instantiate NotificationTarget 
             instances.
        """
        self._channelcls = copyobj(channelcls)
        self._targetcls = copyobj(targetcls)
        self._channels = {}
        self._targets = {}

    def register_channel_class(self, name, channelcls=None):
        """
        make a new ChannelService class available via the given name.  

        The class can be provided either as class object or as a string giving
        the fully-qualified class name (i.e. including the package path in 
        dot-notation).  In the latter case, the module must be discoverable on
        the current module search path.  Alternatively, one can just provide
        the class name only (i.e. as the name): the full classname then will be
        associated with the class object.  

        :param name str:  a name that a configuration can refer to the class by
        :param channelcls str or class:  The ChannelService class to associate 
             with the name.  If this is a string, it must be a fully qualified 
             name for a ChannelService implementation class.  Otherwise, this 
             must be an actual ChannelService implementation class object.  If
             not provided, the name will be assumed to be a fully qualified 
             ChannelService class name.  

        :except ImportError:  if channelcls is provided as a string but cannot
                              be imported as a class.
        """
        if not isinstance(name, (str, unicode)):
            raise TypeError("register_channel_class(): name arg not a str")
        if not channelcls:
            # name argument is also the class name
            channelcls = name

        fqclsname = '(channelcls arg)'
        if isinstance(channelcls, (str, unicode)):
            # class name is provided; import it.
            if '.' not in channelcls:
                raise ValueError("String channelcls is not a fully qualified "+
                                 "class name in dot-notation: "+channelcls)
            (modname, clsname) = channelcls.rsplit('.', 1)
            mod = importlib.import_module(modname)
            if not hasattr(mod, clsname):
                raise ImportError(clsname+" not found in "+modname+" module")
            channelcls = getattr(mod, clsname)

        if not issubclass(channelcls, ChannelService):
            raise ValueError("provided channel class is not a "+
                             "ChannelService: "+fqclsname)

        if name in self._channelcls:
            log.warn("Overriding channel class referred to as "+name)
        self._channelcls[name] = channelcls
        return channelcls

    def has_channel_class(self, name):
        """
        return True if there is a ChannelService class registered with 
        the given name.
        """
        return name in self._channelcls
            
    def register_target_class(self, name, targetcls=None):
        """
        make a new NotificationTarget class available via the given name.  

        The class can be provided either as class object or as a string giving
        the fully-qualified class name (i.e. including the package path in 
        dot-notation).  In the latter case, the module must be discoverable on
        the current module search path.  Alternatively, one can just provide
        the class name only (i.e. as the name): the full classname then will be
        associated with the class object.  

        :param name str:  a name that a configuration can refer to the class by
        :param targetcls str or class:  The NotificationTarget class to 
             associate with the name.  If this is a string, it must be a fully 
             qualified name for a NotificationTarget implementation class.  
             Otherwise, this must be an actual NotificationTarget implementation
             class object.  If not provided, the name will be assumed to be a 
             fully qualified NotificationTarget class name.  

        :except ImportError:  if targetcls is provided as a string but cannot
                              be imported as a class.
        """
        if not isinstance(name, (str, unicode)):
            raise TypeError("register_target_class(): name arg not a str")
        if not targetcls:
            # name argument is also the class name
            targetcls = name

        fqclsname = '(targetcls arg)'
        if isinstance(targetcls, (str, unicode)):
            # class name is provided; import it.
            fqclsname = targetcls
            if '.' not in targetcls:
                raise ValueError("String targetcls is not a fully qualified "+
                                 "class name in dot-notation: "+targetcls)
            (modname, clsname) = targetcls.rsplit('.', 1)
            mod = importlib.import_module(modname)
            if not hasattr(mod, clsname):
                raise ImportError(clsname+" not found in "+modname+" module")
            targetcls = getattr(mod, clsname)

        if not issubclass(targetcls, NotificationTarget):
            raise ValueError("provided target class is not a "+
                             "NotificationTarget: "+fqclsname)

        if name in self._targetcls:
            log.warn("Overriding target class referred to as "+name)
        self._targetcls[name] = targetcls
        return targetcls
            
    def has_target_class(self, name):
        """
        return True if there is a NotificationTarget class registered with 
        the given name.
        """
        return name in self._targetcls
            
    def define_channel(self, config, name=None):
        """
        Instantiate and register a ChannelService with a name as described 
        by the given channel configuration.  The configuration dictionary 
        must include a 'type' property that is a name for ChannelService 
        class (as registered via register_channel_class()).

        :param config dict: the configuration describing the desired channel
        :param name    str: a name to give to the channel (over-riding the 
                            config property, 'name').
        :return ChannelService:  the ChannelService instance registered
        """
        try:
            if not name:
                name = config['name']
            tp = config['type']
        except KeyError as ex:
            raise ConfigurationException(
                "Channel config is missing required property: "+str(ex))

        if tp not in self._channelcls and '.' in tp:
            # assume this is a fully-qualified class name
            self.register_channel_class(tp)
        if tp not in self._channelcls:
            raise ConfigurationException(
                "Channel class with name='"+name+"' is not defined")
        
        channel = self._channelcls[tp](config)
        if name in self._channels:
            log.warn("Multiple channels defined with name='"+name+
                     "'; overriding")
        self._channels[name] = channel
        return channel

    def get_channel(self, name):
        """
        return the ChannelService instance having the given name, 
        or None if the name is not recognized.
        """
        return self._channels.get(name)

    def has_channel(self, name):
        """
        return True if there a configured ChannelService available via 
        a given name
        """
        return name in self._channels

    @property
    def channel_names(self):
        """
        the names of configured ChannelService instances
        """
        return self._channels.keys()

    def define_target(self, config, name=None):
        """
        Instantiate and register a NotificationTarget with a name as described 
        by the given channel configuration.  The configuration dictionary 
        must include a 'type' property that is a name for NotificationTarget 
        class (as registered via register_channel_class()).

        :param config dict: the configuration describing the desired channel
        :param name    str: a name to give to the channel (over-riding the 
                            config property, 'name').
        :return NotificationTarget:  the NotificationTarget instance registered
        """
        try:
            if not name:
                name = config['name']
            tp = config['type']
            channel = config['channel']
        except KeyError as ex:
            raise ConfigurationException(
                "Target config is missing required property: "+str(ex))

        if tp not in self._targetcls and '.' in tp:
            # assume 'type' property is a fully-qualified class name
            self.register_target_class(tp)
        if tp not in self._targetcls:
            raise ConfigurationException(
                "Target class with name='"+name+"' is not defined")
        if channel not in self._channels:
            raise ConfigurationException("Target "+name+": Channel with name='"+
                                         channel+"' is not defined")

        target = self._targetcls[tp](self._channels[channel], config)
        if name in self._targets:
            log.warn("Multiple targets defined with name='"+name+
                     "'; overriding")
        self._targets[name] = target
        return target

    def get(self, targetname):
        """
        return the NotificationTarget instance having the given targetname, 
        or None if the name is not recognized.
        """
        return self._targets.get(targetname)

    def __getitem__(self, targetname):
        """
        equivalent to get() except that it will raise a KeyError if the 
        name is not recognized.
        """
        return self._targets[targetname]

    def has_target(self, targetname):
        """
        return True if there is a defined NotificationTarget with the given 
        targetname.
        """
        return targetname in self._targets

    @property
    def targets(self):
        """
        the names of the configured targets
        """
        return self._targets.keys()

    def __contains__(self, targetname):
        """
        equivalent to has_target()
        """
        return self.has_target(targetname)
    

class NotificationService(object):
    """
    a configuration-driven service for sending notifications through a 
    variety of communication channels.
    """

    def __init__(self, config, channel_configs=None, targetmgr=None):
        """
        Configure the service.  

        :param config dict:  the service configuration
        :param channel_configs list of dicts:  configurations for extra 
                             channels that can be leverage by the service.
        """
        if not targetmgr:
            targetmgr = TargetManager()
        self._targetmgr = targetmgr
        
        if channel_configs is None:
            channel_configs = []
        channel_cfgs = config.get('channels', []) + channel_configs
        if len(channel_cfgs) == 0:
            log.warn("No notification channels configured")

        for cfg in channel_cfgs:
            self._targetmgr.define_channel(cfg)

        target_cfgs = config.get('targets', [])
        if len(target_cfgs) == 0:
            log.warn("No notification targets configured")

        for cfg in target_cfgs:
            self._targetmgr.define_target(cfg)

        self._archiver = None
        self._targets2archive = config.get('archive_targets', [])
        if len(self._targets2archive) > 0:
            archiver = config.get('archive_channel', 'archive')
            self._archiver = self._targetmgr.get_channel(archiver)
            if not self._archiver:
                raise ConfigurationException(
                    "Config Property 'archive_targets' is set, but '" +
                    archiver + "' channel not configured.")

    @property
    def channels(self):
        """
        the names of available channels
        """
        return self._targetmgr.channel_names
              
    @property
    def targets(self):
        """
        the names of available targets.  
        """
        return self._targetmgr.targets
              
    def distribute(self, target, notice):
        """
        send a notification to a target with a given name

        :param target str or list of str:  a logical name or a list of names 
                            for groups to receive a notification
        :param notice Notice:  a fully-formed notification to distribute to 
                            the target(s).
        """
        if not isinstance(target, (list, tuple)):
            target = [target]

        failed = []
        for name in target:
            if name in self._targets2archive:
                self.archive(notice, name)
                
            try:
                tgt = self._targetmgr[name]
                tgt.send_notice(notice)
            except KeyError as ex:
                failed.append(name)
        if failed:
            if len(failed) == 1:
                msg = "requested target has not been configured: "+failed[0]
            else:
                msg = "requested targets have not been configured: " + \
                      ", ".join(failed)
            raise ValueError(msg)
        

    def notify(self, target, type, summary, desc=None, origin=None,
               metadata=None, issued=None):
        """
        send a notification to a target with a given name.  This calls 
        distribute() internally

        :param target str or list of str:  a logical name or a list of names 
                            for groups to receive a notification
        :param type   str:  a label indicating the type or severity of the 
                            notification
        :param summary str: a short title or summary for the notification
        :param desc  str or list of str:  a longer description of the 
                            notification.  When the value is a list, each 
                            string item is a paragraph.
        :param origin str:  a label indicating the system sending the 
                            notification.
        :param metadata dict:  a dictionary of additional metadata to attach 
                            to the notification.  All property values must be 
                            convertable to a string via str().
        :param issued str:  a formatted string for the timestamp when the 
                            notification condition was created.  If None,
                            the current time will be used.
        """
        if metadata is None:
            metadata = {}
        self.distribute(target,
                        Notice(type, summary, desc, origin, issued, **metadata))

    def archive(self, notice, name):
        """
        Send a notification to the configured archive.

        :param notice Notice:  the notification to send
        :param notice name:    the target name to archive it under
        """
        if not self._archiver:
            log.error("Notification archiving requested but 'archive' channel "+
                      "not configured!")
            return
        self._archiver.archive(name, notice)



