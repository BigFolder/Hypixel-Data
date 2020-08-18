import pandas as pd
import csv
import pickle
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

'''
The function used to test our random forest model on our real dataset.
Takes in our dataSet and in this case the model, since we can test all types of models in this file.
'''


def useForest(model, dataSet):
    test = pd.DataFrame(dataSet, index=[0])
    getVal = model.predict(test)

    return int(getVal)


'''
This function is equal to "gatherBazaarData" from hypixelInvest.py, with minor changes to catch errors with hypixel API.
Gathers all data checks to see if it has any orders, also double checks to ensure a list exists of items being sold.

 
IMPORTANT TO NOTE that we include the model we use in the function call here, since we can test many types of models.
In the actual hypixelInvest.py file we only use 1 finalized model.
'''


def true_test(data, model):
    buyData = {}

    if data['success']:
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
                            reliability = useForest(model,
                                                    {'buyVolume': buyVolume, 'buyOrders': buyOrders,
                                                     'buyPrice': buyPrice, 'buyMovingWeek': buyMovingWeek,
                                                     'sellVolume': sellVolume, 'sellOrders': sellOrders,
                                                     'sellPrice': sellPrice, 'sellMovingWeek': sellMovingWeek,
                                                     'RoI': RoI, 'margin': margin, 'buySellDiff': buySellDiff})

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
    else:
        return "Api Error, Data collection unsuccessful"


'''
One of 3 rubrics created to give our data some initial "guess" on whether it is a good investment or not.
You can tweak these however you want! All 3 use the full dataset, and then they are all combined together.
Duplicates are dropped and we are left with a large dataset of possible good investments and bad investments.
We use this data to actually train our models.
'''


def BazaarDataRubricOne():
    with open("bazaarData.txt", 'r') as file:
        reader = csv.reader(file, delimiter=';')
        dataset = {}
        n = 0

        for line in reader:
            di = eval(line[1])
            di.update({'product': line[0]})

            reliability = 0
            volumePerc = (di['sellMovingWeek'] / (
                    di['buyMovingWeek'] + di['sellMovingWeek'])) >= .25
            boolWeekly = di['sellMovingWeek'] >= 150000 and di['buyMovingWeek'] >= 150000
            boolOrder = (di['sellOrders'] >= 20 and di['buyOrders'] >= 20)
            # Determine Weights (A lot of trial and error)

            if di['RoI'] >= 5:
                reliability += 3
                if di['margin'] >= 40:
                    reliability += 3
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                elif 15 < di['margin'] < 40:
                    reliability += 2
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2

            elif 2 < di['RoI'] < 5:
                reliability += 1
                if di['margin'] >= 40:
                    reliability += 3
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                elif 15 < di['margin'] < 40:
                    reliability += 2
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2

            elif 2 <= di["RoI"] <= 0:
                reliability = 0

            di['reliability'] = reliability
            dataset.update({n: di})
            n += 1

        for item in dataset:
            if dataset[item]['reliability'] >= 7:
                dataset[item]['reliability'] = 1
            else:
                dataset[item]['reliability'] = 0

        df = pd.DataFrame.from_dict(dataset, orient='index',
                                    columns=['product', 'buyVolume', 'buyOrders', 'buyPrice', 'buyMovingWeek',
                                             'sellVolume',
                                             'sellOrders', 'sellPrice', 'sellMovingWeek', 'RoI', 'margin',
                                             'buySellDiff', 'reliability'])

        cleanestDF = df.drop_duplicates()

        return cleanestDF


def BazaarDataRubricTwo():
    with open("bazaarData.txt", 'r') as file:
        reader = csv.reader(file, delimiter=';')
        dataset = {}
        n = 0

        for line in reader:
            di = eval(line[1])
            di.update({'product': line[0]})

            reliability = 0
            volumePerc = (di['sellMovingWeek'] / (
                    di['buyMovingWeek'] + di['sellMovingWeek'])) >= .40
            boolWeekly = di['sellMovingWeek'] >= 200000 and di['buyMovingWeek'] >= 200000
            boolOrder = (di['sellOrders'] >= 100 and di['buyOrders'] >= 100)
            # Determine Weights (A lot of trial and error)

            if di['RoI'] >= 5:
                reliability += 3
                if di['margin'] >= 40:
                    reliability += 3
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                elif 15 < di['margin'] < 40:
                    reliability += 2
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2

            elif 2 < di['RoI'] < 5:
                reliability += 1
                if di['margin'] >= 40:
                    reliability += 3
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                elif 15 < di['margin'] < 40:
                    reliability += 2
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2

            elif 2 <= di["RoI"] <= 0:
                reliability = 0

            di['reliability'] = reliability
            dataset.update({n: di})
            n += 1

        for item in dataset:
            if dataset[item]['reliability'] >= 7:
                dataset[item]['reliability'] = 1
            else:
                dataset[item]['reliability'] = 0

        df = pd.DataFrame.from_dict(dataset, orient='index',
                                    columns=['product', 'buyVolume', 'buyOrders', 'buyPrice', 'buyMovingWeek',
                                             'sellVolume',
                                             'sellOrders', 'sellPrice', 'sellMovingWeek', 'RoI', 'margin',
                                             'buySellDiff', 'reliability'])

        cleanestDF = df.drop_duplicates()

        return cleanestDF


def BazaarDataRubricThree():
    with open("bazaarData.txt", 'r') as file:
        reader = csv.reader(file, delimiter=';')
        dataset = {}
        n = 0

        for line in reader:
            di = eval(line[1])
            di.update({'product': line[0]})

            reliability = 0
            volumePerc = (di['sellMovingWeek'] / (
                    di['buyMovingWeek'] + di['sellMovingWeek'])) >= .35
            boolWeekly = di['sellMovingWeek'] >= 100000 and di['buyMovingWeek'] >= 100000
            boolOrder = (di['sellOrders'] >= 35 and di['buyOrders'] >= 35)
            # Determine Weights (A lot of trial and error)

            if di['RoI'] >= 5:
                reliability += 3
                if di['margin'] >= 40:
                    reliability += 3
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                elif 15 < di['margin'] < 40:
                    reliability += 2
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2

            elif 2 < di['RoI'] < 5:
                reliability += 1
                if di['margin'] >= 40:
                    reliability += 3
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                elif 15 < di['margin'] < 40:
                    reliability += 2
                    if volumePerc:
                        reliability += 2
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2
                    else:
                        reliability += 1
                        if boolOrder and boolWeekly:
                            reliability += 1
                        else:
                            reliability -= 2

            elif 2 <= di["RoI"] <= 0:
                reliability = 0

            di['reliability'] = reliability
            dataset.update({n: di})
            n += 1

        for item in dataset:
            if dataset[item]['reliability'] >= 7:
                dataset[item]['reliability'] = 1
            else:
                dataset[item]['reliability'] = 0

        df = pd.DataFrame.from_dict(dataset, orient='index',
                                    columns=['product', 'buyVolume', 'buyOrders', 'buyPrice', 'buyMovingWeek',
                                             'sellVolume',
                                             'sellOrders', 'sellPrice', 'sellMovingWeek', 'RoI', 'margin',
                                             'buySellDiff', 'reliability'])

        cleanestDF = df.drop_duplicates()

        return cleanestDF


'''
This function creates our random forest classifier that predicts whether new items are good investments or not.
To learn about Tweaking parameters of a model or even the basics of machine learning;
Please check the sklearn.RandomForestClassifier Documentation.

Takes in your hypixel API Key so we can test our model on the most current bazaar data. :D
'''


def createTree(HYPIXEL_API_KEY):
    model_data1 = BazaarDataRubricOne()
    model_data2 = BazaarDataRubricTwo()
    model_data3 = BazaarDataRubricThree()

    # Combine all Rubrics
    model_data = model_data1.append([model_data2, model_data3])

    # Remove duplicate entries
    model_data = model_data.drop_duplicates()

    # Basic info on our Dataframe, "Count" on reliability is the number of data entities
    # Head simply shows the first 5 items int he dataframe.
    print(model_data.head())
    print(model_data.describe())

    print("Data Successfully Cleaned")
    print("Creating Model")

    # Feature we want to predict is reliability
    y = model_data['reliability']
    # Remove predictive feature and useless features here.
    X = model_data.drop(columns=['reliability', 'product'])
    # Create TrainTestSplit
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=40)

    # Create the model (Random Forest Classification) Tweak parameters as you wish.
    RFclass = RandomForestClassifier(max_depth=5, random_state=0, criterion='gini', n_estimators=75, bootstrap=True,
                                     max_features=4)
    # Train the model
    RFclass.fit(X_train, y_train)
    # Test the model
    pred = RFclass.predict(X_test)
    # Get Confusion Matrix of model test
    RFclassCFM = confusion_matrix(y_test, pred)
    # Print accuracy of model.
    print(RFclassCFM[0][0] / (RFclassCFM[0][0] + RFclassCFM[1][0]), 'Correct Predictions. classifier')

    # Give API Key to do a 'true test' on current bazaar data.

    dirty_data = requests.get("https://api.hypixel.net/skyblock/bazaar?key=" + HYPIXEL_API_KEY).json()
    test_model = true_test(dirty_data, RFclass)
    # Ran into instance error when using isInstance() so went old school.
    if isinstance(test_model, str):
        print(test_model)
    else:
        print('API Collection and model prediction successful')

    # Shows feature importance OR What % of importance was each feature in our model.
    print("Printing Feature Importance")
    feature_imp = pd.Series(RFclass.feature_importances_, index=X.columns).sort_values(ascending=False)
    print(feature_imp)
    # Sort model by margin, change this if you want.
    reliability_sort = sorted(test_model.items(), key=lambda x: x[1]['margin'], reverse=True)
    return [reliability_sort, RFclass]


# Actual test run of it all count is to help me see how many items actually showed up Invalid shows items that failed.
# Hypixel API Key
API = "c60dea67-78ab-4411-9b97-b890c022b6de"

randomForestPredictions = createTree(API)
count = 0
invalid = []
print("\nRANDOM FOREST OUTCOME\n")
for k in randomForestPredictions[0]:
    if k[1]['reliability'] >= 1:
        print(k[0], count, 'Margin', k[1]['margin'], 'RoI', k[1]['RoI'])
        count += 1
    else:
        invalid.append((k[0], k[1]['margin'], k[1]['RoI']))


# Saving your model to be used on your actual scripts.
filename = 'finalized_model.sav'
pickle.dump(randomForestPredictions[1], open(filename, 'wb'))
