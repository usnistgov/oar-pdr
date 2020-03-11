"""
a module for interacting with the PDR landing page customization service
"""
import os, re, logging, json
from collections import OrderedDict

import urllib
import requests

from ...exceptions import (PDRServiceException, PDRServiceAuthFailure, PDRServerError,
                           PDRServiceClientError, IDNotFound, ConfigurationException)

class CustomizationServiceClient(object):
    """
    a class for interacting with the Customization Service API
    """
    _service_name = "Customization"

    def __init__(self, config, baseurl=None, logger=None):
        """
        initialize the client

        :param dict baseurl:  the base URL for the Customization Service API; if 
                              not provided, the base URL will be pulled from the 
                              configuration data (via "service_endpoint")
        """
        self.cfg = config
        if not baseurl:
            baseurl = self.cfg.get('service_endpoint')
        if not baseurl:
            raise ConfigurationException("Missing required config paramter: " +
                                         "service_endpoint")
        self.baseurl = baseurl
        if not self.baseurl.endswith('/'):
            self.baseurl += '/'
        self._authkey = self.cfg.get('auth_key')
        if not logger:
            logger = logging.getLogger("CustomizationClient")
        self.log = logger

    def _get_json(self, relurl, resp):
        svcnm = self._service_name
        try:
            if resp.status_code >= 500:
                raise PDRServerError(svcnm, relurl, resp.status_code, resp.reason)
            elif resp.status_code == 404:
                raise IDNotFound(relurl, "draft ID not found")
            elif resp.status_code == 401:
                raise PDRServiceAuthFailure(svcnm, relurl, resp.reason)
            elif resp.status_code == 406:
                raise PDRServiceError(svcnm, relurl, resp.status_code, resp.reason,
                                      message="JSON data not available from"+
                                              " this URL (is URL correct?)")
            elif resp.status_code >= 400:
                raise PDRServiceClientError(relurl, resp.status_code, resp.reason)
            elif resp.status_code < 200 or resp.status_code > 201:
                raise PDRServerError(svcnm, relurl, resp.status_code, resp.reason,
                                     message="Unexpected response from server: {0} {1}"
                                     .format(resp.status_code, resp.reason))

            return resp.json(object_pairs_hook=OrderedDict)
        except ValueError as ex:
            if resp and resp.text and \
               ("<body" in resp.text or "<BODY" in resp.text):
                raise PDRServerError(svcnm, midasid,
                                     message="HTML returned where JSON "+
                                             "expected (is service URL correct?)",
                                     cause=ex)
            else:
                raise PDRServerError(svcnm, midasid,
                                     message="Unable to parse response as "+
                                             "JSON (is service URL correct?)",
                                     cause=ex)

    _arkprfx = re.compile(r'^ark:/\d+/')

    def _headers(self):
        hdrs = { "Accept": "application/json" }
        if self._authkey:
            hdrs['Authorization'] = "Bearer " + self._authkey
        return hdrs

    def get_draft(self, id, updates_only=False):
        """
        return the draft NERDm record associated with the given ID
        """
        id = self._arkprfx.sub('', id)
        args = ""
        if updates_only:
            args = "?view=updates"

        resp = None
        try:
            self.log.debug("Retrieving draft NERDm record from customization service for id="+id)
            resp = requests.get(self.baseurl + id + args, headers=self._headers())
            return self._get_json(id, resp)
        except requests.RequestException as ex:
            raise PDRServerError(svcnm, id, cause=ex)

    def delete_draft(self, id):
        """
        delete the current draft previously created with the given identifier
        """
        id = self._arkprfx.sub('', id)
        try:
            self.log.debug("Deleting draft NERDm record from customization service for id="+id)
            resp = requests.delete(self.baseurl + id, headers=self._headers())
            if resp.status_code >= 500:
                raise PDRServerError(svcnm, relurl, resp.status_code, resp.reason)
            if resp.status_code == 404:
                raise IDNotFound(id, "Draft for id="+id+" not found")
            elif resp.status_code == 401:
                raise PDRServiceAuthFailure(svcnm, relurl, resp.reason)
            elif resp.status_code >= 400:
                raise PDRServiceError(svcnm, relurl, resp.status_code, resp.reason)
            elif resp.status_code != 200:
                raise PDRServerError(svcnm, relurl, resp.status_code, resp.reason,
                                     message="Unexpected response from server: {0} {1}"
                                     .format(resp.status_code, resp.reason))
            
        except requests.RequestException as ex:
            raise PDRServerError(svcnm, id, cause=ex)

    def create_draft(self, nerdm):
        """
        create a draft that can be edited via the customization service

        :return dict: the NERDm record that was set up as a draft (based on the given record) 
        """
        if 'ediid' not in nerdm:
            raise ValueError("'ediid' property not in input data (is this a NERDm record?)")
        id = self._arkprfx.sub('', nerdm['ediid'])

        resp = None
        try:
            self.log.debug("Creating draft in customization service for id="+ nerdm['ediid'])
            resp = requests.put(self.baseurl + id, json=nerdm,
                                headers=self._headers())
            return self._get_json(id, resp)
        
        except requests.RequestException as ex:
            raise PDRServerError(svcnm, id, cause=ex)


