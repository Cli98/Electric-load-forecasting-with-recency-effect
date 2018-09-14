# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 19:35:04 2017

@author: Changlin li
"""

import pandas as pd
import numpy as np
from numpy.matlib import repmat
from datetime import datetime
from sklearn.preprocessing import OneHotEncoder
import operator
def dataget():
    testset= pd.read_csv(r'/Users/changlinli/INES 8090/Global Energy Forecasting Competition 2012 - Load Forecasting/test.csv').iloc[:,1:]
#    ##TO DO:Clear null,cleared on 11/11
    ## chekc result of load
    load = pd.read_csv(r'/Users/changlinli/INES 8090/Global Energy Forecasting Competition 2012 - Load Forecasting/GEFCOM2012_Data/update/loadf.csv')
    temp = pd.read_csv(r'/Users/changlinli/INES 8090/Global Energy Forecasting Competition 2012 - Load Forecasting/temperature.csv')
    return load,testset,temp

def getSeriesTep(temp,i):
    if i==11:
        print "Valid range 0-10,automaticlly plus 1"
        return -1
    i = i+1
    res = temp.loc[(temp['station_id'])==i]
    return res.iloc[:-1,:]##Null at -1
              
def gety(load,i):
    ##TO DO:check null, No null
    ##TO DO:USE join to find valid data Cannot achieve in python
    ##stage 1 , trainset ,pass test
    i = i+1
    ytrain = np.array(load.loc[(load['zone_id'] == i) &((load['year']==2004) | (load['year']==2005))].iloc[:,4:]).reshape((-1,1))
    ytest = np.array(load.loc[(load['zone_id'] == i) &(load['year']==2006)].iloc[:,4:]).reshape((-1,1))
    return ytrain,ytest
def getnewytrain(load,i):
    ##For test step
    i=i+1
    y1 = np.array(load[operator.and_(load['zone_id'] == i , operator.or_(load['year']==2005,load['year']==2006))].iloc[:,4:]).reshape((-1,1))
    return y1
def getytest(testset,i):
    ##For test step
    i = i+1
    ytest = np.array(testset.loc[testset['zone_id'] == i].iloc[:,4:]).reshape((-1,1))
    return ytest

def Score(ya,yp):
    return np.mean(np.abs((ya-yp) / (ya))) * 100 #for the case where ya=0

def combSeries(seq,temp):
    res = np.array(getSeriesTep(temp,seq[0]),dtype = np.float64)
    for i in range(1,len(seq)):
        newtep = np.array(getSeriesTep(temp,seq[i]),dtype=np.float64)
        res = res+newtep
    res = np.array(res,dtype=np.float64)*1.0/len(seq)
    return pd.DataFrame(res) 
#1st newgen 2nd Combseries
def newgenhour(tempres):
    res = tempres.iloc[:,4:]
    #get all hours data in this weatherid
    res = np.array(res,dtype=np.float64).reshape((1,-1)).tolist()[0] 
    datamatrix = pd.DataFrame(repmat(np.array(tempres.iloc[:,1:4]),24,1))
    data = datamatrix.sort_values([0,1,2])
    data.columns =  ['year','month','day']
    data['hour'] = repmat(np.array([x for x in range(1,25)]).reshape((-1,1)),len(data)/24,1)
    data['temperature'] = res       
    return data  

def temformat(res,temname):
    ##build cor with temperature related features
    res[temname+"_"+str(2)] = np.array(res[temname],dtype=np.float64)**2
    res[temname+"_"+str(3)] = np.array(res[temname],dtype=np.float64)**3  
    ec = OneHotEncoder()
    ec.fit(np.array(res['month']).reshape((-1,1)))
    nd2 = (ec.transform(np.array(res['month']).reshape((-1,1))).toarray())[:,:-1]
    #res = pd.concat([res,pd.DataFrame(nd2)],axis=1)
    
    ec = OneHotEncoder()
    ec.fit(np.array(res['hour']).reshape((-1,1)))
    nd3 = (ec.transform(np.array(res['hour']).reshape((-1,1))).toarray())[:,:-1]
    #res = pd.concat([res,pd.DataFrame(nd3)],axis=1) 
    col = res.columns.tolist()
    thour = adadot(np.array(res[temname]).reshape((-1,1)),nd3)
    t2hour = adadot(np.array(res[temname+"_"+str(2)]).reshape((-1,1)),nd3)
    t3hour = adadot(np.array(res[temname+"_"+str(3)]).reshape((-1,1)),nd3)
    tmonth = adadot(np.array(res[temname]).reshape((-1,1)),nd2)
    t2month = adadot(np.array(res[temname+"_"+str(2)]).reshape((-1,1)),nd2)
    t3month = adadot(np.array(res[temname+"_"+str(3)]).reshape((-1,1)),nd2)
    
    res = pd.concat([res,pd.DataFrame(thour),pd.DataFrame(t2hour),
                 pd.DataFrame(t3hour),pd.DataFrame(tmonth),pd.DataFrame(t2month),
                             pd.DataFrame(t3month)],axis=1)
    res.columns = col+[temname+"thour"+str(i+1) for i in range(23)]+\
    [temname+"t2hour"+str(i+1) for i in range(23)]+\
    [temname+"t3hour"+str(i+1) for i in range(23)]+\
    [temname+"tmonth"+str(i+1) for i in range(11)]+\
    [temname+"t2month"+str(i+1) for i in range(11)]+\
    [temname+"t3month"+str(i+1) for i in range(11)]
    return res
def auto(res):
    ##Update 11/21 test trend
    ##pass on Tmodel
    #from sklearn import preprocessing
    res.index = [j for j in range(len(res))]
    res['trend'] = res.index

    ##Remove all temperature related feature
    ##to new function called temformat
    daynew = np.ones((24,1642))
    con = 0
    for i in range(0,len(res),24):# 
        mul = datetime(int(res.iloc[i,0]), int(res.iloc[i,1]), int(res.iloc[i,2])).weekday()+1
        daynew[:,con] = daynew[:,con] * mul
        con = con+1
    res['weekday'] = daynew.T.reshape((-1,1))        
    ec = OneHotEncoder()
    ec.fit(np.array(res['weekday']).reshape((-1,1)))
    nd = (ec.transform(np.array(res['weekday']).reshape((-1,1))).toarray())[:,:-1]
    col = res.columns.tolist()
    res = pd.concat([res,pd.DataFrame(nd)],axis=1)
    res.columns = col+["weekday"+str(i+1) for i in range(6)]
    
    ec = OneHotEncoder()
    ec.fit(np.array(res['month']).reshape((-1,1)))
    nd2 = (ec.transform(np.array(res['month']).reshape((-1,1))).toarray())[:,:-1]
    col = res.columns.tolist()
    res = pd.concat([res,pd.DataFrame(nd2)],axis=1)
    res.columns = col+["month"+str(i+1) for i in range(11)]
    
    ec = OneHotEncoder()
    ec.fit(np.array(res['hour']).reshape((-1,1)))
    col = res.columns.tolist()
    nd3 = (ec.transform(np.array(res['hour']).reshape((-1,1))).toarray())[:,:-1]
    res = pd.concat([res,pd.DataFrame(nd3)],axis=1)  
    res.columns = col+["hour"+str(i+1) for i in range(23)]
    
    hourday = adadot(nd,nd3)
    col = res.columns.tolist()
    res = pd.concat([res,pd.DataFrame(hourday)],axis=1)
    res.columns = col+["hourday"+str(i+1) for i in range(23*6)]
    #print np.isinf(res.values).sum().sum()
    #print np.isnan(res.values).sum().sum()
    #print res.isnull().sum().sum()
    return res
def adadot(x,y):
    ##assuming x,y two numpy array
    ##assuming same row
    res = np.zeros((x.shape[0],x.shape[1]*y.shape[1]))
    con = 0
    for i in range(x.shape[1]):
        for j in range(y.shape[1]):
            res[:,con] = (x[:,i]*y[:,j])
            con = con +1
    return res                    

def sysload(load):
    newload= load.loc[load['zone_id'] == 1]
    ntrain = newload.loc[(newload['year']==2004) | (newload['year']==2005)].iloc[:,4:]
    train = np.array(ntrain,dtype=np.float32).reshape((-1,1))
    ncv = newload.loc[newload['year']==2006].iloc[:,4:] 
    cv = np.array(ncv,dtype=np.float32).reshape((-1,1))
    for i in range(2,21):
        newload= load.loc[load['zone_id'] == i]
        ntrain = newload.loc[(newload['year']==2004) | (newload['year']==2005)].iloc[:,4:]
        train = np.array(ntrain,dtype=np.float32).reshape((-1,1))+train
        ncv = newload.loc[newload['year']==2006].iloc[:,4:] 
        cv = np.array(ncv,dtype=np.float32).reshape((-1,1))+cv
    return train,cv

def sysloadtest(load):
    newload= load.loc[load['zone_id'] == 1]
    ntrain = newload.loc[(newload['year']==2005) | (newload['year']==2006)].iloc[:,4:]
    train = np.array(ntrain,dtype=np.int32).reshape((-1,1))
    ntest = newload.loc[newload['year']==2007].iloc[:,4:] 
    test = np.array(ntest,dtype=np.int32).reshape((-1,1))
    for i in range(2,21):
        newload= load.loc[load['zone_id'] == i]
        ntrain = newload.loc[(newload['year']==2005) | (newload['year']==2006)].iloc[:,4:]
        train = np.array(ntrain,dtype=np.int32).reshape((-1,1))+train
        ntest = newload.loc[newload['year']==2007].iloc[:,4:] 
        test = np.array(ntest,dtype=np.int32).reshape((-1,1))+test
    return train,test

import numpy as np
import matplotlib.pyplot as plt

def two_scales(ax1, time, data1, data2, c1, c2):
    
    ax2 = ax1.twinx()

    ax1.plot(time, data1, color=c1)
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('load')

    ax2.plot(time, data2, color=c2)
    ax2.set_ylabel('temperature')
    return ax1, ax2

##Full data comb,better result in some station
def Tmodel(temp,k,d,w):
    ##initialize a trend variable ,which is in P82,
    ##HONG, TAO. Short Term Electric Load Forecasting.
    tempres = getSeriesTep(temp,k)
    #following code generate hour data
    res = newgenhour(tempres)
    ##UPDATE 11/15,genhour
    ##update11/17,iloc nd1-nd3
    ##update 11/19,revise code,newgenhour
    res = auto(res)
    
    
    res = temformat(res,"temperature")
    d,w = d+1,w+1
    if d>1:
        col = res.columns.tolist()
        tep = np.zeros((len(res),d))
        tep[:,0]=np.array(res['temperature']).reshape((len(res),))
        for i in range(1,d):
            tep[d-1:,i]=tep[d-i-1:-i,0]
        resup = pd.DataFrame(tep[:,1:])
        res=res.reset_index(drop=True)
        resup = resup.reset_index(drop=True)
        resup.columns = ["temlag"+str(i) for i in range(1,d)]
        newcols = col+["temlag"+str(i) for i in range(1,d)]
        res= pd.concat([res,resup],axis=1,ignore_index=True)
        res.columns = newcols
        #print res.columns
        for i in range(1,d):
            res = temformat(res,"temlag"+str(i))

    if w>1:
        col = res.columns.tolist()
        tep = np.zeros((len(res),w))
        tep[:,0]=np.array(res['temperature']).reshape((len(res),))
        for i in range(1,w):
            for j in range(i*24,len(res['temperature'])):
                tep[j,i]=sum(tep[j-i*24:j-i*24+24,0])*1.0/24
        resup = pd.DataFrame(tep[:,1:])
        res=res.reset_index(drop=True)
        resup = resup.reset_index(drop=True)
        #resup.columns = ["temweek"+str(i) for i in range(1,w)]
        newcols = col+["temweek"+str(i) for i in range(1,w)]
        res= pd.concat([res,resup],axis=1,ignore_index=True)
        res.columns = newcols
        for i in range(1,w):
            res = temformat(res,"temweek"+str(i))

    if d>1 or w>1:
        #tep = tep[max(d-1,(w-1)*24):,:]
        res = res.iloc[max(d-1,(w-1)*24):,:]
    trainset = res.loc[(res['year']==2004) | (res['year']==2005)]
    trainset = trainset.drop(['year','day','month','hour','weekday'],axis=1) 
    return trainset

def Tmodelcom(temp,seq,d,w):
    ##initialize a trend variable ,which is in P82,
    ##HONG, TAO. Short Term Electric Load Forecasting.
    ##Revise 11/19,should return train,cvset required,no drop
    d,w =d+1,w+1
    tempres = combSeries(seq,temp)
    #following code generate hour data
    res = newgenhour(tempres)
    res = auto(res)
    res = temformat(res,"temperature")
    if d>1:
        col = res.columns.tolist()
        tep = np.zeros((len(res),d))
        tep[:,0]=np.array(res['temperature']).reshape((len(res),))
        for i in range(1,d):
            tep[d-1:,i]=tep[d-i-1:-i,0]
        resup = pd.DataFrame(tep[:,1:])
        res=res.reset_index(drop=True)
        resup = resup.reset_index(drop=True)
        resup.columns = ["temlag"+str(i) for i in range(1,d)]
        newcols = col+["temlag"+str(i) for i in range(1,d)]
        res= pd.concat([res,resup],axis=1,ignore_index=True)
        res.columns = newcols
        for i in range(1,d):
            res = temformat(res,"temlag"+str(i))
    if w>1:
        col = res.columns.tolist()
        tep = np.zeros((len(res),w))
        tep[:,0]=np.array(res['temperature']).reshape((len(res),))
        for i in range(1,w):
            for j in range(i*24,len(res['temperature'])):
                tep[j,i]=sum(tep[j-i*24:j-i*24+24,0])*1.0/24
        resup = pd.DataFrame(tep[:,1:])
        res=res.reset_index(drop=True)
        resup = resup.reset_index(drop=True)
        resup.columns = ["temweek"+str(i) for i in range(1,w)]
        newcols = col+["temweek"+str(i) for i in range(1,w)]
        res= pd.concat([res,resup],axis=1,ignore_index=True)
        res.columns = newcols
        for i in range(1,w):
            res = temformat(res,"temweek"+str(i))
    if d>1 or w>1:
        #tep = tep[max(d-1,(w-1)*24):,:]
        res = res.iloc[max(d-1,(w-1)*24):,:]
    trainset = res.loc[(res['year']==2004) | (res['year']==2005)]
    testset = res.loc[(res['year']==2006)]
    trainset = trainset.drop(['year','day','month','hour','weekday'],axis=1) 
    testset = testset.drop(['year','day','month','hour','weekday'],axis=1) 
    return trainset,testset

def Ttest(temp,seq,d,w):
    ##initialize a trend variable ,which is in P82,
    ##HONG, TAO. Short Term Electric Load Forecasting.
    d,w = d+1,w+1
    tempres = combSeries(seq,temp)
    #following code generate hour data
    res = auto(newgenhour(tempres))
    res = temformat(res,"temperature")
    
    if d>1:
        col = res.columns.tolist()
        tep = np.zeros((len(res),d))
        tep[:,0]=np.array(res['temperature']).reshape((len(res),))
        for i in range(1,d):
            tep[d-1:,i]=tep[d-i-1:-i,0]
        resup = pd.DataFrame(tep[:,1:])
        res=res.reset_index(drop=True)
        resup = resup.reset_index(drop=True)
        #resup.columns = ["temlag"+str(i) for i in range(1,d)]
        newcols = col+["temlag"+str(i) for i in range(1,d)]
        res= pd.concat([res,resup],axis=1,ignore_index=True)
        res.columns = newcols
        for i in range(1,d):
            res = temformat(res,"temlag"+str(i))
    if w>1:
        col = res.columns.tolist()
        tep = np.zeros((len(res),w))
        tep[:,0]=np.array(res['temperature']).reshape((len(res),))
        for i in range(1,w):
            for j in range(i*24,len(res['temperature'])):
                tep[j,i]=sum(tep[j-i*24:j-i*24+24,0])*1.0/24
        resup = pd.DataFrame(tep[:,1:])
        res=res.reset_index(drop=True)
        resup = resup.reset_index(drop=True)
        #resup.columns = ["temweek"+str(i) for i in range(1,w)]
        newcols = col+["temweek"+str(i) for i in range(1,w)]
        res= pd.concat([res,resup],axis=1,ignore_index=True)
        res.columns = newcols
        for i in range(1,w):
            res = temformat(res,"temweek"+str(i))
    ##cut dataset
    testset = res.loc[(res['year']==2007)] 
    trainset = res.loc[(res['year']==2005) | (res['year']==2006)]    ##delete this to turn back
    trainset = trainset.drop(['year','day','month','hour','weekday'],axis=1) 
    testset = testset.drop(['year','day','month','hour','weekday'],axis=1) 
    return trainset,testset
