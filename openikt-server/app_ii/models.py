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


class PKGSection(Model):
    OS_UBUNTU = 1
    OS_TIBER = 2
    OS_YOCTO = 3
    OS_CHOICES = (
        (OS_UBUNTU, "ubuntu"),
        (OS_TIBER, "tiber"),
        (OS_YOCTO, "yocto"),
    )
    name = CharField(max_length=64, unique=True)
    desc = CharField(max_length=256, null=True, blank=True)
    os = IntegerField(choices=OS_CHOICES, default=OS_UBUNTU)


class OSImage(Model):
    os = IntegerField(choices=OS_CHOICES, default=OS_UBUNTU)
    name = CharField(max_length=256, unique=True)
    release = CharField(max_length=64, null=True, blank=True)
    desc = CharField(max_length=256, null=True, blank=True)
    url = CharField(max_length=1024, null=True, blank=True)
    created = DateTimeField(null=True, blank=True)


class Package(Model):
    root_id = IntegerField(default=0)
    name = CharField(max_length=256)
    version = CharField(max_length=64)
    summary = CharField(max_length=1024, null=True, blank=True)
    desc = TextField(null=True, blank=True)
    section = ForeignKey(PKGSection, on_delete=models.DO_NOTHING,
                         null=True, blank=True)
    homepage = CharField(max_length=1024, null=True, blank=True)
    source = CharField(max_length=1024, null=True, blank=True)
    image = ForeignKey(OSImage, on_delete=models.DO_NOTHING, null=True, blank=True)


class PKGExtraInfo(Model):
    KEY_PATCHES = 1
    KEY_PROVIDES = 2
    KEY_MAINTAINER_NAME = 3
    KEY_MAINTAINER_EMAIL = 4
    KEY_OMAINTAINER_NAME = 5
    KEY_OMAINTAINER_EMAIL = 6
    KEY_CHOICES = (
        (KEY_PATCHES, "patches"),
        (KEY_PROVIDES, "provides"),
        (KEY_MAINTAINER_NAME, "maintainer name"),
        (KEY_MAINTAINER_EMAIL, "maintainer email"),
        (KEY_OMAINTAINER_NAME, "ori-maintainer name"),
        (KEY_OMAINTAINER_EMAIL, "ori-maintainer email"),
    )
    package = ForeignKey(Package, on_delete=models.DO_CASCADE)
    key = IntegerField(choices=KEY_CHOICES, default=KEY_PATCHES)
    value = CharField(max_length=1024)


class PKGRelation(Model):
    TYPE_DEPEND = 1
    TYPE_BREAK = 2
    TYPE_REPLACE = 3
    TYPE_CONFLICT = 4
    TYPE_BUILD_DEPEND = 5
    TYPE_CHOICES = (
        (TYPE_DEPEND, "depend"),
        (TYPE_BREAK, "break"),
        (TYPE_REPLACE, "replace"),
        (TYPE_CONFLICT, "conflict"),
        (TYPE_BUILD_DEPEND, "build depend"),
    )
    # comparison operator
    CMP_OPR_NA = 1
    CMP_OPR_GE = 2
    CMP_OPR_EQ = 3
    CMP_OPR_LL = 4
    CMP_OPR_CHOICES = (
        (CMP_OPR_NA, ""),
        (CMP_OPR_GE, ">="),
        (CMP_OPR_EQ, "="),
        (CMP_OPR_LL, "<<"),
    )
    package = ForeignKey(Package, on_delete=models.DO_CASCADE)
    rtype = IntegerField(choices=TYPE_CHOICES, default=TYPE_DEPEND)
    cmpopr = IntegerField(choices=CMP_OPR_CHOICES, default=CMP_OPR_NA)
    name = CharField(max_length=256)


class ImageDiff(Model):
    img_a = ForeignKey(OSImage, related_name='img_a',
                       on_delete=models.DO_NOTHING)
    img_b = ForeignKey(OSImage, related_name='img_b',
                       on_delete=models.DO_NOTHING)
    created = DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('img_a_id', 'img_b_id')

    def __str__(self):
        return "%s -- %s" % (img_a.name, img_b.name)


class ImageDiffPKG(Model):
    TYPE_NEW = 1
    TYPE_UPGRADED = 2
    TYPE_DOWNGRADED = 3
    TYPE_REMOVED = 4
    TYPE_CHOICES = (
        (TYPE_NEW, "new"),
        (TYPE_UPGRADED, "upgraded"),
        (TYPE_DOWNGRADED, "downgraded"),
        (TYPE_REMOVED, "removed")
    )
    imgdiff = ForeignKey(ImageDiff, on_delete=models.CASCADE)
    pkg_a = ForeignKey(Package, on_delete=models.CASCADE,
                       related_name='pkg_a', null=True, blank=True)
    pkg_b = ForeignKey(Package, on_delete=models.CASCADE,
                       related_name='pkg_b', null=True, blank=True)
    pkgtype = IntegerField(choices=TYPE_CHOICES, default=TYPE_NEW)

    def __str__(self):
        return "%s: %s --> %s" % (self.get_pkgtype_display(),
                                  self.pkg_a.name if self.pkg_a else '-'*40,
                                  self.pkg_b.name if self.pkg_b else '-'*40)
