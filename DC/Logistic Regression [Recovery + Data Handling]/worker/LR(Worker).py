import flask
import requests
import numpy as np
import pandas as pd
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)

user=None

sesh=requests.Session()


class User:
    def __init__(self,learning_rate=0.1):
        self.learning_rate = learning_rate
    def init_model(self,train_dataset,train_y,batch_size):
        self.train_dataset = train_dataset      #recieve data from Master
        self.train_y = train_y
        self.batch_size = batch_size
    def fit_model(self,weights,biases,step): 
        self.weights = weights      #recieved data
        self.biases = biases
        y_pred = self.train_dataset[self.batch_size*step : self.batch_size*step + self.batch_size]@self.weights + self.biases
        #y_pred = 1/(1+ np.exp(self.train_dataset[self.batch_size*step : self.batch_size*step + self.batch_size]@self.weights + self.biases))
        mse_loss_grad = (y_pred-self.train_y[self.batch_size*step : self.batch_size*step + self.batch_size].reshape(self.batch_size,1))/self.batch_size
        return (self.train_dataset[self.batch_size*step : self.batch_size*step + self.batch_size].T @ mse_loss_grad)*self.learning_rate,np.mean((y_pred-self.train_y[self.batch_size*step : self.batch_size*step + self.batch_size].reshape(self.batch_size,1)))*self.learning_rate       #send back updates


@app.route('/api/worker/lr/userinit', methods = ['POST'])
def userinit():
    global user
    lr=flask.request.json['learning_rate']
    user=User(lr)
    return flask.Response(status = 200)
    
@app.route('/api/worker/lr/initmodel', methods = ['POST'])
def initmodel():
    global user
    try:
        with open("out",'a') as standardout:
            print("Initialising model",file=standardout)
        #train_dataset=np.array(flask.request.json['train_dataset'])
        #train_y=np.array(flask.request.json['train_y'])
        dataset = pd.read_csv('USA_Housing.csv')
        X = dataset.iloc[:,0:5].values
        y = dataset.iloc[:,5].values
        with open("out",'a') as standardout:
            print("Xshape",X.shape,file=standardout)

        # Feature Scaling
        from sklearn.preprocessing import StandardScaler
        sc_X = StandardScaler()
        X = sc_X.fit_transform(X)
        with open("out",'a') as standardout:
            print("Xshape",X.shape,file=standardout)    
        batch_size=flask.request.json['batch_size']
        user.init_model(X,y,batch_size)
        return flask.Response(status = 200)
    except Exception as e:
        with open("out",'a') as standardout:
            print(str(e),file=standardout)
    
    return flask.Response(status=500)
    
@app.route('/api/worker/lr/fitmodel', methods=['POST'])
def fitmodel():
    global user
    global sesh
    weights=np.array(flask.request.json['weights'])
    biases=flask.request.json['biases']
    step=flask.request.json['step']
    (weights,biases)=user.fit_model(weights,biases,step)
    url = 'http://master:5000/api/master/lr/updatemodel'
    sesh.post(url,json={'weights':weights.tolist(),'biases':biases})
    return flask.Response(status = 200)
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    

