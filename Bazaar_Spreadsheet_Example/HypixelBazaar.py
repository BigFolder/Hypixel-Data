import requests
import pandas as pd
import pickle
import csv
import random

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
                divZero = oldData[product]['buyOrders'] != 0 and oldData[product]['sellOrders'] != 0 and \
                          oldData[product]['margin'] != 0
                if divZero is True:
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
    #print("Crash Data Saved")


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
        file.write(str(product) + ";" + str(data[product]) + '\n')
    file.close()

    #print('Bazaar Data Saved')


'''
Takes in the full api call in json form cleans the data up and does calculations that we see necessary
Also uses the random forest model "finalized_model.sav" (See dataCleaningBazaar.py)

Returns a dictionary of each product and all of the data we considered valuable.
'''


def gather_bazaar_data(API_KEY, modelFile):
    buyData = {}
    data = requests.get("https://api.hypixel.net/skyblock/bazaar?key=" + API_KEY).json()
    productFrequency = getProdFreq()
    for productID in data['products']:
        sumBoolean = len(data['products'][productID]['buy_summary']) > 0 and \
                     len(data['products'][productID]['sell_summary']) > 0
        orderBoolean = data['products'][productID]['quick_status']['buyOrders'] > 0 and \
                       (data['products'][productID]['quick_status']['sellOrders']) > 0

        if orderBoolean and sumBoolean:
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
                margin = ((buyPrice * .99) - .1) - (sellPrice + .1)
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
                                                    'reliability': reliability,
                                                    'reliabilityFreq%': productFrequency[productID]}})

    return buyData


'''
Gets the Frequency at which a product has been considered in the past from our prodFreq file.
'''


def getProdFreq():
    data = {}
    with open("prodFreq.txt", "r") as file:
        for line in file:
            prod = line.split(" ")[0]
            prodFreq = line.split(" ")[1][:-1]
            data.update({prod: prodFreq})

    return data


'''
Sorts the data based off of a simple input from user, simply cleans up code a little.
'''


def sortData(data, dataFeature):
    sortedData = sorted(data.items(), key=lambda x: x[1][str(dataFeature)], reverse=True)

    return sortedData


'''
Heavily WIP, attempts to give possible investment options based on the amount of GP given.
'''


def giveInsight(data, amount):
    recommended_items = {}
    product_weights = {}
    insight = {}

    # Select 5 random items
    while len(recommended_items) < 5:
        random_item = random.choice(list(data.keys()))
        check1 = data[random_item]["reliability"] >= 6 and data[random_item]["RoI"] >= 2
        check0 = (data[random_item]["buyMovingWeek"] + data[random_item]["sellMovingWeek"]) / \
                 (data[random_item]["margin"]) >= 2000
        never = ["ENCHANTED_PUFFERFISH", "STOCK_OF_STONKS"]
        booleanDict = {25e5: {"check2": data[random_item]["margin"] >= 40,
                              "check3": data[random_item]["buyMovingWeek"] >= 6e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 6e5,
                              "check5": float(data[random_item]["reliabilityFreq%"]) >= 45
                              },
                       55e5: {"check2": data[random_item]["margin"] >= 80,
                              "check3": data[random_item]["buyMovingWeek"] >= 6e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 6e5,
                              "check5": float(data[random_item]["reliabilityFreq%"]) >= 45
                              },
                       1e6: {"check2": data[random_item]["margin"] >= 100,
                             "check3": data[random_item]["buyMovingWeek"] >= 75e5,
                             "check4": data[random_item]["sellMovingWeek"] >= 75e5,
                             "check5": float(data[random_item]["reliabilityFreq%"]) >= 40
                             },
                       25e6: {"check2": data[random_item]["margin"] >= 110,
                              "check3": data[random_item]["buyMovingWeek"] >= 75e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 75e5,
                              "check5": float(data[random_item]["reliabilityFreq%"]) >= 35
                              },
                       5e6: {"check2": (data[random_item]["margin"] >= 125),
                             "check3": data[random_item]["buyMovingWeek"] >= 8e5,
                             "check4": data[random_item]["sellMovingWeek"] >= 8e5,
                             "check5": float(data[random_item]["reliabilityFreq%"]) >= 15
                             },
                       75e6: {"check2": data[random_item]["margin"] >= 150,
                              "check3": data[random_item]["buyMovingWeek"] >= 1e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 1e5,
                              "check5": float(data[random_item]["reliabilityFreq%"]) >= 0
                              },

                       }

        for value in booleanDict:
            if amount <= value:
                bool1 = (booleanDict[value]["check2"] and booleanDict[value]["check3"] and booleanDict[value]["check4"])
                bool2 = (booleanDict[value]["check5"] and check1 and check0)
                if bool1 and bool2 and random_item not in never:
                    recommended_items.update({random_item: data[random_item]})

    # Convert to DF to get sums easily
    df = pd.DataFrame.from_dict(recommended_items, orient="index", columns=['buyVolume', 'buyOrders', 'buyPrice',
                                                                            'buyMovingWeek', 'sellVolume', 'sellOrders',
                                                                            'sellPrice', 'sellMovingWeek', 'RoI',
                                                                            'margin', 'buySellDiff', 'reliability',
                                                                            'reliabilityFreq%'])

    df = df.drop(columns=['reliability', 'reliabilityFreq%'])

    # Gather Sum Data
    dfSums = df.sum()

    sumInstantBuys = dfSums['sellMovingWeek']
    sumMargins = dfSums['margin']
    sumInstantSells = dfSums['buyMovingWeek']
    sumRoI = dfSums['RoI']

    # Get product weights for each product randomly chosen
    total_weight = 0
    for product in recommended_items:
        total = 0
        buysWeight = round(recommended_items[product]['sellMovingWeek'] / sumInstantBuys, 2)
        sellsWeight = round(recommended_items[product]['buyMovingWeek'] / sumInstantSells, 2)
        marginsWeight = round(recommended_items[product]['margin'] / sumMargins, 2)
        roiWeight = round(recommended_items[product]['RoI'] / sumRoI, 2)

        check1 = buysWeight >= .30
        check2 = marginsWeight >= .45
        check3 = roiWeight >= .45
        check4 = sellsWeight >= .30

        if check1:
            total += 3
        else:
            total += 0
        if check4:
            total += 2
        else:
            total += 1
        if check2:
            total += 3
        else:
            total += 1
        if check3:
            total += 3
        else:
            total += 1

        total_weight += total

        product_weights.update({product: total})

    entireCost = 0
    entireSoldFor = 0
    for product in product_weights:
        finalWeight = round(product_weights[product] / total_weight, 4)
        # print(product, "prod Weight", product_weights[product], "prod %", finalWeight)
        amountToSpend = round((amount * finalWeight))
        sellPrice = data[product]['sellPrice'] - .1
        buyPrice = (data[product]['buyPrice'] * .99) + .1
        itemQuantity = round(amountToSpend / (sellPrice - .1)) - 1
        margin = data[product]['margin']
        totalSold = itemQuantity * buyPrice
        totalCost = itemQuantity * sellPrice
        totalProfit = totalSold - totalCost
        # print(product, "buy price" , buyPrice, "sell price", sellPrice,
        #      "margin", margin,"Product Amount to spend", amountToSpend,"product quantity to buy", itemQuantity,
        #      "total cost", totalCost, "total sold",totalSold,
        #      "total Profit", totalProfit)

        insight.update({product: {"itemQuantity": itemQuantity,
                                  "totalCost": totalCost,
                                  "productWeight": finalWeight,
                                  "buyMovingWeek": data[product]['buyMovingWeek'],
                                  "sellMovingWeek": data[product]['sellMovingWeek'],
                                  'totalSold': totalSold, 'totalProfit': totalProfit
                                  }})

        entireCost += totalCost
        entireSoldFor += totalSold

    return {'insight': insight, 'entireCost': entireCost, 'playerAmount': amount, 'entireSoldFor': entireSoldFor}


def sellerShuffle(data):
    #BUYCAP = 640

    scuffNames = {"LOG:1": "Spruce Wood", "LOG:3": "Jungle Wood", "LOG:2": "Birch Wood", "CARROT_ITEM": "Carrot",
                  "LOG": "Oak Wood", "POTATO_ITEM": "Potato", "INK_SACK:3": "Cocoa Bean", "LOG_2": "Acacia Wood",
                  "LOG_2:1": "Dark Oak Wood", "ENDER_STONE": "End Stone", "NETHER_STALK": "Nether Wart",
                  "RAW_FISH:3": "Pufferfish", "RAW_FISH:1": "Raw Salmon", "RAW_FISH:2": "Clownfish"}

    sellerItems = {"ROTTEN_FLESH": {"vendorCost": 8}, "BONE": {"vendorCost": 8}, "STRING": {"vendorCost": 10},
                   "SLIME_BALL": {"vendorCost": 14}, "SULPHUR": {"vendorCost": 10},
                   "PACKED_ICE": {"vendorCost": 9}, "ICE_BAIT": {"vendorCost": 12},
                   "FLINT": {"vendorCost": 6}, "RABBIT_FOOT": {"vendorCost": 10},
                   "RED_MUSHROOM": {"vendorCost": 12}, "SAND": {"vendorCost": 4},
                   "GOLD_INGOT": {"vendorCost": 6}, "COAL": {"vendorCost": 4},
                   "RAW_FISH": {"vendorCost": 20}, "BROWN_MUSHROOM": {"vendorCost": 12},
                   "ICE": {"vendorCost": 1}, "WHEAT": {"vendorCost": 2.33},
                   "COBBLESTONE": {"vendorCost": 3}, "IRON_INGOT": {"vendorCost": 5.5},
                   "MELON": {"vendorCost": 2}, "SUGAR_CANE": {"vendorCost": 5},
                   "GRAVEL": {"vendorCost": 6}, "PUMPKIN": {"vendorCost": 8},
                   "MAGMA_CREAM": {"vendorCost": 20}, "OBSIDIAN": {"vendorCost": 50},
                   "Spruce Wood": {"vendorCost": 5}, "Jungle Wood": {"vendorCost": 5},
                   "Birch Wood": {"vendorCost": 5}, "Oak Wood": {"vendorCost": 5},
                   "Acacia Wood": {"vendorCost": 5}, "Nether Wart": {"vendorCost": 10},
                   "GHAST_TEAR": {"vendorCost": 200}, "BLAZE_POWDER": {"vendorCost": 12},
                   "SPIDER_EYE": {"vendorCost": 12}, "Carrot": {"vendorCost": 2.3},
                   "Potato": {"vendorCost": 2.3}, "Cocoa Bean": {"vendorCost": 5},
                   "Raw Salmon": {"vendorCost": 30}, "Clownfish": {"vendorCost": 100},
                   "Pufferfish": {"vendorCost": 40}, "End Stone": {"vendorCost": 10},
                   "Dark Oak Wood": {"vendorCost": 5}
                   }
    finalData = {}

    for product in data:
        if product in scuffNames:
            totalSale = data[product]['sellPrice'] * 640
            product = scuffNames[product]
            totalCost = sellerItems[product]["vendorCost"] * 640
            finalData.update({product: {"buyFor": totalCost, "sellFor": totalSale, "profit": totalSale - totalCost}})
        elif product in sellerItems:
            totalCost = sellerItems[product]["vendorCost"] * 640
            totalSale = data[product]['sellPrice'] * 640
            finalData.update({product: {"buyFor": totalCost, "sellFor": totalSale, "profit": totalSale - totalCost}})

    return finalData
