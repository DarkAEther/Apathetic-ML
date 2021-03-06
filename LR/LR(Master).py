
import numpy
import pandas as pd
import requests
import flask
import threading
import concurrent.futures
import time

numpy.random.seed(42)

app = flask.Flask(__name__)

dataset = pd.read_csv('USA_Housing.csv')
X = dataset.iloc[:,0:5].values
y = dataset.iloc[:,5].values

regressor=None

#iplist=["http://127.0.0.1:5000","http://127.0.0.1:7000"]
s = 'worker'
iplist = [s+'0'+str(i) for i in range(1,3)]

thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 0)

from sklearn.preprocessing import StandardScaler
sc_X = StandardScaler()
X_train = sc_X.fit_transform(X_train)
X_test = sc_X.transform(X_test)


class LinearRegressor:
    def __init__(self,learning_rate = 0.1,n_users = 1):
        self.n_users = n_users
        self.learning_rate = learning_rate
    def fit(self,train_dataset,train_y,batch_size = 200,n_iters = 200):
        global iplist
        self.number_of_weights = train_dataset.shape[1]
        self.weights = numpy.random.rand(self.number_of_weights,1)
        self.biases = numpy.random.rand()
        self.train_dataset = train_dataset
        self.train_y = train_y
        self.batch_size = batch_size
        self.train_dataset_user_batches = numpy.split(self.train_dataset,self.n_users)
        self.train_y_user_batches = numpy.split(self.train_y,self.n_users)
        self.users = [User(ip=iplist[user],learning_rate = self.learning_rate) for user in range(self.n_users)]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for user_i in range(self.n_users):
                executor.submit(self.users[user_i].init_model,self.train_dataset_user_batches[user_i],self.train_y_user_batches[user_i],self.batch_size//self.n_users)
        for j in range(n_iters):
            for step_i in range((train_y.shape[0]//self.batch_size)):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for user_i in range(self.n_users):
                        executor.submit(self.users[user_i].fit_model,self.weights,self.biases,step_i)
                    print("ITER",j)
    def test_loss(self,test_dataset,test_y):
        result = test_dataset @ self.weights + self.biases
        result_loss = numpy.square(result-test_y).mean()
        return result_loss
    def predict(self,X):
        return X@self.weights + self.biases
    def get_weights(self):
        return self.weights,self.biases
    def update_model(self, weights, biases):
        self.weights -= weights      #recieve the updates in a sperate asynchronous function
        self.biases -= biases
        print(self.weights,self.biases)


class User:
    def __init__(self,ip,learning_rate=0.1):
        sesh=get_session()
        self.learning_rate = learning_rate
        self.ip=ip
        url = self.ip+'/api/worker/lr/userinit'
        sesh.post(url,json={'learning_rate':learning_rate})
    def init_model(self,train_dataset,train_y,batch_size):
        sesh=get_session()     
        url = self.ip+'/api/worker/lr/initmodel'       #send train dataset and labels to worker nodes
        sesh.post(url,json={'train_dataset':train_dataset.tolist(),'train_y':train_y.tolist(),'batch_size':batch_size})
        '''
        self.train_dataset = train_dataset
        self.train_y = train_y
        self.batch_size = batch_size
        '''
    def fit_model(self,weights,biases,step):
        sesh=get_session()
        self.weights = weights
        self.biases = biases
        url = self.ip+'/api/worker/lr/fitmodel'
        sesh.post(url,json={'weights':weights.tolist(),'biases':biases,'step':step})        #send weights and biases and recieve weights and biases
        '''
        y_pred = self.train_dataset[self.batch_size*step : self.batch_size*step + self.batch_size]@self.weights + self.biases
        mse_loss_grad = (y_pred-self.train_y[self.batch_size*step : self.batch_size*step + self.batch_size].reshape(self.batch_size,1))/self.batch_size
        return self.weights - (self.train_dataset[self.batch_size*step : self.batch_size*step + self.batch_size].T @ mse_loss_grad)*self.learning_rate,self.biases-np.mean((y_pred-self.train_y[self.batch_size*step : self.batch_size*step + self.batch_size].reshape(self.batch_size,1)))*self.learning_rate
        '''


@app.route('/api/master/lr/start', methods = ['GET'])
def start():
    global regressor
    a=time.time()
    regressor = LinearRegressor(learning_rate=0.001,n_users=2)
    regressor.fit(X_train,y_train,n_iters = 100)
    b=time.time()
    print("TIME TO EXEC:",b-a)
    y_pred = regressor.predict(X_test)
    test_loss=regressor.test_loss(X_test,y_test)
    print(test_loss)
    #print(y_pred[:10])
    return flask.Response(status = 200)

@app.route('/api/master/lr/updatemodel', methods = ['POST'])
def updatemodel():
    global regressor
    weights=numpy.array(flask.request.json['weights'])
    biases=flask.request.json['biases']
    regressor.update_model(weights,biases)
    return flask.Response(status = 200)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4000)

