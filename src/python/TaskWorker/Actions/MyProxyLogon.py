from WMCore.Credential.Proxy import Proxy

from TaskWorker.DataObjects.Result import Result
from TaskWorker.Actions.TaskAction import TaskAction
from TaskWorker.WorkerExceptions import TaskWorkerException
from ServerUtilities import tempSetLogLevel
import logging

# We won't do anything if the proxy is shorted then 1 hour
# NB: in the PoC we had 24 hours, but does that make sense
#     for all possible commands, e.g. kill?
MINPROXYLENGTH = 60 * 60 * 1

class MyProxyLogon(TaskAction):
    """ Retrieves the user proxy from myproxy
    """

    def __init__(self, config, server, resturi, procnum=-1, myproxylen=MINPROXYLENGTH):
        TaskAction.__init__(self, config, server, resturi, procnum)
        self.myproxylen = myproxylen

    def execute(self, *args, **kwargs):
        result = None
        proxycfg = {'vo': kwargs['task']['tm_user_vo'],
                    'logger': self.logger,
                    'myProxySvr': self.config.Services.MyProxy,
                    'proxyValidity' : '144:0',
                    'min_time_left' : 36000, ## do we need this ? or should we use self.myproxylen? 
                    'userDN' : kwargs['task']['tm_user_dn'],
                    'group' : kwargs['task']['tm_user_group'] if kwargs['task']['tm_user_group'] else '',
                    'role' : kwargs['task']['tm_user_role'] if kwargs['task']['tm_user_role'] else '',
                    'server_key': self.config.MyProxy.serverhostkey,
                    'server_cert': self.config.MyProxy.serverhostcert,
                    'serverDN': self.config.MyProxy.serverdn,
                    'uisource': getattr(self.config.MyProxy, 'uisource', ''),
                    'credServerPath': self.config.MyProxy.credpath,
                    'myproxyAccount' : self.server['host'],
                    'cleanEnvironment' : getattr(self.config.MyProxy, 'cleanEnvironment', False)
                   }
        # WMCore proxy methods are awfully verbode, reduce logging level when using them
        with tempSetLogLevel(logger=self.logger, level=logging.ERROR):
            proxy = Proxy(proxycfg)
            userproxy = proxy.getProxyFilename(serverRenewer=True)
            proxy.logonRenewMyProxy()
            timeleft = proxy.getTimeLeft(userproxy)
            usergroups = set(proxy.getAllUserGroups(userproxy))
        if timeleft is None or timeleft <= 0:
            msg = "Impossible to retrieve proxy from %s for %s." % (proxycfg['myProxySvr'], proxycfg['userDN'])
            self.logger.error(msg)
            self.logger.error("\n Will try again in verbose mode")
            self.logger.error("===========PROXY ERROR START ==========================")
            with tempSetLogLevel(logger=self.logger, level=logging.DEBUG):
                userproxy = proxy.getProxyFilename(serverRenewer=True)
                proxy.logonRenewMyProxy()
                timeleft = proxy.getTimeLeft(userproxy)
                usergroups = set(proxy.getAllUserGroups(userproxy))
            self.logger.error("===========PROXY ERROR END   ==========================")
            raise TaskWorkerException(msg)
        else:
            kwargs['task']['user_proxy'] = userproxy
            kwargs['task']['user_groups'] = usergroups
            self.logger.debug("Valid proxy for %s now in %s", proxycfg['userDN'], userproxy)
            result = Result(task=kwargs['task'], result='OK')
        return result
