from flask import Flask, render_template, request
from web import views
import os
import logging
import taskManager

iris = views.startWebViews()
tm = taskManager.TaskManager()
port = int(os.getenv('PORT', 5000))


iris.run(host='0.0.0.0', port=port)