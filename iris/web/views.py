from flask import Flask, render_template, request
import os
import logging

iris=Flask('iris')
lg = logging.getLogger('iris')

logging.basicConfig(level=logging.DEBUG)
print('logger is ' + str(lg))
lg.warning('web view controller online')
lg.debug('just a test log statement')
lg.info('just an info statement')

@iris.route('/')
@iris.route('/index')
def indexRoute():
    print('routing to the index')
    return render_template("stubs/index.html")

@iris.route('/batch')
def batchRoute():
	print('routing to the batch upload portal')
	return render_template("stubs/batch.html")

@iris.route('/batch/<path:specificBatch>', methods = ['GET', 'POST'])
def specificBatchRoute(specificBatch):	
	print('routing to specific batch with URN: ' + str('%s' % specificBatch))
 	
 # 	print('attempting...')
	# print('Headers: ' + str(request.headers))
	# print('Cookies: ' + str(request.cookies))
	# print('environ: '+str(request.environ))
	# print('args: ' + str(request.args))
	# print('form: ' + str(request.form))
	# print('attempt successful!')
	#lg.debug('batch debug test')
	#lg.log('batch log test')
	#lg.wart('batch warn test')
	return render_template("stubs/batch.html", batch = specificBatch)

@iris.route('/collections')
def collectionRoute():
	print('routing to collections interface')
	return render_template("stubs/collections.html")

@iris.route('/collections/<path:specificCollection>')
def specificCollectionRoute(specificCollection):
	print('routing to specific collection with URN: ' + str('%s' + specificCollection))
	return render_template("stubs/collections.html", collection = specificCollection)


@iris.route('/page')
def pageRoute():
	print('routing to OCR editing/cleanup portal')

@iris.route('/page/<path:pageURN>')
def specificPageRoute(pageURN):
	print('routing a specific page of raw OCR output with URN: ' + str('%s' % pageURN))
	return render_template("stubs/page.html")




#Launch a simple dev server if this script is run manually (as __main__).
if __name__ == "__main__":
	port = int(os.getenv('PORT', 5000))
	iris.run(host='0.0.0.0', port=port)
