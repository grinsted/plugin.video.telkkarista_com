# -*- coding: utf-8 -*-

__author__ = 'rasjani'

import urllib2
import json

class APIBaseMixin(object):
  _error = False
  last_error = ''

  def apiCall(self, method, data=None, path=None ):
    requestSuccess = "%s/%s" % (self.apiBase, method)

    response = self._client.request("%s/%s" % (self.apiBase, method), data, path)
    response = json.loads(response)
    if response['status'] == 'ok' and response['method'] in [requestSuccess, method]:
      self._error = False
      return response['payload']
    else:
      self._error = True
      if 'message' in response:
        self.last_error = response['message']
      else:
        print "RESPONSE: ", response
      return None

  def lastCallFailed(self):
    return this.error
