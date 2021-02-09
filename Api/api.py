from flask import Flask,jsonify,request
from flask_cors import CORS
from datetime import datetime
import pymongo
from bson import json_util
from time import sleep
import pprint
from heapq import nsmallest



client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['trading']


advDecCollection=db['advDec']
optionsCollection=db['optionChain']


app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'

CORS(app)

@app.route('/notification')
def index():
    return jsonify({"message":"success"})



  



@app.route('/strikePrice', methods=['POST'])
def optionsGraphsStrikePrice():
     date=request.get_json()['date']
     expiry=request.get_json()['expiry']
     result={}
     filteredStrikes=[]
     topFourMaxOi=[]
     if expiry=="currentExpiry":
        try:
            tempResult=optionsCollection.find({'date':date},{'filtered.data':1}).sort([('_id',-1)]).limit(1)
            resultList=[]
            for data in tempResult:
                  resultList=data['filtered']['data']
                  break
            # print(resultList)   
            for datas in resultList:  
               filteredStrikes.append(datas['strikePrice'])
             
               
            result['strikePrices']=filteredStrikes
            
            
            maxOiResult=optionsCollection.aggregate([
                    {"$match":{"date":date}},
                    {"$project":{"filtered.data":1,"filtered.time":1,"date":1}},
                    {"$unwind":"$filtered.data"},
                    {"$group": {"_id": {"avgOI":"$filtered.data.avgOI","strikePrice":"$filtered.data.strikePrice"}}}, 
                    {"$sort":{'_id.avgOI':-1}},
                  
                    ])


            strikePrice=0  
            count=1          
            for mOI in maxOiResult:
               # strikePrice=mOI['_id']['strikePrice']
               if(mOI['_id']['strikePrice']==strikePrice):
                  pass
               else: 
                  if(count>4):
                     break
                  else:
                    count+=1 
                    topFourMaxOi.append(mOI["_id"])
                    strikePrice=mOI['_id']['strikePrice']
                  

            result["maxOI"]=topFourMaxOi
            return json_util.dumps(result)    

        except Exception as e:
            print(e)
            return jsonify({"message":"failed"})
     
     
     else:

         tempDate=datetime.strptime(expiry,'%d-%b-%Y')
         expiry=tempDate.strftime('%d-%b-%Y')
         try:
           strikes=optionsCollection.find({'date':date,'data.records.expiry':expiry},{'strikePrices':1}).sort([('_id',-1)]).limit(1)  
           
           result["strikePrices"]=strikes


           maxOiResult=optionsCollection.aggregate(
              [
                 {"$match":{"date":date}},
                 #filter unwanted data
                 {"$project":{"data.records":1,"time":1}},
                 
                 {"$unwind":"$data.records"},
                 
                 {"$match":{"data.records.expiry":expiry}},
                 
                 {"$project":{"data.records.values":1,"time":1}},
                 
                 {"$unwind":"$data.records.values"},
                 {"$group": {"_id": {"avgOI":"$data.records.values.avgOI","strikePrice":"$data.records.values.strikePrice"}}}, 
                {"$sort":{'_id.avgOI':-1}},
               #  {"$limit":4}
             ]
            )


           
           strikePrice=0  
           count=1          
           for mOI in maxOiResult:
              if(mOI['_id']['strikePrice']==strikePrice):
                 pass
              else: 
                 if(count>4):
                    break
                 else:
                   count+=1 
                   topFourMaxOi.append(mOI["_id"])
                   strikePrice=mOI['_id']['strikePrice']

           result["maxOI"]=topFourMaxOi



           return json_util.dumps(result)
         except Exception as e:
           print(e)
           return jsonify({"message":"failed"})
      
   
#returns a list of times when given a specific date
@app.route('/getDropdownValues', methods=['POST'])
def getTimeAndStrikes():
  date=request.get_json()['date']
  typeData=request.get_json()['type']
#   tempDate=datetime.strptime(dateData,'%Y-%m-%d')
#   date=tempDate.strftime('%d-%b-%Y')
  dataToSend={}
  timeList=[]
  experies=[]
  try:
    result=optionsCollection.find({'date':date})
    
    for index,data in enumerate(result):
      #  print(index)
      #  print(data)
       if index==1:
          experies=data['experies']
          experies.append("currentExpiry")
          
       timeList.append(data['time'])
    if typeData=="options":
         dataToSend["times"]=timeList 
         dataToSend["experies"]=experies
    else:
        
         dataToSend['experies']=experies

   
    print(dataToSend)  
    return dataToSend
    

  except Exception as e:
     print(e)
     return jsonify({"message":"failed"})



#return strike prices for graphs     

@app.route('/optionsDashBoard', methods=['POST'])
def optionsDashBoard():
  date=request.get_json()['date']
  time=request.get_json()['time']
  tempexpiry=request.get_json()['expiry']
  print(date,time,tempexpiry)
  shortTable={}
  if tempexpiry=="currentExpiry":
    try: 
     result=optionsCollection.find({"date":date,"time":time},{"filtered":1})
     niftyPrice=0.0
     tempValues=[]
     tempData={}
     if result:
       
       for data in result:
         
         #  print("data")
          tempData=data
          
          
          niftyPrice=data['filtered']['niftyPrice']
          tempValues=data['filtered']['data']
         #  return json_util.dumps(data)
           
     
       shortTable=nsmallest(31,tempValues,key=lambda x: abs(x['strikePrice']-niftyPrice))

       sortedTable=sorted(shortTable,key=lambda x: x['strikePrice'])
       
      #  return json_util.dumps(data['data']['records']['values'])
       tempData['filtered']["data"]=sortedTable     
       return json_util.dumps(tempData)
       
     else:

        return jsonify({"message":"no else data"})  
    except Exception as e:

       return jsonify({"message":"no data"})  
 
  
  
  else:
     try:
       result=optionsCollection.aggregate([
            {"$match":{"date":date,"time":time}},
            {"$project":{"data.records":1,"time":1}},
            {"$unwind":"$data.records"},
            {"$match":{"data.records.expiry":tempexpiry}}
            # {"$sort":{"data.records.values.strikePrice":-1}}
   ])
       niftyPrice=0.0
       tempValues=[]
       tempData={}
       if result:
         for data in result:
            tempData=data
            niftyPrice=data['data']['records']['niftyPrice']
            tempValues=data['data']['records']['values']
       
         shortTable=nsmallest(31,tempValues,key=lambda x: abs(x['strikePrice']-niftyPrice))
  
         sortedTable=sorted(shortTable,key=lambda x: x['strikePrice'])
         
        #  return json_util.dumps(data['data']['records']['values'])
         tempData["data"]["records"]["values"]=sortedTable     
         return json_util.dumps(tempData)
         
       else:

          return jsonify({"message":"no data"})  
     
     except Exception as e:
         return jsonify({"message":"no data"})  









#returns a list of experies when given a specific date
@app.route('/dataForSelectedDateTimeExpiry', methods=['POST'])
def sendDataForSelectedDateTime():
  date=request.get_json()['date']
  time=request.get_json()['time']
  tempexpiry=request.get_json()['expiry']
  print(date,time,tempexpiry)

  
  if tempexpiry=="currentExpiry":


     try:
       result=optionsCollection.find({"date":date,"time":time},{"filtered":1})
       if result:
         for data in result: 
            return json_util.dumps(data)
       else: 
            return jsonify({"message":"no data "})
       
       
   
     except Exception as e:
        print(e)
        return jsonify({"message":"failed"})


  else:
     #dateObj=datetime.strptime(tempexpiry,'%Y-%m-%d')
     #expiry=dateObj.strftime('%d-%b-%Y')
     print("else block")
     try:
       result=optionsCollection.aggregate([
            {"$match":{"date":date,"time":time}},
            {"$project":{"data.records":1,"time":1}},
            {"$unwind":"$data.records"},
             {"$match":{"data.records.expiry":tempexpiry}}
   ])
       if result:
         for data in result:
            return json_util.dumps(data)
       else:
            return jsonify({"message":"no data "})
     except Exception as e:
        print("error in try")
        print(e)
        return jsonify({"message":"failed"})




@app.route('/graphWithExpiryPutsStrikeDate', methods=['POST'])
def graphWithPutsExpiryStrikeDate():
   putsOIForStrikePrice=[]
   callsOIForStrikePrice=[]
   putsIVForStrikePrice=[]
   callsIVForStrikePrice=[]
   putsCOIForStrikePrice=[]
   callsCOIForStrikePrice=[]
   xAxisData=[]
   ratioXAxis=[]
   ratioYAxisNifty=[]
   ratioYAxisAdvDecRatio=[]
   advValues=[]
   decValues=[]
   advDecDataObj={}
   advRatioDataObj={}
   finalResult={}

   date=request.get_json()['date']
   tempExpiry=request.get_json()['expiry']
   strike=request.get_json()['strikePrice']

   print(strike)
   print(tempExpiry)
   print(date)




   if tempExpiry=="currentExpiry":

      try:
         
         advDecResult=advDecCollection.find({'date':date})
         result=optionsCollection.aggregate([
             {"$match":{"date":date}},
             {"$project":{"filtered.data":1,"filtered.time":1}},
             {"$unwind":"$filtered.data"},
             {"$match":{"filtered.data.strikePrice":int(strike)}},
             {"$project":{"filtered.time":1,"filtered.data.avgOI":1,"filtered.data.CE.openInterest":1,"filtered.data.PE.openInterest":1,"filtered.data.CE.impliedVolatility":1,"filtered.data.PE.impliedVolatility":1,"filtered.data.CE.changeinOpenInterest":1,"filtered.data.PE.changeinOpenInterest":1}},
             
          ])
         
         for data in result:
                print(data)
               
                xAxisData.append(data['filtered']['time'])
                callsOIForStrikePrice.append(data['filtered']['data']['CE']['openInterest'])
                putsOIForStrikePrice.append(data['filtered']['data']['PE']['openInterest'])
       
                callsCOIForStrikePrice.append(data['filtered']['data']['CE']['changeinOpenInterest'])
                putsCOIForStrikePrice.append(data['filtered']['data']['PE']['changeinOpenInterest'])
       
                callsIVForStrikePrice.append(data['filtered']['data']['CE']['impliedVolatility'])
                putsIVForStrikePrice.append(data['filtered']['data']['PE']['impliedVolatility'])
       
                
         finalResult["OI"]={"puts":putsOIForStrikePrice,"calls":callsOIForStrikePrice,"xAxis":xAxisData}
         finalResult['IV']={"puts":putsIVForStrikePrice,"calls":callsIVForStrikePrice,"xAxis":xAxisData}
         finalResult['COI']={"puts":putsCOIForStrikePrice,"calls":callsCOIForStrikePrice,"xAxis":xAxisData}


         for advDec in advDecResult:
             ratioXAxis.append(advDec['time']) 
             ratioYAxisNifty.append(advDec['records']['data']['niftyPrice'])
             ratioYAxisAdvDecRatio.append(advDec['records']['data']['advDecRatio'])
             advValues.append(advDec['records']['data']['advances'])
             decValues.append(advDec['records']['data']['declines'])

         #ratio graph
         advRatioDataObj["xAsis"]=ratioXAxis
         advRatioDataObj["yAsisNifty"]=ratioYAxisNifty
         advRatioDataObj["yAsisAdvDecRatio"]=ratioYAxisAdvDecRatio
         #adv dec graph
         advDecDataObj["xAsis"]=ratioXAxis
         advDecDataObj["yAsisAdvances"]=advValues
         advDecDataObj["yAsisDeclines"]=decValues          
        
         finalResult["ratio"]=advRatioDataObj
         finalResult["advDec"]=advDecDataObj

         maxOiResult=optionsCollection.aggregate([
                    {"$match":{"date":date}},
                    {"$project":{"filtered.data":1,"filtered.time":1,"date":1}},
                    {"$unwind":"$filtered.data"},
                    {"$group": {"_id": {"avgOI":"$filtered.data.avgOI","strikePrice":"$filtered.data.strikePrice"}}}, 
                    {"$sort":{'_id.avgOI':-1}},
                  
                    ])


         strikePrice=0 
         topFourMaxOi=[] 
         count=1          
         for mOI in maxOiResult:
              # strikePrice=mOI['_id']['strikePrice']
              if(mOI['_id']['strikePrice']==strikePrice):
                 pass
              else: 
                 if(count>4):
                    break
                 else:
                   count+=1 
                   topFourMaxOi.append(mOI["_id"])
                   strikePrice=mOI['_id']['strikePrice']
                 

         finalResult["maxOI"]=topFourMaxOi

          
       
         return finalResult
      except Exception as e:
          print(e)
          return jsonify({"message":"failed"})
   
   
   
   else:
      
      
      tempDate=datetime.strptime(tempExpiry,'%d-%b-%Y')
      expiry=tempDate.strftime('%d-%b-%Y')
     
      

      try:
          advDecResult=advDecCollection.find({'date':date})
          result=optionsCollection.aggregate([
                 #filter data wise
                 {"$match":{"date":date}},
                 #filter unwanted data
                 {"$project":{"data.records":1,"time":1}},
                 
                 {"$unwind":"$data.records"},
                 
                 {"$match":{"data.records.expiry":expiry}},
                 
                 {"$project":{"data.records.values":1,"time":1}},
                 
                 {"$unwind":"$data.records.values"},
                 
                 {"$match":{"data.records.values.strikePrice":int(strike)}},
                 
                 {"$project":{"time":1,"data.records.values.avgOI":1,"data.records.values.CE.openInterest":1,"data.records.values.PE.openInterest":1,"data.records.values.CE.impliedVolatility":1,"data.records.values.PE.impliedVolatility":1,"data.records.values.CE.changeinOpenInterest":1,"data.records.values.PE.changeinOpenInterest":1}},
    
                  ])
          print("looping over options data")
          for data in result:

            #  print(pprint.pprint(data))
             xAxisData.append(data['time'])
             callsOIForStrikePrice.append(data['data']['records']['values']['CE']['openInterest'])
             putsOIForStrikePrice.append(data['data']['records']['values']['PE']['openInterest'])
    
             callsCOIForStrikePrice.append(data['data']['records']['values']['CE']['changeinOpenInterest'])
             putsCOIForStrikePrice.append(data['data']['records']['values']['PE']['changeinOpenInterest'])
    
             callsIVForStrikePrice.append(data['data']['records']['values']['CE']['impliedVolatility'])
             putsIVForStrikePrice.append(data['data']['records']['values']['PE']['impliedVolatility'])
    
          finalResult["OI"]={"puts":putsOIForStrikePrice,"calls":callsOIForStrikePrice,"xAxis":xAxisData}
          finalResult['IV']={"puts":putsIVForStrikePrice,"calls":callsIVForStrikePrice,"xAxis":xAxisData}
          finalResult['COI']={"puts":putsCOIForStrikePrice,"calls":callsCOIForStrikePrice,"xAxis":xAxisData}

          for advDec in advDecResult:
              ratioXAxis.append(advDec['time']) 
              ratioYAxisNifty.append(advDec['records']['data']['niftyPrice'])
              ratioYAxisAdvDecRatio.append(advDec['records']['data']['advDecRatio'])
              advValues.append(advDec['records']['data']['advances'])
              decValues.append(advDec['records']['data']['declines'])
 
          #ratio graph
          advRatioDataObj["xAsis"]=ratioXAxis
          advRatioDataObj["yAsisNifty"]=ratioYAxisNifty
          advRatioDataObj["yAsisAdvDecRatio"]=ratioYAxisAdvDecRatio
          #adv dec graph
          advDecDataObj["xAsis"]=ratioXAxis
          advDecDataObj["yAsisAdvances"]=advValues
          advDecDataObj["yAsisDeclines"]=decValues          
         
          finalResult["ratio"]=advRatioDataObj
          finalResult["advDec"]=advDecDataObj


          maxOiResult=optionsCollection.aggregate(
              [
                 {"$match":{"date":date}},
                 #filter unwanted data
                 {"$project":{"data.records":1,"time":1}},
                 
                 {"$unwind":"$data.records"},
                 
                 {"$match":{"data.records.expiry":expiry}},
                 
                 {"$project":{"data.records.values":1,"time":1}},
                 
                 {"$unwind":"$data.records.values"},
                 {"$group": {"_id": {"avgOI":"$data.records.values.avgOI","strikePrice":"$data.records.values.strikePrice"}}}, 
                {"$sort":{'_id.avgOI':-1}},
               #  {"$limit":4}
             ]
            )


           
          strikePrice=0  
          count=1 
          topFourMaxOi=[]         
          for mOI in maxOiResult:
              if(mOI['_id']['strikePrice']==strikePrice):
                 pass
              else: 
                 if(count>4):
                    break
                 else:
                   count+=1 
                   topFourMaxOi.append(mOI["_id"])
                   strikePrice=mOI['_id']['strikePrice']

          finalResult["maxOI"]=topFourMaxOi
             
    
          return finalResult
      except Exception as e:
          print(e)
          return jsonify({"message":"failed"})
      
   
   




@app.route('/graphWithExpiryCallsStrikeDate', methods=['POST'])
def graphWithCallsExpiryStrikeDate():
   putsOIForStrikePrice=[]
   callsOIForStrikePrice=[]
   putsIVForStrikePrice=[]
   callsIVForStrikePrice=[]
   putsCOIForStrikePrice=[]
   callsCOIForStrikePrice=[]
   xAxisData=[]
   ratioXAxis=[]
   ratioYAxisNifty=[]
   ratioYAxisAdvDecRatio=[]
   advValues=[]
   decValues=[]
   advDecDataObj={}
   advRatioDataObj={}
   finalResult={}

   date=request.get_json()['date']
   tempExpiry=request.get_json()['expiry']
   strike=request.get_json()['strikePrice']
   print(date)
   print(tempExpiry)
   print(strike)
   
 


   if tempExpiry=="currentExpiry":
      try:
         
         advDecResult=advDecCollection.find({'date':date})
         result=optionsCollection.aggregate([
             {"$match":{"date":date}},
             {"$project":{"filtered.data":1,"filtered.time":1}},
             {"$unwind":"$filtered.data"},
             {"$match":{"filtered.data.strikePrice":int(strike)}},
             {"$project":{"filtered.time":1,"filtered.data.avgOI":1,"filtered.data.CE.openInterest":1,"filtered.data.PE.openInterest":1,"filtered.data.CE.impliedVolatility":1,"filtered.data.PE.impliedVolatility":1,"filtered.data.CE.changeinOpenInterest":1,"filtered.data.PE.changeinOpenInterest":1}},
             
          ])
         
         for data in result:
                print(data)
               
                xAxisData.append(data['filtered']['time'])
                callsOIForStrikePrice.append(data['filtered']['data']['CE']['openInterest'])
                putsOIForStrikePrice.append(data['filtered']['data']['PE']['openInterest'])
       
                callsCOIForStrikePrice.append(data['filtered']['data']['CE']['changeinOpenInterest'])
                putsCOIForStrikePrice.append(data['filtered']['data']['PE']['changeinOpenInterest'])
       
                callsIVForStrikePrice.append(data['filtered']['data']['CE']['impliedVolatility'])
                putsIVForStrikePrice.append(data['filtered']['data']['PE']['impliedVolatility'])
       
                
         finalResult["OI"]={"puts":putsOIForStrikePrice,"calls":callsOIForStrikePrice,"xAxis":xAxisData}
         finalResult['IV']={"puts":putsIVForStrikePrice,"calls":callsIVForStrikePrice,"xAxis":xAxisData}
         finalResult['COI']={"puts":putsCOIForStrikePrice,"calls":callsCOIForStrikePrice,"xAxis":xAxisData}


         for advDec in advDecResult:
             ratioXAxis.append(advDec['time']) 
             ratioYAxisNifty.append(advDec['records']['data']['niftyPrice'])
             ratioYAxisAdvDecRatio.append(advDec['records']['data']['advDecRatio'])
             advValues.append(advDec['records']['data']['advances'])
             decValues.append(advDec['records']['data']['declines'])

         #ratio graph
         advRatioDataObj["xAsis"]=ratioXAxis
         advRatioDataObj["yAsisNifty"]=ratioYAxisNifty
         advRatioDataObj["yAsisAdvDecRatio"]=ratioYAxisAdvDecRatio
         #adv dec graph
         advDecDataObj["xAsis"]=ratioXAxis
         advDecDataObj["yAsisAdvances"]=advValues
         advDecDataObj["yAsisDeclines"]=decValues          
        
         finalResult["ratio"]=advRatioDataObj
         finalResult["advDec"]=advDecDataObj

         maxOiResult=optionsCollection.aggregate([
                    {"$match":{"date":date}},
                    {"$project":{"filtered.data":1,"filtered.time":1,"date":1}},
                    {"$unwind":"$filtered.data"},
                    {"$group": {"_id": {"avgOI":"$filtered.data.avgOI","strikePrice":"$filtered.data.strikePrice"}}}, 
                    {"$sort":{'_id.avgOI':-1}},
                  
                    ])


         strikePrice=0 
         topFourMaxOi=[] 
         count=1          
         for mOI in maxOiResult:
              # strikePrice=mOI['_id']['strikePrice']
              if(mOI['_id']['strikePrice']==strikePrice):
                 pass
              else: 
                 if(count>4):
                    break
                 else:
                   count+=1 
                   topFourMaxOi.append(mOI["_id"])
                   strikePrice=mOI['_id']['strikePrice']
                 

         finalResult["maxOI"]=topFourMaxOi
          
       
         return finalResult
      except Exception as e:
          print(e)
          return jsonify({"message":"failed"})
   
   
   
   else:
      
      
      # tempDate=datetime.strptime(tempExpiry,'%d-%b-%Y')
      # expiry=tempDate.strftime('%d-%b-%Y')
     
      

      try:

          advDecResult=advDecCollection.find({'date':date})
          result=optionsCollection.aggregate([
                 #filter data wise
                 {"$match":{"date":date}},
                 #filter unwanted data
                 {"$project":{"data.records":1,"time":1}},
                 
                 {"$unwind":"$data.records"},
                 
                 {"$match":{"data.records.expiry":tempExpiry}},
                 
                 {"$project":{"data.records.values":1,"time":1}},
                 
                 {"$unwind":"$data.records.values"},
                 
                 {"$match":{"data.records.values.strikePrice":int(strike)}},
                 
                 {"$project":{"time":1,"data.records.values.avgOI":1,"data.records.values.CE.openInterest":1,"data.records.values.PE.openInterest":1,"data.records.values.CE.impliedVolatility":1,"data.records.values.PE.impliedVolatility":1,"data.records.values.CE.changeinOpenInterest":1,"data.records.values.PE.changeinOpenInterest":1}},
    
                  ])
          
          for data in result:
            #  print(pprint.pprint(data))
             xAxisData.append(data['time'])
             callsOIForStrikePrice.append(data['data']['records']['values']['CE']['openInterest'])
             putsOIForStrikePrice.append(data['data']['records']['values']['PE']['openInterest'])
    
             callsCOIForStrikePrice.append(data['data']['records']['values']['CE']['changeinOpenInterest'])
             putsCOIForStrikePrice.append(data['data']['records']['values']['PE']['changeinOpenInterest'])
    
             callsIVForStrikePrice.append(data['data']['records']['values']['CE']['impliedVolatility'])
             putsIVForStrikePrice.append(data['data']['records']['values']['PE']['impliedVolatility'])
    
          finalResult["OI"]={"puts":putsOIForStrikePrice,"calls":callsOIForStrikePrice,"xAxis":xAxisData}
          finalResult['IV']={"puts":putsIVForStrikePrice,"calls":callsIVForStrikePrice,"xAxis":xAxisData}
          finalResult['COI']={"puts":putsCOIForStrikePrice,"calls":callsCOIForStrikePrice,"xAxis":xAxisData}

          for advDec in advDecResult:
              ratioXAxis.append(advDec['time']) 
              ratioYAxisNifty.append(advDec['records']['data']['niftyPrice'])
              ratioYAxisAdvDecRatio.append(advDec['records']['data']['advDecRatio'])
              advValues.append(advDec['records']['data']['advances'])
              decValues.append(advDec['records']['data']['declines'])
 
          #ratio graph
          advRatioDataObj["xAsis"]=ratioXAxis
          advRatioDataObj["yAsisNifty"]=ratioYAxisNifty
          advRatioDataObj["yAsisAdvDecRatio"]=ratioYAxisAdvDecRatio
          #adv dec graph
          advDecDataObj["xAsis"]=ratioXAxis
          advDecDataObj["yAsisAdvances"]=advValues
          advDecDataObj["yAsisDeclines"]=decValues          
         
          finalResult["ratio"]=advRatioDataObj
          finalResult["advDec"]=advDecDataObj

          maxOiResult=optionsCollection.aggregate(
              [
                 {"$match":{"date":date}},
                 #filter unwanted data
                 {"$project":{"data.records":1,"time":1}},
                 
                 {"$unwind":"$data.records"},
                 
                 {"$match":{"data.records.expiry":tempExpiry}},
                 
                 {"$project":{"data.records.values":1,"time":1}},
                 
                 {"$unwind":"$data.records.values"},
                 {"$group": {"_id": {"avgOI":"$data.records.values.avgOI","strikePrice":"$data.records.values.strikePrice"}}}, 
                {"$sort":{'_id.avgOI':-1}},
               #  {"$limit":4}
             ]
            )


           
          strikePrice=0  
          count=1 
          topFourMaxOi=[]         
          for mOI in maxOiResult:
              if(mOI['_id']['strikePrice']==strikePrice):
                 pass
              else: 
                 if(count>4):
                    break
                 else:
                   count+=1 
                   topFourMaxOi.append(mOI["_id"])
                   strikePrice=mOI['_id']['strikePrice']

          finalResult["maxOI"]=topFourMaxOi
             
    
          return finalResult
      except Exception as e:
          print(e)
          return jsonify({"message":"failed"})
      
   
   













   

@app.route('/optionsDataDateWise', methods=['POST'])
def optionsDataDateWise():
   data =request.get_json()
   tempDate=data['date'].strptime('%Y-%m-%d')
   date=tempDate.strftime('%d-%b-%Y')
   time=data['time']
   expiry=data['expiry']
   try:
     result=optionsCollection.find_one({'date':date, 'time':time},{'data':1})
     
      
     for data in result:
        if data=="data":
           dataList=result[data]["records"]
           for record in dataList:
              if record['expiry']==expiry:
                 print(record)
                 return json_util.dumps(record)
             
     

   except Exception as e:
     print(e)
     return jsonify({"message":"failed"})
     






#LIVE DATA SENDING SECTION
#request without expiry (current expiry)      
@app.route('/options', methods=['GET'])
def options():
   try:
     result=optionsCollection.find({},{'filtered':1,'experies':1}).sort([('_id',-1)]).limit(1)   
     return json_util.dumps(result)
   except Exception as e:
     print(e)
     return jsonify({"message":"failed"})




#request with expiry for live data
@app.route('/optionsWithExpiry', methods=['POST'])
def optionsWithExpiry():
  
  tempExpiry=request.get_json()['date']
  tempDate=datetime.strptime(tempExpiry,'%Y-%m-%d')
  expiry=tempDate.strftime('%d-%b-%Y')

  try:
     result=optionsCollection.find({'data.records.expiry':expiry,},{'data.records.$':1}).sort([('_id',-1)]).limit(1)  
     return json_util.dumps(result)
  except Exception as e:
     print(e)
     return jsonify({"message":"failed"})


   
#################live graphs endpoints #################################
#################live graphs for options################################
@app.route('/liveGraphs', methods=['POST'])
def liveGraphs():
   date=request.get_json()['date']
   finalResult = {}
   oiDataObj={}
   ivDataObj={}
   coiDataObj={}
   advRatioDataObj={}
   advDecDataObj={}
   ratioXAxis=[]
   ratioYAxisNifty=[]
   ratioYAxisAdvDecRatio=[]
   advValues=[]
   decValues=[]
   putsOIForMaxStrikePrice=[]
   callsOIForMaxStrikePrice=[]
   putsIVForMaxStrikePrice=[]
   callsIVForMaxStrikePrice=[]
   putsCOIForMaxStrikePrice=[]
   callsCOIForMaxStrikePrice=[]
   strikePricesForOI=[]
   optionsXAxis=[]


   try:
       #optionsResult=optionsCollection.find({'date':date,},{'filtered':1})
       advDecResult=advDecCollection.find({'date':date})

       #advdecRatio and advdec data object creation
       for advDec in advDecResult:
             ratioXAxis.append(advDec['time']) 
             ratioYAxisNifty.append(advDec['records']['data']['niftyPrice'])
             ratioYAxisAdvDecRatio.append(advDec['records']['data']['advDecRatio'])
             advValues.append(advDec['records']['data']['advances'])
             decValues.append(advDec['records']['data']['declines'])

       #ratio graph
       advRatioDataObj["xAsis"]=ratioXAxis
       advRatioDataObj["yAsisNifty"]=ratioYAxisNifty
       advRatioDataObj["yAsisAdvDecRatio"]=ratioYAxisAdvDecRatio
       
       #adv dec graph
       advDecDataObj["xAsis"]=ratioXAxis
       advDecDataObj["yAsisAdvances"]=advValues
       advDecDataObj["yAsisDeclines"]=decValues


      #  for options in optionsResult:
      #     optionsXAxis.append(options['filtered']['time'])
      #     maxStrikeObject=options['filtered']['data'][-1]


      #     strikePricesForOI.append(maxStrikeObject['strikePrice'])


      #     putsOIForMaxStrikePrice.append(maxStrikeObject["PE"]['openInterest'])
      #     callsOIForMaxStrikePrice.append(maxStrikeObject["CE"]['openInterest'])


      #     putsCOIForMaxStrikePrice.append(maxStrikeObject["PE"]['changeinOpenInterest'])
      #     callsCOIForMaxStrikePrice.append(maxStrikeObject["CE"]['changeinOpenInterest'])

      #     putsIVForMaxStrikePrice.append(maxStrikeObject["PE"]['impliedVolatility'])
      #     callsIVForMaxStrikePrice.append(maxStrikeObject["CE"]['impliedVolatility'])

      #  oiDataObj['xAxis']=optionsXAxis
      #  oiDataObj["puts"]=putsOIForMaxStrikePrice
      #  oiDataObj['calls']=callsOIForMaxStrikePrice
      #  oiDataObj['strikePrice']=strikePricesForOI

      #  ivDataObj['xAxis']=optionsXAxis
      #  ivDataObj['puts']=putsIVForMaxStrikePrice
      #  ivDataObj['calls']=callsIVForMaxStrikePrice

      #  coiDataObj['xAxis']=optionsXAxis
      #  coiDataObj['puts']=putsCOIForMaxStrikePrice
      #  coiDataObj['calls']=callsCOIForMaxStrikePrice



       

       
      #  finalResult["IV"]=ivDataObj
      #  finalResult["COI"]=coiDataObj
      #  finalResult["OI"]=oiDataObj
       finalResult["AdvDecRatio"]=advRatioDataObj
       finalResult["advDec"]=advDecDataObj
       return jsonify({"result":finalResult})  
   except Exception as e:
      print(e) 
      return jsonify({"message":"failed"})      


@app.route('/premiumDecayData', methods=['POST'])
def premiumDecayData():
    fromDate=request.get_json()['fromDate'] 
    toDate=request.get_json()['toDate'] 

    try:
       result=optionsCollection.find({'date':{'$gte':fromDate,'$lte':toDate},'premiumDecay':'true'})
       for data in result:
          print(data)
       return "ok"   
    except Exception as e:
       pass









if __name__ == '__main__':
  app.run(host='127.0.0.1', port=5000, debug=True)
 