import os
import sys
import urllib
import tarfile
from distutils.core import Command

target = "http://l.unchti.me/nidaba/tests.tar.bz2"

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
	def dlProgress(count, blockSize, totalSize):
	    percent = int(count*blockSize*100/totalSize)
	    sys.stdout.write("\rDownloading test data... %d%%" % percent)
	    sys.stdout.flush()
	 
	file_tmp = urllib.urlretrieve(target, filename=None, reporthook=dlProgress)[0]
	tar = tarfile.open(file_tmp)
	tar.extractall()
	tar.close()
        print('')
