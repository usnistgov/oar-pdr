"""
This module proivdes the implementation for email-based notifications.
"""

import os, smtplib, json
from email.mime.text import MIMEText
from cStringIO import StringIO

from .base import NotificationTarget, ChannelService
from ..exceptions import ConfigurationException

def _fmtemail(empair):
    if isinstance(empair, tuple):
        return '"{0}" <{1}>' % empair
    return empair

def _rawemail(empair):
    if isinstance(empair, tuple):
        return empair[1]
    return empair

class Mailer(ChannelService):
    """
    A ChannelService that can send notifications via email
    """

    def __init__(self, config):
        super(Mailer, self).__init__(config)

        try:
            self._server = self.cfg['smtp_server']
            self._port = self.cfg.get('port')
        except KeyError as ex:
            raise ConfigurationException("Missing email notification "+
                                         "configuration property: "+str(ex))
        except (ValueError, TypeError) as ex:
            raise ConfigurationException("Bad email notification "+
                                         "config property value/type "+str(ex))

    def send_email(self, from, addrs, message=""):
        """
        send an email to a list of addresses

        :param from str:   the email address to indicate as the origin of the 
                           message
        :param addrs list:  a list of (raw) email addresses to send the email to
        :param message str:  the formatted contents (including the header) to 
                           send.
        """
        smtp = smtplib.SMTP(self._server, self._port)
        smtp.sendmail(from, addrs, message)
        smtp.quit()

class EmailTarget(NotificationTarget):
    """
    a NotificationTarget where the notice is sent via an email to a list of 
    addresses.
    """
    type = "email"

    def __init__(self, mailer, config, name=None, fullname=None):
        """
        initialize the target.  

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
            self._from = self._hdr['From']
            
            self._hdr = {}
            self._hdr['To'] = self.cfg['to']
            self._hdr['Cc'] = self.cfg.get('cc', [])
            self._hdr['Bcc'] = self.cfg.get('bcc', [])
        except KeyError as ex:
            raise ConfigurationException("Missing email notification "+
                                         "configuration property: "+str(ex))

        self._recips = []
        for key in self._hdr:
            # quick check of format
            if isinstance(self._hdr[key], (str, unicode)):
                self._hdr[key] = [self._hdr[key]]
            if not isinstance(self._hdr[key], list):
                raise ConfigurationException("Incorrect type for email "+
                                             "notification property: "+key)

            self._recips += [_rawemail(e) for e in self._hdr[key]]
            self._hdr[key] = [_fmtemail(e) for e in self._hdr[key]]
        del self._hdr['Bcc']
        
        self._hdr['From'] = _fmtemail(self._from)
        self._from = _rawemail(self._from) 

    @property
    def from(self):
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

    def send_notice(self, notice):
        """
        send the given notice to this notification target.

        :param notice Notice:  the notification to send to the target
        """
        msg = self._make_message(self.format_subject(notice),
                                 self.format_body(notice))

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
        if 'Cc' in hdr:
            msg['Cc'] = hdr.pop('Cc')
        if 'Bcc' in hdr:
            hdr.pop('Bcc')
        msg['Subject'] = subject
        
        return msg.as_string(True)

    def format_body(self, notice):
        """
        format the body of the email from data in the notice
        """
        out = StringIO()
        out.write("Notifcation Type: {0}\n".format(notice.type))
        if notice.origin:
            out.write("Origin: {0}\n".format(notice.type))
        out.write("\n")
        if notice.title:
            out.write(textwrap.fill(notice.title, 80) + "\n\n")

        desc = notice.description
        if not isinstance(desc, list):
            desc = [desc]
        for d in desc:
            out.write(textwrap.fill(desc))
            out.write('\n\n')

        out.write("Issued: {0}\n".format(notice.issued))
        for key in self._md:
            val = self._md[key]
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

    
        
        
        
    

