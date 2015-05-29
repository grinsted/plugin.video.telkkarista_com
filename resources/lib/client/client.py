__author__ = 'rasjani'

from .user import User
from .streams import Streams
from .epg import Epg
from .vod import Vod
from .cache import Cache
from .ui import Ui


import urllib2
import json


class Client:

  apiEndPoint = ''
  loginService = ''
  clientName = None
  clientVersion = None
  versionString = None
  apiVersion = '1'
  streamService = ''
  debug = False

  _streams = {}
  _epg = {}
  _vod = {}
  _cacheServers = {}
  _settings = {}

  _plugin = None
  _sessionId = None

  _xlibversion = 'libStreamingClient/0.1.5 20150313 (friday the 13th edition)'

  def __init__(self, host, plugin, xbmcgui):
    self._plugin = plugin
    self._useProxy = plugin.get_setting('use_proxy',bool)
    # self.debug = plugin.get_setting('debug',bool)
    if self.debug:
      self._debugLevel = 1
    else:
      self._debugLevel = 0
    self.apiEndPoint = 'http://api.%s' % host
    self.loginService = 'http://login.%s' % host
    self.clientName = plugin.addon.getAddonInfo('id')
    # getAddonInfo version doesnt seem to work  ? returns "Unavailable"
    # self.clientVersion = plugin.addon.getAddonInfo('version')
    self.clientVersion = "0.0.1"
    self.versionString = "%s/%s" % (self.clientName, self.clientVersion )
    self.User = User(self, plugin)
    self.Streams = Streams(self, plugin)
    self.Epg = Epg(self, plugin)
    self.Cache = Cache(self, plugin)

    self.ui = Ui(plugin, xbmcgui, self)

    self._sessionId = plugin.get_setting('sessionId', unicode)
    self.streamService = plugin.get_setting('cachehost', unicode)

    self.handleLogin()

  def checkCacheServer(self):
    hostList = self._cacheServers['payload']
    if not self.streamService in [u['host'] for u in hostList if u['status']=='up' ]:
      return False
    else:
      return True


  def populateCache(self, invalidate = False):
    self._streams = self._plugin.get_storage('streams')
    self._cacheServers = self._plugin.get_storage('cacheServers')
    if len(self._streams.items())==0 or invalidate == True:
      self._streams.update( {"payload": self.Streams.get() })
      self._streams.sync()

    if len(self._cacheServers.items())==0 or invalidate == True:
      self._cacheServers.update({"payload": self.Cache.get() })
      self._cacheServers.sync()


  def handleLogin(self):
    invalidateCache = False
    if self._sessionId != None:
      if self.User.checkSession() == False:
        invalidateCache = True
        self.User.login()
    else:
      self.User.login()
      invalidateCache = True

    self.populateCache(invalidateCache)

    if not self.checkCacheServer():
      self.ui.cacheHostDialog()

  def setSessionId(self, id):
    self._plugin.set_setting("sessionId", id)
    self._sessionId = id

  def request(self, apiMethod, data=None, path=None):
    uri = path
    if not path:
      uri = "%s/%s/%s" % (self.apiEndPoint, self.apiVersion, apiMethod)

    conn = None
    if data != None:
      payload = json.dumps(data)
      req = urllib2.Request(uri, payload)
      contentLength = len(payload)
      req.add_header('Content-Length', contentLength)
      req.add_header('Content-Type', 'application/json')
    else:
      req = urllib2.Request(uri)

    req.add_header('User-Agent', self.versionString)
    # req.add_header('X-LIBVERSION', self._xlibversion)
    if self._sessionId != None:
      req.add_header('X-SESSION', self._sessionId)

    if self._useProxy:
      proxies = {
        'http': 'http://' + plugin.get_setting('proxy_host',unicode) + ":" + plugin.get_setting('proxy_port', unicode),
        'https': 'http://' + plugin.get_setting('proxy_host', unicode) + ":" + plugin.get_setting('proxy_port', unicode),
      }
      opener = urllib2.build_opener(urllib2.ProxyHandler(proxies, debuglevel=self._debugLevel))
      urllib2.install_opener(opener)
      conn = opener.open(req)
    else:
      opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=self._debugLevel))
      urllib2.install_opener(opener)
      conn = opener.open(req)

    resp = conn.read()
    conn.close()
    return resp
