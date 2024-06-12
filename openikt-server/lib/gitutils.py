#!/usr/bin/env  python3

import sys
import os
import sh
import json
import io
import shutil
import re
import pty
import git
import time
import logging
from urllib.parse import urlsplit
from datetime import datetime, timedelta, timezone
from github import Github, GithubException, UnknownObjectException

from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.db.models import Q, F

from lib.pushd import pushd
from lib import utils


logger = logging.getLogger(__name__)


#
# Functions
#
IS_SHA = 1
IS_TAG = 2
IS_BRANCH = 3
NOT_EXIST = 4
INVALID_REPO = 5
def peek_repo(ref, url=None, repo=None):
    """
    Check if the ref is a branch or tag in the git repo.

    param repo_url: the url of the git repository
    param ref: ref of the branch or tag
    returns: (<IS_TAG|IS_BRANCH|NOT_EXIST>, sha1)
    """
    sha = None
    reftype = None
    # check if ref is a sha
    m = re.search(r'^[0-9a-f]{4,}$', ref)
    if m:
        sha = ref
        #FIXME: cannot check if the sha exists
        reftype = IS_SHA
    else:
        output = None
        if url:
            g = git.cmd.Git()
            try:
                output = g.ls_remote(
                  "--heads", "--tags", url, ref.replace("origin/", ''))
                if not output:
                    reftype = NOT_EXIST
            except git.exc.GitCommandError as e:
                reftype = INVALID_REPO
                logger.error("Invalid repo: %s" % url)
        else:
            try:
                r = repo or git.Repo(os.getcwd())
                output = r.git.ls_remote(
                  "--heads", "--tags", "origin", ref.replace("origin/", ''))
                if not output:
                    reftype = NOT_EXIST
            except git.exc.InvalidGitRepositoryError as e:
                reftype = INVALID_REPO
                logger.error("Current dir is not a valid repo")
        if output:
            outlst = output.splitlines()
            assert len(outlst) == 1, "Multiple results: %s" % output
            outlst = output.split()
            sha = outlst[0]
            m = re.search(r'^refs/heads', outlst[1])
            if m:
                reftype = IS_BRANCH
            else:
                reftype = IS_TAG

    return (reftype, sha,)

def gen_repo_path(url):
    wsdir = os.environ.get("WORKSPACE")
    project = re.sub('(^\/|\/$|\.git$)', '', urlsplit(url).path)
    if wsdir:
        path = os.path.join(wsdir, 'job', project)
    else:
        path = os.path.join(os.getcwd(), project)

    return path

@utils.retry(err_kw="HTTP code 503")
def prepare_repo(url, path=None, ref=None):
    if not path:
        path = gen_repo_path(url)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    try:
        logger.info("Clone repo %s ..." % url)
        repo = git.Repo.clone_from(url, path)
    except git.exc.GitCommandError as e:
        # repo already exists
        repo = git.Repo(path)
        # clean up the existing repo
        try:
            repo.git.am("--abort")
        except git.exc.GitCommandError as e:
            pass
        try:
            #FIXME: remove .git/rebase folder?
            repo.git.rebase("--abort")
        except git.exc.GitCommandError as e:
            pass
        repo.git.reset("--hard")
        repo.git.clean("-xdff")
        repo.git.checkout("--detach")
        # fetch remote(s)
        for rmt in repo.remotes:
            logger.info("Fetch remote %s ..." % rmt.name)
            repo.git.fetch("--tags",
                           "--force",
                           "--prune",
                           "--prune-tags",
                           rmt.name)

    if ref:
        reftype, sha = peek_repo(ref, repo=repo)
        if sha:
            try:
                repo.git.reset("--hard", sha)
                repo.git.checkout(sha)
            except git.exc.GitCommandError as e:
                pass

    return repo


def prepare_repos(repo_list, path=None):
    """ clone/fetch multiple repos in one folder
    parm repo_list: ((remote_name, url),...)
    """
    # clone/fetch the first repo
    origin_url = repo_list[0][1]
    repo = prepare_repo(origin_url, path)

    # add other repo as remote and fetch it
    for ri in repo_list[1:]:
        new_rmt = None
        # skip the duplicated repo
        if ri[1] == origin_url:
            continue
        try:
            logger.info("Try to add remote: %s - %s" % (ri[0], ri[1]))
            new_rmt = git.remote.Remote.add(repo, ri[0], ri[1])
        except git.exc.GitCommandError as e:
            # the remote already exist
            logger.warning(e)
        if new_rmt:
            # repo.git.fetch() prints real error message from
            # cmdline while rmt.fetch() prints useless message
            #rmt.fetch("--tags", verbose=True)
            logger.info("Fetch remote %s ..." % new_rmt.name)
            repo.git.fetch("--tags", new_rmt.name)

    return repo

def get_ref_commit(cmt_msg, repo_prj=None):
    # sample:
    #   [ Upstream commit 3780bb29311eccb7a1c9641032a112eed237f7e3 ]
    #   commit 96f60dfa5819a065bfdd2f2ba0df7d9cbce7f4dd upstream.
    rv = None
    if repo_prj and repo_prj == 'openkylin/linux':
        refcmt_re = r'^\s*(mainline|lts):\s*([\da-f]{8,})\s*$'
        m = re.search(refcmt_re, cmt_msg, flags=re.I|re.M)
        if m:
            rv = "%s:%s" % (m.group(1).lower(), m.group(2))
    else:
        refcmt_re = r'^\s*\[?\s*(?:upstream commit|commit) ([\da-f]{8,})(?: upstream\.?|)\s*\]?\s*$'
        m = re.search(refcmt_re, cmt_msg, flags=re.I|re.M)
        if m:
            rv = m.group(1)

    return rv

def parse_commit(git_commit):
    author = git_commit.author.email.lower()
    repo = git_commit.repo
    ref_cmt = get_ref_commit(git_commit.message)
    patch = {
        'commit': git_commit.hexsha,
        'payload_hash': get_patchid(git_commit.hexsha, repo),
        'subject': git_commit.summary,
        'files': sorted(git_commit.stats.files.keys()),
        'insert_size': git_commit.stats.total['insertions'],
        'delete_size': git_commit.stats.total['deletions'],
        'author': author,
        'author_date': git_commit.authored_datetime,
        'committer': git_commit.committer.email.lower(),
        'commit_date': git_commit.committed_datetime,
        'ref_commit': ref_cmt,
        'trailers': git_commit.trailers_dict,
    }

    return patch

## get_baseline()
#
# get the upstream kernel version for a revision(branch/tag/sha1)
#
# arg1: kernel branch/tag/sha1
# return: (kernek version, sha1)
#
def get_baseline(rev, is_rt=False, path=None, since=False, count_cherrypick=False):
    cmd = r"""
    declare rev=%s
    declare is_rt=%s
    declare path=%s
    declare since=%s
    declare count_cherrypick=%s
    declare tmpfl=/tmp/tags.$$
    declare opt=""
    test "${since}" == "True" && opt="--since='7 month ago'"
    test -n "${path}" && cd ${path}
    if [ "$count_cherrypick" == "True" ]; then
        git log --format='%%H:%%s' ${opt} ${rev} | \
          sed -rn 's/^([0-9a-f]+):Linux\s+([0-9]+\.[0-9\.rct-]*)\s*$/v\2.\1/p' \
             > $tmpfl
    else
        git log ${opt} \
          --decorate=full --simplify-by-decoration --pretty=oneline ${rev} | \
            sed -rn 's/^([0-9a-f]+)\s+\(tag(:\s+|:\s+refs\/tags\/)(v[0-9]+\.[0-9\.rct-]*),*.*$/\3.\1/p' \
              > $tmpfl
    fi
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        rm -f $tmpfl
        exit 1
    fi
    # output sample:
    #   v4.17-rc7.hash
    #   v4.17-rc6.hash
    #   v4.17-rc5.hash
    #   v4.17.hash
    # or:
    #   v4.14-rc8.hash
    #   v4.14.55.hash
    #   v4.14.54.hash
    # strip '-rcN' and commit, then sort, the last one is the latest base
    declare kernel_ver
    declare kernel_ver_base
    # disable errtrace here
    set +e
    if [[ "${rev}" =~ \-rt[0-9]+ ]] || [ "${is_rt}" == "True" ]; then
        # for rt kernel tag
        kernel_ver_base=$(\
            grep -E '\-rt[0-9]+' $tmpfl | \
              sed -r -e 's/-rc[0-9]+//' \
                     -e 's/-rt[0-9]+//' \
                     -e 's/\.[0-9a-f]{4,}$//' | \
                sort -t'.' -k1.2,1n -k2,2n -k3,3n | tail -1)
        # check if official release(i.e. w/o -rcN) exists
        kernel_ver=$(\
            grep -E "^${kernel_ver_base}-rt[0-9]+\.[0-9a-f]{4,}\$" $tmpfl | \
              sort | tail -1)
        test -z "$kernel_ver" && \
          kernel_ver=$(\
            grep -E "^${kernel_ver_base}-rc[0-9]+-rt[0-9]+" $tmpfl | \
              sort | tail -1)
    else
        # for kernel tag w/o -rtN
        kernel_ver_base=$(\
            grep -vE '\-rt[0-9]+' $tmpfl | \
              sed -r -e 's/-rc[0-9]+//' \
                     -e 's/-rt[0-9]+//' \
                     -e 's/\.[0-9a-f]{4,}$//' | \
                sort -t'.' -k1.2,1n -k2,2n -k3,3n | tail -1)
        # check if official release(i.e. w/o -rcN) exists
        kernel_ver=$(grep -E "^${kernel_ver_base}\.[0-9a-f]{4,}\$" $tmpfl)
        test -z "$kernel_ver" && \
          kernel_ver=$(\
              grep -E "^${kernel_ver_base}-rc[0-9]+\.[0-9a-f]{4,}" $tmpfl | \
                sort | tail -1)
    fi
    rm -f $tmpfl
    # note that the first precent sign is escaped by python
    echo "${kernel_ver%%.*} ${kernel_ver##*.}"
    """ % (rev, str(is_rt), path or "", str(since), str(count_cherrypick))
    (rc, out, err) = utils.cmd_pipe(cmd)
    if rc != 0:
        raise utils.ShCmdError("get kernel version failed: %s\n%s" % \
                                 (rev, err))
    return out.strip().split()


def gen_rangediff(url_a, url_b, ref_a, ref_b, base_a=None,
                  base_b=None, repo_path=None, check_base=True):
    ref_dict = {
        'a': {
            'url': url_a,
            'ref': ref_a,
            'base': base_a,
        },
        'b': {
            'url': url_b,
            'ref': ref_b,
            'base': base_b,
        },
    }
    for ref in ref_dict.values():
        reftype, sha = peek_repo(ref['ref'], ref['url'])
        assert (reftype not in (INVALID_REPO, NOT_EXIST,)), \
               "Tag/branch not exist: %s, %s" % (ref['url'], ref['ref'])
        ref['sha'] = sha
        ref['reftype'] = reftype

    # initialize the repo(s)
    if not repo_path:
        repo_path = gen_repo_path(url_b)
    if url_a != url_b:
        shutil.rmtree(repo_path, ignore_errors=True)
    os.makedirs(repo_path, exist_ok=True)
    # clone repos everytime for multiple remotes
    repo = prepare_repos((
        ("rangediff_b", url_b,),
        ("rangediff_a", url_a,),
    ), repo_path)
    rt_re = re.compile(r'-rt\d*\b')
    reltag_re = re.compile(r'(v[3-9]\.[\d\.\-rct]+)-.*\d{6}T\d{6}Z$')
    for ref in ref_dict.values():
        if ref['base']:
            reftype, sha = peek_repo(ref['base'], ref['url'])
            assert (reftype not in (INVALID_REPO, NOT_EXIST,)), \
                   "Tag/branch not exist: %s, %s" % (ref['url'], ref['base'])
            ref['basesha'] = sha
        else:
            m = rt_re.search(ref['ref'])
            is_rt = True if m else False
            with pushd(repo_path):
                ref['base'], ref['basesha'] = get_baseline(ref['sha'], is_rt)
        if ref['reftype'] == IS_TAG and check_base:
            # check if the tag consistence
            m = reltag_re.search(ref['ref'])
            if m:
                baseline_bytag = m.group(1)
                assert (ref['base'] == baseline_bytag), \
                       "Baseline inconsistent: %s, %s(from tag)" % \
                         (ref['base'], baseline_bytag)
        # use basesha instead of baseline(i.e. kernel version) in case
        # some repository has no upstream tag, e.g. anolis/cloud-kernel
        ref['range'] = "%s..%s" % (ref['basesha'], ref['sha'])
        ref['repo'] = repo

    # generate range diff
    logger.info("Generate rangediff: %s, %s" % \
                  (ref_dict['a']['range'], ref_dict['b']['range']))
    diff_text = repo.git.range_diff(ref_dict['a']['range'],
                                    ref_dict['b']['range'])
    logger.info("Parse the rangediff ...")
    diffs = parse_rangediff(diff_text, repo)
    ref_dict['diff'] = diff_text

    return (ref_dict, diffs,)

def is_same_patchid(sha1_a, sha1_b, repo=None):
    pid_a = get_patchid(sha1_a, repo)
    pid_b = get_patchid(sha1_b, repo)
    return (pid_a and pid_b and pid_a == pid_b)

def check_updated_patch(cmconly_patches, updated_patches,
                        up_candidate, up_confirmed, psb_codechg, repo=None):
    if up_confirmed:
        updated_patches.append(up_candidate)
    elif psb_codechg:
        # check if the patch-ids is the same
        if is_same_patchid(up_candidate[1], up_candidate[2], repo):
            cmconly_patches.append(up_candidate)
        else:
            updated_patches.append(up_candidate)
    elif not psb_codechg:
        cmconly_patches.append(up_candidate)

# git-range-diff sometimes gives a twisted diff which is a false positive:
# 8025:  7f0de68338ad ! 2707:  6d6e4bb1acc7 Revert "drm/i915/display: Re-add check for low voltage sku...
# 2707:  6d6e4bb1acc7 ! 8025:  7f0de68338ad drm/i915/display: Remove check for low voltage sku...
# or twisted in loop:
# commit_a ! commit_b
# commit_b ! commit_c
# commit_c ! commit_a
def _rm_twisted_diff(patches):
    cmt_a_dict = {}
    cmt_b_dict = {}
    for p in patches:
        cmt_a_dict[p[1]] = p[2]
        cmt_b_dict[p[2]] = p[1]
    # twisted commits
    tw_cmts = { a: True for a in cmt_a_dict.keys() if a in cmt_b_dict }
    if tw_cmts:
        rv = [ p for p in patches if p[1] not in tw_cmts ]
    else:
        rv = patches
    return rv

def parse_rangediff(diff_text, repo=None):
    if not repo:
        repo = git.Repo()
    # rl_rep: re pattern for result lines
    # e.g.: " 1:  c0debee = 2:  cab005e Add a helpful message at the start"
    #       " X:  effdc5234c5ee <    -:  ------------- net: stmmac: fix ..."
    rl_rep = re.compile(r'^\s*[\d-]+:\s+([0-9a-f-]{10,})\s+([=!><])\s+[\d-]+:\s+([0-9a-f-]{10,})\s+(\S.*)$')
    # commit message meta info.
    cm_metas = [
        'Change-Id',
        'Signed-off-by',
        'Reviewed-on',
        'Reviewed-by',
        'Tested-by',
        'Tracked-On',
        'Acked-by',
        'Link',
    ]
    # cm_rep: re pattern for commit message meta info. line
    cm_rep = re.compile(r"^\s*(%s):" % '|'.join(cm_metas), flags=re.I)

    same_patches = []
    new_patches = []
    # cmconly_patches: commit message change only patches
    cmconly_patches = []
    updated_patches = []
    removed_patches = []
    # updated patch candidate
    up_candidate = None
    # flag for the first hunk header
    is_1st_hheader = False
    # flag for if it is a diff block
    in_diff = None
    # flag for detecting a possible code change line
    psb_codechg = False
    # flag for confirming the update patch
    up_confirmed = False
    # diff text between updated-patch-pair
    payload = []
    # sequence no in the rangediff
    seq = 0
    # sample:
    #    @@ -14,9 +14,9 @@
    #    ^    identifier position
    #      ^  identifier offset 2 position
    #     --- a/arch/x86/include/asm/cpufeatures.h
    #     +++ b/arch/x86/include/asm/cpufeatures.h
    #     @@
    #     ^   identifier offset 1 position
    #       ^ identifier offset 3 position
    #    + #define X86_FEATURE_MD_CLEAR      (18*32+10)...
    # the postion of the identifier: +/-
    iidx = None
    # the postition of identifier offset 1
    io1idx = None
    # the postition of identifier offset 2
    io2idx = None
    # the postition of identifier offset 3
    io3idx = None
    #
    # git range-diff output sample:
    #   -:  ------- > 1:  0ddba11 Prepare for the inevitable! <-- result line
    #   1:  c0debee = 2:  cab005e Add a helpful message at    <-- result line
    #   2:  f00dbal ! 3:  decafe1 Describe a bug              <-- result line
    #       @@ -1,3 +1,3 @@                                   <-- 1st line of diff
    #        Author: A U Thor <author@example.com>
    #
    #       -TODO: Describe a bug
    #       +Describe a bug
    #       @@ -324,5 +324,6
    #         This is expected.
    #
    #       -+What is unexpected is that it will also crash.
    #       ++Unexpectedly, it also crashes. This is a bug, and the jury is
    #       ++still out there how to fix it best. See ticket #314 for details.
    #
    #         Contact
    #   3:  bedead < -:  ------- TO-UNDO
    #
    for l in diff_text.splitlines():
        m = rl_rep.search(l)
        if m:
            # this is result line
            # check if the previous lines are diff content
            if in_diff:
                check_updated_patch(cmconly_patches,
                                    updated_patches,
                                    up_candidate,
                                    up_confirmed,
                                    psb_codechg,
                                    repo)
                # reset the flags and data
                in_diff = False
                up_confirmed = False
                psb_codechg = False
                up_candidate = None
                payload = []

            # increase sequence no.
            seq += 1
            # extract commit ids and commit message
            rev_a = m.group(1)
            rev_b = m.group(3)
            c_msg = m.group(4)
            # don't need to rev_parse
            #sha_re = re.compile(r'^[0-9a-f]{4,}$')
            #rev_a = repo.git.rev_parse(rev_a) if sha_re.search(rev_a) else None
            #rev_b = repo.git.rev_parse(rev_b) if sha_re.search(rev_b) else None
            if m.group(2) == '=':
                same_patches.append((seq, rev_a, rev_b, c_msg))
            elif m.group(2) == '>':
                new_patches.append((seq, None, rev_b, c_msg))
            elif m.group(2) == '!':
                is_1st_hheader = True
                up_candidate = [seq, rev_a, rev_b, c_msg, payload]
            elif m.group(2) == '<':
                removed_patches.append((seq, rev_a, None, c_msg))
        else:
            # this is diff line, need to figure out
            # whether there is any code change
            payload.append(l)
            if is_1st_hheader:
                # this is the first hunk header
                in_diff = True
                # reset the flags
                is_1st_hheader = False

                iidx = l.find(r'@')
                io1idx = iidx + 1
                io2idx = iidx + 2
                io3idx = iidx + 3
            elif not up_confirmed:
                llen = len(l)
                if llen >= io2idx and l[io1idx] in '+-':
                    # check if there is a +/- at the io1idx postion. If yes,
                    # this must be a code change line. Set flag and skip all
                    # the following diff lines
                    up_confirmed = True
                elif not psb_codechg and llen >= io3idx and l[iidx] in '+-':
                    # check if insertion/deletion line is a commit message line
                    # or not. If not, this line could be a code change, set
                    # psb_codechg = True, igmore all the following diff lines
                    # and compare the patch ids later
                    m = cm_rep.search(l[io1idx:])
                    if not m:
                        psb_codechg = True

    # check the last updated patch out of the loop
    if in_diff:
        check_updated_patch(cmconly_patches,
                            updated_patches,
                            up_candidate,
                            up_confirmed,
                            psb_codechg,
                            repo)

    # remove patches from the twisted diff
    if cmconly_patches:
        cmconly_patches = _rm_twisted_diff(cmconly_patches)
    if updated_patches:
        updated_patches = _rm_twisted_diff(updated_patches)
    return [same_patches, cmconly_patches,
            updated_patches, new_patches, removed_patches]

def get_patchid(commit, repo=None, pid_only=True):
    if not repo:
        repo = git.Repo()
    out = repo.git.execute(
            ["git show %s | git patch-id" % commit], shell=True).split()
    if out:
        rv = out[0] if pid_only else out
    else:
        rv = None
    return rv

# compare two versions, like <major ver>.<minor ver>[.<micro ver>]
#   if ver a > ver b, return 1
#   if ver a == ver b, return 0
#   if ver a < ver b, return -1
def cmp_ver(ver_a, ver_b):
    rv = 0
    ver_a_fds = ver_a.lstrip('v').split('.')
    ver_b_fds = ver_b.lstrip('v').split('.')
    a_fd_len = len(ver_a_fds)
    b_fd_len = len(ver_b_fds)
    for i in range(min(a_fd_len, b_fd_len)):
        va = int(ver_a_fds[i])
        vb = int(ver_b_fds[i])
        if va == vb:
            continue
        elif va < vb:
            rv = -1
            break
        elif va > vb:
            rv = 1
            break
    if rv == 0:
        if a_fd_len < b_fd_len:
            rv = -1
        elif a_fd_len > b_fd_len:
            rv = 1
    return rv

# note: tags should be generated by git-tag --sort=v:refname
def sort_upstream_tags(tags, start_tag=None,
                       reverse=False, out_type=list, rc=False):
    rv = []
    if not tags:
        return rv

    kmv_re = re.compile(r'^(v?\d+\.\d+)(?:\.\d+){0,1}(-rc\d+|)(-rt\d+|)(-dontuse|-rebase|-patches|)')
    rc_re = re.compile(r'^(v\d+\.\d+(?:\.\d+){0,1})(-rc\d+)')
    released_tags = []
    rctag_dict = {}
    started = False
    max_kmv = '0'
    for tag in tags:
        m = kmv_re.search(tag)
        if m:
            if start_tag and not started:
                if tag == start_tag:
                    started = True
                continue

            # strip -dontuse tag
            if m.group(4):
                continue

            kmv = m.group(1)
            if m.group(2):
                # is a rc tag

                m = rc_re.search(tag)
                kv = m.group(1)
                rctag_dict.setdefault(kv, []).append(tag)
            else:
                released_tags.append(tag)
            # check the max_kmv
            if cmp_ver(kmv, max_kmv) == 1:
                max_kmv = kmv

    sorted_tags = []
    for tag in released_tags:
        if rc and tag in rctag_dict:
            sorted_tags.extend(rctag_dict[tag])
        sorted_tags.append(tag)
    # add the last set of rc tags which have no official release tag
    if max_kmv in rctag_dict and max_kmv not in released_tags:
        sorted_tags.extend(rctag_dict[max_kmv])

    if reverse:
        sorted_tags.reverse()
    if out_type == list:
        rv = sorted_tags
    elif out_type == dict:
        # convert list into dict
        rv = {}
        for tag in sorted_tags:
            m = kmv_re.search(tag)
            kmv = m.group(1)
            rv.setdefault(kmv, []).append(tag)

    return rv

def get_upstream_tags(repo=None, start_tag=None,
                      reverse=False, out_type=list, rc=False):
    if not repo:
        # try to load gitpython.repo from current dir
        # git.exc.InvalidGitRepositoryError might be raised
        repo = git.Repo()
    tags = repo.git.tag('--sort', 'v:refname').splitlines()
    return sort_upstream_tags(tags, start_tag, reverse, out_type, rc)

def find_mergebase(commit, repo=None, rc=True, tag_re=None):
    mbase = None
    if not tag_re:
        tag_re = r'v[2-9]\.*'
    try:
        if not repo:
            repo = git.Repo()
        tags = repo.git.tag('--contains', commit, '--list',
                            tag_re, '--sort', 'v:refname').splitlines()
        tags = sort_upstream_tags(tags, rc=rc)
        mbase = tags[0]
        logger.info("find merge base: %s" % mbase)
    except:
        pass
    return mbase

# functions for identifying similar patches by comparing the diff context
def get_hunks(diff, with_context=False):
    hunks = {}
    diff_re = re.compile(r'^diff --git a\/(\S+) b\/')
    bin_re = re.compile(r'^Binary files a\/')
    hunk_re = re.compile(r'^@@ ')
    # changed lines
    chgl_re = re.compile(r'^([+-])[^+-]*')
    curr_file = None
    curr_hunk = None
    for l in diff.splitlines():
        if curr_file == None:
            m = diff_re.search(l)
            if m:
                curr_file = m.group(1)
                curr_hunk = None
                hunks[curr_file] = []
        else:
            #if not hit_hunk:
            if curr_hunk == None:
                m1 = hunk_re.search(l)
                m2 = bin_re.search(l)
                if m1:
                    curr_hunk = []
                elif m2:
                    # binary file has no +/- line, os this
                    # is the end of current binary file
                    curr_file = None
            else:
                m1 = diff_re.search(l)
                m2 = hunk_re.search(l)
                m3 = chgl_re.search(l)
                if m1:
                    hunks[curr_file].append(curr_hunk)
                    curr_file = m1.group(1)
                    curr_hunk = None
                    hunks[curr_file] = []
                elif m2:
                    if curr_hunk:
                        hunks[curr_file].append(curr_hunk)
                    curr_hunk = []
                else:
                    if with_context or m3:
                        curr_hunk.append(l)

    if curr_hunk:
        hunks[curr_file].append(curr_hunk)

    return hunks

def similar_hunks(a_hunks, b_hunks):
    #FIXME: use match ratio
    def same_hunk(h1, h2):
        rv = True
        if len(h1) == len(h2):
            for i in range(len(h1)):
                if h1[i] != h2[i]:
                    rv = False
                    break
        else:
            rv = False
        return rv

    if a_hunks == [] and b_hunks == []:
        # this is binary file
        sim = 1
        total = 1
    else:
        sim = 0
        total = max(len(a_hunks), len(b_hunks))
        for ha in a_hunks:
            for i, hb in enumerate(b_hunks):
                if (same_hunk(ha, hb)):
                    sim += 1
                    del b_hunks[i]
                    break
    return (sim, total)

def similar_patches(diff_a, diff_b):
    sim = 0
    total = 0
    b_files = {}
    a_hunks = get_hunks(diff_a)
    b_hunks = get_hunks(diff_b)
    for f in b_hunks.keys():
        fname = os.path.split(f)[-1]
        if fname in b_files:
            b_files[fname].append(f)
        else:
            b_files[fname] = [ f ]
    # go through files in a_hunks
    for f, h in a_hunks.items():
        s = 0
        t = len(h)
        fname = os.path.split(f)[-1]
        if f in b_hunks:
            s, t = similar_hunks(h, b_hunks[f])
            del b_hunks[f]
            b_files[fname].remove(f)
        elif fname in b_files:
            # in case file path get changed
            for fb in b_files[fname]:
                if fb not in a_hunks:
                    s2, t2 = similar_hunks(h, b_hunks[fb])
                    # if all hunks matched, count it
                    if s2 == t2:
                        s = s2
                        t = t2
                        del b_hunks[fb]
                        b_files[fname].remove(fb)
                        break
        sim += s
        total += t
    # go throught files only in b_hunks
    for f, h in b_hunks.items():
        total += len(h)
    return ((sim+0.0)/total, sim, total)

# find the similar patch by comparing hunks
def find_similar_patch2(gitcmt_a, gitrepo_b, ref_b=None, min_ratio=0.8,
                        sub_exact_match=True, latest_first=False, fast=False):
    matched = None
    # narrow down the similar patches by search subject
    params = [ '--format=%H', '--grep' ]
    sub = re.escape(gitcmt_a.summary)
    # unescape chars '{', '}', because \{, \} are metacharacters for git-grep
    sub = re.sub(r'\\([{}])', r'\1', sub)
    if sub_exact_match:
        params.append('^%s$' % sub)
    else:
        params.append(sub)
    if not latest_first:
        params.append('--reverse')
    if ref_b:
        # search on a particular branch/tag
        params.append(ref_b)
    out = gitrepo_b.git.log(params)
    # diff text of commit a
    da = gitcmt_a.repo.git.show(gitcmt_a.hexsha)
    max_ratio = (0.0, 0, 0)
    for rev in out.splitlines():
        # diff text of commit b
        db = gitrepo_b.git.show(rev)
        ratio = similar_patches(da, db)
        if ratio[0] == 1.0:
            matched = rev
            max_ratio = ratio
            break
        elif ratio[0] >= min_ratio:
            if fast:
                # match strategy: fast or best
                #   fast: find the first qualified patch and stop
                #   best: scan all patches in the list and find the best
                matched = rev
                max_ratio = ratio
                break
            else:
                if ratio[0] > max_ratio[0]:
                    max_ratio = ratio
                    matched = rev
    if matched:
        matched = gitrepo_b.commit(matched)
        logger.info("similar patch matched: %s - %s(%i/%i, %s)" % \
                      (gitcmt_a.hexsha, matched.hexsha, max_ratio[1],
                       max_ratio[2], gitrepo_b.remotes.origin.url))

    return (matched, max_ratio)

# find the similar patch by searching files
def find_similar_patch_by_files(gitcmt_a, gitrepo_b, ref_b=None, since=True,
                                latest_first=False, min_ratio=None, fast=False):
    files = []
    for f in gitcmt_a.stats.files.keys():
        if os.path.isfile(os.path.join(gitrepo_b.working_dir, f)):
            files.append(f)
    if not files:
        logger.info("No file matched in repo b")
        return (None, None)
    # narrow down the similar patches by search subject
    git_params = [ '--format=%H' ]
    if since:
        cmt_date = gitcmt_a.authored_datetime.strftime("%Y-%m-%d %H:%M:%S %z")
        git_params.append('--since="%s"' % cmt_date)
    if not latest_first:
        git_params.append('--reverse')
    if ref_b:
        # search on a particular branch/tag
        git_params.append(ref_b)
    git_params.extend(files)
    out = gitrepo_b.git.log(git_params)
    rev_list = out.splitlines()
    if not rev_list:
        logger.info("No patch found by files in repo b")
        return (None, None)
    params = {
        'gitcmt_a': gitcmt_a,
        'gitrepo_b': gitrepo_b,
        'rev_list': rev_list,
        'fast': fast
    }
    if min_ratio:
        params['min_ratio'] = min_ratio
    return find_similar_patch(**params)

# find the similar patch by searching author
def find_similar_patch_by_author(gitcmt_a, gitrepo_b, ref_b=None, since=True,
                                 latest_first=False, min_ratio=None, fast=False):
    if not gitcmt_a.author.email:
        logger.info("Cannot find author's email")
        return (None, None)
    # narrow down the similar patches by search subject
    git_params = [ '--format=%H' ]
    git_params.append('--author=%s' % gitcmt_a.author.email)
    if since:
        cmt_date = gitcmt_a.authored_datetime.strftime("%Y-%m-%d %H:%M:%S %z")
        git_params.append('--since="%s"' % cmt_date)
    if not latest_first:
        git_params.append('--reverse')
    if ref_b:
        # search on a particular branch/tag
        git_params.append(ref_b)
    logger.debug(" ".join(git_params))
    out = gitrepo_b.git.log(git_params)
    rev_list = out.splitlines()
    if not rev_list:
        logger.info("No patch found by author in repo")
        return (None, None)
    params = {
        'gitcmt_a': gitcmt_a,
        'gitrepo_b': gitrepo_b,
        'rev_list': rev_list,
        'fast': fast
    }
    if min_ratio:
        params['min_ratio'] = min_ratio
    return find_similar_patch(**params)

# find the similar patch by searching subject
def find_similar_patch_by_sub(gitcmt_a, gitrepo_b, ref_b=None,
                              since=False, sub_exact_match=True,
                              latest_first=False, min_ratio=None, fast=False):
    # narrow down the similar patches by search subject
    git_params = [ '--format=%H', '--grep' ]
    sub = re.escape(gitcmt_a.summary)
    # unescape chars '{', '}', because \{, \} are metacharacters for git-grep
    sub = re.sub(r'\\([{}()])', r'\1', sub)
    if sub_exact_match:
        git_params.append('^%s$' % sub)
    else:
        git_params.append(sub)
    if since:
        cmt_date = gitcmt_a.authored_datetime.strftime("%Y-%m-%d %H:%M:%S %z")
        git_params.append('--since="%s"' % cmt_date)
    if not latest_first:
        git_params.append('--reverse')
    if ref_b:
        # search on a particular branch/tag
        git_params.append(ref_b)
    try:
        out = gitrepo_b.git.log(git_params)
    except git.exc.GitCommandError as e:
        logger.error(e)
        return (None, None)
    rev_list = out.splitlines()
    if not rev_list:
        logger.info("No patch found by subject in repo")
        return (None, None)
    params = {
        'gitcmt_a': gitcmt_a,
        'gitrepo_b': gitrepo_b,
        'rev_list': rev_list,
        'fast': fast
    }
    if min_ratio:
        params['min_ratio'] = min_ratio
    return find_similar_patch(**params)

def find_similar_patch(gitcmt_a, gitrepo_b, rev_list, min_ratio=0.8, fast=False):
    matched = None
    max_ratio = (0.0, 0, 0)
    if rev_list:
        # get diff text of commit a
        da = gitcmt_a.repo.git.show(gitcmt_a.hexsha)
        for rev in rev_list:
            # diff text of commit b
            db = gitrepo_b.git.show(rev)
            ratio = similar_patches(da, db)
            if ratio[0] == 1.0:
                matched = rev
                max_ratio = ratio
                break
            elif ratio[0] >= min_ratio:
                if fast:
                    # match strategy: fast or best
                    #   fast: find the first qualified patch and stop
                    #   best: scan all patches in the list and find the best
                    matched = rev
                    max_ratio = ratio
                    break
                else:
                    if ratio[0] > max_ratio[0]:
                        max_ratio = ratio
                        matched = rev
        if matched:
            matched = gitrepo_b.commit(matched)
            logger.info("similar patch matched: %s - %s(%i/%i, %s)" % \
                          (gitcmt_a.hexsha, matched.hexsha, max_ratio[1],
                           max_ratio[2], gitrepo_b.remotes.origin.url))

    return (matched, max_ratio)

def find_upstreamed_tag(gitcmt_a, gitrepo_b, pids_b=None, fast=True):
    def find_tag_by_pid(gitcmt, pids):
        tag = None
        if pids:
            pid = get_patchid(gitcmt.hexsha, gitcmt.repo)
            if pid in pids:
                logger.info("matched upstream patch by pid: %s, tag=%s" % \
                              (pids[pid]['commit'], pids[pid]['tag']))
                tag = pids[pid]['tag'] or pids[pid]['commit']
        return tag

    tag = find_tag_by_pid(gitcmt_a, pids_b)
    if tag:
        return tag

    logger.info("Try to find patch by files")
    c, stat = find_similar_patch_by_files(gitcmt_a, gitrepo_b)
    if not fast and not c:
        logger.info("Try to find patch by author")
        c, stat = find_similar_patch_by_author(gitcmt_a, gitrepo_b)
        if not c:
            logger.info("Try to find patch by subject")
            c, stat = find_similar_patch_by_sub(gitcmt_a,
                                                gitrepo_b,
                                                sub_exact_match=False)
    if c:
        tag = find_tag_by_pid(c, pids_b) or \
                find_mergebase(c.hexsha, gitrepo_b)
    return tag

def find_parent_merge_commit(git_cmt, ref):
    # parent merge commit
    pmc = None
    repo = git_cmt.repo
    cmt_range = "%s..%s" % (git_cmt.hexsha, ref)
    try:
        # cmd: git rev-list --ancestry-path --merges <sha1>..<tag/branch>
        out = repo.git.rev_list("--ancestry-path", "--merges", cmt_range)
    except git.exc.GitCommandError as e:
        out = None
        logger.error(e)
    if not out:
        logger.warning("No parent merge commit found: %s" % cmt_range)
        return
    revlist = out.splitlines()
    revlist.reverse()
    for mc in revlist:
        # cmd: git merge-base --is-ancestor cmt <merge_cmt>^
        # note: <merge cmt>^ means the last commit of base branch before merge
        try:
            repo.git.merge_base("--is-ancestor", git_cmt.hexsha, mc + '^')
        except git.exc.GitCommandError as e:
            if str(e).find('exit code(1)') >= 0:
                pmc = mc
                break
            else:
                logger.error(e)
    return repo.commit(pmc) if pmc else None

def is_intel_patch(git_cmt):
        return git_cmt.author.email.lower().find('intel.com') > 0

def gen_quiltdiff(url_a, url_b, ref_a, ref_b, base_a=None, base_b=None,
                  repo_path=None, check_base=True, intel_only=True, epids_a=None,
                  epids_b=None):
    ref_dict = {
        'a': {
            'url': url_a,
            'ref': ref_a,
            'base': base_a,
            # excluded patch id dict
            'epids': epids_a or [],
        },
        'b': {
            'url': url_b,
            'ref': ref_b,
            'base': base_b,
            'epids': epids_b or [],
        },
    }
    for ref in ref_dict.values():
        reftype, sha = peek_repo(ref['ref'], ref['url'])
        assert (reftype not in (INVALID_REPO, NOT_EXIST,)), \
               "Tag/branch not exist: %s, %s" % (ref['url'], ref['ref'])
        ref['sha'] = sha
        ref['reftype'] = reftype

    # initialize the repo(s)
    ref_dict['b']['path'] = repo_path or gen_repo_path(url_b)
    os.makedirs(ref_dict['b']['path'], exist_ok=True)
    ref_dict['b']['repo'] = prepare_repo(url_b, ref_dict['b']['path'])
    if url_a == url_b:
        ref_dict['a']['path'] = ref_dict['b']['path']
        ref_dict['a']['repo'] = ref_dict['b']['repo']
    else:
        ref_dict['a']['path'] = gen_repo_path(url_a)
        os.makedirs(ref_dict['a']['path'], exist_ok=True)
        ref_dict['a']['repo'] = prepare_repo(url_a, ref_dict['a']['path'])
    rt_re = re.compile(r'-rt\d*\b')
    reltag_re = re.compile(r'(v[3-9]\.[\d\.\-rct]+)-.*\d{6}T\d{6}Z$')
    for ref in ref_dict.values():
        repo = ref['repo']
        if ref['base']:
            basetype, sha = peek_repo(ref['base'], ref['url'])
            # only accept base in tag or sha
            assert basetype in (IS_TAG, IS_SHA,), \
              "Invalid base: %s, %s(type: %i)" % (ref['url'], ref['base'], basetype)
            ref['basesha'] = sha
        else:
            m = rt_re.search(ref['ref'])
            is_rt = True if m else False
            with pushd(ref['path']):
                ref['base'], ref['basesha'] = get_baseline(ref['sha'], is_rt)
            basetype = IS_TAG
        if check_base and ref['reftype'] == basetype == IS_TAG:
            # check if the tag consistence
            m = reltag_re.search(ref['ref'])
            if m:
                baseline_bytag = m.group(1)
                assert (ref['base'] == baseline_bytag), \
                       "Baseline inconsistent: %s, %s(from tag)" % \
                         (ref['base'], baseline_bytag)
        # generate range diff
        # use basesha instead of baseline(i.e. kernel version) in case
        # some repository has no upstream tag, e.g. anolis/cloud-kernel
        ref['range'] = "%s..%s" % (ref['basesha'], ref['sha'])
        logger.info("Generate quilt %s: %s" % (ref['ref'], ref['range']))
        revs = repo.git.rev_list("--no-merges", "--reverse", ref['range'])
        ref['quilt'] = []
        # dict: mapping commit to git commit object
        ref['gitcs'] = {}
        # dict: mapping commit to pid
        ref['pids'] = {}
        epids = ref['epids']
        for c in revs.splitlines():
            pid  = get_patchid(c, repo)
            if pid in epids:
                logger.info("    exluded commit %s, up=%s" % (c, epids[pid]))
                continue
            gitc = repo.commit(c)
            if intel_only and not is_intel_patch(gitc):
                continue

            ref['quilt'].append(gitc)
            ref['gitcs'][c]  = gitc
            ref['pids'][c]  = pid

    ref_b = ref_dict['b']
    # dict: mapping pid to commits
    ref_b['pid2c'] = {}
    # dict: mapping file to commits
    ref_b['file2c'] = {}
    # dict: mapping author to commits
    ref_b['author2c'] = {}
    for gitc in ref_b['quilt']:
        c = gitc.hexsha
        pid = ref_b['pids'][c]
        if pid:
            if pid in ref_b['pid2c']:
                ref_b['pid2c'][pid].append(c)
            else:
                ref_b['pid2c'][pid] = [ c ]
        ae = gitc.author.email.lower()
        if ae in ref_b['author2c']:
            ref_b['author2c'][ae].append(c)
        else:
            ref_b['author2c'][ae] = [ c ]
        for f in gitc.stats.files.keys():
            if f in ref_b['file2c']:
                ref_b['file2c'][f].append(c)
            else:
                ref_b['file2c'][f] = [ c ]
    # compare commit a with quilt b one by one
    ref_a = ref_dict['a']
    # a = b
    same = []
    # commit message changed only
    cmco = []
    updated = []
    new = []
    removed = []
    found = {}
    for seq, gitc in enumerate(ref_a['quilt']):
        c = gitc.hexsha
        pid = ref_a['pids'][c]
        logger.info("commit(from quilt a): %s" % c)
        if c in ref_b['gitcs']:
            same.append((seq, c, c, gitc.summary,))
            found[c] = True
            logger.info("    added in same")
        elif pid and pid in ref_b['pids']:
            cb = ref_b['pid2c'][pid][0]
            gitcb = ref_b['gitcs'][cb]
            for cb_ in ref_b['pid2c'][pid]:
                found[cb_] = True
            if gitc.message == gitcb.message:
                same.append((seq, c, cb, gitc.summary,))
                logger.info("    added in same")
            else:
                cmco.append((seq, c, cb, gitcb.summary,))
                logger.info("    added in cmco")
        else:
            gitcb = None
            # search by files
            revs = [ cmt for f in gitc.stats.files.keys() \
                           for cmt in ref_b['file2c'].get(f, []) ]
            if revs:
                gitcb, _ = find_similar_patch(gitc, ref_b['repo'], revs)
            # search by author
            if not gitcb:
                ae = gitc.author.email.lower()
                revs = ref_b['author2c'].get(ae)
                if revs:
                    gitcb, _ = find_similar_patch(gitc, ref_b['repo'], revs)
            # search by subject
            if not gitcb:
                gitcb, _ = find_similar_patch_by_sub(gitc,
                                                     ref_b['repo'],
                                                     ref_b['range'])
            if gitcb:
                found[gitcb.hexsha] = True
                updated.append((seq, c, gitcb.hexsha, gitcb.summary,))
                logger.info("    added in updated")
            else:
                removed.append((seq, c, None, gitc.summary,))
                logger.info("    added in removed")

    for gitc in ref_b['quilt']:
        c = gitc.hexsha
        logger.info("commit(from quilt b): %s" % c)
        if c not in found:
            logger.info("    added in new")
            seq += 1
            new.append((seq, None, c, gitc.summary,))
        else:
            logger.info("    skipped")

    return (ref_dict, (same, cmco, updated, new, removed,),)
