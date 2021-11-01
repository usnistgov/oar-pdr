"""
A module that can check the health of running services by sending test queries.  
"""
import re, textwrap
from collections import Sequence

import requests
try:
    from requests.exceptions import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

CONNECTION_FAILED = "Connection failed"

class CheckResult(object):
    """
    the results of checking a the health of a service endpoint
    """

    def __init__(self, url, method, message=None, status=CONNECTION_FAILED, ok=None,
                 returned_text=None, returned_data=None):
        """
        initialize the public attributes of this instance that describes the result data.  
        This constructor allows one to create the result access with partial information 
        (e.g. before check is executed) and then updated attributes afterwards.
        :param str url:      the URL that was accessed to check the health of the system
        :param str method:   the HTTP method that was applied to access the URL
        :param str message:  a message summarizing a conclusion about the test results (e.g.
                             what it means if the test failed).
        :param str status:   Normally, this should be a string concatonation of the return 
                             HTTP status number and status message; however, if the service
                             never responds, it may have some other message it in.  The 
                             default (appropriate for a non-response from the service) is 
                             "Connection failed".
        :param bool ok:      A boolean indicating whether the service responded with a
                             healthy response.  
        :param str returned_text:  The plain-text format of the response contents.  This 
                             should be empty if the HTTP method used was "HEAD". 
        :param str returned_data:  The JSON-parsed response data.  This should be empty if 
                             the response was not in JSON format. 
        """
        self.url = url
        self.method = method
        self.message = message
        self.status = status
        self.ok = ok
        self.returned_text = returned_text
        
def check_service(url, method='HEAD', ok_status=200, failure_status=[], desc=None, cred=None, **kw):
    """
    return a CheckResult instance reporting the result of checking a service.  To be considered 
    healthy, the service must not return an HTTP status from one of the `failure_status` values.
    If given, it must match one of the `ok_status` values to be considered healthy.  This determines 
    the value of the `ok` attribute in the returned results.  
    :param str url:     the URL endpoin to access whose response determines the health of the service
    :param str method:  the HTTP method to access the URL with
    :param ok_status:   the HTTP status codes that are allowed to be considered healthy
                        :type ok_status: int or list of ints
    :param failure_status: the HTTP status codes that are not allowed to be considered healthy
                        :type ok_status: int or list of ints
    :param str desc:    a short statement that makes summarizes what a check failure means (e.g. 
                        "the XXX service is not available").  
    """
    if ok_status is None:
        ok_status = 200
    if not isinstance(ok_status, Sequence):
        ok_status = [ ok_status ]
    if failure_status is None:
        failure_status = []
    if not isinstance(failure_status, Sequence):
        failure_status = [ failure_status ]

    if not method:
        method = 'HEAD'
    if not url:
        raise ValueError("check_service(): no URL provided")

    out = CheckResult(url, method, message=desc)
    try:

        hdr={}
        if cred:
            hdr['Authorization'] = "Bearer "+cred
        resp = requests.request(method, url, header=hdr)
        if not out.message:
            out.message = resp.reason
        out.status = "%i %s" % (resp.status_code, resp.reason)
        out.ok = resp.status_code not in failure_status and resp.status_code in ok_status
        try:
            out.json = resp.json()
        except JSONDecodeError:
            out.text = resp.text

    except requests.RequestException as ex:
        out.message = str(ex)
        out.status = CONNECTION_FAILURE
        out.ok = False

    return out

def check_and_notify(services, notifier, on_failure=None, on_success=None, message=None,
                     origin=None, platform="unknown", name="unnamed"):
    """
    execute checks on the given services and send notifications about the results.  
    :param services:        the service checks to execute.  Each element is a dictionary whose 
                            keys are parameteers for the :py:method:`check_service` function.  
                            :type services: a dict or list of dicts
    :param NotificationService notifier:  the notification service to use to send a notification
    :param str on_failure:  the target to send a notification to if any one of the given 
                            service checks fail.  
    :param str on_success:  the target to send a notification to if all of the given 
                            service checks succeed.  
    :param str message:     a summarizing description of the given series of service checks
    :param origin str:      a label indicating the system sending the notification.
    :param str platform:    a label indicating the PDR system platform this health check is being 
                            run on (e.g. 'prod', 'test', etc.).  
    :param str name:        a name for this check of the given services.  
    :return:  True if all of the service checks were successful in their outcomes; False, if
              any of the checks failed.  
    """
    if not isinstance(services, Sequence):
        services = [ services ]

    # execute each service check and save the results
    res = []
    for svc in services:
        res.append(check_service(**svc))

    ok = all([s.ok for s in res])
    notifytarget = ok and on_success or not ok and on_failure
    if notifytarget:
        summary = message
        if summary is None and len(res) == 1 and res[0].message:
            if not re.match(r'^\d\d\d ', res[0].status):
                summary = res[0].status
            else:
                summary = res[0].message
        if summary is None:
            summary = "%s check failed" % name

        desc = []
        for r in res:
            bullet = []
            if not re.match(r'^\d\d\d ', r.status):
                bullet.append(r.status)
            if r.message and not r.ok:
                bullet.extend(textwrap.wrap(r.message, 76))
            bullet.append("{0} {1}".format(r.method, r.url))
            bullet.append("Response status: {0}".format(r.status))
            desc.append("\n    ".join(bullet))
        desc = "Note the following health checks alerts:\n  * " + "\n  * ".join(desc)

        notifier.alert(notifytarget, summary, desc, origin, formatted=True, platform=platform)
        return True

    return False

    

    
    
