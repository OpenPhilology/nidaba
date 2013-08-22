# This module contains tools for working with images. Any component of Iris which needs to work with images should do so through this module.

from PIL import Image
import logging

log = logging.getLogger('irisImagePreviewLogger')
logging.basicConfig(level=logging.DEBUG)
log.debug('image preview module loaded')

def previewImage(image):
    if(imageType(image)):
        PILImage = Image.open(image)
        PILImage.show()
        log.debug('image displayed succesfully')
    else:
    	log.debug('the image could not be previewed.')


    
def imageType(file):
	try:
	    image = Image.open(file)
	    image.load()
	    format = image.format
	    log.debug('The file ' + file.filename + ' was a valid ' + format)
	    return format
	except:
		log.debug('The file ' + file.filename + ' was not a valid image.')
		return False
