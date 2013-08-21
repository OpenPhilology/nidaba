from flask import Flask, render_template, request
import imagePreview
import os
import logging


log = logging.getLogger('iris')
log.info('Web view interface online.')
logging.basicConfig(level=logging.DEBUG)

iris = Flask('iris')

def startWebViews():
	print('starting webviews')
	return iris

@iris.route('/')
@iris.route('/index')
def indexRoute():
    log.debug('routing to the index')
    return render_template("stubs/index.html")

@iris.route('/batch', methods = ['GET', 'POST'])
def batchRoute():
	log.debug('routing to the batch upload portal')
	log.debug('begin printing headers -----------------------------------')
	log.debug(request.headers)
	log.debug('end printing headers -------------------------------------')
	log.debug(str(len(request.files)) + ' files were upload')
	file = request.files['photo']
	imagePreview.previewImage(file)
	return render_template("stubs/batch.html")

@iris.route('/batch/<path:specificBatch>', methods = ['GET', 'POST'])
def specificBatchRoute(specificBatch):	
	log.debug('routing to specific batch with URN: ' + str('%s' % specificBatch))
	return render_template("stubs/batch.html", batch = specificBatch)

@iris.route('/collections')
def collectionRoute():
	log.debug('routing to collections interface')
	return render_template("stubs/collections.html")

@iris.route('/collections/<path:specificCollection>')
def specificCollectionRoute(specificCollection):
	log.debug('routing to specific collection with URN: ' + str('%s' + specificCollection))
	return render_template("stubs/collections.html", collection = specificCollection)


@iris.route('/page')
def pageRoute():
	log.debug('routing to OCR editing/cleanup portal')

@iris.route('/page/<path:pageURN>')
def specificPageRoute(pageURN):
	log.debug('routing a specific page of raw OCR output with URN: ' + str('%s' % pageURN))
	return render_template("stubs/page.html")
