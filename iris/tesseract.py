import os
import tempfile as temp
import subprocess
import StringIO
from irisconfig import TESS_PATH as tesseract

#More readable aliases for tesseract's language abbreviations.
greek = 'grc'

def ocr(imagepath, outputfilepath, language):
	"""Scan a single image with tesseract using the specified language,
	and writing output to the specified file. Returns a 3 tuple of the
	format (absolute path to output, tesseract's stdout, tesseract's 
	stderr)."""
	abs_in = os.path.abspath(os.path.expanduser(imagepath))
	abs_out = os.path.abspath(os.path.expanduser(outputfilepath))
	p = subprocess.Popen(['tesseract', '-l', language, abs_in, abs_out, 'hocr'],
						  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()
	return (abs_out, out, err)


if __name__ == '__main__':
	pass