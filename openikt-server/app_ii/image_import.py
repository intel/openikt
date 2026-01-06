#!/usr/bin/env python3

import os
import sys
import re
import git
import time
import logging
import argparse
import requests
import subprocess

if not "DJANGO_SETTINGS_MODULE" in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
    import django
    django.setup()

from app_ii.models import *


logger = logging.getLogger(__name__)


class ImagePKGImporter:
    def __init__(self, image):
        self.image = image
        # section dict keyed by name
        self.sections = {
            s.name: s for s in PKGSection.objects.filter(os=self.image.os)
        }
        # contributor dict keyed by email
        self.contributors = { c.email: c for c in Contributor.objects.all() }
        # root packages queryset
        self.rpkg_qs = Package.objects.filter(root_id=0)
        self.arch_dict = { a[1]: a[0] for a in Package.ARCH_CHOICES }
        # pkg relation type dict
        self.reltype_dict = { r[1]: r[0] for r in PKGRelation.TYPE_CHOICES }
        # pkg relation comparison operator dict
        self.rel_cmpopr_dict = {
            o[1]: o[0] for o in PKGRelation.CMP_OPR_CHOICES if o[1]
        }
        # contributor type dict
        self.ctortype_dict = { t[1]: t[0] for t in PKGContributor.TYPE_CHOICES }
        self.raw_pkgs = []

    def parse(self):
        pass

    def cleanup(self):
        PKGContributor.objects.filter(package__image_id=self.image.id).delete()
        PKGExtraInfo.objects.filter(package__image_id=self.image.id).delete()
        PKGRelation.objects.filter(package__image_id=self.image.id).delete()
        Package.objects.filter(image_id=self.image.id).delete()

    def find_root_pkg(self, raw_pkg):
        pass

    def import_pkg(self, raw_pkg):
        pass

    def import_image(self):
        self.imported_pkgs = []
        self.parse()
        for p in self.raw_pkgs:
            self.imported_pkgs.append(self.import_pkg(p))

        return self.imported_pkgs


class UbuntuPKGImporter(ImagePKGImporter):
    #def __init__(self, image):
    #   super().__init__(image)

    def parse(self):
        # pkg key-value pair line regex
        kv_re = re.compile(r'^\s*([A-Z][\w-]*):\s+(\S.*\S)\s*$')
        pkg_started = False
        desc_started = False
        pkg = None
        for l in self.image.raw_data.splitlines():
            m = kv_re.search(l)
            if m:
                if m.group(1) == "Package":
                    pkg_started = True
                    pkg = { 'name': m.group(2) }
                    self.raw_pkgs.append(pkg)
                elif m.group(1) == 'Description':
                    desc_started = True
                    pkg['summary'] = m.group(2)
                elif pkg_started:
                    if desc_started:
                        desc_started = False
                    pkg[m.group(1).lower()] = m.group(2)
            else:
                if l == '':
                    if pkg_started:
                        pkg_started = False
                    if desc_started:
                        desc_started = False
                elif desc_started:
                    if 'desc' not in pkg:
                        pkg['desc'] = ''
                    pkg['desc'] += '\n' if l.strip() == '.' else l[2:]

        return self.raw_pkgs

    def import_pkg(self, raw_pkg):
        email_re = re.compile(r'([\w\s\(\)]+\S)\s+<(.*@.*)>')
        # pkg relation regex
        dep_re = re.compile(r'^([\w+-\.]+)(?:\(([=><]+)(.*)\)|(:any))?$')
        root_pkg = self.find_root_pkg(raw_pkg)
        if raw_pkg["section"] in self.sections:
            sec = self.sections[raw_pkg["section"]]
        else:
            sec = PKGSection(name=raw_pkg["section"],
                             os=self.image.os)
            sec.save()
            self.sections[sec.name] = sec
        #FIXME: should reuse the data from root pkg?
        pkgobj = Package(root_id=root_pkg.id if root_pkg else 0,
                         name=raw_pkg["name"],
                         version=raw_pkg["version"],
                         summary=raw_pkg["summary"],
                         desc=raw_pkg["desc"],
                         section_id=sec.id,
                         homepage=raw_pkg.get("homepage"),
                         source=raw_pkg.get("source"),
                         image_id=self.image.id,
                         arch=self.arch_dict[raw_pkg["architecture"]])
        pkgobj.save()

        # record pkg relations
        pkgrel_objs = []
        for k in self.reltype_dict.keys():
            if k not in raw_pkg:
                continue

            group = 0
            for g in raw_pkg[k].replace(' ', '').split('|'):
                for d in g.split(','):
                    m = dep_re.search(d)
                    if not m:
                        logger.warning("    relation doesn't match: %s" % d)
                        continue

                    if m.group(2):
                        cmpopr = self.rel_cmpopr_dict[m.group(2)]
                    elif m.group(4):
                        cmpopr = PKGRelation.CMP_OPR_ANY
                    else:
                        cmpopr = PKGRelation.CMP_OPR_NA
                    pkgrel_obj = PKGRelation(package_id=pkgobj.id,
                                             rtype=self.reltype_dict[k],
                                             cmpopr=cmpopr,
                                             name=m.group(1),
                                             version=m.group(3),
                                             group=group)
                    pkgrel_objs.append(pkgrel_obj)

                group += 1
        PKGRelation.objects.bulk_create(pkgrel_objs)

        # record pkg contributors
        for k in self.ctortype_dict.keys():
            if k not in raw_pkg:
                continue
            m = email_re.search(raw_pkg[k])
            if not m:
                logger.warning("    email addr. not matched: %s" % raw_pkg[k])
                continue
            if m.group(2) in self.contributors:
                ctor = self.contributors[m.group(2)]
            else:
                ctor = Contributor(email=m.group(2),
                                   name=m.group(1))
                ctor.save()
                self.contributors[ctor.email] = ctor
            pkgctor = PKGContributor(package_id=pkgobj.id,
                                     contributor_id=ctor.id,
                                     ctype=self.ctortype_dict[k])
            pkgctor.save()

def download_file_from_url(url, output_path, retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), timeout=3):
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    try:
        session = requests.Session()
        
        retry_strategy = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            # Enable retries for connection and read errors
            allowed_methods=frozenset(['GET', 'POST']),
            raise_on_status=False  # Do not raise an exception immediately on bad status codes
        )
        
        # Mount the retry strategy to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # Send a GET request without verifying the SSL certificate and with a timeout
        response = session.get(url, stream=True, verify=False, timeout=timeout)
        
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0

            with open(output_path, 'wb') as f:
                logger.info("    Downloading the ISO  from %s", url)
                for chunk in response.iter_content(chunk_size=40960):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        # Optional: Log progress
                        #logger.info(f"Downloaded {bytes_downloaded} / {total_size} bytes ({(bytes_downloaded / total_size) * 100:.2f}%)")

            logger.info("    File downloaded successfully to path: %s", output_path)
            return True
        else:
            logger.error("    Failed to download file, status code: %d", url, response.status_code)
            return False
    except requests.exceptions.RequestException as e:
        logger.error("    An error occurred while download file,  error: %s", str(e))
        return False

def mount(iso_file_path, iso_mount_point):
    """
    Mount the iso file to the mount point
    """
    if os.path.exists(iso_file_path):
        os.makedirs(iso_mount_point, exist_ok=True)
        cmd = ('mount --options loop %s %s' % (iso_file_path, iso_mount_point))
        logger.debug('    cmd: %s', cmd)
        ret = subprocess.run(cmd, shell=True)
        ret = ret.returncode
    else:
        logger.error("    File %s is not exists", iso_file_path)
        ret = 1
    return ret

def create_raw_data(iso_file_path, iso_mount_point='/mnt'):
    ret = mount(iso_file_path, iso_mount_point)
    if ret > 0:
        logger.error("    mount failed, ret: %s", ret)
        sys.exit(1)
    logger.info("    mount %s to %s successfully", iso_file_path, iso_mount_point)

    cmd = ('cd %s/pool; for p in $(find . -name "*.deb"); do dpkg-deb -I $p; echo ""; echo ""; done > /opt/raw_data' % iso_mount_point)
    logger.debug('    cmd: %s', cmd)
    ret = subprocess.run(cmd, shell=True)
    ret = ret.returncode
    return ret

if __name__ == '__main__':
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO')
    logging.basicConfig(level=LOGLEVEL, format='%(levelname)-5s: %(message)s')

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('--image', '-i', action='store', required=True,
                        help="Specify OS image name")
    parser.add_argument('--data-file', '-f', action='store',
                        help="Specify package data file")
    parser.add_argument('--overwrite', '-o', action='store_true', default=False,
                        help="Overwrite the existing image packages")
    args = parser.parse_args()

    image = OSImage.objects.filter(name=args.image).first()
    assert image, "Image %s doesn't exist" % args.image

    exists = Package.objects.filter(image=image.id).exists()
    if exists:
        logger.info("Image id: %s exists in table OSImage and exit" % image.id)
        sys.exit(0)

    logger.info("Import package information of the image %s ..." % args.image)
    if args.data_file:
        logger.info("raw data file: %s" % args.data_file)
        if not os.path.isfile(args.data_file):
            logger.error("raw data file doesn't exist, quit")
            sys.exit(1)
        with open(args.data_file, 'r') as f:
            image.raw_data = f.read()
            image.save()
    else:
        if not image.raw_data and image.url:
            logger.info("Begin to download ISO from url: %s" % image.url)
            success = download_file_from_url(image.url, "/opt/download.iso")
            if success:
                ret = create_raw_data('/opt/download.iso')
                if ret > 0:
                    logger.error("create_raw_data run failed, ret: %s", ret)
                    sys.exit(1)
                logger.info("create_raw_data run successfully: %s" % image.url)
                if not os.path.isfile('/opt/raw_data'):
                    logger.error("raw_data file doesn't exist, quit")
                    sys.exit(1)
                with open('/opt/raw_data', 'r') as f:
                    image.raw_data = f.read()
                    image.save()
            else:
                logger.error("No file downloaded from URL: %s", image.url)

    assert image.raw_data, "Package data(image.raw_data) doesn't exist"

    importer_cls = globals()["%sPKGImporter" % image.get_os_display().capitalize()]
    importer = importer_cls(image)
    if len(Package.objects.filter(image_id=image.id)):
        if args.overwrite:
            logger.info("Packages already exist, overwrite them")
            importer.cleanup()
        else:
            logger.info("Packages already exist, aborted")
            sys.exit(0)

    importer.import_image()
