from datetime import datetime
import requests as req
import json
from time import sleep
import pymongo 
import threading
import math


requiredExperiesDict={}
requiredExperiesList=[]
tempNextMonth=[]
tempCurrentMonth=[]
tempNextSecondMonth=[]
tempNextThirdMonth=[]
#used for days after current month expery
tempExtraMonth=[]



#flag to take care of only 1 time expery is calculated in 1 day
countExperyFlag=0

#todays date 
todayDate=datetime.now().strftime("%Y-%m-%d")
expiryDates= []

headers={"content-type": "application/json"}
api="localhost:3000/notification"

           




class advAndDec():

    global todayDate,headers,api
    maxTries=20
    # this constructors does configuration with database
    def __init__(self,):

       #HEADERS AND COOKIES CONFIGURATION
       self.headers={"Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7","Accept-Encoding": "gzip, deflate, br", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}
       self.url = "https://www1.nseindia.com/live_market/dynaContent/live_analysis/changePercentage.json"
       req.session().cookies.set('bm_sv',
                              '2B6823F5190DB60C95506066CE15E4EE~h7R316R9Klusk/OZg2Iof0r/bfX2p9aYaOvOsKsQfnWAOOqnVRSg53yHAYwOzvrVQVJhfHgdQxAiEcHLXEqVE24jfB25brBJYS++kOu1z3YXTtjfY2uD8/DfgyDMs8agUBbt33Ig4uwL8NmcU/11IBp1x4cE50m1eVUiYLHDojI')
       

       #DATABASE CONFIGURATION
       client=pymongo.MongoClient("mongodb://localhost:27017/")
       self.database=client["trading"]
       self.advDecDB=self.database["advDec"]
       

       
    
    
    def fetchAdvAndDecData(self,):
         
             status=self.makeRequestAdv()
         
             currentTime=datetime.now()
             if status==1:
                 self.maxTries=20
                 print("successfully fetched advance decline data")
                 self.currentTime=datetime.now().strftime("%H:%M")

                 #preparing data as per requirements so that it can be inserted well
                 advDataDict=self.response['rows'][0]   # returns a list with one object of {adv dec total and unchanged} value so fetching zero next to get dictonary
                 #calculate the adv and decline ratio and add to result
                 advDataDict.update({'advDecRatio':round(advDataDict["advances"]/advDataDict["declines"],2)}) 
                #  advDataDict.update({'marketStatus'})
                 advDataDict.update({'niftyPrice':round(self.niftyResponse['marketState'][0]['last'],2)})
                 
                 #for all value for the day other than first
                 self.finalAdvDataDict={}
                 self.finalAdvDataDict["data"]=advDataDict



                 #insert into collection
                 self.insertIntoAdvDecDb()



             else:
                  self.maxTries-=1
                  print("Maxtries of adv to decline {}".format(self.maxTries))
                  if self.maxTries==0:
                     self.maxTries=20 
                     try:
                          print("all max tries over try changeing cookie")
                          req.post(url=self.api,headers=self.headers,data={"message":"cookie expired, please reset cookie and start script again"},timeout=2)
                          
                          return
                     except:
                          return
                  else:
                      sleep(1)
                      self.fetchAdvAndDecData()


       

    def insertIntoAdvDecDb(self,):
        global todayDate
        dataToinsert = self.finalAdvDataDict
        
        #check if exits then insert else update data
        self.advDecDB.insert_one({'date':todayDate,'time':self.currentTime,'records':dataToinsert})


    def makeRequestAdv(self,):
        try:
             self.response = req.get(url=self.url, timeout=2, headers=self.headers).json()
             req.session().cookies.set('bm_sv',
                              'C8CADBDE740FFFDC6F3009E3F582807F~28wDCWC6c+qrlKfUe95NwbKApbHTk84g2Uee0oDrrZr/Qh2AmaUAGhB1TDqD+cJNgvELlaDBg/x2ve90BUGh5K/VVZ1U8mbPAtgBJF2FkOGvV8GnIY1JvbseMAmxCaNnkpjPgqbtQr/r7kZBoYVAJKBeWdG6nWjcbturYqV5PPA')
       
             self.niftyResponse=req.get(url="https://www.nseindia.com/api/marketStatus", timeout=2, headers=self.headers).json()['marketState'][0]
             if self.response:
                 return 1
             else:
                 return 0 
        except:
            return 0             
   
                







class optionChain():
    
    global expiryDates
    maxTries=20
    
    # this constructors does configuration with database
    def __init__(self,):

       #HEADERS AND COOKIES CONFIGURATION
       self.headers={"Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7","Accept-Encoding": "gzip, deflate, br", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"}
       self.url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
       req.session().cookies.set('bm_sv',
                              '3FEC8A4BCF42B8F27EFD1B17E19B71E0~m7+E+lFLzkXwN9i5cPsuUlfkbN5YY8ihdhPWXGoMLlkZZcEOb90pT4I2JqUvBR4+PHYX+UNJbjqiiXvEUp4umgkax35p49EwtAUbQBQurQdaQwwJXZRLkiAH0hohuNcueIz//dhIWLRBj0O1FlO35z59IYMf1DI12XyZa2Eaeb4')
       

       #DATABASE CONFIGURATION
       client=pymongo.MongoClient("mongodb://localhost:27017/")
       self.database=client["trading"]
       self.optionChain=self.database["optionChain"]



    def reqExperies(self,AllExperyDates):

      global tempNextMonth,tempCurrentMonth,tempNextSecondMonth,tempNextSecondMonth,tempExtraMonth,requiredExperiesList
      #holds status whether month last expery has finished and still month days are there or no 
      statusExpery=0
      requiredExperiesList=[]
      #checks  whether month last expery has finished and still month days are there or no 
      todayMon=datetime.today().month
      expMon=datetime.strptime(AllExperyDates[0],'%d-%b-%Y').month 
      if expMon>todayMon:
        statusExpery=1
     
    
    
      d2 = datetime.today()
    
      for dateString in AllExperyDates:

         d1 = datetime.strptime(dateString,'%d-%b-%Y')
         
     
     
         # find current week expery
         if d1.isocalendar()[1] == d2.isocalendar()[1]  and d1.year == d2.year:
             
             requiredExperiesList.append(dateString)
         
                  
         
         
         #find next week expery    
         elif d1.isocalendar()[1] == d2.isocalendar()[1]+1  and d1.year == d2.year:
            
             requiredExperiesList.append(dateString)
         
         #find current month expery if applicable not applicable if last week of month or last second week of month
         elif d1.month == d2.month  and d1.year == d2.year:
             tempCurrentMonth.append(dateString)
                     
     
     
     
         #find next month expery    
         elif d1.month == d2.month+1  and d1.year == d2.year:
             tempNextMonth.append(dateString)         

     
     
     
         #find next second month expery    
         elif d1.month == d2.month+2  and d1.year == d2.year:
             tempNextSecondMonth.append(dateString)         
 
     
     
     
         # find next third month expery
         elif d1.month == d2.month+3  and d1.year == d2.year:
             tempNextThirdMonth.append(dateString)
            #  print(tempNextThirdMonth)         
             

     
             
         #dont do anything
         else:
             pass


      #***********************************************************************
      #normal behaviour
      if tempCurrentMonth and statusExpery==0:
          requiredExperiesList.append(max(tempCurrentMonth))    
      #extraMonth behaviour condition
      if statusExpery==1:
          requiredExperiesList.append(max(tempNextMonth))
      #***********************************************************************


      #***********************************************************************
      #normal behaviour
      if tempNextMonth and statusExpery==0:     
           requiredExperiesList.append(max(tempNextMonth))
      #extraMonth behaviour condition
      if tempNextSecondMonth and statusExpery==1:
           requiredExperiesList.append(max(tempNextSecondMonth))
      #*********************************************************************** 


      #*************************************************************************
      #normal behaviour
      if tempNextSecondMonth and statusExpery==0:
           requiredExperiesList.append(max(tempNextSecondMonth))
      #extraMonth behaviour condition
      if tempNextThirdMonth and statusExpery==1:     
           requiredExperiesList.append(max(tempNextThirdMonth))
      #**************************************************************************  


      #**************************************************************************
      #normal behaviour
      if tempNextThirdMonth and statusExpery==0:     
           requiredExperiesList.append(max(tempNextThirdMonth))
      #extraMonth behaviour condition
      #next third month data is not available due to unorder months data coming for nse website
      
      #**************************************************************************         

      return requiredExperiesList


   
       
    

    def fetchOptionChainData(self,):
       global api,headers
       status=self.makeRequestOpt()
         
       try:
          
           
          if status == 1:



             self.allRequiredExperies=[] 
             self.maxTries=20
             expiryDates,data,currentExperyData=self.response['records']['expiryDates'],self.response['records']['data'],self.response['filtered']
             
             self.strikePricesList=self.response['records']['strikePrices']
             niftyPrice=self.response['records']['underlyingValue']

             for strikePrices in self.strikePricesList:
                    # print(strikePrices,niftyPrice)
                    if(math.isclose(niftyPrice,strikePrices,abs_tol=50)):
                    
                        self.premiumDecay=True
                        self.matchedStrikePrice=strikePrices
                        print(niftyPrice,strikePrices)
                        print("recording premium decay")
                        break
                    else:
                        print("else")
                        self.premiumDecay=False
                        self.matchedStrikePrice="noMatch"

            
             self.currentTime=datetime.now().strftime("%H:%M")
             

             self.allRequiredExperies=self.reqExperies(expiryDates)  # returns a list of all required experies
        
             print("successfully fetched option chain data")
             self.dataObj={}
             values={}
             valuesList=[]
             recordObj={}
             recordList=[]
             
             for expiry in self.allRequiredExperies: 
               
                #print(expiry) 
                recordObj["expiry"]=expiry
                recordObj["niftyPrice"]=niftyPrice 
                for info in data:
                    
                    if info['expiryDate']==expiry: 
                        values={} 
                        values['strikePrice']=info["strikePrice"]                      
                            
                        
                     
                        # for obj in info:
                         #remove not required things from ce
                        if "CE" in info:
                             
                             tempCE=info["CE"]
                             ceOIValue=tempCE['openInterest']
                             tempCE.pop('expiryDate',None)
                             tempCE.pop('identifier',None)
                             tempCE.pop('underlying',None)
                             tempCE.pop('underlyingValue',None)
                             tempCE.pop('totalBuyQuantity',None)
                             tempCE.pop('totalSellQuantity',None)
                             tempCE.pop('bidQty',None)
                             tempCE.pop('bidprice',None)
                             tempCE.pop('askQty',None)
                             tempCE.pop('askPrice',None)
                             tempCE['change']=round(tempCE['change'],2)
                             tempCE['changeinOpenInterest']=round(tempCE['changeinOpenInterest'],2)
                             tempCE['impliedVolatility']=round(tempCE['impliedVolatility'],2)
                             tempCE['lastPrice']=round(tempCE['lastPrice'],2)
                             tempCE['openInterest']=round(tempCE['openInterest'],2)
                             tempCE['pChange']=round(tempCE['pChange'],2)
                             tempCE['pchangeinOpenInterest']=round(tempCE['pchangeinOpenInterest'],2)
                             tempCE['totalTradedVolume']=round(tempCE['totalTradedVolume'],2)
                    
                             values["CE"]=tempCE

                        else:
                             tempPE='None'          


                        if "PE" in info:
                             #remove not required things from pe
                            
                             tempPE=info["PE"]
                             peOIValue=tempPE["openInterest"]
                             tempPE.pop('expiryDate',None)
                             tempPE.pop('identifier',None)
                             tempPE.pop('underlying',None)
                             tempPE.pop('underlyingValue',None)
                             tempPE.pop('totalBuyQuantity',None)
                             tempPE.pop('totalSellQuantity',None)
                             tempPE.pop('bidQty',None)
                             tempPE.pop('bidprice',None)
                             tempPE.pop('askQty',None)
                             tempPE.pop('askPrice',None)
                             tempPE['change']=round(tempPE['change'],2)
                             tempPE['changeinOpenInterest']=round(tempPE['changeinOpenInterest'],2)
                             tempPE['impliedVolatility']=round(tempPE['impliedVolatility'],2)
                             tempPE['lastPrice']=round(tempPE['lastPrice'],2)
                             tempPE['openInterest']=round(tempPE['openInterest'],2)
                             tempPE['pChange']=round(tempPE['pChange'],2)
                             tempPE['pchangeinOpenInterest']=round(tempPE['pchangeinOpenInterest'],2)
                             tempPE['totalTradedVolume']=round(tempPE['totalTradedVolume'],2)

                             values["PE"]=tempPE 
                             
                        else:
                             tempPE='None' 
                        
                        
                        values["avgOI"]=round(peOIValue+ceOIValue,2)
                        peOIValue=0.0
                        ceOIValue=0.0
                        valuesList.append(values)
                        tempCE={}
                        tempPE={}         
                        
                recordObj["values"]=valuesList 
             
                    
                recordList.append(recordObj)               
                valuesList=[] 
                recordObj={}
               
             self.dataObj['records']=recordList 

             
             
             #for current  expery 
             self.todayExperyDict={}
             self.todayExperyDict["CE"]=currentExperyData["CE"]
             self.todayExperyDict["PE"]=currentExperyData["PE"]
             self.todayExperyDict["niftyPrice"]=niftyPrice
             self.todayExperyDict['time']=self.currentTime
             currentExperyDataList=[]
             currentExperyDataObj={}
             data=currentExperyData["data"]



            #  print(type(currentExperyData))
             for dataObj in data:
                 currentExperyDataObj['expiryDate']=dataObj['expiryDate']
                 currentExperyDataObj['strikePrice']=dataObj['strikePrice']
              
                 if "CE" in dataObj:
                             tempCE={}
                             tempCE=dataObj["CE"]
                             ceOIValue=tempCE['openInterest']
                             tempCE.pop('expiryDate',None)
                             tempCE.pop('identifier',None)
                             tempCE.pop('underlying',None)
                             tempCE.pop('underlyingValue',None)
                             tempCE.pop('totalBuyQuantity',None)
                             tempCE.pop('totalSellQuantity',None)
                             tempCE.pop('bidQty',None)
                             tempCE.pop('bidprice',None)
                             tempCE.pop('askQty',None)
                             tempCE.pop('askPrice',None)
                             tempCE['change']=round(tempCE['change'],2)
                             tempCE['changeinOpenInterest']=round(tempCE['changeinOpenInterest'],2)
                             tempCE['impliedVolatility']=round(tempCE['impliedVolatility'],2)
                             tempCE['lastPrice']=round(tempCE['lastPrice'],2)
                             tempCE['openInterest']=round(tempCE['openInterest'],2)
                             tempCE['pChange']=round(tempCE['pChange'],2)
                             tempCE['pchangeinOpenInterest']=round(tempCE['pchangeinOpenInterest'],2)
                             tempCE['totalTradedVolume']=round(tempCE['totalTradedVolume'],2)
                             currentExperyDataObj['CE']=tempCE
                 else:
                             tempCE='None'   

                 if "PE" in dataObj:
                             #remove not required things from pe
                             tempPE={}
                             tempPE=dataObj["PE"]
                             peOIValue=tempPE["openInterest"]
                             tempPE.pop('expiryDate',None)
                             tempPE.pop('identifier',None)
                             tempPE.pop('underlying',None)
                             tempPE.pop('underlyingValue',None)
                             tempPE.pop('totalBuyQuantity',None)
                             tempPE.pop('totalSellQuantity',None)
                             tempPE.pop('bidQty',None)
                             tempPE.pop('bidprice',None)
                             tempPE.pop('askQty',None)
                             tempPE.pop('askPrice',None)
                             tempPE['change']=round(tempPE['change'],2)
                             tempPE['changeinOpenInterest']=round(tempPE['changeinOpenInterest'],2)
                             tempPE['impliedVolatility']=round(tempPE['impliedVolatility'],2)
                             tempPE['lastPrice']=round(tempPE['lastPrice'],2)
                             tempPE['openInterest']=round(tempPE['openInterest'],2)
                             tempPE['pChange']=round(tempPE['pChange'],2)
                             tempPE['pchangeinOpenInterest']=round(tempPE['pchangeinOpenInterest'],2)
                             tempPE['totalTradedVolume']=round(tempPE['totalTradedVolume'],2)
                             currentExperyDataObj['PE']=tempPE             
                             
                 else:
                             tempPE='None'             
                 
                 currentExperyDataObj["avgOI"]=round(peOIValue+ceOIValue,2)
                 peOIValue=0.0
                 ceOIValue=0.0
                 currentExperyDataList.append(currentExperyDataObj)
                 currentExperyDataObj={}


             self.todayExperyDict["data"]=currentExperyDataList
           

             self.insertIntoOptionDb()

          else:

             self.maxTries-=1
             print("Maxtries of option chain: {}".format(self.maxTries))
             if self.maxTries==0:
                try: 
                    self.maxTries=20
                    print("all max tries over try changeing cookie")
                    req.post(url=self.api,headers=self.headers,data={"message":"cookie expired, please reset cookie and start script again"})
                    
                    return
                except:
                    return 
             else:
                 sleep(0.5)
                 self.fetchOptionChainData()

       
       except Exception as e :
                 print(e)
                 sleep(0.5)
                 self.fetchOptionChainData()
             


            





    def insertIntoOptionDb(self,):
         global todayDate

         experies=self.allRequiredExperies
         dataObject=self.dataObj
         todayExperyAllData=self.todayExperyDict

         #check if exits then insert else update data
         try:

            self.optionChain.insert_one({'date':todayDate,'premiumDecay':self.premiumDecay,'matchedStrikePrice':self.matchedStrikePrice,'strikePrices':self.strikePricesList,'experies':experies,'time':self.currentTime,'data':dataObject,'filtered':todayExperyAllData})
           
         except Exception as e:
             print(e)
             print("failed to insert into database")


     

    def makeRequestOpt(self,):
        global headers,api
        try:
             self.response = req.get(url=self.url, timeout=2, headers=self.headers).json()
             if self.response:
                 return 1
             else:
                 return 0 
        except:
            return 0         


# class premiumDecay():
#     maxTries=20
    
#     # this constructors does configuration with database
#     def __init__(self,):

#        #HEADERS AND COOKIES CONFIGURATION
#        self.headers={"Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7","Accept-Encoding": "gzip, deflate, br", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"}
#        self.url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
#        req.session().cookies.set('bm_sv',
#                               '3FEC8A4BCF42B8F27EFD1B17E19B71E0~m7+E+lFLzkXwN9i5cPsuUlfkbN5YY8ihdhPWXGoMLlkZZcEOb90pT4I2JqUvBR4+PHYX+UNJbjqiiXvEUp4umgkax35p49EwtAUbQBQurQdaQwwJXZRLkiAH0hohuNcueIz//dhIWLRBj0O1FlO35z59IYMf1DI12XyZa2Eaeb4')
       

#        #DATABASE CONFIGURATION
#        client=pymongo.MongoClient("mongodb://localhost:27017/")
#        self.database=client["trading"]
#        self.premiumDecay=self.database["premiumDecay"]



#     def fetchPremiumData(self,):
#        global api,headers
#        status=self.makeRequestOpt()
         
#        try:
          
           
#           if status == 1:

#              self.maxTries=20
#              currentExperyData=self.response['filtered']
             
#              lastNiftyPrice=0

#              currentNiftyPrice=self.response['records']['underlyingValue']
#              print("checking premiumDecay")

#              if (math.isclose(currentNiftyPrice,lastNiftyPrice,5)):

#                     print("")

#                     lastNiftyPrice=currentNiftyPrice
#                     self.currentTime=datetime.now().strftime("%H:%M")
               
#                     print("successfully fetched premium data")
       
                    
#                     #for current  expery 
#                     self.todayExperyDict={}
#                     self.todayExperyDict["CE"]=currentExperyData["CE"]
#                     self.todayExperyDict["PE"]=currentExperyData["PE"]
#                     self.todayExperyDict["niftyPrice"]=currentNiftyPrice
#                     self.todayExperyDict['time']=self.currentTime
                    
                    
#                     currentExperyDataList=[]
#                     currentExperyDataObj={}
#                     data=currentExperyData["data"]
       
       
       
#                    #  print(type(currentExperyData))
#                     for dataObj in data:
#                         currentExperyDataObj['expiryDate']=dataObj['expiryDate']
#                         currentExperyDataObj['strikePrice']=dataObj['strikePrice']
                     
#                         if "CE" in dataObj:
#                                     tempCE={}
#                                     tempCE=dataObj["CE"]
#                                     tempCE.pop('expiryDate',None)
#                                     tempCE.pop('identifier',None)
#                                     tempCE.pop('underlying',None)
#                                     tempCE.pop('underlyingValue',None)
#                                     tempCE.pop('totalBuyQuantity',None)
#                                     tempCE.pop('totalSellQuantity',None)
#                                     tempCE.pop('bidQty',None)
#                                     tempCE.pop('bidprice',None)
#                                     tempCE.pop('askQty',None)
#                                     tempCE.pop('askPrice',None)
#                                     tempCE.pop('change',None)
#                                     tempCE.pop('changeinOpenInterest',None)
#                                     tempCE['impliedVolatility']=round(tempCE['impliedVolatility'],2)
#                                     tempCE.pop('lastPrice',None)
#                                     tempCE['openInterest']=round(tempCE['openInterest'],2)
#                                     tempCE.pop('pChange',None)
#                                     tempCE.pop('pchangeinOpenInterest',None)
#                                     tempCE['totalTradedVolume']=round(tempCE['totalTradedVolume'],2)
#                                     currentExperyDataObj['CE']=tempCE
#                         else:
#                                     tempCE='None'   
       
#                         if "PE" in dataObj:
#                                     #remove not required things from pe
#                                     tempPE={}
#                                     tempPE=dataObj["PE"]
#                                     tempPE.pop('expiryDate',None)
#                                     tempPE.pop('identifier',None)
#                                     tempPE.pop('underlying',None)
#                                     tempPE.pop('underlyingValue',None)
#                                     tempPE.pop('totalBuyQuantity',None)
#                                     tempPE.pop('totalSellQuantity',None)
#                                     tempPE.pop('bidQty',None)
#                                     tempPE.pop('bidprice',None)
#                                     tempPE.pop('askQty',None)
#                                     tempPE.pop('askPrice',None)
#                                     tempPE.pop('change',None)
#                                     tempPE.pop('changeinOpenInterest',None)
#                                     tempPE['impliedVolatility']=round(tempPE['impliedVolatility'],2)
#                                     tempPE.pop('lastPrice',None)
#                                     tempPE['openInterest']=round(tempPE['openInterest'],2)
#                                     tempPE.pop('pChange',None)
#                                     tempPE.pop('pchangeinOpenInterest',None)
#                                     tempPE['totalTradedVolume']=round(tempPE['totalTradedVolume'],2)
#                                     currentExperyDataObj['PE']=tempPE             
                                    
#                         else:
#                                     tempPE='None'             
                        
#                         currentExperyDataList.append(currentExperyDataObj)
#                         currentExperyDataObj={}
       
       
#                     self.todayExperyDict["data"]=currentExperyDataList
                  
       
#                     self.insertIntoOptionDb()
       
#           else:
       
#                     self.maxTries-=1
#                     print("Maxtries of option chain: {}".format(self.maxTries))
#                     if self.maxTries==0:
#                        try: 
#                            self.maxTries=20
#                            print("all max tries over try changeing cookie")
#                            req.post(url=self.api,headers=self.headers,data={"message":"cookie expired, please reset cookie and start script again"})
                           
#                            return
#                        except:
#                            return 
#                     else:
#                         sleep(0.5)
#                         self.fetchPremiumData()   
       
              
#        except Exception as e:
#                         sleep(0.5)
#                         self.fetchPremiumData()   




#     def makeRequestOpt(self,):
#         global headers,api
#         try:
#              self.response = req.get(url=self.url, timeout=2, headers=self.headers).json()
#              if self.response:
#                  return 1
#              else:
#                  return 0 
#         except:
#             return 0         


       
#     def insertIntoOptionDb(self,):
#          global todayDate
#          todayExperyAllData=self.todayExperyDict

#          #check if exits then insert else update data
#          try:

#             self.premiumDecay.insert_one({'date':todayDate,'time':self.currentTime,'filtered':todayExperyAllData})
           
#          except Exception as e:
#              print(e)
#              print("failed to insert into database")
 



       


#########################################################################################################################################
#                         MAIN PROGRAM STARTS AND THREADS ARE CREATED FOR ALL CLASSSES 
#########################################################################################################################################

def startAdvDec():
    
# #     #*************************objects for advnaces decline class*****************************
    AaDObj=advAndDec()
    while True:
       AaDObj.fetchAdvAndDecData()
       sleep(180)




def startOptionChain():
    
#    #*************************objects for option chain class*****************************
   ocObj=optionChain()
   while True :
      ocObj.fetchOptionChainData()
      sleep(180)



# def startPremiumDecay():      

#    pdObj=premiumDecay()
#    while True :
#       pdObj.fetchPremiumData()
#       sleep(180)


advDecThread = threading.Thread(target=startAdvDec)
optionChainThread = threading.Thread(target=startOptionChain)
# premiumDecayThread = threading.Thread(target=startPremiumDecay)

advDecThread.start()
optionChainThread.start()
# premiumDecayThread.start()














#*************************************************************************************************************************************
#                             TESING FUNCTION PLEASE DONT UNCOMMENT THIS FUNCTION
#**************************************************************************************************************************************
# count=0
# def loadData():
#     global count
#     headers={"Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7","Accept-Encoding": "gzip, deflate, br", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"}
#     url2="https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
#     req.session().cookies.set('bm_sv','A88ED6FF61D42AF0CC726000AA5F1EAD~HSJV4b9qeac8l+6xGqebdUu2BXOlMI5toiCbh/deSLQadS7QiYFBh3dqszZTLvQK+GDze1UNRj9U/bQzIkiK4qLzSw6NDSJarCkQKpcZksHIOmNyJMDNYck/S+ryZbIZbF9XYdjxk+xxhd18w1bdXoABf6WPO9cg9Nh71iVlWls')
#     try:
#       res = req.get(url=url2, timeout=4, headers=headers)       
#       print(res.status_code)
#       response=res.json() 
#       with open('nse'+str(count)+'.json','a') as nse:
#               nse.write(json.dumps(json.dump(response,nse),sort_keys=True, indent=4))
#               nse.close()
#       with open('nse'+str(count)+'.json', 'rb+') as f:
#             f.seek(0,2)                 # end of file
#             size=f.tell()               # the size...
#             f.truncate(size-4) 
#       count+=1      
#     except Exception as e:
#         print(e)

# while 1:
#   loadData()
#   sleep(180)  
#*****************************************************************************************************************************************
#*****************************************************************************************************************************************













#***************************************************************************************************************************************
#                              OPTION CHAIN DATA STORED IN optionChain COLLECTION STRUCTURE
#***************************************************************************************************************************************
# {
# 	"_id" : ObjectId("5e84a409f458c363ad3bad5f"),
# 	"date" : "2020-04-01",
#	"time" : "19:54",
# 	"data" : 
# 		{
# 			
# 			"records" : [
# 				{
# 					"expiry" : "01-Apr-2020",
# 					"niftyPrice" : 8253.8,
# 					"values" : [
# 						{
# 							"CE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 0,
# 								"changeinOpenInterest" : 0,
# 								"pchangeinOpenInterest" : 0,
# 								"totalTradedVolume" : 0,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0,
# 								"change" : 0,
# 								"pChange" : -100
# 							},
# 							"PE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 335,
# 								"changeinOpenInterest" : 6,
# 								"pchangeinOpenInterest" : 1.8237082066869301,
# 								"totalTradedVolume" : 284,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0.05,
# 								"change" : -0.7999999999999999,
# 								"pChange" : -94.11764705882352
# 							}
# 						},
# 						{
# 							"CE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 0,
# 								"changeinOpenInterest" : 0,
# 								"pchangeinOpenInterest" : 0,
# 								"totalTradedVolume" : 0,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0,
# 								"change" : 0,
# 								"pChange" : -100
# 							},
# 							"PE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 335,
# 								"changeinOpenInterest" : 6,
# 								"pchangeinOpenInterest" : 1.8237082066869301,
# 								"totalTradedVolume" : 284,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0.05,
# 								"change" : -0.7999999999999999,
# 								"pChange" : -94.11764705882352
# 							}
# 						},
# 						{
# 							"CE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 0,
# 								"changeinOpenInterest" : 0,
# 								"pchangeinOpenInterest" : 0,
# 								"totalTradedVolume" : 0,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0,
# 								"change" : 0,
# 								"pChange" : -100
# 							},
# 							"PE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 335,
# 								"changeinOpenInterest" : 6,
# 								"pchangeinOpenInterest" : 1.8237082066869301,
# 								"totalTradedVolume" : 284,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0.05,
# 								"change" : -0.7999999999999999,
# 								"pChange" : -94.11764705882352
# 							}
# 						},
# 						{
# 							"CE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 0,
# 								"changeinOpenInterest" : 0,
# 								"pchangeinOpenInterest" : 0,
# 								"totalTradedVolume" : 0,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0,
# 								"change" : 0,
# 								"pChange" : -100
# 							},
# 							"PE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 335,
# 								"changeinOpenInterest" : 6,
# 								"pchangeinOpenInterest" : 1.8237082066869301,
# 								"totalTradedVolume" : 284,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0.05,
# 								"change" : -0.7999999999999999,
# 								"pChange" : -94.11764705882352
# 							}
# 						},
# 						{
# 							"CE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 0,
# 								"changeinOpenInterest" : 0,
# 								"pchangeinOpenInterest" : 0,
# 								"totalTradedVolume" : 0,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0,
# 								"change" : 0,
# 								"pChange" : -100
# 							},
# 							"PE" : {
# 								"strikePrice" : 6300,
# 								"openInterest" : 335,
# 								"changeinOpenInterest" : 6,
# 								"pchangeinOpenInterest" : 1.8237082066869301,
# 								"totalTradedVolume" : 284,
# 								"impliedVolatility" : 0,
# 								"lastPrice" : 0.05,
# 								"change" : -0.7999999999999999,
# 								"pChange" : -94.11764705882352
# 							}
# 						}
# 					]
# 				},
# 				
# 			
# 		}
# 	],
# 
# 	
# }

#***************************************************************************************************************************************
#***************************************************************************************************************************************



#*******************************************************************************************************************************
#  AN EXAMPLE OF OF THE FORMAT OF JSON DATA FOR FURTHER REFERENCES (BELOW OBJECT IS FOR 1 DAY, NEW OBJECT EVERYDAY )
#*******************************************************************************************************************************
#
#  {
# 	"_id" : ObjectId("5e858e187503fcaa7f566e56"),
# 	"date" : "2020-04-02",
# 	"time" : "12:32",
# 	"records" : {
# 		"data" : {
# 			"advances" : 935,
# 			"declines" : 863,
# 			"unchanged" : 95,
# 			"total" : 1893,
# 			"advDecRatio" : 1.0834298957126303
# 		}
# 	}
# }

#*****************************************************************************************************************************************
#*****************************************************************************************************************************************
        
