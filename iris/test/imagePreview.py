from PIL import Image
import logging

log = logging.getLogger('irisImagePreviewLogger')
logging.basicConfig(level=logging.DEBUG)
log.debug('image preview module loaded')

def previewImage(image):
    log.debug('attempting to preview an image')
    PILImage = Image.open(image)
    PILImage.show()
    log.debug('image displayed succesfully')