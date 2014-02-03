
import irisconfig
import time

from clusterfileserver import ClusterFileServer, launch_daemon_server
from celery import Celery
from tasks import app, checksystem

if __name__ == '__main__':
    print 'Creating FTP file store...'
    print irisconfig.FTP_ADDR
    serverproc, killqueue = launch_daemon_server(irisconfig.FTP_ADDR)
    print 'queueing test task...'
    results = checksystem.apply_async()
    print 'did issue system check.'
    print 'sleeping for 5 sec'
    time.sleep(5)
    print 'woke up!'
    killqueue.put('kill')
    serverproc.join()
    print 'quitting.'
