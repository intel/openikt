#!/usr/bin/env python3
import os
import re
import sys
import logging
from difflib import SequenceMatcher
from datetime import timezone as dttz
from datetime import datetime, timedelta
from argparse import ArgumentTypeError
from django.db import models
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q, CharField, TextField, ForeignKey, IntegerField, \
                             DateTimeField, BooleanField, OneToOneField, \
                             ManyToManyField, BigIntegerField, Model, CASCADE, \
                             DO_NOTHING
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

    def __str__(self):
        return self.name


class OSImage(Model):
    os = IntegerField(choices=PKGSection.OS_CHOICES, default=PKGSection.OS_UBUNTU)
    name = CharField(max_length=256, unique=True)
    release = CharField(max_length=64, null=True, blank=True)
    desc = CharField(max_length=256, null=True, blank=True)
    url = CharField(max_length=1024, null=True, blank=True)
    created = DateTimeField(null=True, blank=True)
    raw_data = TextField(null=True, blank=True)
    imported = BooleanField(default=False)

    def __str__(self):
        return self.name


class Contributor(Model):
    email = CharField(max_length=64, unique=True)
    name = CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.email


class Package(Model):
    ARCH_I386 = 1
    ARCH_AMD64 = 2
    ARCH_ALL = 3
    ARCH_CHOICES = (
        (ARCH_I386, "i386"),
        (ARCH_AMD64, "amd64"),
        (ARCH_ALL, "all"),
    )
    root_id = IntegerField(default=0)
    name = CharField(max_length=256)
    version = CharField(max_length=64)
    summary = CharField(max_length=1024, null=True, blank=True)
    desc = TextField(null=True, blank=True)
    section = ForeignKey(PKGSection, on_delete=DO_NOTHING,
                         null=True, blank=True)
    homepage = CharField(max_length=1024, null=True, blank=True)
    source = CharField(max_length=1024, null=True, blank=True)
    image = ForeignKey(OSImage, on_delete=DO_NOTHING, null=True, blank=True)
    maintainer = ManyToManyField(Contributor, through="PKGContributor")
    arch = IntegerField(choices=ARCH_CHOICES, default=ARCH_I386)
    # yocto only
    layer = CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return "%s %s" % (self.name, self.version)


class PKGContributor(Model):
    TYPE_MAINTAINER = 1
    # original maintainer
    TYPE_ORI_MAINTAINER = 2
    TYPE_CHOICES = (
        (TYPE_MAINTAINER, "maintainer"),
        (TYPE_ORI_MAINTAINER, "original-maintainer"),
    )
    package = ForeignKey(Package, on_delete=CASCADE)
    contributor = ForeignKey(Contributor, on_delete=CASCADE)
    # contributor type
    ctype = IntegerField(choices=TYPE_CHOICES, default=TYPE_MAINTAINER)
    
    def __str__(self):
        return "%s ( %s )" % (self.contributor.name, self.get_ctype_display())


class PKGExtraInfo(Model):
    KEY_PATCHES = 1
    KEY_CHOICES = (
        (KEY_PATCHES, "patches"),
    )
    package = ForeignKey(Package, on_delete=CASCADE)
    key = IntegerField(choices=KEY_CHOICES, default=KEY_PATCHES)
    value = CharField(max_length=1024)

    def __str__(self):
        return "%s: (%s, %s)" % (self.package.name, self.key, self.value)


class PKGRelation(Model):
    TYPE_DEPENDS = 1
    TYPE_RECOMMENDS = 2
    TYPE_SUGGESTS = 3
    TYPE_BREAKS = 4
    TYPE_CONFLICTS = 5
    TYPE_REPLACES = 6
    TYPE_PROVIDES = 7
    TYPE_CHOICES = (
        (TYPE_DEPENDS, "depends"),
        (TYPE_RECOMMENDS, "recommends"),
        (TYPE_SUGGESTS, "suggests"),
        (TYPE_BREAKS, "breaks"),
        (TYPE_CONFLICTS, "conflicts"),
        (TYPE_REPLACES, "replaces"),
        (TYPE_PROVIDES, "provides"),
    )
    # comparison operator
    CMP_OPR_NA = 1
    CMP_OPR_GT = 2
    CMP_OPR_GE = 3
    CMP_OPR_EQ = 4
    CMP_OPR_LE = 5
    CMP_OPR_LT = 6
    CMP_OPR_ANY = 7
    CMP_OPR_CHOICES = (
        (CMP_OPR_NA, ""),
        (CMP_OPR_GT, ">>"),
        (CMP_OPR_GE, ">="),
        (CMP_OPR_EQ, "="),
        (CMP_OPR_LE, "<="),
        (CMP_OPR_LT, "<<"),
        (CMP_OPR_ANY, ":any")
    )
    package = ForeignKey(Package, on_delete=CASCADE)
    rtype = IntegerField(choices=TYPE_CHOICES, default=TYPE_DEPENDS)
    cmpopr = IntegerField(choices=CMP_OPR_CHOICES, default=CMP_OPR_NA)
    name = CharField(max_length=64)
    version = CharField(max_length=64, null=True, blank=True)
    group = IntegerField(default=0)

    def __str__(self):
        return "%s %s: %s %s" % (self.package.name,
                                 self.get_rtype_display(),
                                 self.get_cmpopr_display(),
                                 self.name)


class ImageDiff(Model):
    img_a = ForeignKey(OSImage, related_name='img_a', on_delete=DO_NOTHING)
    img_b = ForeignKey(OSImage, related_name='img_b', on_delete=DO_NOTHING)
    created = DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('img_a', 'img_b')

    def __str__(self):
        return "%s -- %s" % (self.img_a.name, self.img_b.name)


class ImageDiffPKG(Model):
    TYPE_NEW = 1
    TYPE_SAME = 2
    TYPE_UPGRADED = 3
    TYPE_DOWNGRADED = 4
    TYPE_REMOVED = 5
    TYPE_MODIFICATION = 6
    TYPE_VERSION_CHANGED = 7
    TYPE_REPLACED = 8
    TYPE_CHOICES = (
        (TYPE_NEW, "new"),
        (TYPE_SAME, "same"),
        (TYPE_UPGRADED, "upgraded"),
        (TYPE_DOWNGRADED, "downgraded"),
        (TYPE_REMOVED, "removed"),
        (TYPE_MODIFICATION, "modification"),
        (TYPE_VERSION_CHANGED, "version changed"),
        (TYPE_REPLACED, "replaced"),
    )
    imgdiff = ForeignKey(ImageDiff, on_delete=CASCADE)
    pkg_a = ForeignKey(Package, on_delete=CASCADE, related_name='pkg_a',
                       null=True, blank=True)
    pkg_b = ForeignKey(Package, on_delete=CASCADE, related_name='pkg_b',
                       null=True, blank=True)
    pkgtype = IntegerField(choices=TYPE_CHOICES, default=TYPE_NEW)

    def __str__(self):
        return "%s: %s --> %s" % (self.get_pkgtype_display(),
                                  self.pkg_a.name if self.pkg_a else '-'*40,
                                  self.pkg_b.name if self.pkg_b else '-'*40)
