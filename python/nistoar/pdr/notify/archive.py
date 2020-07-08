"""
This module proivdes the implementation for archiving notifications.
"""

import os, fcntl, time
from .base import NotificationTarget, ChannelService, NotificationError
from ..exceptions import ConfigurationException, StateException

class Archiver(ChannelService):
    """
    A ChannelService for archiving notifications to disk.  This provides 
    a persistent record of sent notifications.  This writes appends a
    notification's data to a file representing a particular logical target 
    (that is, each target has a different file) in JSON format.
    """
    def __init__(self, config):
        """
        configure the Archiver.  

        The following configuration properties are supported:
        :prop dir str:  the directory where notification archive files are saved
                        (required)
        :prop pretty bool:   if true (default) the JSON output will feature 
                        indentation and newlines for readability; otherwise,
                        the JSON will be a compact single line per record.
        :prop timeout int:   the number of seconds to wait for a lock on a 
                        busy archive file (default: 60).  
        """
        super(Archiver, self).__init__(config)

        try:
            self._cdir = self.cfg['dir']
            self._pretty = self.cfg.get('pretty', True)
            self._timeout = self.cfg.get('timeout', 60)
        except KeyError as ex:
            raise ConfigurationException("Missing email notification "+
                                         "configuration property: "+str(ex))
        if not os.path.isdir(self._cdir):
            raise StateException("Notification archive dir is not an existing "+
                                 "directory: " + self._cdir)

    def archive(self, target, notice):
        """
        append the notification data to a file named after the target
        """
        try:
            with self.open_archive_file(target) as fd:
                fd.write(notice.to_json(self._pretty))
                fd.write('\n,\n')  # this line is an end-of-record marker
        except IOError as ex:
            raise NotificationError("Failed to archive notification to " +
                                    target + " due to IOError: " + str(ex), ex)

    def open_archive_file(self, target):
        """
        determine which file should be written to and open it.
        """
        tfile = os.path.join(self._cdir, target+".txt")

        # if log rotation is to be done, add it here

        # now open and lock the file
        out = open(tfile, 'a')
        t0 = time.time()
        while time.time() - t0 < self._timeout:
            try:
                fcntl.flock(out, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return out
            except IOError as ex:
                time.sleep(0.1)

        out.close()
        raise NotificationError("Unable to archive: failed to get lock on "+
                                "archive file: " + tfile)

class ArchiveTarget(NotificationTarget):
    """
    a NotificationTarget for messages that should be archived to disk.
    """
    def __init__(self, archiver, config=None, name=None, fullname=None):
        """
        initialize the target

        This class supports the following configuration properties:
        :prop name str:  the logical name for the target
        :prop fullname str:  a full name intended for display

        :param archiver Archiver: the email service to associate with this 
                         destination.  
        :param config dict:  a data for configuring this target
        :param name str: a default label to use as a unique identifier for this
                         target; this value will be overridden by the 
                         'name' property in the configuration.
        :param fullname str: a default, human-friendly name to use for 
                         identifying the target of the notification.  This can 
                         be a person's name, but more often it is a name for a 
                         functional group.  This value will be overridden by the 
                         'fullname' property in the configuration.
        """
        super(ArchiveTarget, self).__init__(archiver, config, name, fullname)

        if not isinstance(archiver, Archiver):
            raise TypeError("service is not of type Archiver")

        self.service = archiver

    def send_notice(self, notice, targetname=None, fullname=None):
        """
        send the given notice to this notification target.

        :param notice Notice:  the notification to send to the target
        :param targetname str: a name to use as the name of the target, 
                               over-riding this target's configured name.
        :param fullname str: a name to use as the full name of the target, 
                               over-riding this target's configured fullname.
        """
        if not targetname:
            targetname = self.name
        self.service.archive(targetname, notice)

        
