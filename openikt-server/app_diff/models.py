#!/usr/bin/env python3
import os
import re
import sys
import logging
from difflib import SequenceMatcher
from datetime import timezone as dttz
from datetime import datetime, timedelta
from django.db import models
from argparse import ArgumentTypeError
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q, CharField, TextField, ForeignKey, IntegerField, \
                             DateTimeField, BooleanField, OneToOneField, \
                             ManyToManyField, BigIntegerField, Model
from django.db.models.functions import Cast
from django.db.models.expressions import F, Value, Func

from lib.gitutils import parse_commit


class Repository(Model):
    REFTYPE_SHA = 1
    REFTYPE_TAG = 2
    REFTYPE_BRANCH = 3
    REFTYPE_NOT_EXIST = 4
    REFTYPE_INVALID_REPO = 5

    protocol = CharField(max_length=16, null=True)
    host = CharField(max_length=255, null=True)
    project = CharField(max_length=255, null=True)
    external = BooleanField(default=False)
    name = CharField(max_length=64, null=True, blank=True)

    def url(self):
        '''
        Returns full URL for the repository
        Suitable for commands like 'git clone'
        
        :returns: full URL for the repository
        :rtype: str
        '''
        return "%s://%s/%s" % (self.protocol, self.host, self.project)

    def pr_url(self, prno):
        url = None
        try:
            if not isinstance(prno, int):
                prno = int(prno)
            if self.host == 'github.com':
                url = "%s/pull/%i" % (self.url(), prno)
            elif self.host == 'gitee.com':
                url = "%s/pulls/%i" % (self.url(), prno)
        except Exception:
            pass
        return url

    def pr_url_base(self):
        url = None
        if self.host == 'github.com':
            url = "%s/pull/" % self.url()
        elif self.host == 'gitee.com':
            url = "%s/pulls/" % self.url()
        return url

    def get_prno_by_url(self, url):
        prno = None
        if self.host in ('github.com', 'gitee.com',):
            prno_re = '\/pulls?\/(\d+)$'
            m = re.search(prno_re, url)
            if m:
                prno = m.group(1)

        return prno


class UpstreamedPatch(Model):
    commit = CharField(max_length=64)
    payload_hash = CharField(max_length=64)
    subject = CharField(max_length=1024)
    files = ArrayField(CharField(max_length=1024), null=True, blank=True)
    insert_size = IntegerField(default=0, null=True, blank=True)
    delete_size = IntegerField(default=0, null=True, blank=True)

    author = models.CharField(max_length=128, null=False )
    author_date = DateTimeField(null=True, blank=True)
    committer = models.CharField(max_length=128, null=False )
    commit_date = DateTimeField(null=True, blank=True)
    # tags in commit message(e.g. reviewer, tester)
    trailers = JSONField(null=True, blank=True)

    imported_date = DateTimeField(auto_now_add=True)
    # release tag or branch
    upstreamed_in = CharField(max_length=64, null=True, blank=True)
    # from which git repo
    repo = ForeignKey(Repository, on_delete=models.DO_NOTHING)
    # reference commit: e.g. a mainline commit id may be referred in
    # the lts kernel commit message:
    #   [ Upstream commit 3780bb29311eccb7a1c9641032a112eed237f7e3 ]
    ref_commit = CharField(max_length=64, null=True, blank=True)

    class Meta:
        unique_together = ('commit', 'repo')
    
    def __str__(self):
        return "{}: {}".format(self.commit, self.subject)

    @classmethod
    def import_patch(cls, git_cmt, tag, repo_id):
        parsed_cmt = parse_commit(git_cmt)
        # create upstreamedpatch in DB
        patch = cls(commit=parsed_cmt['commit'],
                    payload_hash=parsed_cmt['payload_hash'],
                    subject=parsed_cmt['subject'],
                    files=parsed_cmt['files'],
                    insert_size=parsed_cmt['insert_size'],
                    delete_size=parsed_cmt['delete_size'],
                    author=parsed_cmt['author'],
                    author_date=parsed_cmt['author_date'],
                    committer=parsed_cmt['committer'],
                    commit_date=parsed_cmt['commit_date'],
                    trailers=parsed_cmt.get('trailers'),
                    upstreamed_in=tag,
                    repo_id=repo_id,
                    ref_commit=parsed_cmt.get('ref_commit')
        )

        return patch


class PR(Model):
    prno = CharField(max_length=64)
    url = CharField(max_length=1024, unique=True, null=True)
    repo = ForeignKey(Repository, on_delete=models.DO_NOTHING,
                      null=True, blank=True)
    commits = ManyToManyField(UpstreamedPatch)

    def __str__(self):
        return self.repo.pr_url(self.prno)


class RangeDiff(Model):
    TYPE_GITDIFF = 1
    TYPE_QUILTDIFF = 2
    TYPE_QUILT = 3
    TYPE_CHOICES = (
        (TYPE_GITDIFF, "git range diff"),
        (TYPE_QUILTDIFF, "quilt diff"),
        (TYPE_QUILT, "quit"),
    )
    ref_a = CharField(max_length=256)
    ref_b = CharField(max_length=256)
    refsha_a = CharField(max_length=256, null=True, blank=True)
    refsha_b = CharField(max_length=256, null=True, blank=True)
    base_a = CharField(max_length=64)
    base_b = CharField(max_length=64)
    basesha_a = CharField(max_length=256, null=True, blank=True)
    basesha_b = CharField(max_length=256, null=True, blank=True)
    repo_a = ForeignKey(Repository, related_name='repo_a',
                        on_delete=models.DO_NOTHING)
    repo_b = ForeignKey(Repository, related_name='repo_b',
                        on_delete=models.DO_NOTHING, null=True, blank=True)
    difftype = IntegerField(choices=TYPE_CHOICES, default=TYPE_GITDIFF)
    diff = TextField(null=True, blank=True)
    created_date = DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('repo_a', 'repo_b', 'refsha_a', 'refsha_b')


class RangeDiffPatch(Model):
    TYPE_NEW = 1
    TYPE_UPDATED = 2
    TYPE_REMOVED = 3
    # commit message changed only
    TYPE_CMCO = 4
    TYPE_SAME = 5
    TYPE_CHOICES = (
        (TYPE_SAME, "same" ),
        (TYPE_NEW, "new" ),
        (TYPE_UPDATED, "updated" ),
        (TYPE_REMOVED, "removed" ),
        (TYPE_CMCO, "cmtmsg changed only"),
    )
    rangediff = ForeignKey(RangeDiff, on_delete=models.CASCADE)
    cmt_a = ForeignKey(UpstreamedPatch, on_delete=models.CASCADE,
                       related_name='cmt_a', null=True, blank=True)
    cmt_b = ForeignKey(UpstreamedPatch, on_delete=models.CASCADE,
                       related_name='cmt_b', null=True, blank=True)
    patchtype = IntegerField(choices=TYPE_CHOICES, default=TYPE_NEW)
    pr = ForeignKey(PR, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return "%s: %s --> %s" % (self.get_patchtype_display(),
                                  self.cmt_a.commit if self.cmt_a else '-'*40,
                                  self.cmt_b.commit if self.cmt_b else '-'*40)


class KorgPatch(Model):
    commit = CharField(max_length=64)
    payload_hash = CharField(max_length=64)
    tag = models.CharField(max_length=64, null=True, blank=True)
    repo = ForeignKey(Repository, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.commit
