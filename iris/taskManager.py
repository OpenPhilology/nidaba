

# This is the central task management and scheduler class for Iris.
# TaskManager is responsible for keeping track of all ongoing pipline tasks from start to finish, such as OCR, error correction, etc. 
# It transparently breaks user-visible application level tasks, such as performing OCR on a page, into smaller subtasks (e.g. a single binarization scan of a page) which can be parallelized.
# Taskmaster provides APIs for creating, pausing, enabling, querying, deleting, and scheduling OCR tasks at all necessary levels of granularity. 
# For example, a user may view that a given set of pages is currently in the OCR phase of the pipeline (as opposed to, for example, human error correction).
# Tasks are serchable by various pieces of data, including userId (the user that initiated the task, age (how long the task has been alive), pause time how long a task has been paused), associated URNs, etc.
# Obviously, varying levels of control and visibility of the ongoing tasks can be restricted to users of any desired access level.
# Other objects, such as those which process REST messages from the web, communicate with TaskManager via a delegate model. That is, they inform a TaskManager of relevant events, and TaskManager responds appropriately.
# For example, the views.py module will not do any processing of incoming POST data itself; rather, it passes a TaskManager object a reference to the incoming data, at which point Taskmaster does the "heavy lifting",
# creating subtasks to process the data, and passing the Flask/WSGI layer the appropriate response data.
import logging
import time
import tasks
import datetime
from celery import Celery
from tasks import imageFromFile
from tasks import processOrgArchive
from tasks import processArchiveGroup
import ConfigParser
import sys
import inspect
import irisconfig



#Configure logging
logger = logging.getLogger('taskManager')
logging.basicConfig(level=logging.DEBUG)

logger.debug(irisConfig.ARCHIVE_URL)
logger.debug(irisConfig.IRIS_HOME)


class TaskManager: 
    archiveJobs = ['blah']    #A dictionary of all archive.org OCR jobs. #TODO rename!!

    def __init__(self):
        logger.debug('TaskManager object initialized')
        print(str(self.archiveJobs))

    def createArchiveJob(self, archiveId, userName):
        task = OCRTask('testUser', 'this is the tag')
        # task = OCRTask.archiveDotOrgJob('testUser', 'the tag', 'mechanicaesynta00philgoog')
        print('about to print task')
        print task
        print('__class is__'+str(task.__class__)+"\n")
        print('about to print second task')
        task1 = OCRTask.archiveDotOrgJob('newTestUser', 'new tag', 'mechanicaesynta00philgoog')
        print task1
        print('task1 type is: '+str(type(task1)))
        print('printing __class__: ' + str(task1.__class__))
        # global archiveJobs
        # print(str(self.archiveJobs))
        # self.archiveJobs[0] = task
        task1.engage()


    def loadIrisConfig():
        pass


#Encapsulates all data for an entire, start-to-finish OCR job.
#username is the unqiue ID of the user who created the job. Tag is an optional field, used to store a comment or description by the user which created the task.
class OCRTask:

    def __init__(self, userName, tag):
        self.creationTime = datetime.time()
        self.userName = userName
        self.tag = tag
        self.archiveID = None
        self._phases = ['created', 'scheduled', 'downloading', 'OCRing', 'proofreading', 'finished']
        self._states = ['not yet started', 'running', 'paused', 'failed', 'completed']
        self._phase = 0
        self._state = 0


    @classmethod
    def archiveDotOrgJob(cls, userName, tag, archiveID):
        print ('initial print of cls is: '+str(cls))
        cls = OCRTask(userName, tag)
        cls.archiveID = archiveID
        return cls

    def engage(self):
        results = processOrgArchive.apply_async([self.archiveID])
        # results = processArchiveGroup.apply_async([self.archiveID])


    def __str__(self):
        print('custom str override called')
        return 'OCRTask createdBy:{0}, tag:{1}, phase:{2}, state:{3}'.format(self.userName, self.tag, self._phases[self._phase], self._states[self._state])


    @property
    def userName(self):
        return self._userName

    @property
    def tag(self):
        return self._tag

    @property
    def creationTime(self):
        return self._creationTime

    @property
    def phase(self):
        return self._phases[phase]

    @property
    def state(self):
        return self._states[state]
