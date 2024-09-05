#!/usr/bin/env  python3

import os
import io
import re
import sh
import sys
import pty
import json
import fcntl
import shutil
import traceback
import subprocess
import select
import math
import tarfile
import tempfile
import logging
import hashlib
from functools import wraps
from time import sleep
from subprocess import PIPE
from datetime import datetime
from difflib import SequenceMatcher
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


#
# Functions
#
def retry(*, retry_times=3, err_kw=None):
    intervals = (5, 8, 13, 21, 34, 55)
    retry_times = min(len(intervals), retry_times)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retry_times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if err_kw and err_kw not in str(e):
                        raise e
                    else:
                        logger.warning(e)
                        logger.warning("Retry (%i/%i) in %i seconds..." % \
                                         (i, retry_times, intervals[i]))
                        sleep(intervals[i])
            return None

        return wrapper

    return decorator


class ShCmdError(Exception):
    pass


def cmd_pipe(command):
    logger.debug("Run shell cmd: %s", command)
    returncode = 1
    output = None
    error = None
    try:
        proc = subprocess.Popen(command,
                                shell=True, \
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                executable='/bin/bash')

        output = proc.stdout.read().decode().strip()
        error = proc.stderr.read().decode().strip()
        returncode = proc.wait()
    except (OSError, ValueError) as e:
        returncode = 2
        error = str(e)
    finally:
        if output:
            logger.info(output)
        if error:
            logger.error(error)
        return returncode, output, error

def hash_str(s, n=40):
    h = hashlib.sha256(s.encode('utf-8')).hexdigest()
    return h[:n] if n>0 else h

def requests_retry_session(retries=10,
                           backoff_factor=0.3,
                           status_forcelist=(401, 500, 502, 504),
                           session=None):
    session = session or requests.Session()
    retry = Retry(total=retries,
                  read=retries,
                  connect=retries,
                  backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def requests_get(url, q_data=None, auth=None):
    resp = None
    logger.debug("Query URL: %s" % url)
    try:
        resp = requests_retry_session().get(url, auth=auth, verify=False)
        logger.debug(resp.text)
        if resp.status_code != requests.codes.ok:
            logger.error(resp.reason)
            logger.error(resp.text)
            sys.exit(resp.status_code)
    except Exception as e:
        logger.error(e)
        logger.error("requests.get() failed after retries: %s, terminated" % \
                       e.__class__.__name__)
        sys.exit(500)

    return resp.text


def requests_post(url, data, headers, auth, verify=False):
    resp = None
    logger.debug("Post URL: %s" % url)
    try:
        resp = requests_retry_session().post(url,
                                             data=data,
                                             headers=headers,
                                             auth=auth,
                                             verify=verify)
    except Exception as e:
        logger.error(e)
        logger.error("requests.post() failed: %s, terminated" % \
                       e.__class__.__name__)
        sys.exit(500)

    return resp
