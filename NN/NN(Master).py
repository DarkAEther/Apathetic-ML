
import numpy as np

import keras
 
from keras import Sequential

from keras.layers import Dense

from keras.datasets import mnist

import requests

import flask

import threading

import tensorflow as tf

from keras import backend as K

from keras.models import model_from_json

from keras.models import load_model

import concurrent.futures

from tensorflow import Graph , Session

import time

tf.reset_default_graph()

from sklearn.metrics import accuracy_score as acc_score

app = flask.Flask(__name__)

iplist=["http://127.0.0.1:5000","http://127.0.0.1:7000","http://127.0.0.1:9000","http://127.0.0.1:11000","http://127.0.0.1:13000"]

thread_local = threading.local()

def get_session():

    if not hasattr(thread_local, "session"):

        thread_local.session = requests.Session()

    return thread_local.session

def preprocess():

    (X_train,y_train),(X_test,y_test) = mnist.load_data()

    X_train_flat = X_train.reshape((X_train.shape[0],-1))

    X_test_flat  = X_test.reshape((X_test.shape[0],-1))

    y_train_oh = keras.utils.to_categorical(y_train,10)

    return (X_train_flat,y_train_oh),(X_test_flat,y_test)

class Sequential:
    
    def __init__(self , n_users , steps):
        
        self.n_users = n_users
        
        self.steps = steps

        self.graph = Graph()

        with self.graph.as_default():

            self.sess = Session()

        K.set_session(self.sess)

        with self.graph.as_default():
        
            self.model = keras.Sequential()

        self.users=[]
        futures=[]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for _ in range(n_users):
                futures.append(executor.submit(User,iplist[_],_))
        for i in futures:
            self.users.append(i.result())
            
    def add(self,layer):

        K.set_session(self.sess)

        with self.graph.as_default():
        
            self.model.add(layer)
        
    def compile(self , optimizer = None , loss = None , metrics = None):

        K.set_session(self.sess)

        with self.graph.as_default():
        
            self.model.compile(optimizer = optimizer , loss = loss , metrics = metrics)

            model_json = self.model.to_json()

            with open("model.json", "w") as json_file:

                json_file.write(model_json)

            self.model.save_weights("model.h5")

            #for _ in range(self.n_users):
                
                #self.users[_].compile(optimizer = optimizer , loss = loss , metrics = metrics)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                for _ in range(self.n_users):
                    executor.submit(self.users[_].compile,optimizer,loss,metrics)

    def fit(self , X_train , y_train , X_test , y_test , batch_size = None , epochs = None):
        
        X_train_split = np.array([np.split(_,self.steps) for _ in np.split(X_train,self.n_users)])
        
        y_train_split = np.array([np.split(_,self.steps) for _ in np.split(y_train,self.n_users)])
        
        batch_size_step = batch_size
        
        for epoch_i in range(epochs):
            
            print('EPOCH : ' + str(epoch_i + 1))
            
            for step_i in range(self.steps):
                
                print('\tSTEP : ' + str(step_i + 1))

                #for user_i in range(self.n_users):
                    
                    #print('\t\tUSER : ' + str(user_i + 1))
                    
                    #self.users[user_i].fit(X_train_split[user_i][step_i] , y_train_split[user_i][step_i] , 1 , batch_size_step)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for user_i in range(self.n_users):
                        print('\t\tUSER : ' + str(user_i + 1))
                        executor.submit(self.users[user_i].fit, X_train_split[user_i][step_i], y_train_split[user_i][step_i], 1, batch_size_step)

                #accuracies = []
                
                #for user_i in range(self.n_users):
                    
                    #accuracies.append(self.users[user_i].accuracy_score(X_test , y_test))
                
                accuracies=[]
                futures=[]
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for user_i in range(self.n_users):
                        futures.append(executor.submit(self.users[user_i].accuracy_score,X_test,y_test))
                for i in futures:
                    accuracies.append(i.result())
                    
                print('\tACCURACY : ' + str(max(accuracies)))
                    
                self.best_user_id = np.argmax(np.array(accuracies))
                
                self.users[self.best_user_id].best_model()

                #for user_i in range(self.n_users):
                    
                    #if user_i != self.best_user_id :
                        
                        #self.users[user_i].update_model()
                        
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for user_i in range(self.n_users):
                        if user_i != self.best_user_id:
                            executor.submit(self.users[user_i].update_model)
        
        K.set_session(self.sess)

        with self.graph.as_default():

            self.model.load_weights('best_model.h5')
     
    def predict(self , X):

        K.set_session(self.sess)

        with self.graph.as_default():
                
            return self.model.predict(X)

      
class User:
    
    def __init__(self , ip, user_id = None):
        
        sesh=get_session()

        self.ip=ip

        url = self.ip+'/api/worker/nn/userinit'

        sesh.post(url,json={'user_id':user_id})
        

        
    def compile(self , optimizer , loss , metrics):
    
        sesh=get_session()     

        url = self.ip+'/api/worker/nn/usercompile'   

        sesh.post(url,json={'optimizer':optimizer,'loss':loss,'metrics':metrics})
        
        

    def fit(self , X_train , y_train , epochs = 1 , batch_size = None):
    
        sesh=get_session()     

        url = self.ip+'/api/worker/nn/userfit'

        sesh.post(url,json={'X_train':X_train.tolist(),'y_train':y_train.tolist(),'epochs':epochs,'batch_size':batch_size})
        

    
    def accuracy_score(self , X_test , y_test):
    
        sesh=get_session()     

        url = self.ip+'/api/worker/nn/accuracyscore' 

        r=sesh.post(url,json={'X_test':X_test.tolist(),'y_test':y_test.tolist()})

        return r.json()['accuracy']

    
    def best_model(self):
        
        sesh=get_session()   

        url = self.ip+'/api/worker/nn/bestmodel'  

        sesh.post(url)
        
    
    def update_model(self):
    
        sesh=get_session()     

        url = self.ip+'/api/worker/nn/updatemodel' 

        sesh.post(url)
        

    
@app.route('/api/master/nn/start', methods = ['GET'])
def start():

    (X_train,y_train),(X_test,y_test) = preprocess()

    model = Sequential(n_users = 5 , steps = 5)

    model.add(Dense(input_dim = 784 , units = 256 , activation = 'sigmoid'))

    model.add(Dense(units = 128 , activation = 'sigmoid'))
    
    model.add(Dense(units = 128 , activation = 'sigmoid'))
    
    model.add(Dense(units = 128 , activation = 'sigmoid'))
        
    model.add(Dense(units = 128 , activation = 'sigmoid'))    

    model.add(Dense(units = 10 , activation = 'sigmoid'))

    model.compile(optimizer = 'adam' , loss = 'binary_crossentropy' , metrics = ['accuracy'])

    a = time.time()

    model.fit(X_train_flat , y_train_oh , X_test_flat , y_test , batch_size = 10 , epochs = 20)


    y_pred = model.predict(X_test_flat)
            
    y_pred = [np.argmax(i) for i in y_pred]

    acc = acc_score(y_test , y_pred)

    print(acc)

    print(time.time()-a)

    return flask.Response(status = 200)

if __name__ == '__main__':

    app.run(host='127.0.0.1', port=3000)
