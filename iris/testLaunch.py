from flask import Flask, render_template, request
from web import views
from test import imagePreview
import os
import logging

iris = views.startWebViews()
# print('approot is: ' + 	iris.root_path)
# iris.root_path = os.path.abspath(os.path.dirname(__file__))
port = int(os.getenv('PORT', 5000))


iris.run(host='0.0.0.0', port=port)