from flask import Flask, render_template, request
from web import views
from test import imagePreview
import os
import logging


port = int(os.getenv('PORT', 5000))
iris = views.startWebViews()
iris.run(host='0.0.0.0', port=port)