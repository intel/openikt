#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import F, Q
from django.db import transaction

if not "DJANGO_SETTINGS_MODULE" in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
    import django
    django.setup()

from app_diff.models import *
from lib.pushd import pushd
from lib.gitutils import gen_rangediff, parse_rangediff, find_mergebase, \
                         find_upstreamed_tag, prepare_repo, is_intel_patch, \
                         find_parent_merge_commit, gen_quiltdiff, \
                         gen_repo_path, get_patchid, get_upstream_tags

logger = logging.getLogger(__name__)


# find pr info by parent merge commit
def find_pr_by_pmc(git_cmt, djm_repo, ref):
    prno = None
    prurl = None
    pr_re = re.compile(r'^\s*!(\d+)\s+')
    pmc = find_parent_merge_commit(git_cmt, ref)
    if pmc:
        m = pr_re.search(pmc.summary)
        if m:
            prno = m.group(1)
            prurl = djm_repo.pr_url(prno)

    return (prno, prurl)

def find_pr_by_cmtmsg(git_cmt, djm_repo):
    prno = None
    prurl = None
    # label key
    lkey = 'Link'
    if git_cmt.trailers_dict and lkey in git_cmt.trailers_dict:
        for l in git_cmt.trailers_dict.get(lkey):
            prno = djm_repo.get_prno_by_url(l)
            if prno:
                prurl = l
                break
    return (prno, prurl,)

def find_pr(git_cmt, djm_repo, ref):
    prno = None
    prurl = None
    if djm_repo.project == 'openeuler/kernel':
        prno, prurl = find_pr_by_pmc(git_cmt, djm_repo, ref)
    elif djm_repo.project == 'anolis/cloud-kernel':
        prno, prurl = find_pr_by_cmtmsg(git_cmt, djm_repo)
    return (prno, prurl,)

def gen_quilt(url_b, ref_b, ref_a=None, repo_path=None):
    ref_dict = {
        'a': {
            'url': url_b,
            'ref': ref_a,
        },
        'b': {
            'url': url_b,
            'ref': ref_b,
        },
    }

    for ref in ref_dict.values():
        if ref['ref']:
            reftype, sha = peek_repo(ref['ref'], ref['url'])
            assert (reftype not in (INVALID_REPO, NOT_EXIST,)), \
                   "Tag/branch not exist: %s, %s" % (ref['url'], ref['ref'])
            ref['sha'] = sha
            ref['reftype'] = reftype

    if not repo_path:
        repo_path = gen_repo_path(url_b)
    os.makedirs(repo_path, exist_ok=True)
    # initialize the repo
    repo = prepare_repo(url_b, path=repo_path)
    rt_re = re.compile(r'-rt\d*\b')
    reltag_re = re.compile(r'(v[3-9]\.[\d\.\-rct]+)-.*\d{6}T\d{6}Z$')
    for ref in ref_dict.values():
        if ref['ref']:
            m = rt_re.search(ref['ref'])
            is_rt = True if m else False
            with pushd(repo_path):
                ref['base'], ref['basesha'] = get_baseline(ref['ref'], is_rt)
        ref['repo'] = repo
    if not ref_a:
        # if ref_a is omitted, use base of ref_b
        ref_dict['a']['ref'] = ref_dict['b']['base']
        ref_dict['a']['sha'] = ref_dict['b']['basesha']
        ref_dict['a']['base'] = ref_dict['b']['base']
        ref_dict['a']['basesha'] = ref_dict['b']['basesha']

    # generate range diff
    logger.info("Generate quilt: %s, %s" % \
                  (ref_dict['a']['ref'], ref_dict['b']['ref']))
    out = repo.git.rev_list("--no-merges", "%s..%s" % \
                              (ref_dict['a']['sha'], ref_dict['b']['sha']))
    quilts = []
    for i, c in enumerate(out.splitlines()):
        gc = repo.commit(c)
        quilts.append((i, None, c, gc.summary,))

    return (ref_dict, ((), (), (), quilts, (),))

def import_rdiff(repo_a, repo_b, rangediff, rd_out, intel_only=False,
                 chk_upstream=False, no_bulk_create=False, no_upstream_scan=False):
    # refer to korg repos to find the upstream status of the patch
    # django model object of kernel.org main repo
    djm_mrepo = Repository.objects.get(name='kernel.org main')
    # django model object of kernel.org stable repo
    djm_srepo = Repository.objects.get(name='kernel.org stable')
    # git object of kernel.org main repo
    git_mrepo = prepare_repo(djm_mrepo.url())
    # git object of kernel.org stable repo
    git_srepo = prepare_repo(djm_srepo.url())
    # get all korg patch ids
    korgqs = KorgPatch.objects.all().order_by('-id')
    # dict keyed by patch ids of korg main repo
    km_pids = {}
    # dict keyed by patch ids of korg stable repo
    ks_pids = {}
    for p in korgqs:
        if p.repo_id == djm_mrepo.id:
            km_pids[p.payload_hash] = {
                'commit': p.commit,
                'tag': p.tag
            }
        elif p.repo_id == djm_srepo.id:
            ks_pids[p.payload_hash] = {
                'commit': p.commit,
                'tag': p.tag
            }
    # rangediff out sample:
    #   [
    #       same_patches,
    #       cmconly_patches,
    #       updated_patches,
    #       new_patches,
    #       removed_patches
    #   ]
    ptype_dict =  {
        0: RangeDiffPatch.TYPE_SAME,
        1: RangeDiffPatch.TYPE_CMCO,
        2: RangeDiffPatch.TYPE_UPDATED,
        3: RangeDiffPatch.TYPE_NEW,
        4: RangeDiffPatch.TYPE_REMOVED,
    }
    # django model repo object
    djmrepo_a = rangediff.repo_a
    djmrepo_b = rangediff.repo_b
    repo_ids = [ djmrepo_a.id ]
    if djmrepo_b:
        repo_ids.append(djmrepo_b.id)
    else:
        djmrepo_b = djmrepo_a
    upqs = UpstreamedPatch.objects.filter(repo_id__in=repo_ids)
    up_dict = { "%i:%s" % (up.repo_id, up.commit): up for up in upqs }
    prqs = PR.objects.filter(repo_id__in=repo_ids)
    pr_dict = { pr.url: pr for pr in prqs }
    rdiff_patches = []
    for rd_out_idx, pl in enumerate(rd_out):
        pl_len = len(pl)
        logger.info("handling patch list #%i, len: %i" % (rd_out_idx, pl_len))
        for i, diff_data in enumerate(pl):
            logger.debug(diff_data[:-1])
            is_intel = False
            # commit a
            ca = diff_data[1]
            # commit b
            cb = diff_data[2]
            if ca:
                # commit object a
                coa = repo_a.commit(ca)
                # re-assign the long hexsha to ca
                ca = coa.hexsha
                if intel_only:
                    is_intel = is_intel_patch(coa)
            if cb:
                # commit object b
                cob = repo_b.commit(cb)
                # re-assign the long hexsha to cb
                cb = cob.hexsha
                if intel_only:
                    is_intel = is_intel_patch(cob)
            # ignore non-intel patches
            if not intel_only or is_intel:
                logger.info("#%i-%i/%i: commit a: %s, commit b: %s" % \
                              (rd_out_idx, i, pl_len, ca, cb))
                # rangediffpatch object
                rdp = RangeDiffPatch(rangediff_id=rangediff.id,
                                     patchtype=ptype_dict[rd_out_idx])
                logger.info("patch type: %s" % rdp.get_patchtype_display())
                if cb:
                    pr = None
                    ckey = "%i:%s" % (djmrepo_b.id, cb)
                    if ckey in up_dict:
                        # django model object
                        djmob = up_dict[ckey]
                        if not djmob.upstreamed_in and chk_upstream:
                            up_in = find_upstreamed_tag(cob, git_mrepo, km_pids) or \
                                      find_upstreamed_tag(cob, git_srepo, ks_pids)
                            if up_in:
                                djmob.upstreamed_in = up_in
                                djmob.save()
                        pr = djmob.pr_set.first()
                    else:
                        if no_upstream_scan:
                            up_in = None
                        else:
                            up_in = find_upstreamed_tag(cob, git_mrepo, km_pids) or \
                                      find_upstreamed_tag(cob, git_srepo, ks_pids)
                        djmob = UpstreamedPatch.import_patch(cob, up_in, djmrepo_b.id)
                        djmob.save()
                        logger.info("    imported commit b")
                        prno, prurl = find_pr(cob, djmob.repo, rangediff.refsha_b)
                        if prno:
                            logger.info("    find pr: %s" % prurl)
                            if prurl in pr_dict:
                                pr = pr_dict[prurl]
                            else:
                                pr = PR(prno=prno, url=prurl, repo_id=djmrepo_b.id)
                                pr.save()
                                logger.info("    imported pr")
                                pr_dict[prurl] = pr
                            pr.commits.add(djmob)
                    rdp.cmt_b_id = djmob.id
                    rdp.pr = pr
                if ca and ca != cb:
                    ckey = "%i:%s" % (djmrepo_a.id, ca)
                    if ckey in up_dict:
                        # django model object
                        djmoa = up_dict[ckey]
                        if not djmoa.upstreamed_in and chk_upstream:
                            up_in = find_upstreamed_tag(coa, git_mrepo, km_pids) or \
                                      find_upstreamed_tag(coa, git_srepo, ks_pids)
                            if up_in:
                                djmoa.upstreamed_in = up_in
                                djmoa.save()
                    else:
                        if no_upstream_scan:
                            up_in = None
                        else:
                            up_in = find_upstreamed_tag(coa, git_mrepo, km_pids) or \
                                      find_upstreamed_tag(coa, git_srepo, ks_pids)
                        djmoa = UpstreamedPatch.import_patch(coa, up_in, djmrepo_a.id)
                        djmoa.save()
                        logger.info("    imported commit a")
                    rdp.cmt_a_id = djmoa.id

                rdiff_patches.append(rdp)
                if no_bulk_create:
                    rdp.save()
                logger.info("    add rangediff patch")

    with transaction.atomic():
        if not no_bulk_create and rdiff_patches:
            RangeDiffPatch.objects.bulk_create(rdiff_patches)
        else:
            logger.info("No rangediff patch imported")

def get_lts_pids(base):
    kmv_re = re.compile(r'^(v?\d+\.\d+)(?:\.\d+){0,1}(-rc\d+|)(-rt\d+|)(-dontuse|-rebase|-patches|)')
    m = kmv_re.search(base)
    assert m, "Unrecognized kernel base version %s" % base

    kmv = m.group(1)
    djm_srepo = Repository.objects.get(name='kernel.org stable')
    git_srepo = prepare_repo(djm_srepo.url())
    # get the latest stable update kernel version
    tags = get_upstream_tags(git_srepo, out_type=dict)
    latest_tag = tags[kmv][-1]
    pids = {}
    out = git_srepo.git.rev_list("--no-merges", "%s..%s" % (base, latest_tag))
    for rev in out.splitlines():
        pid = get_patchid(rev, git_srepo)
        pids[pid] = rev
    return pids

def main(args):
    logger.info("Repo url(start ref): %s" % args.repo_url_from)
    logger.info("Repo url(end ref): %s" % args.repo_url_to)
    logger.info("Start ref: %s, base=%s" % (args.ref_from, args.base_from))
    logger.info("End ref: %s, base=%s" % (args.ref_to, args.base_to))
    logger.info("Type: %s" % args.diff_type)

    repo_qs = Repository.objects.all()
    repo_url_from = None
    repo_url_to = re.sub('(\/|\.git)$', '', args.repo_url_to)
    if args.repo_url_from and args.repo_url_from != args.repo_url_to:
        repo_url_from = re.sub('(\/|\.git)$', '', args.repo_url_from)
    # django model object of repo
    djmrepo_a = None
    djmrepo_b = None
    for r in repo_qs:
        u = r.url()
        if repo_url_to == u:
            djmrepo_b = r
        elif repo_url_from and repo_url_from == u:
            djmrepo_a = r
    assert djmrepo_b, "Unrecognized repo %s" % args.repo_url_to
    assert not repo_url_from or (repo_url_from and djmrepo_a), \
           "Unrecognized repo %s" % args.repo_url_from

    ref_a = re.sub('^origin\/', '', args.ref_from) if args.ref_from else None
    ref_b = re.sub('^origin\/', '', args.ref_to)
    base_a = re.sub('^origin\/', '', args.base_from) if args.base_from else None
    base_b = re.sub('^origin\/', '', args.base_to) if args.base_to else None
    rdqs = RangeDiff.objects.select_related(
             'repo_a', 'repo_b').filter(
               ref_a=ref_a,
               ref_b=ref_b,
               repo_b_id=djmrepo_b.id)
    if djmrepo_a:
        rdqs.filter(repo_a_id=djmrepo_a.id)
    else:
        rdqs.filter(repo_a__isnull=True)
    rdiff = rdqs.first()
    if rdiff:
        if args.overwrite:
            logger.info("The rangediff already exists, going to overwrite it")
            RangeDiffPatch.objects.filter(rangediff_id=rdiff.id).delete()
        else:
            assert False, "The rangediff already exists, skipped"
    else:
        rdiff = RangeDiff(ref_a=ref_a,
                          ref_b=ref_b,
                          repo_a=djmrepo_a,
                          repo_b_id=djmrepo_b.id)

    if args.diff_type == 'rangediff':
        ref_dict, diffs = gen_rangediff(repo_url_from or repo_url_to,
                                        repo_url_to,
                                        ref_a,
                                        ref_b,
                                        base_a,
                                        base_b)[:3]
        rdiff.diff = ref_dict['diff']
        # write the raw diff into file
        diff_fl = os.path.join(os.environ.get("WORKSPACE"), "diff.txt")
        logger.info("Dump the raw rangediff output to %s" % diff_fl)
        with open(diff_fl, 'w') as f:
            f.write(rdiff.diff)
    elif args.diff_type == 'quiltdiff':
        pids515 = None
        epids_a = None
        epids_b = None
        if repo_url_from.find('jammy') >= 0:
            pids515 = get_lts_pids('v5.15')
            epids_a = pids515
        if repo_url_to.find('jammy') >= 0:
            epids_b = pids515 or get_lts_pids('v5.15')
        ref_dict, diffs = gen_quiltdiff(repo_url_from or repo_url_to,
                                        repo_url_to,
                                        ref_a,
                                        ref_b,
                                        base_a,
                                        base_b,
                                        intel_only=args.intel_only==True,
                                        epids_a=epids_a,
                                        epids_b=epids_b)
    else:
        ref_dict, diffs = gen_quilt(repo_url_to,
                                    ref_b,
                                    ref_a)

    repo_a = ref_dict['a']['repo']
    repo_b = ref_dict['b']['repo']
    # update rangediff variables
    rdiff.created_date = timezone.now()
    rdiff.refsha_a = ref_dict['a']['sha']
    rdiff.refsha_b = ref_dict['b']['sha']
    rdiff.base_a = ref_dict['a']['base']
    rdiff.base_b = ref_dict['b']['base']
    rdiff.basesha_a = ref_dict['a']['basesha']
    rdiff.basesha_b = ref_dict['b']['basesha']
    dtype_dict = {
        'rangediff': RangeDiff.TYPE_GITDIFF,
        'quiltdiff': RangeDiff.TYPE_QUILTDIFF,
        'quilt': RangeDiff.TYPE_QUILT,
    }
    rdiff.difftype = dtype_dict[args.diff_type]
    # update rangediff in database
    try:
        rdiff.save()
    except django.db.utils.InternalError as e:
        logger.error(e)
        # don't save diff text in DB if get the exception:
        #   InternalError: invalid memory alloc request size xxx
        rdiff.diff = None
        rdiff.save()

    logger.info("Import the rangediff patches ...")
    import_rdiff(repo_a,
                 repo_b,
                 rdiff,
                 diffs,
                 args.intel_only==True,
                 args.check_upstream==True,
                 args.no_bulk_create==True,
                 args.no_upstream_scan==True)


if __name__ == '__main__':
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO')
    logging.basicConfig(level=LOGLEVEL, format='%(levelname)-5s: %(message)s')

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('--repo-url-from', '-f', action='store',
                        help="Repository url of start ref")
    parser.add_argument('--repo-url-to', '-t', action='store', required=True,
                        help="Repository url of end ref, could be omitted if duplicated")
    parser.add_argument('--ref-from', '-s', action='store',
                        help="Start point of git range, could be tag, branch or sha1")
    parser.add_argument('--ref-to', '-e', action='store', required=True,
                        help="End point of git range, could be tag, branch or sha1")
    parser.add_argument('--base-from', '-S', action='store',
                        help="Start point of git range base, could be tag, branch or sha1")
    parser.add_argument('--base-to', '-E', action='store',
                        help="End point of git range base, could be tag, branch or sha1")
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help="Overwrite the existing rangediff if it exists")
    parser.add_argument('--intel-only', '-i', action='store_true',
                        help="Only count the patches contributed by Intel")
    parser.add_argument('--check-upstream', '-u', action='store_true',
                        help="Check upstream status for patches already imported")
    parser.add_argument('--diff-type', '-T', default='rangediff',
                        choices=['rangediff', 'quiltdiff', 'quilt'],
                        help="Use text diff instead of git-range-diff")
    parser.add_argument('--no-bulk-create', '-B', action='store_true',
                        help="Don't use bulk_create to avoid memory alloc issue")
    parser.add_argument('--no-upstream-scan', '-U', action='store_true',
                        help="Don't scan upstream repos to associate the tag")
    args = parser.parse_args()
    
    assert os.environ.get("WORKSPACE")
    main(args)
