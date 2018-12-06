"""
This module proivdes the implementation for email-based notifications.
See also .base module for documentation of base classes.
"""
from __future__ import absolute_import
import os, smtplib, json, textwrap
from copy import deepcopy
from cStringIO import StringIO
from email.mime.text import MIMEText

from .base import NotificationTarget, ChannelService
from ..exceptions import ConfigurationException, StateException

def _fmtemail(empair):
    if isinstance(empair, (list, tuple)):
        return '"{0}" <{1}>'.format(*empair)
    return empair

def _rawemail(empair):
    if isinstance(empair, (list, tuple)):
        return empair[1]
    return empair

class Mailer(ChannelService):
    """
    A ChannelService that can send notifications via email
    """

    def __init__(self, config):
        """
        configure the Mailer.  

        The following configuration properties are supported:
        :prop smtp_server str:  the ISDN of the SMTP server to send email 
                                messages to (required).
        :prop smtp_port int:    the port of the SMTP server to connect to
        """
        super(Mailer, self).__init__(config)

        try:
            self._server = self.cfg['smtp_server']
            self._port = self.cfg.get('smtp_port')
        except KeyError as ex:
            raise ConfigurationException("Missing email notification "+
                                         "configuration property: "+str(ex))
        except (ValueError, TypeError) as ex:
            raise ConfigurationException("Bad email notification "+
                                         "config property value/type "+str(ex))

    def send_email(self, fromaddr, addrs, message=""):
        """
        send an email to a list of addresses

        :param from str:   the email address to indicate as the origin of the 
                           message
        :param addrs list:  a list of (raw) email addresses to send the email to
        :param message str:  the formatted contents (including the header) to 
                           send.
        """
        smtp = smtplib.SMTP(self._server, self._port)
        smtp.sendmail(fromaddr, addrs, message)
        smtp.quit()

class FakeMailer(Mailer):
    """
    A Mailer ServiceChannel that simulates sending an email.  This is intended
    mainly for testing purposes.
    """
    def __init__(self, config, cache=None):
        super(FakeMailer, self).__init__(config)
        try:
            if not cache:
                cache = config['cachedir']
        except KeyError as ex:
            raise ConfigurationException("Missing fakeemail notification "+
                                         "configuration property: "+str(ex))
        if not os.path.isdir(cache):
            raise StateException("Cache dir is not an existing directory: " +
                                 cache)
        self.cache = cache

    def send_email(self, froma, addrs, message=""):
        """
        send an email to a list of addresses

        :param from str:   the email address to indicate as the origin of the 
                           message
        :param addrs list:  a list of (raw) email addresses to send the email to
        :param message str:  the formatted contents (including the header) to 
                           send.
        """
        with open(os.path.join(self.cache, "notice.txt"), 'w') as fd:
            fd.write("To ")
            fd.write(" ".join(addrs))
            fd.write("\n")
            fd.write("From "+froma)
            fd.write("\n")
            fd.write(message)

class EmailTarget(NotificationTarget):
    """
    a NotificationTarget where the notice is sent via an email to a list of 
    addresses.
    """
    type = "email"

    def __init__(self, mailer, config, name=None, fullname=None):
        """
        initialize the target.  

        This class supports the following configuration properties:
        :prop name str:  the logical name for the target
        :prop fullname str:  a full name intended for display
        :prop from 2-list of str:  a pair of strings giving the return address
                             for outgoing message where the first is the 
                             display name and the second is the email address.
        :prop to list of 2-lists of str:  a list of primary email recipients to 
                             be used in the email's "To:" field; each element
                             is a pair of strings giving the display name of the
                             recipient and its email address.
        :prop cc list of 2-lists of str:  a list of secondary email recipients to
                             be used in the email's "Cc:" field; each element
                             is a pair of strings giving the display name of the
                             recipient and its email address.
        :prop bcc list of 2-lists of str:  a list of "blind" email recipients to 
                             be used in the email's "Bcc:" field; each element
                             is a pair of strings giving the display name of the
                             recipient and its email address.

        :param mailer Mailer: the email service to associate with this 
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
        super(EmailTarget, self).__init__(mailer, config, name, fullname)

        if not isinstance(mailer, Mailer):
            raise TypeError("service is not of type Mailer")

        try:
            self._from = self._cfg['from']
            
            self._hdr = {}
            self._hdr['To']  = deepcopy( self._cfg['to'] )
            if 'cc' in self._cfg:
                self._hdr['Cc'] = deepcopy( self._cfg['cc'] )
            if 'bcc' in self._cfg:
                self._hdr['Bcc'] = deepcopy( self._cfg['bcc'] )
        except KeyError as ex:
            raise ConfigurationException("Missing email notification "+
                                         "configuration property: "+str(ex))

        
        self._recips = []
        for key in "To Cc Bcc".split():
            if key not in self._hdr:
                continue
            
            # quick check of format
            if isinstance(self._hdr[key], (str, unicode)):
                # we're allowing the config value to be just a single
                # email address
                self._hdr[key] = [self._hdr[key]]
            if not isinstance(self._hdr[key], list):
                raise ConfigurationException("Incorrect type for email "+
                                             "notification property: "+key)

            # sneak the target's fullname into the first recipient
            if key == 'To' and self.fullname:
                if isinstance(self._hdr[key][0], (str, unicode)):
                    self._hdr[key][0] = [ self.fullname, self._hdr[key][0] ]
                else:
                    self._hdr[key][0][0] = \
                        "{0}: {1}".format(self.fullname, self._hdr[key][0][0])

            self._recips += [_rawemail(e) for e in self._hdr[key]]
            self._hdr[key] = [_fmtemail(e) for e in self._hdr[key]]
        self._hdr.pop('Bcc', [])
        
        self._hdr['From'] = _fmtemail(self._from)
        self._from = _rawemail(self._from) 

    @property
    def fromaddr(self):
        """
        the address to show as the sender of the email notification
        """
        return self._from

    @property
    def mail_header(self):
        """
        a dictionary representing data to appear in the email's header
        """
        return self._hdr

    @property
    def recipients(self):
        """
        the list of email addresses to send the notification to
        """
        return self._recips

    def send_notice(self, notice, targetname=None, fullname=None):
        """
        send the given notice to this notification target.

        :param notice Notice:  the notification to send to the target
        :param targetname str: a name to use as the name of the target, 
                               over-riding this target's configured name.
        :param fullname str: a name to use as the full name of the target, 
                               over-riding this target's configured fullname.
        """
        msg = self._make_message(self.format_subject(notice),
                                 self.format_body(notice, fullname))

        self.service.send_email(self._from, self._recips, msg)

    def _make_header(self, subject):
        hdr = self._hdr.copy()
        out = ["From: " + hdr.pop('From')]
        if 'Cc' in hdr:
            out.append("Cc: " + hdr.pop('Cc'))
        if 'Bcc' in hdr:
            hdr.pop('Bcc')

        out.append("Subject: " + subject)
        
        for key in hdr:
            out.append("{0}: {1}".format(key, hdr[key]))

        return "\n".join(out)

    def _make_message(self, subject, body):
        msg = MIMEText(body)

        hdr = self._hdr.copy()
        msg['From'] = hdr.pop('From')
        msg['To'] = ", ".join(hdr.pop('To'))
        if 'Cc' in hdr:
            msg['Cc'] = ", ".join(hdr.pop('Cc'))
        if 'Bcc' in hdr:
            hdr.pop('Bcc')
        msg['Subject'] = subject
        
        return msg.as_string(False)

    def format_body(self, notice, fullname=None):
        """
        format the body of the email from data in the notice.  The output does 
        not include the message header. 

        :param notice Notice:  the notification data to form the body from
        :param fullname  str:  use this as the full name for the recipient 
                               (default: self.fullname)
        """
        if not fullname:
            fullname = self.fullname or self.name

        out = StringIO()
        out.write("Attention: {0}\n".format(fullname))
        out.write("Notification Type: {0}\n".format(notice.type))
        if notice.origin:
            out.write("Origin: {0}\n".format(notice.origin))
        out.write("\n")
        if notice.title:
            out.write(textwrap.fill(notice.title, 80) + "\n\n")

        desc = notice.description
        if desc:
            if not isinstance(desc, list):
                desc = [desc]
            for d in desc:
                if notice.doformat:
                    d = textwrap.fill(d, 80)
                out.write(d)
                out.write('\n\n')

        out.write("Issued: {0}\n".format(notice.issued))
        for key in notice.metadata:
            val = notice.metadata[key]
            if isinstance(val, list):
                val = json.dumps(val, indent=2, separators=(', ', ': '))
            else:
                val = str(val)
            out.write("{0}: {1}\n".format(key, val))

        return out.getvalue()

    def format_subject(self, notice):
        """
        return a string to use as the email subject
        """
        return "PDR Notice: {0}: {1}".format(notice.type, notice.title)

    
        
        
        
    

