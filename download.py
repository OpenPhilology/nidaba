import os
import urllib2
import urlparse
import shutil
from distutils.core import Command

manifest_url = "http://l.unchti.me/nidaba/MANIFEST"
download_prefix = "http://l.unchti.me/nidaba/"

class DownloadCommand(Command):
    command_name = 'download'
    description = ('Download misc. data files (dictionaries, sample inputs and'
                   'models for tests etc.)')
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("Downloading manifest...")
        manifest = [x.strip() for x in
                    urllib2.urlopen(manifest_url).readlines()]
        print("Downloading: ")
        for f in manifest:
            print('\t* ' + f)
            try:
                os.makedirs(os.path.dirname(f))
            except OSError:
                pass
            r = urllib2.urlopen(urlparse.urljoin(download_prefix, f))
            with open(f, 'wb') as fp:
                shutil.copyfileobj(r, fp)
