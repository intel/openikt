#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from debian.debian_support import version_compare
from django.utils import timezone
from django.db.models import F, Q
from django.db import transaction

if not "DJANGO_SETTINGS_MODULE" in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
    import django
    django.setup()

from app_ii.models import *

logger = logging.getLogger(__name__)


# only for ubuntu image comparison
def gen_imagediff(imgdiff, img_a, img_b):
    pqs = Package.objects.filter(image_id__in=(img_a.id,img_b.id))
    a_pkgs = { p.name: p for p in pqs if p.image_id == img_a.id }
    b_pkgs = { p.name: p for p in pqs if p.image_id == img_b.id }
    rqs = PKGRelation.objects.select_related(
            'package').filter(
              rtype=PKGRelation.TYPE_REPLACES,
              package_id__in=[ p.id for p in b_pkgs.values() ]).order_by(
                'package_id', 'name')
    # replaced pkgs(a_pkg) keyed by b_pkg name
    b_pkgrs = defaultdict(list)
    for r in rqs:
        if r.name in a_pkgs:
            # replaced package
            rpkg = a_pkgs[r.name]
            if r.rtype in (PKGRelation.CMP_OPR_NA, PKGRelation.CMP_OPR_ANY,):
                b_pkgrs[r.package.name].append(rpkg)
            else:
                # compare value
                cv = version_compare(rpkg.version, r.version)
                if cv == 0 and r.rtype in (PKGRelation.CMP_OPR_EQ,
                                           PKGRelation.CMP_OPR_LE,) or \
                   cv == -1 and r.rtype in (PKGRelation.CMP_OPR_LE,
                                            PKGRelation.CMP_OPR_LT,):
                    b_pkgrs[r.package.name].append(rpkg)

    a_pnms = set(a_pkgs.keys())
    b_pnms = set(b_pkgs.keys())
    new = []
    removed = []
    same = []
    upgraded = []
    downgraded = []
    replaced = []
    for pn in sorted(b_pnms - a_pnms):
        if pn in b_pkgrs:
            for rpkg in b_pkgrs[pn]:
                diff = ImageDiffPKG(imgdiff_id=imgdiff.id,
                                    pkg_a_id=rpkg.id,
                                    pkg_b_id=b_pkgs[pn].id,
                                    pkgtype=ImageDiffPKG.TYPE_REPLACED)
                replaced.append(diff)
        else:
            diff = ImageDiffPKG(imgdiff_id=imgdiff.id, pkg_b_id=b_pkgs[pn].id)
            new.append(diff)
    for pn in sorted(a_pnms & b_pnms):
        pkga = a_pkgs[pn]
        pkgb = b_pkgs[pn]
        if pn in b_pkgrs:
            for rpkg in b_pkgrs[pn]:
                diff = ImageDiffPKG(imgdiff_id=imgdiff.id,
                                    pkg_a_id=rpkg.id,
                                    pkg_b_id=pkgb.id,
                                    pkgtype=ImageDiffPKG.TYPE_REPLACED)
                replaced.append(diff)
        cv = version_compare(pkga.version, pkgb.version)
        diff = ImageDiffPKG(imgdiff_id=imgdiff.id,
                            pkg_a_id=pkga.id,
                            pkg_b_id=pkgb.id)
        if cv == 1:
            diff.pkgtype = ImageDiffPKG.TYPE_DOWNGRADED
            downgraded.append(diff)
        elif cv == 0:
            diff.pkgtype = ImageDiffPKG.TYPE_SAME
            same.append(diff)
        elif cv == -1:
            diff.pkgtype = ImageDiffPKG.TYPE_UPGRADED
            upgraded.append(diff)
    for pn in sorted(a_pnms - b_pnms):
        diff = ImageDiffPKG(imgdiff_id=imgdiff.id,
                            pkg_a_id=a_pkgs[pn].id,
                            pkgtype=ImageDiffPKG.TYPE_REMOVED)
        removed.append(diff)

    diffs = (new, same, upgraded, downgraded, removed, replaced, [], [])
    all_diffs = []
    for g in diffs:
        all_diffs.extend(g)

    if all_diffs:
        with transaction.atomic():
            ImageDiffPKG.objects.bulk_create(all_diffs)

    return diffs

def main(args):
    iqs = OSImage.objects.filter(name__in=(args.image_a, args.image_b,))
    # image names that queried
    inms = { i.name: i for i in iqs }
    assert args.image_a in inms, "Image doesn't exist: %s" % args.image_a
    assert args.image_b in inms, "Image doesn't exist: %s" % args.image_b
    imga = inms[args.image_a]
    imgb = inms[args.image_b]
    logger.info("Compare images ...")
    logger.info("    Image A: %s" % imga.name)
    logger.info("    Image B: %s" % imgb.name)

    idiff = ImageDiff.objects.filter(img_a_id=imga.id, img_b_id=imgb.id).first()
    if idiff:
        if args.overwrite:
            logger.info("The image diff already exists, going to overwrite it")
            ImageDiffPKG.objects.filter(imgdiff_id=idiff.id).delete()
        else:
            #assert False, "The image diff already exists, skipped"
            logger.info("The image diff already exists, skipped")
            sys.exit(0)
    else:
        idiff = ImageDiff(img_a_id=imga.id, img_b_id=imgb.id)
        idiff.save()
    gen_imagediff(idiff, imga, imgb)


if __name__ == '__main__':
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO')
    logging.basicConfig(level=LOGLEVEL, format='%(levelname)-5s: %(message)s')

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('--image-a', '-a', action='store', required=True,
                        help="The name of image A")
    parser.add_argument('--image-b', '-b', action='store', required=True,
                        help="The name of image B")
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help="Overwrite the existing image diffs")
    args = parser.parse_args()
    
    assert os.environ.get("WORKSPACE")
    main(args)
