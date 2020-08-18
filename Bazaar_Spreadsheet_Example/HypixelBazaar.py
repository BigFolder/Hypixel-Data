import requests
import pandas as pd
import pickle
import csv

'''
Loads our Machine Learning model using Pickle, creates a dataframe of our bazaar product
Runs the model and predicts whether to invest into the product or not, 0 = No : 1= Yes.
See dataCleaningBazaar.py for in depth explanation of forest and how to modify the model. :D
'''


def useModel(modelFile, dataSet):

    model = pickle.load(open(modelFile, 'rb'))
    test = pd.DataFrame(dataSet, index=[0])
    getVal = model.predict(test)

    return int(getVal)


'''
Checks if there were possible market crashes.
Using the previous bazaar data and the most recent bazaar data.
'''


def checkCrashData(newData):
    with open("crashData.txt", 'r') as file:
        reader = csv.reader(file)
        oldData = {}
        for line in reader:
            line = ", ".join(line)
            line = eval(line)
            product = line['product']
            del line['product']
            oldData.update({product: line})

        possibleCrash = []
        for product in newData:
            if product in oldData:
                # Tweak these however you want.
                perc1 = newData[product]['buyOrders'] / oldData[product]['buyOrders'] <= .5
                perc2 = newData[product]['sellOrders'] / oldData[product]['sellOrders'] <= .5
                perc3 = newData[product]['margin'] / oldData[product]['margin'] >= 3

                if (perc1 or perc2 or perc3) and (newData[product]['margin'] >= 15):
                    x = [product, newData[product]['buyOrders'] / oldData[product]['buyOrders'],
                         newData[product]['sellOrders'] / oldData[product]['sellOrders'],
                         newData[product]['margin'] / oldData[product]['margin'],
                         newData[product]['margin'], oldData[product]['margin']]
                    possibleCrash.append(x)

                else:
                    continue

        return possibleCrash


'''
Saves the most recent bazaar data into a file for later use, can skip this later on and use a dictionary.
Writing here is done simply to see if a crash occurs here, if its from an item or not.
A program crash has never occurred, so it is an irrelevant step that can be deprecated.
'''


def saveCrashData(data):
    file = open("crashData.txt", 'w')
    for product in data:
        data[product].update({'product': product})
        file.write(str(data[product]) + '\n')
    file.close()
    print("Crash Data Saved")


'''
Saves the bazaar data into a file that holds ALL past bazaar data sets.
This is used to train machine learning models (See dataCleaningBazaar.py)
Always have this on if you want to keep a log of all bazaar data over some time span.
currently data is saved every 10 calls or ~20 minutes.

Date time is not included here to avoid possible malicious use (Let people think, not bots)
'''


def saveBazaarData(data):

    file = open("bazaarData.txt", 'a+')
    for product in data:
        file.write(str(product)+";" + str(data[product]) + '\n')
    file.close()

    print('Bazaar Data Saved')


'''
Takes in the full api call in json form cleans the data up and does calculations that we see necessary
Also uses the random forest model "finalized_model.sav" (See dataCleaningBazaar.py)

Returns a dictionary of each product and all of the data we considered valuable.
'''


def gather_bazaar_data(API_KEY, modelFile):
    buyData = {}
    data = requests.get("https://api.hypixel.net/skyblock/bazaar?key=" + API_KEY).json()
    for productID in data['products']:
        if data['products'][productID]['quick_status']['buyOrders'] > 0 and (
                data['products'][productID]['quick_status']['sellOrders']) > 0:
            if isinstance(data['products'][productID]['sell_summary'], (list, tuple)) and \
                    isinstance(data['products'][productID]['buy_summary'], (list, tuple)):
                buyVolume = data['products'][productID]['quick_status']['buyVolume']
                buyOrders = data['products'][productID]['quick_status']['buyOrders']
                # What people are selling the product at
                buyPrice = data['products'][productID]['buy_summary'][0]['pricePerUnit']
                buyMovingWeek = data['products'][productID]['quick_status']['buyMovingWeek']
                sellVolume = data['products'][productID]['quick_status']['sellVolume']
                # What people are buying the product at
                sellPrice = data['products'][productID]['sell_summary'][0]['pricePerUnit']
                sellOrders = data['products'][productID]['quick_status']['sellOrders']
                sellMovingWeek = data['products'][productID]['quick_status']['sellMovingWeek']
                margin = buyPrice - sellPrice
                buySellDiff = buyVolume - sellVolume

                if buyPrice != 0:
                    # Return of Investment calculation
                    soldFor = round((buyPrice - .1) * .99, 3)

                    boughtFor = round((sellPrice + .1), 3)

                    RoI = round(((soldFor - boughtFor) / boughtFor) * 100, 3)

                    if productID not in buyData:
                        reliability = useModel(modelFile=modelFile, dataSet={'buyVolume': buyVolume,
                                                                             'buyOrders': buyOrders,
                                                                             'buyPrice': buyPrice,
                                                                             'buyMovingWeek': buyMovingWeek,
                                                                             'sellVolume': sellVolume,
                                                                             'sellOrders': sellOrders,
                                                                             'sellPrice': sellPrice,
                                                                             'sellMovingWeek': sellMovingWeek,
                                                                             'RoI': RoI,
                                                                             'margin': margin,
                                                                             'buySellDiff': buySellDiff})

                        buyData.update({productID: {'buyVolume': buyVolume,
                                                    'buyOrders': buyOrders,
                                                    'buyPrice': buyPrice,
                                                    'buyMovingWeek': buyMovingWeek,
                                                    'sellVolume': sellVolume,
                                                    'sellOrders': sellOrders,
                                                    'sellPrice': sellPrice,
                                                    'sellMovingWeek': sellMovingWeek,
                                                    'RoI': RoI, 'margin': margin,
                                                    'buySellDiff': buySellDiff,
                                                    'reliability': reliability}})

    return buyData


def sortData(data, dataFeature):

    sortedData = sorted(data.items(), key=lambda x: x[1][str(dataFeature)], reverse=True)

    return sortedData
