import numpy as np
import pandas as pd
import requests
import flask
import threading
import concurrent.futures
import time
from flask_cors import CORS
import ast
from json import dumps,loads
from kafka import KafkaConsumer,KafkaProducer
import copy
import sys
import cProfile
np.random.seed(42)

app = flask.Flask(__name__)
CORS(app)

# Importing the dataset
dataset = pd.read_csv('USA_Housing.csv')
X = dataset.iloc[:,0:5].values
y = dataset.iloc[:,5].values

# Splitting the dataset into the Training set and Test set
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25, random_state = 0)

# Feature Scaling
from sklearn.preprocessing import StandardScaler
sc_X = StandardScaler()
X_train = sc_X.fit_transform(X_train)
X_test = sc_X.transform(X_test)

regressor=None
#CS
#s = 'http://worker'
wb = []
producer = KafkaProducer(value_serializer=lambda v: dumps(v).encode('utf-8'),bootstrap_servers = ['kafka-service:9092'])
#topics=['m2w1','m2w2']
topics=[]
#iplist=["http://127.0.0.1:5000","http://127.0.0.1:7000","http://127.0.0.1:9100","http://127.0.0.1:11100","http://127.0.0.1:13000"]
#thread_local = threading.local()
'''
def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session
'''
#CE

class LinearRegressor:
    def __init__(self,learning_rate = 0.1,n_users = 1):
        self.n_users = n_users
        self.learning_rate = learning_rate
    def fit(self,train_dataset,train_y,X_test,y_test,n_iters = 200,batch_size = 200):
        #CS        
        global topics
        global producer
        #CE
        self.number_of_weights = train_dataset.shape[1]
        self.weights = np.random.rand(self.number_of_weights,1)
        self.biases = np.random.rand()
        self.train_dataset = train_dataset
        self.train_y = train_y
        self.batch_size = batch_size
        #self.train_dataset_user_batches = np.split(self.train_dataset,self.n_users)
        #self.train_y_user_batches = np.split(self.train_y,self.n_users)
        #CS
        self.users = [User(learning_rate = self.learning_rate,topic=topics[user]) for user in range(self.n_users)]
        producer.flush()
        #CE
        '''
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for user_i in range(self.n_users):
                #executor.submit(self.users[user_i].init_model,self.train_dataset_user_batches[user_i],self.train_y_user_batches[user_i],self.batch_size//self.n_users)
                executor.submit(self.users[user_i].init_model,self.batch_size//self.n_users)
        '''
        for user_i in range(self.n_users):
            #executor.submit(self.users[user_i].init_model,self.train_dataset_user_batches[user_i],self.train_y_user_batches[user_i],self.batch_size//self.n_users)
            self.users[user_i].init_model(self.batch_size//self.n_users)
        a = time.time()
        #CS
        producer.flush()
        '''
        cons = threading.Thread(target=consumer, args=(self.n_users,))
        cons.start()
        for j in range(n_iters):
            for step_i in range((train_y.shape[0]//self.batch_size)):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for user_i in range(self.n_users):
                        executor.submit(self.users[user_i].fit_model,self.weights,self.biases,step_i)
                    #with open("out",'a') as standardout:
                    #   print("ITER",j,file=standardout)
                
                producer.flush()
        
        cons.join()
        '''
        for j in range(n_iters):
                for step_i in range((train_y.shape[0]//self.batch_size)):
                        for user_i in range(self.n_users):
                                self.users[user_i].fit_model(self.weights,self.biases,step_i)
                    
                        producer.flush()
                        consumer(self.n_users)
                with open("out",'a') as standardout:
                        print("ITER",j,file=standardout)
        #CE
        b = time.time()
        with open("out",'a') as standardout:
            print("EXEC TIME:",b-a,'s',file=standardout)
        y_pred = self.predict(X_test)
        test_loss=self.test_loss(X_test,y_test)
        with open("out",'a') as standardout:
            print("Test Loss",test_loss,file=standardout)

    def test_loss(self,test_dataset,test_y):
        result = test_dataset @ self.weights + self.biases
        result_loss = np.square(result-test_y).mean()
        return result_loss
    def predict(self,X):
        return X@self.weights + self.biases
    def get_weights(self):
        with open("out",'a') as standardout:
            print("Weights:",self.weights," Biases:",self.biases,file=standardout)
        return self.weights,self.biases
    def update_model(self, weights, biases):
        self.weights -= weights      #recieve the updates in a sperate asynchronous function
        self.biases -= biases
        global wb
        wb.append([[self.weights,weights],[self.biases,biases]])
        #with open("out",'a') as standardout:
            #print(self.weights,self.biases,file=standardout)


#CS
class User:
    def __init__(self,topic,learning_rate=0.1):
        global producer
        self.topic=topic
        #sesh=get_session()
        #self.ip=ip
        #url = self.ip+'/api/worker/lr/userinit'
        #sesh.post(url,json={'learning_rate':learning_rate})
        producer.send(self.topic,{'fun':'userinit','learning_rate':learning_rate})
    def init_model(self,batch_size):
        global producer
        producer.send(self.topic,{'fun':'initmodel','batch_size':batch_size})
        #sesh=get_session()     
        #url = self.ip+'/api/worker/lr/initmodel'       #send train dataset and labels to worker nodes
        #sesh.post(url,json={'train_dataset':train_dataset.tolist(),'train_y':train_y.tolist(),'batch_size':batch_size})
        '''
        self.train_dataset = train_dataset
        self.train_y = train_y
        self.batch_size = batch_size
        '''
    def fit_model(self,weights,biases,step):
        #sesh=get_session()
        #self.weights = weights
        #self.biases = biases
        #url = self.ip+'/api/worker/lr/fitmodel'
        #sesh.post(url,json={'weights':weights.tolist(),'biases':biases,'step':step})        #send weights and biases and recieve weights and biases
        global producer
        producer.send(self.topic,{'fun':'fitmodel','weights':weights.tolist(),'biases':biases,'step':step})
        '''
        y_pred = self.train_dataset[self.batch_size*step : self.batch_size*step + self.batch_size]@self.weights + self.biases
        mse_loss_grad = (y_pred-self.train_y[self.batch_size*step : self.batch_size*step + self.batch_size].reshape(self.batch_size,1))/self.batch_size
        return self.weights - (self.train_dataset[self.batch_size*step : self.batch_size*step + self.batch_size].T @ mse_loss_grad)*self.learning_rate,self.biases-np.mean((y_pred-self.train_y[self.batch_size*step : self.batch_size*step + self.batch_size].reshape(self.batch_size,1)))*self.learning_rate
        '''

kconsumer = KafkaConsumer('w2m',bootstrap_servers=['kafka-service:9092'],auto_offset_reset='earliest',group_id='master',value_deserializer=lambda x: loads(x.decode('utf-8')))
spart = 0
soff = 0
first = False #first consumer call should start from its own offset
def consumer(nw):
    global regressor,kconsumer,first,spart,soff
    cnt=0
    first_it = False #first iteration should be skipped if not first consumer call
    if not first:
            with open("out",'a') as stout:
                    print(spart,soff,file=stout,flush=True)
            kconsumer.seek(spart,soff)
            first_it = True
    #consumerl = list(kconsumer)
    
    for msg in kconsumer:
        #x=ast.literal_eval(msg.value)
        x=msg.value
        if (regressor is not None):
                if not first_it:
                        first_it=True
                        continue
                else:   
                        regressor.update_model(np.array(x['wgrad']),x['bgrad'])
                        cnt+=1
                        if cnt == nw:
                                with open("out",'a') as stout:
                                        print(str(type(msg.partition)),file=stout)
                                spart=msg.partition
                                soff = msg.offset
                                break
    #kconsumer.close()
#CE

@app.route('/api/master/lr/start/<string:workers>', methods = ['GET'])
def start(workers):
    global regressor
    global X_test
    global y_test
    #CS
    #global iplist
    global topics
    with open("out",'a') as standardout:
        print("Starting processing\n",file=standardout)
    #iplist = [s+str(i)+':5000' for i in range(0,int(workers))]
    topics=['m2w'+str(i+1) for i in range(int(workers))]
    #CE
    regressor = LinearRegressor(learning_rate=0.001,n_users=int(workers))
    #initw = threading.Thread(target=regressor.fit, args=(X_train,y_train,X_test,y_test,100))
    #initw.start()
    pr = cProfile.Profile()
    pr.enable()
    regressor.fit(X_train,y_train,X_test,y_test,10)
    pr.disable()
    #temp = copy.deepcopy(sys.stdout)
    with open("out",'a') as sys.stdout:
            pr.print_stats()
    #sys.stdout = temp
    return flask.Response(status = 200)

#CS
'''
@app.route('/api/master/lr/updatemodel', methods = ['POST'])
def updatemodel():
    global regressor
    weights=np.array(flask.request.json['weights'])
    biases=flask.request.json['biases']
    regressor.update_model(weights,biases)
    return flask.Response(status = 200)
'''
#CE

@app.route('/api/gimmeresults')
def results():
    global wb
    with open('a','w') as myfile:
        print(wb,file=myfile)
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
#app.run(host='127.0.0.1', port=3000)
