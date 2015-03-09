"""
nibada.image
~~~~~~~~~~

Common image processing functions encapsulating the PIL or pythonica image
interface to absolute file paths.
"""

from PIL import Image

def imageFromFile(file):
    try:
        image = Image.open(file)
        image.load()
        return image
    except Exception as err:
        return None

def rgb_to_gray(imagepath, resultpath):
    """
    Converts an RGB or CMYK image into a 8bpp grayscale image.

    Arguments:
        imagepath: Path of the input image
        resultpath: Path of the output image

    Returns:
        resultpath: Path of the actual output file
    """

    img = imageFromFile(imagepath)
    img.convert('L').save(resultpath)
    return resultpath


