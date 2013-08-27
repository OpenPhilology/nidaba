

# This is the central task management and scheduler class for Iris.
# TaskManager is responsible for keeping track of all ongoing pipline tasks from start to finish, such as OCR, error correction, etc. 
# It transparently breaks user-visible application level tasks, such as performing OCR on a page, into smaller subtasks (e.g. a single binarization scan of a page) which can be parallelized.
# Taskmaster provides APIs for creating, pausing, enabling, querying, deleting, and scheduling OCR tasks at all necessary levels of granularity. 
# For example, a user may view that a given set of pages is currently in the OCR phase of the pipeline (as opposed to, for example, human error correction).
# Tasks are serchable by various pieces of data, including userId (the user that initiated the task, age (how long the task has been alive), pause time how long a task has been paused), associated URNs, etc.
# Obviously, varying levels of control and visibility of the ongoing tasks can be restricted to users of any desired access level.
# Other objects, such as those which process REST messages from the web, communicate with TaskManager via a delegate model. That is, they inform a TaskManager of relevant events, and TaskManager responds appropriately.
# For example, the views.py module will not do any processing of incoming POST data itself; rather, it passes a TaskManager object a reference to the incoming data, at which point Taskmaster does the "heavy lifting",
# creating subtasks to process the data, and passing the Flask stack the appropriate response data.
import logging
from celery import Celery
celery = Celery(main='taskManager', broker='redis://localhost:5001/0')
logger = logging.getLogger('taskManager')
logging.basicConfig(level=logging.DEBUG)

class TaskManager: 

    def __init__(self):
        logger.debug('TaskManager object initialized')

    # @celery.task
    def testTask():
        log.debug('logged this asynchronously!')