#nnet_survival_examples.py

#Examples of neural network survival model with simulated data
#Designed to be run interactively. Go to the directory containing nnet_survival.py and then start Python (or add that directory to Python path).

#Author: Michael Gensheimer, Stanford University, michael.gensheimer@gmail.com
#Tested with Python version 3.6, Keras version 2 (using TensorFlow backend)

from __future__ import print_function
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from keras.preprocessing import sequence
from keras.models import Sequential, Model
from keras.layers import Input, Dense, Dropout, Activation, LSTM, GRU, Embedding, Concatenate, Conv1D, GlobalMaxPooling1D, MaxPooling1D, GlobalAveragePooling1D, BatchNormalization, TimeDistributed
from keras import optimizers, layers, regularizers
import keras.backend as K
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import load_model
import math
from lifelines import KaplanMeierFitter
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index

import nnet_survival


##########################################################################
#Define the time intervals for the discrete-time survival model
#Since there are fewer events per day at later follow-up times, increasing
#time interval width at later times may improve parameter estimation.

fixed_interval_width = 0
if fixed_interval_width:
	breaks=np.arange(0.,365.*5,365./8)
	n_intervals=len(breaks)-1
	timegap = breaks[1:] - breaks[:-1]
else:
	halflife=365.*2
	breaks=-np.log(1-np.arange(0.0,0.96,0.05))*halflife/np.log(2) 
	n_intervals=len(breaks)-1
	timegap = breaks[1:] - breaks[:-1]
 
##################################################################
#Flexible model (non-proportional hazards).
#All pts with same exponential survival distribution, no censoring

halflife1 = 365.
n_samples=1000
np.random.seed(seed=0)
t = np.random.exponential(scale=1 / (np.log(2)/halflife1), size=n_samples)
f=np.ones(n_samples) #all patients failed (none censored)
#y_train=nnet_survival.make_surv_array(t,f)
y_train=nnet_survival.make_surv_array(t,f,breaks)
x_train = np.zeros(n_samples)

model = Sequential()
#Hidden layers would go here. For this example, using simple linear model with no hidden layers.
model.add(Dense(n_intervals,input_dim=1, kernel_initializer='zeros', bias_initializer='zeros'))
model.add(Activation('sigmoid'))
model.compile(loss=nnet_survival.surv_likelihood(n_intervals), optimizer=optimizers.RMSprop())
#model.summary()
early_stopping = EarlyStopping(monitor='loss', patience=2)
history=model.fit(x_train, y_train, batch_size=256, epochs=100000, callbacks=[early_stopping])
y_pred=model.predict_proba(x_train,verbose=0)

kmf = KaplanMeierFitter()
kmf.fit(t, event_observed=f)
plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred[0,:]))),'bo-')
plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,color='k')
plt.xlabel('Follow-up time (days)')
plt.ylabel('Proportion surviving')
plt.title('All patients from same survival distribution, no censoring. Actual=black, predicted=blue.')
plt.show()

############################################################################
#Flexible model (non-proportional hazards).
#All pts with same exponential survival distribution, some patients censored

halflife1 = 365.*2
n_samples=1000
np.random.seed(seed=0)
time = np.random.exponential(scale=1 / (np.log(2)/halflife1), size=n_samples)
censtime = np.random.exponential(scale=1 / (np.log(2)/(1.0*halflife1)), size=n_samples)
f = time<censtime
t = time
t[~f] = censtime[~f]
y_train=nnet_survival.make_surv_array(t,f,breaks)
x_train = np.zeros(n_samples)

model = Sequential()
#Hidden layers would go here. For this example, using simple linear model with no hidden layers.
model.add(Dense(n_intervals,input_dim=1, kernel_initializer='zeros', bias_initializer='zeros'))
model.add(Activation('sigmoid'))
model.compile(loss=nnet_survival.surv_likelihood(n_intervals), optimizer=optimizers.RMSprop())
#model.summary()
early_stopping = EarlyStopping(monitor='loss', patience=2)
history=model.fit(x_train, y_train, batch_size=256, epochs=10000, callbacks=[early_stopping])
y_pred=model.predict_proba(x_train,verbose=0)

kmf = KaplanMeierFitter()
kmf.fit(t, event_observed=f)
plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred[0,:]))),'bo-')
plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,color='k')
plt.xlabel('Follow-up time (days)')
plt.ylabel('Proportion surviving')
plt.title('All patients from same survival distribution, some censored. Actual=black, predicted=blue.')
plt.show()

########################################################
#Flexible model (non-proportional hazards).
#some patients censored, one discrete predictor variable

halflife1 = 200
halflife2 = 400
halflife_cens = 400
n_samples=5000
np.random.seed(seed=0)
t1 = np.random.exponential(scale=1 / (np.log(2)/halflife1), size=int(n_samples/2))
t2 = np.random.exponential(scale=1 / (np.log(2)/halflife2), size=int(n_samples/2))
t=np.concatenate((t1, t2))
censtime = np.random.exponential(scale=1 / (np.log(2)/(halflife_cens)), size=n_samples)
f = t<censtime
t[~f] = censtime[~f]

y_train=nnet_survival.make_surv_array(t,f,breaks)
x_train = np.zeros(n_samples)
x_train[int(n_samples/2):]=1

model = Sequential()
#Hidden layers would go here. For this example, using simple linear model with no hidden layers.
model.add(Dense(n_intervals,input_dim=1, kernel_initializer='zeros', bias_initializer='zeros'))
model.add(Activation('sigmoid'))
model.compile(loss=nnet_survival.surv_likelihood(n_intervals), optimizer=optimizers.RMSprop())
#model.summary()
early_stopping = EarlyStopping(monitor='loss', patience=2)
history=model.fit(x_train, y_train, batch_size=256, epochs=1000, callbacks=[early_stopping])
y_pred=model.predict_proba(x_train,verbose=0)

kmf = KaplanMeierFitter()
kmf.fit(t[0:int(n_samples/2)], event_observed=f[0:int(n_samples/2)])
plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred[0,:]))),'bo-')
plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,color='k')
kmf.fit(t[int(n_samples/2)+1:], event_observed=f[int(n_samples/2)+1:])
plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred[-1,:]))),'ro-')
plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,color='k')
plt.xticks(np.arange(0, 2000.0001, 200))
plt.yticks(np.arange(0, 1.0001, 0.125))
plt.xlim([0,2000])
plt.ylim([0,1])
plt.xlabel('Follow-up time (days)')
plt.ylabel('Proportion surviving')
plt.title('One covariate. Actual=black, predicted=blue/red.')
plt.show()

##########################################################
#Proportional hazards model with flexible baseline hazard:
#One binary predictor variable

breaks=np.arange(0,5000,50)
n_intervals=len(breaks)-1
timegap = breaks[1:] - breaks[:-1]

halflife1 = 200
halflife2 = 400
halflife_cens = 400
n_samples=5000
np.random.seed(seed=0)
t1 = np.random.exponential(scale=1 / (np.log(2)/halflife1), size=int(n_samples/2))
t2 = np.random.exponential(scale=1 / (np.log(2)/halflife2), size=int(n_samples/2))
t=np.concatenate((t1, t2))
censtime = np.random.exponential(scale=1 / (np.log(2)/(halflife_cens)), size=n_samples)
f = t<censtime
t[~f] = censtime[~f]

y_train=nnet_survival.make_surv_array(t,f,breaks)
x_train = np.zeros(n_samples)
x_train[int(n_samples/2):]=1

model = Sequential()
#Hidden layers would go here. For this example, using simple linear model with no hidden layers.
model.add(Dense(1,input_dim=1, use_bias=0, kernel_initializer='zeros'))
model.add(nnet_survival.PropHazards(n_intervals))
model.compile(loss=nnet_survival.surv_likelihood(n_intervals), optimizer=optimizers.RMSprop())
#model.summary()
early_stopping = EarlyStopping(monitor='loss', patience=2)
history=model.fit(x_train, y_train, batch_size=32, epochs=1000, callbacks=[early_stopping])
y_pred=model.predict_proba(x_train,verbose=0)

kmf = KaplanMeierFitter()
kmf.fit(t[0:int(n_samples/2)], event_observed=f[0:int(n_samples/2)])
plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred[0,:]))),'bo-')
plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,color='k')
kmf.fit(t[int(n_samples/2)+1:], event_observed=f[int(n_samples/2)+1:])
plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred[-1,:]))),'ro-')
plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,color='k')
plt.xticks(np.arange(0, 2000.0001, 200))
plt.yticks(np.arange(0, 1.0001, 0.125))
plt.xlim([0,2000])
plt.ylim([0,1])
plt.xlabel('Follow-up time (days)')
plt.ylabel('Proportion surviving')
plt.title('One covariate. Actual=black, predicted=blue/red.')
plt.show()

myData=pd.DataFrame({'x_train' : x_train, 't' : t, 'f' : f}) 
cf = CoxPHFitter()
cf.fit(myData, 't', event_col='f')
cox_coef = cf.hazards_.x_train.values[0]
nn_coef = model.get_weights()[0][0][0]
print('Cox model coefficient:')
print(cox_coef)
print('Cox model hazard ratio:')
print(np.exp(cox_coef))
print('Neural network coefficient:')
print(nn_coef)
print('Neural network hazard ratio:')
print(np.exp(nn_coef))

##########################################################
#Proportional hazards model with flexible baseline hazard:
#Multiple variables, mix of discrete and continuous

breaks=np.arange(0.,365.*5,365./8)
n_intervals=len(breaks)-1
timegap = breaks[1:] - breaks[:-1]

sampleSize = 10000

np.random.seed(12345)

beta1 = -.015
beta2 = .2
beta3 = .001;
lambdaT = 365./np.log(2)
lambdaC = 2*365./np.log(2)

age = np.random.choice(np.arange(40,71),size=sampleSize)
sex = np.random.choice([0,1],size=sampleSize)
lab = np.random.normal(size=sampleSize)
trueTime = np.random.exponential(scale = lambdaT * np.exp(-(beta1*age + beta2*sex + beta3*lab )),
	size=sampleSize)
censoringTime = np.random.exponential(scale = lambdaC, size=sampleSize)
time = np.minimum(trueTime, censoringTime)
event = (time == trueTime)*1.
myData=pd.DataFrame({'age':age, 'lab':lab, 'sex':sex, 'time':time, 'event':event}) 

y_train=nnet_survival.make_surv_array(time,event,breaks)
x_train=myData.as_matrix(columns=['age','sex','lab',])

model = Sequential()
#Hidden layers would go here. For this example, using simple linear model with no hidden layers.
model.add(Dense(1,input_dim=x_train.shape[1], use_bias=0, kernel_initializer='zeros'))
model.add(nnet_survival.PropHazards(n_intervals))
model.compile(loss=nnet_survival.surv_likelihood(n_intervals), optimizer=optimizers.RMSprop())
#model.summary()
early_stopping = EarlyStopping(monitor='loss', patience=2)
history=model.fit(x_train, y_train, batch_size=16, epochs=1000, callbacks=[early_stopping])
#y_pred=model.predict_proba(x_train,verbose=0)
print('Neural net coefficients are close to beta coefficients used to generate the data distribution.')
print(model.get_weights()[0])


###################################################################################
#Flexible model: "Real" neural network using MNIST data
#Adapted from https://github.com/keras-team/keras/blob/master/examples/mnist_cnn.py
#For this example, using 5 groups of digits: 0-1, 2-3, 4-5, 6-7, 8-9
#Higher digits have shorter average survival. Task: Given an image of a digit, predict survival curve.

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D

num_classes = 5
img_rows, img_cols = 28, 28

(x_train, y_train), (x_test, y_test) = mnist.load_data()
if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

#condense from 10 to 5 classes
y_train=np.floor(y_train/2.)
y_test=np.floor(y_test/2.)

#Create simulated survival data, with higher digits having shorter average survival
sampleSizeTrain = 60000
sampleSizeTest = 10000
np.random.seed(0)
beta = 0.9
lambdaT = 365./np.log(2)
lambdaC = 2*365./np.log(2)
trueTime = np.random.exponential(scale = lambdaT * np.exp(-(beta*y_train)),
	size=sampleSizeTrain)
censoringTime = np.random.exponential(scale = lambdaC, size=sampleSizeTrain)
time = np.minimum(trueTime, censoringTime)
event = (time == trueTime)*1.

trueTimeTest = np.random.exponential(scale = lambdaT * np.exp(-(beta*y_test)),
	size=sampleSizeTest)
censoringTimeTest = np.random.exponential(scale = lambdaC, size=sampleSizeTest)
timeTest = np.minimum(trueTimeTest, censoringTimeTest)
eventTest = (timeTest == trueTimeTest)*1.

#Convert event data to array format
breaks=np.concatenate((np.arange(0,200,10),np.arange(200,1001,25)))
n_intervals=len(breaks)-1
timegap = breaks[1:] - breaks[:-1]
y_train_array=nnet_survival.make_surv_array(time,event,breaks)

#Train model
model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3),
                 activation='relu',
                 input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
prop_hazards=0
if prop_hazards:
	model.add(Dense(1, use_bias=0, kernel_initializer='zeros'))
	model.add(nnet_survival.PropHazards(n_intervals))
else:
	model.add(Dense(n_intervals, kernel_initializer='zeros', bias_initializer='zeros'))
	model.add(Activation('sigmoid'))
model.compile(loss=nnet_survival.surv_likelihood(n_intervals), optimizer=optimizers.RMSprop())
early_stopping = EarlyStopping(monitor='loss', patience=1)
history=model.fit(x_train, y_train_array, batch_size=64, epochs=20, verbose=1, callbacks=[early_stopping])
y_pred=model.predict_proba(x_train,verbose=0)

#Training set results
kmf = KaplanMeierFitter()
matplotlib.style.use('default')
actual = []
predicted = []
for i in range(num_classes):
	kmf.fit(time[y_train==i], event_observed=event[y_train==i])
	actual.append(plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,ls='--',c='C'+str(i)))
	y_pred_class_mean = np.mean(y_pred[np.where(y_train==i)[0],:],axis=0)
	predicted.append(plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred_class_mean))),ls='-',c='C'+str(i)))
plt.xticks(np.arange(0, 1000.0001, 200))
plt.yticks(np.arange(0, 1.0001, 0.125))
plt.xlim([0,1000])
plt.ylim([0,1])
plt.xlabel('Follow-up time (days)')
plt.ylabel('Proportion surviving')
plt.legend(['0-1: Actual','0-1: Predicted',
	'2-3: Actual','2-3: Predicted',
	'4-5: Actual','4-5: Predicted',
	'6-7: Actual','6-7: Predicted',
	'8-9: Actual','8-9: Predicted'])
plt.title('Training set. Higher digit = shorter survival.')
plt.show()

#Test set results
y_pred=model.predict_proba(x_test,verbose=0)
kmf = KaplanMeierFitter()
matplotlib.style.use('default')
actual = []
predicted = []
for i in range(num_classes):
	kmf.fit(timeTest[y_test==i], event_observed=eventTest[y_test==i])
	actual.append(plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,ls='--',c='C'+str(i)))
	y_pred_class_mean = np.mean(y_pred[np.where(y_test==i)[0],:],axis=0)
	predicted.append(plt.plot(breaks,np.concatenate(([1],np.cumprod(y_pred_class_mean))),ls='-',c='C'+str(i)))
plt.xticks(np.arange(0, 1000.0001, 200))
plt.yticks(np.arange(0, 1.0001, 0.125))
plt.xlim([0,1000])
plt.ylim([0,1])
plt.xlabel('Follow-up time (days)')
plt.ylabel('Proportion surviving')
plt.legend(['0-1: Actual','0-1: Predicted',
	'2-3: Actual','2-3: Predicted',
	'4-5: Actual','4-5: Predicted',
	'6-7: Actual','6-7: Predicted',
	'8-9: Actual','8-9: Predicted'])
plt.title('Test set. Higher digit = shorter survival.')
plt.show()


#############################################################
#Flexible model: investigate optimal width of time intervals.
#True survival times are drawn from Weibull distribution.

sampleSize = 5000

np.random.seed(0)

beta1 = 1.0
lambdaT = 365./np.log(2)
lambdaC = 2*365./np.log(2)

lab = np.random.choice([0,1],size=sampleSize)
from scipy.stats import weibull_min
trueTime = weibull_min.rvs(c=1.5,scale = lambdaT * np.exp(-(beta1*lab)),
	size=sampleSize)
censoringTime = np.random.exponential(scale = lambdaC, size=sampleSize)
time = np.minimum(trueTime, censoringTime)
event = (time == trueTime)*1.
x_train=lab

kmf = KaplanMeierFitter()
kmf.fit(time, event_observed=np.ones([sampleSize]))
print('Actual median survival, in days:')
print(kmf.median_)

halflife=365.
breaks_list = [np.arange(0.,365.*5.01,365.),
	np.arange(0.,365.*5.01,365./4),
	np.arange(0.,365.*5.01,365./12),
	np.arange(0.,365.*5.01,365./52),
	-np.log(1-np.arange(0.0,0.96,0.05))*halflife/np.log(2)]

breaks_description_list = ['uniform intervals every year',
	'uniform intervals every 3 months',
	'uniform intervals every month',
	'uniform intervals every week',
	'increasing intervals over time, half-life 1 year']

for breaks_i in range(len(breaks_list)):
	breaks=breaks_list[breaks_i]
	n_intervals=len(breaks)-1
	timegap = breaks[1:] - breaks[:-1]
	y_train=nnet_survival.make_surv_array(time,event,breaks)
	model = Sequential()
	model.add(Dense(n_intervals,input_dim=1, kernel_initializer='zeros', bias_initializer='zeros'))
	model.add(Activation('sigmoid'))
	model.compile(loss=nnet_survival.surv_likelihood(n_intervals), optimizer=optimizers.RMSprop())
	#model.summary()
	early_stopping = EarlyStopping(monitor='loss', patience=2)
	history=model.fit(x_train, y_train, batch_size=16, epochs=1000, callbacks=[early_stopping],verbose=0)
	y_pred=model.predict_proba(x_train,verbose=0)
	surv_1yr = np.zeros([y_pred.shape[0]])
	for i in range(y_pred.shape[0]):
		surv_1yr[i] = np.interp(365.,breaks,np.concatenate(([1],np.cumprod(y_pred[i,:]))))
	print('Harrell C-index for: '+breaks_description_list[breaks_i])
	print(concordance_index(time,surv_1yr,event))

if 0:
	kmf = KaplanMeierFitter()
	kmf.fit(time, event_observed=np.ones([sampleSize]))
	print(kmf.median_)
	plt.plot(kmf.survival_function_.index.values, kmf.survival_function_.KM_estimate,color='k')
	plt.xlim([0,2000])
	plt.ylim([0,1])
	plt.show()

