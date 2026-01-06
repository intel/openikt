#!/bin/env python3
import sys
import re
import os
import time
import logging

logger = logging.getLogger(__name__)

FACELESS_USER_TEST = os.environ.get('FACELESS_USER_TEST')
CJE_JENKINS_URL = os.environ.get('CJE_JENKINS_URL')
BUILD_SERVERS = {
    'cje_jenkins': {
        'url': CJE_JENKINS_URL,
        'def_group': 'NEX-Kernel',
        'type': 'jenkins',
        'user': FACELESS_USER_TEST,
        'pass': os.environ.get('SYS_TESTING_CRED_CJE_API'),
    },
}

COMMON_RETRY_EXCEPTIONS = {
    'TFConnectionError': [
        { 'msg': 'TeamForge connection timed out',
          'rep': r'ssh: connect to host git-amr-[^\r\n]*: Connection timed out',
        },
        { 'msg': 'TeamForge bad handshake',
          'rep': r'Failure: xutils.services.api.api_teamforge.TeamforgeError: \[Errno bad handshake\]',
        },
    ],
}


class JobWrapperRetryException(Exception):
    pass


class TFConnectionTimeout(JobWrapperRetryException):
    pass

class ArtifactoryAuthError(JobWrapperRetryException):
    pass


class ACRNDeviceError(JobWrapperRetryException):
    pass


class ServerNotFound(JobWrapperRetryException):
    pass


class JobWrapper:
    def __init__(self, **kwargs):
        sta_chk_interval = None


    def trigger_job(self):
        pass


    def handle_result(self, job_info):
        pass


    def get_job_url(self):
        pass


    def get_job_no(self):
        pass


    def poll_status(self):
        pass


    def retry_check(self, log, specific_excepts=None):
        # merge common retry exceptions and specific ones
        retry_excepts = { **COMMON_RETRY_EXCEPTIONS, **specific_excepts } \
                          if specific_excepts else COMMON_RETRY_EXCEPTIONS
        for e, errors in retry_excepts.items():
            for err in errors:
                match = re.search(err['rep'], log, re.M|re.S)
                if match:
                    exc_class = globals()[e]
                    exc = exc_class(err['msg'])
                    raise exc


    def _do(self):
        trigger_result = self.trigger_job()
        if not trigger_result:
            logger.error("Triggered job failed, quit")
            sys.exit(14)
    
        time.sleep(10)
        self.get_job_no()
        while True:
            self.poll_status()
            time.sleep(self.sta_chk_interval)

    def do(self):
        retry_max = 3
        retry_count = 0
        retry_interval = 60
        while True:
            try:
                self._do()
                break
            except JobWrapperRetryException as e:
                logger.error(e)
                if retry_count < retry_max:
                    retry_count += 1
                    logger.error("Retry(#%d) in %d seconds" % \
                                  (retry_count, retry_interval))
                    time.sleep(retry_interval)
                else:
                    logger.error("Still failed after %d retries, quit" % \
                                  retry_max)
                    break
