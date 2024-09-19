#!/usr/bin/env python3

import re
import sys, os
import json
import time
import socket
import logging
from lib.utils import requests_get, requests_post
from lib.jobwrapper import BUILD_SERVERS, JobWrapper, ServerNotFound


logger = logging.getLogger(__name__)

class JenkinsWrapper(JobWrapper):
    # set job_name, group and url related vars
    # either 'name' or 'url' has to be specified
    def __reload_job(self, name=None, group=None, has_parms=True, job_url=None):
        self.build_number = None
        if job_url:
            self.job_url_base = job_url
            self.name = None
            self.group = None
        elif name:
            self.job_name = name
            if not hasattr(self, 'group'):
                self.group = group or self.server_info.get('def_group')
            elif group:
                self.group = group

            if self.group:
                self.job_url_base = '/'.join(
                    (self.server_url, 'job', self.group, 'job', self.job_name))
            else:
                self.job_url_base = '/'.join(
                    (self.server_url, 'job', self.job_name))
        else:
            return
        # jenkins url related vars
        self.query_job_url_base = '{u}/%s/api/json%s'.format(
                                    u=self.job_url_base)
        self.view_job_url_base = '{u}/%s'.format(u=self.job_url_base)
        self.stop_job_url_base = '{u}/%s/stop'.format(u=self.job_url_base)
        self.log_url_base = '{u}/%s/logText/progressiveText?start=%i'.format(
                              u=self.job_url_base)
        if has_parms:
            self.trigger_job_url = self.view_job_url_base % \
                                     'buildWithParameters'
        else:
            self.trigger_job_url = self.view_job_url_base % 'build'


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # get build server name argument
        server_name = kwargs.get('server_name')
        if not server_name:
            raise ServerNotFound("server_name is missed")
        elif server_name not in BUILD_SERVERS:
            raise ServerNotFound("Build server %s not found" % server_name)
        # get build server information
        self.server_info = BUILD_SERVERS[server_name]
        self.job_type = self.server_info['type']
        self.server_url = self.server_info['url']
        self.auth = (self.server_info['user'], self.server_info['pass'],)

        # retrieve the crubm token
        result = requests_get('/'.join((
            self.server_url,
            'crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)'
        )), auth=self.auth)
        csrf_token_list = result.split(':')
        self.post_headers = {'cache-control': 'no-cache',
                             'content-type': 'application/x-www-form-urlencoded',
                             csrf_token_list[0]: csrf_token_list[1]}

        # set job_name, group and url related vars
        self.__reload_job(kwargs.get('job_name'), kwargs.get('group'))

        self.build_number = kwargs.get('build_number')
        if self.build_number and (not isinstance(self.build_number, str)):
            self.build_number = str(self.build_number)
        self.job_data = kwargs.get('job_data')
        self.param_file = kwargs.get('param_file')
        self.query_label_url_base = '{u}/label/%s/api/json%s'.format(
                                      u=self.server_url)

        self.queue_id = None


    @staticmethod
    def ptchlst2pidlst(patch_list_str, keep_patchset=True):
        pid_re = r'^(?:http.*/)?(\d{3,}|\d{3,}/\d{1,3})/?$'
        pids = []
        for url in patch_list_str.split(','):
            # pid: <pid>/[<patchset_id>]
            pid = re.sub(pid_re, '\\1', url)
            if not keep_patchset:
                pid = pid.split('/')[0]
            pids.append(pid)
        return ','.join(pids)


    def trigger_job(self, name=None, group=None, data=None, job_url=None):
        '''
           trigger job
           return True or False
        '''
        has_parms = False
        if data:
            has_parms = True
            self.job_data = data
        self.__reload_job(name, group, has_parms, job_url)
        resp = requests_post(self.trigger_job_url,
                             data=self.job_data,
                             headers=self.post_headers,
                             auth=self.auth,
                             verify=False)
        #resp.raise_for_status()
        logger.debug(self.job_data)
        logger.debug(resp.reason)
        logger.debug(resp.text)
        if resp.status_code != 201:
            logger.error(resp.text)
            return False
        else:
            self.queue_id = int(resp.headers['Location'].split('/')[-2])
            logger.debug("Queue ID: %d" % self.queue_id)
            return True


    def get_builds(self, name=None, group=None, job_url=None):
        """
        output sample:
        {
            _class: "hudson.model.FreeStyleProject",
            builds: [
                {
                    _class: "hudson.model.FreeStyleBuild",
                    id: "11",
                    number: 11,
                    queueId: 123713,
                    result: "SUCCESS"
                },
                ...
            ],
            queueItem: null
        }
        """
        self.__reload_job(name, group, True, job_url)
        url = self.query_job_url_base % \
          ('', '?tree=builds[id,number,result,queueId],queueItem[id,why]')
        try:
            resp = json.loads(requests_get(url, auth=self.auth))
            logger.debug(resp)
        except Exception as e:
            logger.error(e)
            resp = {}
        return resp


    def get_job_no(self):
        # retrieve job no interval
        retr_jno_interval = 30
        while not self.build_number:
            resp = self.get_builds()
            qitem = resp['queueItem']
            if qitem and qitem.get('id') == self.queue_id:
                logger.info("%s, polling again in %d seconds" % \
                              (qitem['why'], retr_jno_interval))
            else:
                for b in resp['builds']:
                    if b['queueId'] == self.queue_id:
                        self.build_number = str(b['number'])
                        break
            if not self.build_number:
                time.sleep(retr_jno_interval)

        build_url = self.view_job_url_base % self.build_number
        logger.info("Build URL: %s" % build_url)
        return build_url

    def poll_status(self):
        '''
           detect job status
           return job status json
        '''
        jinfo = requests_get(self.query_job_url_base % (self.build_number, ''),
                             auth=self.auth)
        jinfo = json.loads(jinfo)
        if jinfo['result']:
            self.handle_result(jinfo)

        logger.debug("Build info.: %s" % str(jinfo))
        logger.info("Status: ongoing, polling again in %d seconds" % \
                      self.sta_chk_interval)


    def retry_check(self, job_info, excepts=None):
        q_con_url = self.log_url_base % (self.build_number, 0)
        con_log = requests_get(q_con_url, auth=self.auth)
        JobWrapper.retry_check(self, con_log, excepts)


    def download_log(self, name=None, group=None, bno=None, job_url=None):
        '''
           download build log at /tmp/<job_name>-b<build_number>.log
        '''
        self.__reload_job(name, group, True, job_url)
        if bno:
            self.build_number = str(bno)
        if not self.build_number:
            logger.error("No build number specified")
            return

        q_con_url = self.log_url_base % (self.build_number, 0)
        con_log = requests_get(q_con_url, auth=self.auth)
        logfl = "/tmp/%s-b%s.log" % (self.job_name, self.build_number)
        with open(logfl, 'w') as l:
            l.write(con_log)


    def stop(self, name=None, group=None, bno=None, job_url=None):
        '''
           stop job
           return True or False
        '''
        self.__reload_job(name, group, True, job_url)
        if bno:
            self.build_number = str(bno)
        if not self.build_number:
            logger.error("No build number specified")
            return

        resp = requests_post(self.stop_job_url_base % self.build_number,
                             headers=self.post_headers,
                             data=None,
                             auth=self.auth,
                             verify=False)
        # resp.raise_for_status()
        logger.debug(resp.reason)
        logger.debug(resp.text)
        if resp.status_code != 200:
            logger.error(resp.text)
            return False
        else:
            return True

    def get_status(self, name=None, group=None, bno=None, job_url=None):
        '''
           get job state
           return state
        '''
        self.__reload_job(name, group, True, job_url)
        if bno:
            self.build_number = str(bno)
        if not self.build_number:
            logger.error("No build number specified")
            return

        url = self.query_job_url_base % (self.build_number, '')
        try:
            res = requests_get(url, auth=self.auth)
            result = json.loads(res)['result']
        except:
            result = 'Not Found'
        return result


    def get_build_info(self, name=None, group=None, bno=None, job_url=None):
        self.__reload_job(name, group, True, job_url)
        if bno:
            self.build_number = str(bno)
        if not self.build_number:
            logger.error("No build number specified")
            return

        url = self.query_job_url_base % (self.build_number, '')
        try:
            res = requests_get(url, auth=self.auth)
            result = json.loads(res)
        except:
            result = {}
        return result


    def get_build_log(self, name=None, group=None,
                      bno=None, start=6000000, job_url=None):
        self.__reload_job(name, group, True, job_url)
        if bno:
            self.build_number = str(bno)
        if not self.build_number:
            logger.error("No build number specified")
            return

        url = self.log_url_base % (self.build_number, start)
        try:
            resp = requests_get(url, auth=self.auth)
            logger.debug(resp)
        except Exception as e:
            logger.error(e)
            resp = None

        return resp


    def get_node_label_load(self, label_name):
        try:
            request_url = self.query_label_url_base % (label_name, '?depth=1')
            res = requests_get(request_url, auth=self.auth)
            result = json.loads(res)
            data = [result["busyExecutors"], result["idleExecutors"]]
        except Exception as e:
            logger.error(f'get jenkins node label load information failed. {e}')
            raise e
        else:
            return data
