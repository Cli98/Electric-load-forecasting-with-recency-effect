# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 19:29:25 2017

@author: Changlin Li
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from support import dataget,getSeriesTep,Tmodel,Score,gety,combSeries,Tmodelcom,getytest
from support import Ttest,getnewytrain,newgenhour,sysload,sysloadtest
from sklearn.linear_model import LinearRegression

load,testset,temp = dataget()
#generate system zone
cond = None
finalscore = []
group = []
for j in range(20):
    for w in range(0,8):
    ##Do remember to change d back to 0
        for d in range(0,49):
            score = []
            ytrain,ytest = gety(load,j)  #decide Zoneid
            for k in range(11):
                m = Tmodel(temp,k,d,w) #prefitted model,decide stationid
                lr = LinearRegression()
                lr.fit(m,ytrain[max(d,w*24):],cond = cond)
                yact = lr.predict(m)
                score.append(Score(ytrain[max(d,w*24):],yact))
            score = pd.DataFrame(score)
            score = score.sort_values(by=score.columns[0])
            scind = score.index.tolist()
            ##combine temperature
            newscore,testscore = [],[]
            for i in range(11):
                xtrain,xtest = Tmodelcom(temp,scind[:i+1],d,w) 
                lr.fit(xtrain,ytrain[max(d,w*24):],cond=cond)
                yact = lr.predict(xtest)
                newscore.append(Score(ytest,yact))
            print 'result for zone '+str(j+1)
            print 'the lowest MAPE is: '+str(min(newscore))
            finalscore.append(min(newscore))
#            print 'the correspont stations are: '+ str(scind[:np.argmin(np.array(newscore))+1])
            group.append(scind[:np.argmin(np.array(newscore))+1])
            
            ytrain,ytest = getnewytrain(load,j),getytest(testset,j)
            xtrain,xtest = Ttest(temp,scind[:np.argmin(np.array(newscore))+1],d,w)
            lr = LinearRegression(n_jobs=-1)
            #lr = LinearRegression(n_jobs=1)
            lr.fit(xtrain,ytrain,cond = cond)
            yact = lr.predict(xtest)
            testscore.append(Score(ytest,yact))
            print finalscore[-1],testscore[-1]

##Test on paper #2
##stage 1 pass
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from support import dataget,getSeriesTep,Tmodel,Score,gety,combSeries,Tmodelcom,getytest
from support import Ttest,getnewytrain,newgenhour,sysload,sysloadtest
from sklearn.linear_model import LinearRegression

load,testset,temp = dataget()
##check ytrain/ytest
#np.linalg.matrix_rank(np.array(xtrain))
cvscore,testscore =[],[]
cond = None
for w in range(7,8):
    ##Do remember to change d back to 0
    for d in range(0,49):
#w,d = 0,15
        ytrain,ytest = sysload(load)
        score = []
        lr = LinearRegression(n_jobs=-1)
        for k in range(11):
            m = Tmodel(temp,k,d,w) #prefitted model,decide stationid
            lr.fit(m,ytrain[max(d,w*24):],cond = cond)
            yact = lr.predict(m)
            score.append(Score(ytrain[max(d,w*24):],yact))
        score = pd.DataFrame(score)
        score = score.sort_values(by=score.columns[0])
        scind = score.index.tolist()
        newscore = []
        for i in range(11):
            xtrain,xtest = Tmodelcom(temp,scind[:i+1],d,w) 
            lr.fit(xtrain,ytrain[max(d,w*24):],cond=cond)
            yact = lr.predict(xtest)
            newscore.append(Score(ytest,yact))
        
#        print 'result for zone 21'
#        print 'the lowest MAPE is: '+str(min(newscore))
#        print 'the correspont stations are: '+ str(scind[:np.argmin(np.array(newscore))+1]) 
        cvscore.append(min(newscore))
        
        ytrain,ytest = sysloadtest(load)
        xtrain,xtest = Ttest(temp,[i for i in range(11)],d,w)
        lr = LinearRegression(n_jobs=-1)
        #lr = LinearRegression(n_jobs=1)
        lr.fit(xtrain,ytrain,cond = cond)
        yact = lr.predict(xtest)
        testscore.append(Score(ytest,yact))
        print cvscore[-1],testscore[-1]