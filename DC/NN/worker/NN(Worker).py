import flask
import requests
import numpy as np
import json
from sklearn.metrics import accuracy_score as acc_score
from keras import *
from flask_cors import CORS
def imports():
    global keras, K,tf,Dense,Graph,Session,load_model,model_from_json
    from keras import backend as K
    import tensorflow as tf
    from keras.layers import Dense
    from tensorflow import Graph , Session
    from keras.models import load_model
    from keras.models import model_from_json
    tf.reset_default_graph()

app = flask.Flask(__name__)
CORS(app)
user=None

sesh=requests.Session()

class User:
    
    def __init__(self , ip, user_id = None):
        
        self.user_id = user_id

        self.graph = Graph()

        with self.graph.as_default():

            self.sess = Session()

        
    def compile(self , optimizer , loss , metrics):

        K.set_session(self.sess)

        with self.graph.as_default():
    
            json_file = open('/dev/core/model.json', 'r')

            loaded_model_json = json_file.read()

            json_file.close()

            loaded_model = model_from_json(loaded_model_json)

            loaded_model.load_weights("/dev/core/model.h5")

            self.model = loaded_model

            print(optimizer,loss,metrics)

            self.model.compile(optimizer = optimizer , loss = loss , metrics = metrics)

    def fit(self , X_train , y_train , epochs = 1 , batch_size = None):

        K.set_session(self.sess)

        with self.graph.as_default():
        
            self.model.fit(X_train , y_train , epochs = 1 , batch_size = int(batch_size))
    
    def accuracy_score(self , X_test , y_test):

        K.set_session(self.sess)

        with self.graph.as_default():
    
            y_pred = self.model.predict(X_test)
            
            y_pred = [np.argmax(i) for i in y_pred]

            accuracy = acc_score(y_test, y_pred)

            return accuracy
    
    def best_model(self):

        K.set_session(self.sess)

        with self.graph.as_default():
        
            self.model.save_weights('/dev/core/best_model.h5')
    
    def update_model(self):

        K.set_session(self.sess)

        with self.graph.as_default():
    
            self.model.load_weights('/dev/core/best_model.h5')

        
@app.route('/api/worker/nn/userinit', methods = ['POST'])
def userinit():

    global user
    imports()
    user_id=flask.request.json['user_id']

    user=User(user_id)

    return flask.Response(status = 200)
    
@app.route('/api/worker/nn/usercompile', methods = ['POST'])
def usercompile():

    global user

    optimizer=flask.request.json['optimizer']

    loss=flask.request.json['loss']

    metrics=flask.request.json['metrics']

    user.compile(optimizer,loss,metrics)

    return flask.Response(status = 200)
    
@app.route('/api/worker/nn/userfit', methods = ['POST'])
def userfit():

    global user

    X_train=np.array(flask.request.json['X_train'])

    y_train=np.array(flask.request.json['y_train'])

    epochs=flask.request.json['epochs']

    batch_size=flask.request.json['batch_size']

    user.fit(X_train,y_train,epochs,batch_size)

    return flask.Response(status = 200)
    
@app.route('/api/worker/nn/accuracyscore', methods = ['POST'])
def accuracyscore():

    global user

    X_test=np.array(flask.request.json['X_test'])

    y_test=np.array(flask.request.json['y_test'])

    accuracy=user.accuracy_score(X_test,y_test)

    return flask.Response(json.JSONEncoder().encode({'accuracy':accuracy}),mimetype='application/json',status = 200)
    
@app.route('/api/worker/nn/bestmodel', methods = ['POST'])
def bestmodel():

    global user

    user.best_model()

    return flask.Response(status = 200)
    
@app.route('/api/worker/nn/updatemodel', methods = ['POST'])
def updatemodel():

    global user

    user.update_model()

    return flask.Response(status = 200)
    
if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)

