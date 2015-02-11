# This module contains celery tasks for working with images.
# For the sake of speed and memory, all methods which take an image as a parameter will assume that the image has been validated, rather than loading and checking redundantly. This should be done through imageFromFile(file).
from __future__ import absolute_import

from PIL import Image
from celery import Celery
from celery.contrib.methods import task
import logging

log = logging.getLogger('irisImagePreviewLogger')
logging.basicConfig(level=logging.DEBUG)

#Open and completely load the file. This will determine if the file is a valid image. We could use PIL.Image.verify(), but this is not as robust as it will not catch decoding errors.
@celery.task(name='imageLoadTask')
def imageFromFile(file):
	try:
	    image = Image.open(file)   #Lazy; won't load until we access or force.
	    image.load()               #..and force the load.
	    log.debug('Image \"' + file.filename +'\" was valid!')
	    return image
	except Exception as err:
		log.debug('Image was not valid')
		log.debug(err)
		return None


def imageConformsToOCRRequirements(image):
    acceptableFormats = ['png', 'tiff']
    try:
        if(image.format.lower() not in acceptableFormats):
            return False
        else:
            return True
    except Exception as err:
        log.debug('imageConformsToOCRRequirements: The parameter was not a valid image.')


def getDPI(image):
    log.debug(str(image.info))
    if('dpi' in image.info):
        log.debug(str(image.info["dpi"]))
    else:
    	pass
