import flask
import subprocess
from flask_cors import CORS
import logging
app = flask.Flask(__name__)
CORS(app)
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

path_to_run = './'          #directory here
py_name = 'KM(Subworker).py'   #fileName here
args = ["python3", "{}{}".format(path_to_run, py_name)]
#args = ["gunicorn", "-b","0.0.0.0:5000","KM(Subworker):app" ,"--timeout", "360","--log-level=debug"]
lrw=None

@app.route('/api/subworker/start', methods = ['GET'])
def start():
    global lrw
    if lrw is not None:    #if process is running or has run before
        return flask.Response(status=409)   #code:conflict
    else:                   #process never run
       
        lrw=subprocess.Popen(args)
        return flask.Response(status=202)   #code:accepted

@app.route('/api/subworker/stop', methods = ['GET'])
def stop():
    global lrw
    if lrw is not None:    #if process is running or has completed
        lrw.terminate()
        lrw=None
        return flask.Response(status=200)   #code:ok
    else:                   #process never run
        return flask.Response(status=403)   #code:forbidden


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
