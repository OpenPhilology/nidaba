# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import shutil
import time
import SimpleHTTPServer
import SocketServer
import requests
import tasks
import irisconfig
import BaseHTTPServer
import SocketServer
import zipfile
import atexit


from fs import ftpfs, errors
from multiprocessing import Process, Queue
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.servers import ThreadedFTPServer, FTPServer
from pyftpdlib.handlers import FTPHandler
from Queue import Empty 
from requests.adapters import HTTPAdapter


class IrisTests(unittest.TestCase):
    
# ------------------------------------------------------------------------------------------
# Setup and helper methods -----------------------------------------------------------------
# ------------------------------------------------------------------------------------------
    
    def launch_ftp_server(self, queue):
        """Create a temporary HTTP server to serve as the cluster file store."""

        auth = DummyAuthorizer()
        auth.add_user('testuser', 'testpassword', self._ftp_storage, perm='elradfmwM')
        h = FTPHandler
        h.authorizer = auth
        server = ThreadedFTPServer(irisconfig.FTP_TEST_ADDR, h)

        killsig = ''
        while True:
            try:
                killsig = queue.get(block=False)
            except Empty, e:
                pass
            if killsig != 'kill':
                server.serve_forever(blocking=False, timeout=.5)
            else:
                break

    def launch_http_server(self, queue):
        """Create a temporary FTP server to serve as the cluster file store."""

        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.ThreadingTCPServer(irisconfig.HTTP_TEST_ADDR, Handler, False) # Do not automatically bind
        httpd.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
        httpd.server_bind()     # Manually bind, to support allow_reuse_address
        httpd.server_activate() # (see above comment)
        httpd.timeout = .5
        os.chdir(self._http_storage)    # SimpleHTTPServer only serves out of the working dir.
        killsig = ''
        while True:
            try:
                killsig = queue.get(block=False)
            except Empty, e:
                pass
            if killsig != 'kill':
                httpd.handle_request()
            else:
                print 'exiting http proc...'
                break
            

    def connect_to_ftp_server(self):
        """Ensure the ftp server is up by connecting and immediately disconnecting."""

        connected = False

        while not connected:
            try:
                fsystem = ftpfs.FTPFS(host=irisconfig.FTP_TEST_ADDR[0], user='testuser', passwd='testpassword', port=irisconfig.FTP_TEST_ADDR[1])
                connected = True
                print '***** connected!! *****'        
            except errors.RemoteConnectionError as e:
                pass

    def connect_to_http_server(self):
        """Ensure the http server is up by sending HEAD requests until we receive a 200 status code."""

        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=5))
        s.mount('https://', HTTPAdapter(max_retries=5))

        while s.head('http://localhost:%s/' % irisconfig.HTTP_TEST_ADDR[1]).status_code != 200:
            pass

    def setUp(self):
        atexit.register(self.cleanup_with_os_sig)    # Ensures that cleanup is performed even in the event of an anomalous exit, such as a keyboard interrupt.

        self._ftp_storage = tempfile.mkdtemp()
        self._ftp_killQueue = Queue()
        self._ftp_serverprocess = Process(target=self.launch_ftp_server, args=(self._ftp_killQueue,))
        self._ftp_serverprocess.start()
        self.connect_to_ftp_server()

        self._http_storage = tempfile.mkdtemp()
        self._http_killQueue = Queue()
        self._http_serverprocess = Process(target=self.launch_http_server, args=(self._http_killQueue,))
        self._http_serverprocess.start()
        self.connect_to_http_server()



    def tearDown(self):
        self._ftp_killQueue.put('kill')
        self._http_killQueue.put('kill')


    def doCleanups(self):
        self._ftp_killQueue.put('kill')
        self._http_killQueue.put('kill')
        self._ftp_serverprocess.join()
        self._http_serverprocess.join()
        shutil.rmtree(self._ftp_storage)
        shutil.rmtree(self._http_storage)

    def cleanup_with_os_sig(self):
        self._ftp_killQueue.put('kill')
        self._http_killQueue.put('kill')
        self._ftp_serverprocess.join()
        self._http_serverprocess.join()
        # The temp dir may have been already cleared by doCleanups. If so, ignore the failure.
        try:
            shutil.rmtree(self._ftp_storage)
            shutil.rmtree(self._http_storage)
        except OSError:
            pass


    def connect(self):
        """Mount the FTP-backed file system."""
        return ftpfs.FTPFS(host=irisconfig.FTP_TEST_ADDR[0], user='testuser', passwd='testpassword', port=irisconfig.FTP_TEST_ADDR[1])

    def create_http_file(self, name, contents):
        """Helper method creates a file to be served by the test http server."""

        path = os.path.join(self._http_storage, name)
        with open(path, 'w+') as f:
            f.write(contents)
        return path

    def create_ftp_file(self, name, contents):
        """Helper method creates a file to be served by the test http server."""
        
        ftpsys = ftpfs.FTPFS(host=irisconfig.FTP_TEST_ADDR[0], user='testuser', passwd='testpassword', port=irisconfig.FTP_TEST_ADDR[1])
        ftpsys.createfile(name)
        ftpsys.setcontents(name, contents)
        ftpsys.close()

# ------------------------------------------------------------------------------------------
# Unit tests for the celery tasks ----------------------------------------------------------
# ------------------------------------------------------------------------------------------

class TaskTests(IrisTests):

    def test_http_download(self):
        """Test by downloading a file via http and verifying its existence in the file store.
        They are not intended to be unit test so much as system diagnostics."""

        # Create a sample file for the http server to serve.
        self.create_http_file('servedfile.txt', 'file contents')

        # Run the download task and get the result.
        cluster_storage_path = 'downloadedfile.txt'
        url = 'http://localhost:%s/%s' % (irisconfig.HTTP_TEST_ADDR[1], 'servedfile.txt')
        http_dowload_res = tasks.http_download.delay('testuser', 'testpassword', url, cluster_storage_path, fsaddr=irisconfig.FTP_TEST_ADDR)
        res = http_dowload_res.get()

        ftpsys = self.connect()
        self.assertTrue(ftpsys.isfile(cluster_storage_path))
        self.assertEqual(ftpsys.listdir(), [cluster_storage_path])
        self.assertEqual(ftpsys.getcontents(cluster_storage_path), 'file contents')

    def test_unzip_default_dir(self):
        """Create a zip archive on the filestore, then extract and verify its contents via celery task."""

        # Create a zip archive with a file in it and load it into the FTP server.
        to_archive = self.create_ftp_file('to_archive.txt', 'contents')
        archive = zipfile.ZipFile(os.path.join(self._ftp_storage, 'archive.zip'), mode='w')
        archive.write(os.path.join(self._ftp_storage, 'to_archive.txt'))
        archive.close()

        unzip_task = tasks.unzip_archive.delay('testuser', 'testpassword', '/archive.zip', fsaddr=irisconfig.FTP_TEST_ADDR)
        unzip_res = unzip_task.get()
        ftpsys = self.connect()

        self.assertTrue(ftpsys.isfile('/to_archive.txt'))
        self.assertEqual('contents', ftpsys.getcontents('/to_archive.txt'))
        ftpsys.close()

# ------------------------------------------------------------------------------------------
# Diagnostic tests to exercise the celery workers ------------------------------------------
# ------------------------------------------------------------------------------------------


class SystemTests(IrisTests):
    """These tests exist to test that the celery cluster and filestore are up and functioning correctly."""

    def test_ftp_connect(self):
        """Simply connect and disconnect to the FTP file server."""

        result = tasks.ftp_connect_task.delay(irisconfig.FTP_TEST_ADDR, 'testuser', 'testpassword')
        self.assertEqual('successful', result.get())

    def test_file_create(self):
         """Create a file on the cluster file store."""
         
         name = 'test file'
         result = tasks.create_test_file.delay(irisconfig.FTP_TEST_ADDR, 'testuser', 'testpassword', 'test file contents')
         path = result.get()
         ftpsys = self.connect()

         self.assertIsNotNone(path)
         self.assertTrue(ftpsys.isfile(path))
         self.assertEqual('test file contents', ftpsys.getcontents(path))
         ftpsys.close()


    def test_file_delete(self):
        """Create a file, then delete it."""

        name = 'test file'
        create_result = tasks.create_test_file.delay(irisconfig.FTP_TEST_ADDR, 'testuser', 'testpassword', 'test file contents')
        path = create_result.get()
        ftpsys = self.connect()

        self.assertIsNotNone(path)
        self.assertTrue(ftpsys.isfile(path))

        delresult = tasks.delete_file.delay(irisconfig.FTP_TEST_ADDR, 'testuser', 'testpassword', path)

        self.assertEqual(path, delresult.get())
        self.assertFalse(ftpsys.isfile(path))
        ftpsys.close()

    def test_dir_create(self):
        """Create a directory."""
         
        dir_create_result = tasks.create_dir.delay(irisconfig.FTP_TEST_ADDR, 'testuser', 'testpassword')
        dirpath = dir_create_result.get()
        ftpsys = self.connect()

        self.assertIsNotNone(dirpath)
        self.assertTrue(ftpsys.isdir(dirpath))
        self.assertTrue(ftpsys.isdirempty(dirpath))
        ftpsys.close()

    def test_dir_delete(self):
        """Create a directory, then delete it."""

        dir_create_result = tasks.create_dir.delay(irisconfig.FTP_TEST_ADDR, 'testuser', 'testpassword')
        dirpath = dir_create_result.get()
        ftpsys = self.connect()

        self.assertIsNotNone(dirpath)
        self.assertTrue(ftpsys.isdir(dirpath))
        self.assertTrue(ftpsys.isdirempty(dirpath))

        dir_delete_result = tasks.delete_dir.delay(irisconfig.FTP_TEST_ADDR, 'testuser', 'testpassword', dirpath)

        self.assertEqual(dirpath, dir_delete_result.get())
        self.assertFalse(ftpsys.isdir(dirpath))
        ftpsys.close()



if __name__ == '__main__':
    unittest.main()