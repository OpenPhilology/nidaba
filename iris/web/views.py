from flask import Flask, render_template
import os

iris=Flask('iris')

@iris.route('/')
@iris.route('/index')
def indexRoute():
    print('routing to the index')
    return render_template("stubs/index.html")

@iris.route('/batch')
def batchRoute():
	print('routing to the batch upload portal')


@iris.route('/batch/<path:specificBatch>')
def specificBatchRoute(specificBatch):
	print('routing to specific batch with URN: ' + str('%s' % specificBatch))
	return render_template("stubs/	batch.html")

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
