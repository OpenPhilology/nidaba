# This module contains tools for working with images. Any component of Iris which needs to work with images should do so through this module.
# For the sake of speed and memory, all methods which take an image as a parameter will assume that the image has been validated (rather than loading and checking redundantly. This should be done through imageFromFile(file).

from PIL import Image
import logging

log = logging.getLogger('irisImagePreviewLogger')
logging.basicConfig(level=logging.DEBUG)

#Open and completely load the file. This will determine if the file is a valid image.
def imageFromFile(file):
	try:
	    image = Image.open(file)
	    image.load()
	    log.debug('Image \"' + file.filename +'\" was valid!')
	    return image
	except Exception, err:
		log.debug('Image was not valid')
		log.debug(err)
		return None