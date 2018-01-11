"""
A module for sending out notifications
"""

class NotificationService(object):
    """
    a configuration-driven service for sending notifications through a 
    variety of communication channels.
    """

    def __init__(self, config, channel_configs=None):
        """
        Configure the service.  

        :param config dict:  the service configuration
        :param channel_configs list of dicts:  configurations for extra 
                             channels that can be leverage by the service.
        """
        # configure the channels and the targets
        pass

    def notify(self, target, type, summary, desc=None, origin=None, issued=None):
        """
        send a notification to a target with a given name

        :param target str:  a logical name for a group to receive a notification
        :param type   str:  a label indicating the type or severity of the 
                            notification
        :param summary str: a short title or summary for the notification
        :param desc  str or list of str:  a longer description of the 
                            notification.  When the value is a list, each 
                            string item is a paragraph.
        :param origin str:  a label indicating the system sending the 
                            notification.
        :param issued str:  a formatted string for the timestamp when the 
                            notification condition was created.  If None,
                            the current time will be used.
        """
        pass

