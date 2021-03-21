import requests
import pandas as pd
import pickle
import csv
import random
from datetime import datetime

'''
Uses Each model to return the most popular reliability between all of the models.
Very simple but effective approach for Classification using an ensemble of models.
'''


def get_vote(models: list, dataset: dict) -> int:
    test = pd.DataFrame(dataset, index=[0])
    votes = []

    for model in models:
        getVal = model.predict(test)
        votes.append(int(getVal))

    return max(set(votes), key=votes.count)


'''
Loads all of the Models supplied in a list to be used in predicting product reliability.
Example valid files are any saved in pickle from SKlearn or other models (Typically filename.sav)
'''


def load_models(fileList: list) -> list:
    models = []

    for file in fileList:
        models.append(pickle.load(open(file, 'rb')))

    return models


'''

Checks if there were possible market crashes.
Using the previous bazaar data and the most recent bazaar data.

Currently checks to see if a product has less than 50% of it's previous number of buy orders and sell orders
as well as if the margin is 3x what it was during the last request from the api.

If a case is hit (typically >1 case) the item has crashed in some way.

Returns a Dictionary

KEYS
'product': Products name, 
'buyOrderDiff': Products Current number of buy orders Divided by the previous number of sell orders
'sellOrderDiff': Products Current number of sell orders Divided by the previous number of sell orders
'marginDiff': Products Current margin Divided by the previous margin
'newMargin': Products current margin of profit
'oldMargin': Products previous margin of profit
'dateTime': Date time of this occurrence. 

'''


def check_crash_data(newData: dict) -> list:
    try:

        oldData = pd.read_csv("crashData.csv",
                              usecols=['product', 'buyVolume', 'buyOrders', 'buyPrice', 'buyMovingWeek',
                                       'sellVolume', 'sellOrders', 'sellPrice', 'sellMovingWeek', 'RoI',
                                       'margin', 'buySellDiff', 'reliability', 'avgVolume', 'datetime',
                                       'event'], index_col=[0]).to_dict(orient='index')

        # Lazy Fix for indexing on .csv file

        possible_crash = []
        if oldData == {}:
            for product in newData:
                if product in oldData:
                    divZero = oldData[product]['buyOrders'] != 0 and oldData[product]['sellOrders'] != 0 and \
                              oldData[product]['margin'] != 0
                    if divZero is True:
                        # Tweak these however you want.
                        perc1 = newData[product]['buyOrders'] / oldData[product]['buyOrders'] <= .5
                        perc2 = newData[product]['sellOrders'] / oldData[product]['sellOrders'] <= .5
                        perc3 = newData[product]['margin'] / oldData[product]['margin'] >= 3
                        # Product, buyOrderDiff, sellOrderDiff, marginDiff, newMargin, oldMargin, datetime
                        if (perc1 or perc2 or perc3) and (newData[product]['margin'] >= 15):
                            x = {'product': product,
                                 'buyOrderDiff': newData[product]['buyOrders'] / oldData[product]['buyOrders'],
                                 'sellOrderDiff': newData[product]['sellOrders'] / oldData[product]['sellOrders'],
                                 'marginDiff': newData[product]['margin'] / oldData[product]['margin'],
                                 'newMargin': newData[product]['margin'], 'oldMargin': oldData[product]['margin'],
                                 'dateTime': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                 }
                            possible_crash.append(x)

                        else:
                            continue
                else:
                    oldData.update({product: newData[product]})
        else:
            for product in newData:
                oldData.update({product: newData[product]})

        # Save our new Data into the crash data text file, fix index and name scheme.
        df = pd.DataFrame.from_dict(newData, orient='index')
        df.index.name = "product"
        df.to_csv("crashData.csv")

        return possible_crash
    # Create File if it does not already exist.
    except FileNotFoundError:
        create = open("crashData.csv", 'w')
        create.close()
        check_crash_data(newData)


'''
Saves the bazaar data into a file that holds ALL past bazaar data.
Always have this on if you want to keep a log of all bazaar data over some time span.

Uses for this can be unlimited There is always use in Data just think about it!
'''


def save_bazaar_data(data: dict) -> None:
    try:
        file = open("bazaarData.txt", 'a+')
        for product in data:
            file.write(str(product) + ";" + str(data[product]) + '\n')
        file.close()
        # First time saving data? this will create the file for you.
    except FileNotFoundError:
        file = open('bazaarData.txt', 'w')
        file.close()


'''
Takes your API KEY (Currently not needed, but I'll leave this in if they do decide to require one.)
As well as your LIST of ML models ['modelName.sav', 'nextModel.sav', ...]

Here the application of your ML models is done.

Returns a dictionary of each product and all of the data in a much cleaner format

KEYS; NOTE: The Product name is the key for each of these 
'buyVolume': Total buy volume of the product
'buyOrders': Total number of buy orders of the product
'buyPrice': Current buy price for the product
'buyMovingWeek': Weekly amount bought
'sellVolume': Total sell volume of the product
'sellOrders': Total sell orders of the product
'sellPrice': current selling price for the product
'sellMovingWeek': Weekly amount sold
'RoI': % Return on investment for the product, 
'margin': Margin of profit for the product (Includes Bazaar Fee)
'buySellDiff': Difference in the weekly bought and sold for the product.
'reliability': Models prediction for our product (0-9)
'avgVolume': Average volume of our product
'datetime': DateTime of the data acquisition 
'event': 1/0 True/False whether an item comes from an holiday event.
'''


def gather_bazaar_data(API_KEY: str, fileList: list) -> dict:
    buyData = {}

    ml_models = load_models(fileList)

    event_items = ['GREEN_CANDY', 'PURPLE_CANDY', 'ECTOPLASM', 'PUMPKIN_GUTS', 'SPOOKY_SHARD', 'WEREWOLF_SKIN',
                   'SOUL_FRAGMENT', 'WHITE_GIFT', 'GREEN_GIFT', 'RED_GIFT']

    session = requests.Session()

    data = session.get("https://api.hypixel.net/skyblock/bazaar?key=" + API_KEY).json()

    for productID in data['products']:
        # Two boolean checks to determine if an item has ever been sold or bought in the past.
        summary_boolean1 = len(data['products'][productID]['buy_summary']) > 0
        summary_boolean2 = len(data['products'][productID]['sell_summary']) > 0
        summary_boolean = summary_boolean1 and summary_boolean2

        # Two boolean checks to determine if there are active orders for the item
        order_boolean1 = data['products'][productID]['quick_status']['buyOrders'] > 0
        order_boolean2 = data['products'][productID]['quick_status']['sellOrders'] > 0
        order_boolean = order_boolean1 and order_boolean2

        if order_boolean and summary_boolean:
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
                avgVolume = round((buyMovingWeek + sellMovingWeek) / 2, 2)

                if buyPrice != 0:
                    # Return of Investment calculation
                    soldFor = round((buyPrice - .1) * .99, 3)

                    boughtFor = round((sellPrice + .1), 3)

                    RoI = round(((soldFor - boughtFor) / boughtFor) * 100, 3)

                    if productID in event_items:
                        event = 1
                    else:
                        event = 0

                    dataset = {'buyVolume': buyVolume,
                               'buyOrders': buyOrders,
                               'buyPrice': buyPrice,
                               'buyMovingWeek': buyMovingWeek,
                               'sellVolume': sellVolume,
                               'sellOrders': sellOrders,
                               'sellPrice': sellPrice,
                               'sellMovingWeek': sellMovingWeek,
                               'RoI': RoI,
                               'margin': margin,
                               'buySellDiff': buySellDiff,
                               'avgVolume': avgVolume,
                               'event': event}

                    if productID not in buyData:
                        reliability = get_vote(models=ml_models, dataset=dataset)

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
                                                    'avgVolume': avgVolume,
                                                    'datetime': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                                    'event': event}})

    return buyData


'''
Sorts the data based off of a simple input from user, simply cleans up code a little.
I got kind of lazy and wanted sorting done out side of functions that I'm using for other projects.
So I carried this over to here :)
'''


def sort_data(data: dict, dataFeature: str) -> list:
    sortedData = sorted(data.items(), key=lambda x: x[1][str(dataFeature)], reverse=True)
    return sortedData


'''
Attempts to give valid investment options of the current products in the Hypixel Bazaar.
A lot of fun to try and do something that doesn't involve a model assisting me, overall I wouldn't use this seriously
UNLESS you retrain models to take more information into consideration
Perhaps whether a product is from a holiday or not :D
'''


def give_insight(data: dict, amount: int) -> dict:
    recommended_items = {}
    product_weights = {}
    insight = {}

    # Select 5 random items
    while len(recommended_items) < 5:
        random_item = random.choice(list(data.keys()))
        check1 = data[random_item]["reliability"] >= 6 and data[random_item]["RoI"] >= 2
        check0 = (data[random_item]["buyMovingWeek"] + data[random_item]["sellMovingWeek"]) / \
                 (data[random_item]["margin"]) >= 2000
        # These were never good
        never = ["ENCHANTED_PUFFERFISH", "STOCK_OF_STONKS"]
        # Each key is the amount to invest and the minimum thresholds decided to be "ok" for investing in the item.
        # Check 5 resides there for you to add more and more, however many you want! Simply a Skeleton example.
        booleanDict = {25e5: {"check2": data[random_item]["margin"] >= 40,
                              "check3": data[random_item]["buyMovingWeek"] >= 6e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 6e5,
                              "check5": True
                              },

                       55e5: {"check2": data[random_item]["margin"] >= 80,
                              "check3": data[random_item]["buyMovingWeek"] >= 6e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 6e5,
                              "check5": True
                              },

                       1e6: {"check2": data[random_item]["margin"] >= 100,
                             "check3": data[random_item]["buyMovingWeek"] >= 75e5,
                             "check4": data[random_item]["sellMovingWeek"] >= 75e5,
                             "check5": True
                             },

                       25e6: {"check2": data[random_item]["margin"] >= 110,
                              "check3": data[random_item]["buyMovingWeek"] >= 75e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 75e5,
                              "check5": True
                              },

                       5e6: {"check2": (data[random_item]["margin"] >= 125),
                             "check3": data[random_item]["buyMovingWeek"] >= 8e5,
                             "check4": data[random_item]["sellMovingWeek"] >= 8e5,
                             "check5": True
                             },

                       75e6: {"check2": data[random_item]["margin"] >= 150,
                              "check3": data[random_item]["buyMovingWeek"] >= 1e5,
                              "check4": data[random_item]["sellMovingWeek"] >= 1e5,
                              "check5": True
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
    # Finally the insight to be given!
    for product in product_weights:
        finalWeight = round(product_weights[product] / total_weight, 4)
        # print(product, "prod Weight", product_weights[product], "prod %", finalWeight)
        amountToSpend = round((amount * finalWeight))
        sellPrice = data[product]['sellPrice'] - .1
        buyPrice = (data[product]['buyPrice'] * .99) + .1
        itemQuantity = round(amountToSpend / (sellPrice - .1)) - 1

        totalSold = itemQuantity * buyPrice
        totalCost = itemQuantity * sellPrice
        totalProfit = totalSold - totalCost

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


'''
Gets all items you can purchase from the vendors and determine how much profit (if any) you'd get selling it to the
Bazaar 'Instantly'

BUYCAP is 640 Change if needed.

The Dictionary "sellerItems" holds all of the vendors current selling price for each of the items in the bazaar.
Change these if things change in game!

Returns a dictionary; NOTE The product name is the key for each entry

product: {"buyFor": total cost to buy the BUYCAP of the item,
          "sellFor": total amount made from selling the item instantly to the bazaar,
          "profit": Expected Profit if done right now!}

'''


def seller_shuffle(data: dict) -> dict:
    BUYCAP = 640

    scuffNames = {
        "BROWN_MUSHROOM": "Brown Mushroom",
        "INK_SACK:3": "Cocoa Beans",
        "INK_SACK:4": "Lapis Lazuli",
        "SPOOKY_SHARD": "Spooky Shard",
        "TARANTULA_WEB": "Tarantula Web",
        "CARROT_ITEM": "Carrot",
        "ENCHANTED_POTATO": "Enchanted Potato",
        "EXP_BOTTLE": "Experience Bottle",
        "JERRY_BOX_GREEN": "Green Jerry Box",
        "ENCHANTED_SLIME_BALL": "Enchanted Slimeball",
        "ENCHANTED_RED_MUSHROOM": "Enchanted Red Mushroom",
        "ENCHANTED_GOLDEN_CARROT": "Enchanted Golden Carrot",
        "ENCHANTED_RABBIT_HIDE": "Enchanted Rabbit Hide",
        "ENCHANTED_BIRCH_LOG": "Enchanted Birch Wood",
        "ENCHANTED_GUNPOWDER": "Enchanted Gunpowder",
        "ENCHANTED_MELON": "Enchanted Melon",
        "ENCHANTED_SUGAR": "Enchanted Sugar",
        "CACTUS": "Cactus",
        "ENCHANTED_BLAZE_ROD": "Enchanted Blaze Rod",
        "ENCHANTED_CAKE": "Enchanted Cake",
        "PUMPKIN": "Pumpkin",
        "ENCHANTED_BROWN_MUSHROOM": "Enchanted Brown Mushroom",
        "NURSE_SHARK_TOOTH": "Nurse Shark Tooth",
        "WHEAT": "Wheat",
        "ENCHANTED_RAW_SALMON": "Enchanted Raw Salmon",
        "ENCHANTED_GLISTERING_MELON": "Enchanted Glistering Melon",
        "PRISMARINE_SHARD": "Prismarine Shard",
        "PROTECTOR_FRAGMENT": "Protector Dragon Fragment",
        "ENCHANTED_EMERALD": "Enchanted Emerald",
        "ENCHANTED_SPIDER_EYE": "Enchanted Spider Eye",
        "RED_MUSHROOM": "Red Mushroom",
        "GRAND_EXP_BOTTLE": "Grand Experience Bottle",
        "MUTTON": "Mutton",
        "ENCHANTED_MELON_BLOCK": "Enchanted Melon Block",
        "SHARK_FIN": "Shark Fin",
        "DIAMOND": "Diamond",
        "WISE_FRAGMENT": "Wise Dragon Fragment",
        "COBBLESTONE": "Cobblestone",
        "REFINED_MITHRIL": "Refined Mithril",
        "SPIDER_EYE": "Spider Eye",
        "RAW_FISH": "Raw Fish",
        "ENCHANTED_PUFFERFISH": "Enchanted Pufferfish",
        "POTATO_ITEM": "Potato",
        "ENCHANTED_HUGE_MUSHROOM_1": "Enchanted Brown Mushroom Block",
        "REFINED_DIAMOND": "Refined Diamond",
        "ENCHANTED_COBBLESTONE": "Enchanted Cobblestone",
        "TIGHTLY_TIED_HAY_BALE": "Tightly-Tied Hay Bale",
        "ENCHANTED_HUGE_MUSHROOM_2": "Enchanted Red Mushroom Block",
        "ICE_BAIT": "Ice Bait",
        "PORK": "Raw Porkchop",
        "PRISMARINE_CRYSTALS": "Prismarine Crystals",
        "ICE": "Ice",
        "TIGER_SHARK_TOOTH": "Tiger Shark Tooth",
        "HUGE_MUSHROOM_1": "Brown Mushroom Block",
        "HUGE_MUSHROOM_2": "Red Mushroom Block",
        "LOG_2:1": "Dark Oak Wood",
        "ENCHANTED_SNOW_BLOCK": "Enchanted Snow Block",
        "GOLDEN_TOOTH": "Golden Tooth",
        "HYPER_CATALYST": "Hyper Catalyst",
        "STRING": "String",
        "RABBIT_FOOT": "Rabbit's Foot",
        "REDSTONE": "Redstone",
        "JERRY_BOX_GOLDEN": "Golden Jerry Box",
        "PUMPKIN_GUTS": "Pumpkin Guts",
        "ENCHANTED_CACTUS_GREEN": "Enchanted Cactus Green",
        "BOOSTER_COOKIE": "Booster Cookie",
        "ENCHANTED_CARROT_ON_A_STICK": "Was Temporarily: Enchanted Carrot on a Stick",
        "ENCHANTED_LAPIS_LAZULI_BLOCK": "Enchanted Lapis Block",
        "ENCHANTED_ENDSTONE": "Enchanted End Stone",
        "ENCHANTED_COOKIE": "Enchanted Cookie",
        "ENCHANTED_SAND": "Enchanted Sand",
        "COLOSSAL_EXP_BOTTLE": "Colossal Experience Bottle",
        "ENCHANTED_STRING": "Enchanted String",
        "STRONG_FRAGMENT": "Strong Dragon Fragment",
        "SLIME_BALL": "Slimeball",
        "SNOW_BALL": "Snowball",
        "HOLY_FRAGMENT": "Holy Dragon Fragment",
        "ENCHANTED_ACACIA_LOG": "Enchanted Acacia Wood",
        "ENCHANTED_EGG": "Enchanted Egg",
        "SAND": "Sand",
        "SOUL_FRAGMENT": "Soul Fragment",
        "RAW_CHICKEN": "Raw Chicken",
        "ANCIENT_CLAW": "Ancient Claw",
        "ENCHANTED_LAPIS_LAZULI": "Enchanted Lapis Lazuli",
        "ENCHANTED_GHAST_TEAR": "Enchanted Ghast Tear",
        "ENCHANTED_COCOA": "Enchanted Cocoa Bean",
        "CARROT_BAIT": "Carrot Bait",
        "SEEDS": "Seeds",
        "ENCHANTED_LEATHER": "Enchanted Leather",
        "ENCHANTED_SHARK_FIN": "Enchanted Shark Fin",
        "ENCHANTED_SPONGE": "Enchanted Sponge",
        "HAY_BLOCK": "Hay Bale",
        "FLINT": "Flint",
        "INK_SACK": "Ink Sack",
        "ENCHANTED_ROTTEN_FLESH": "Enchanted Rotten Flesh",
        "WOLF_TOOTH": "Wolf Tooth",
        "ENCHANTED_SPRUCE_LOG": "Enchanted Spruce Wood",
        "ENCHANTED_GRILLED_PORK": "Enchanted Grilled Pork",
        "ENCHANTED_NETHER_STALK": "Enchanted Nether Wart",
        "ENCHANTED_REDSTONE_BLOCK": "Enchanted Redstone Block",
        "ENCHANTED_QUARTZ_BLOCK": "Enchanted Quartz Block",
        "ENCHANTED_ANCIENT_CLAW": "Enchanted Ancient Claw",
        "GREEN_CANDY": "Green Candy",
        "ENCHANTED_REDSTONE": "Enchanted Redstone",
        "ENCHANTED_REDSTONE_LAMP": "Enchanted Redstone Lamp",
        "GREAT_WHITE_SHARK_TOOTH": "Great White Shark Tooth",
        "GRAVEL": "Gravel",
        "MELON": "Melon",
        "ENCHANTED_LAVA_BUCKET": "Enchanted Lava Bucket",
        "ENCHANTED_PACKED_ICE": "Enchanted Packed Ice",
        "RAW_FISH:3": "Pufferfish",
        "ENCHANTED_PRISMARINE_SHARD": "Enchanted Prismarine Shard",
        "RECOMBOBULATOR_3000": "Recombobulator 3000",
        "ENCHANTED_IRON_BLOCK": "Enchanted Iron Block",
        "ENCHANTED_CARROT_STICK": "Enchanted Carrot on a Stick",
        "BONE": "Bone",
        "RAW_FISH:2": "Clownfish",
        "RAW_FISH:1": "Raw Salmon",
        "REVENANT_FLESH": "Revenant Flesh",
        "ENCHANTED_GLOWSTONE": "Enchanted Glowstone",
        "ENCHANTED_PORK": "Enchanted Pork",
        "FEATHER": "Feather",
        "NETHERRACK": "Netherrack",
        "WHALE_BAIT": "Whale Bait",
        "SPONGE": "Sponge",
        "BLAZE_ROD": "Blaze Rod",
        "ENCHANTED_DARK_OAK_LOG": "Enchanted Dark Oak Wood",
        "YOUNG_FRAGMENT": "Young Dragon Fragment",
        "ENCHANTED_CLOWNFISH": "Enchanted Clownfish",
        "REFINED_MINERAL": "Refined Mineral",
        "ENCHANTED_GOLD": "Enchanted Gold",
        "ENCHANTED_RAW_CHICKEN": "Enchanted Raw Chicken",
        "ENCHANTED_WATER_LILY": "Enchanted Lily Pad",
        "LOG:1": "Spruce Wood",
        "TITANIUM_ORE": "Titanium",
        "BLUE_SHARK_TOOTH": "Blue Shark Tooth",
        "CATALYST": "Catalyst",
        "LOG:3": "Jungle Wood",
        "LOG:2": "Birch Wood",
        "BLESSED_BAIT": "Blessed Bait",
        "ENCHANTED_GLOWSTONE_DUST": "Enchanted Glowstone Dust",
        "ENCHANTED_INK_SACK": "Enchanted Ink Sack",
        "ENCHANTED_CACTUS": "Enchanted Cactus",
        "ENCHANTED_SUGAR_CANE": "Enchanted Sugar Cane",
        "ENCHANTED_COOKED_SALMON": "Enchanted Cooked Salmon",
        "ENCHANTED_SEEDS": "Enchanted Seeds",
        "LOG": "Oak Wood",
        "JACOBS_TICKET": "Jacob's Ticket",
        "ENCHANTED_BONE_BLOCK": "Enchanted Bone Block",
        "GHAST_TEAR": "Ghast Tear",
        "UNSTABLE_FRAGMENT": "Unstable Dragon Fragment",
        "ENCHANTED_ENDER_PEARL": "Enchanted Ender Pearl",
        "PURPLE_CANDY": "Purple Candy",
        "ENCHANTED_FERMENTED_SPIDER_EYE": "Enchanted Fermented Spider Eye",
        "POLISHED_PUMPKIN": "Polished Pumpkin",
        "SPIKED_BAIT": "Spiked Bait",
        "ENCHANTED_GOLD_BLOCK": "Enchanted Gold Block",
        "ENCHANTED_JUNGLE_LOG": "Enchanted Jungle Wood",
        "ENCHANTED_FLINT": "Enchanted Flint",
        "IRON_INGOT": "Iron Ingot",
        "ENCHANTED_EMERALD_BLOCK": "Enchanted Emerald Block",
        "ENCHANTED_CLAY_BALL": "Enchanted Clay",
        "GLOWSTONE_DUST": "Glowstone Dust",
        "GOLD_INGOT": "Gold Ingot",
        "REVENANT_VISCERA": "Revenant Viscera",
        "TARANTULA_SILK": "Tarantula Silk",
        "TITANIC_EXP_BOTTLE": "Titanic Experience Bottle",
        "ENCHANTED_MUTTON": "Enchanted Mutton",
        "SUPER_COMPACTOR_3000": "Super Compactor 3000",
        "SUPER_EGG": "Super Enchanted Egg",
        "ENCHANTED_IRON": "Enchanted Iron",
        "STOCK_OF_STONKS": "Stock of Stonks",
        "MITHRIL_ORE": "Mithril",
        "ENCHANTED_HAY_BLOCK": "Enchanted Hay Bale",
        "ENCHANTED_PAPER": "Enchanted Paper",
        "ENCHANTED_TITANIUM": "Enchanted Titanium",
        "ENCHANTED_BONE": "Enchanted Bone",
        "ENCHANTED_DIAMOND_BLOCK": "Enchanted Diamond Block",
        "SPOOKY_BAIT": "Spooky Bait",
        "SUPERIOR_FRAGMENT": "Superior Dragon Fragment",
        "EMERALD": "Emerald",
        "ENCHANTED_RABBIT_FOOT": "Enchanted Rabbit Foot",
        "LIGHT_BAIT": "Light Bait",
        "HOT_POTATO_BOOK": "Hot Potato Book",
        "ENCHANTED_ICE": "Enchanted Ice",
        "CLAY_BALL": "Clay",
        "OLD_FRAGMENT": "Old Dragon Fragment",
        "GREEN_GIFT": "Green Gift",
        "PACKED_ICE": "Packed Ice",
        "WATER_LILY": "Lily Pad",
        "LOG_2": "Acacia Wood",
        "HAMSTER_WHEEL": "Hamster Wheel",
        "ENCHANTED_OBSIDIAN": "Enchanted Obsidian",
        "ENCHANTED_COAL": "Enchanted Coal",
        "ENCHANTED_QUARTZ": "Enchanted Quartz",
        "COAL": "Coal",
        "ENDER_PEARL": "Ender Pearl",
        "ENCHANTED_COAL_BLOCK": "Enchanted Block of Coal",
        "WEREWOLF_SKIN": "Werewolf Skin",
        "ENCHANTED_PRISMARINE_CRYSTALS": "Enchanted Prismarine Crystals",
        "DAEDALUS_STICK": "Daedalus Stick",
        "ENCHANTED_WET_SPONGE": "Enchanted Wet Sponge",
        "ENCHANTED_RAW_FISH": "Enchanted Raw Fish",
        "ENDER_STONE": "End Stone",
        "QUARTZ": "Nether Quartz",
        "FOUL_FLESH": "Foul Flesh",
        "RAW_BEEF": "Raw Beef",
        "JERRY_BOX_PURPLE": "Purple Jerry Box",
        "ENCHANTED_EYE_OF_ENDER": "Enchanted Eye of Ender",
        "ECTOPLASM": "Ectoplasm",
        "SUGAR_CANE": "Sugar Cane",
        "MAGMA_CREAM": "Magma Cream",
        "SHARK_BAIT": "Shark Bait",
        "RED_GIFT": "Red Gift",
        "ENCHANTED_MITHRIL": "Enchanted Mithril",
        "JERRY_BOX_BLUE": "Blue Jerry Box",
        "ENCHANTED_RAW_BEEF": "Enchanted Raw Beef",
        "ENCHANTED_FEATHER": "Enchanted Feather",
        "ENCHANTED_SLIME_BLOCK": "Enchanted Slime Block",
        "ENCHANTED_OAK_LOG": "Enchanted Oak Wood",
        "RABBIT_HIDE": "Rabbit Hide",
        "WHITE_GIFT": "White Gift",
        "RABBIT": "Raw Rabbit",
        "SULPHUR": "Gunpowder",
        "DARK_BAIT": "Dark Bait",
        "NETHER_STALK": "Nether Wart",
        "ENCHANTED_CARROT": "Enchanted Carrot",
        "ENCHANTED_PUMPKIN": "Enchanted Pumpkin",
        "GRIFFIN_FEATHER": "Griffin Feather",
        "ROTTEN_FLESH": "Rotten Flesh",
        "ENCHANTED_COOKED_FISH": "Enchanted Cooked Fish",
        "OBSIDIAN": "Obsidian",
        "MINNOW_BAIT": "Minnow Bait",
        "ENCHANTED_MAGMA_CREAM": "Enchanted Magma Cream",
        "ENCHANTED_FIREWORK_ROCKET": "Enchanted Firework Rocket",
        "STARFALL": "Starfall",
        "LEATHER": "Leather",
        "ENCHANTED_COOKED_MUTTON": "Enchanted Cooked Mutton",
        "REFINED_TITANIUM": "Refined Titanium",
        "ENCHANTED_RABBIT": "Enchanted Raw Rabbit",
        "MUTANT_NETHER_STALK": "Mutant Nether Wart",
        "ENCHANTED_BREAD": "Enchanted Bread",
        "FUMING_POTATO_BOOK": "Fuming Potato Book",
        "ENCHANTED_CHARCOAL": "Enchanted Charcoal",
        "ENCHANTED_BLAZE_POWDER": "Enchanted Blaze Powder",
        "SUMMONING_EYE": "Summoning Eye",
        "FISH_BAIT": "Fish Bait",
        "SNOW_BLOCK": "Snow Block",
        "ENCHANTED_BAKED_POTATO": "Enchanted Baked Potato",
        "COMPACTOR": "Compactor",
        "ENCHANTED_DIAMOND": "Enchanted Diamond"
    }

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
            totalSale = data[product]['sellPrice'] * BUYCAP
            product = scuffNames[product]
            totalCost = sellerItems[product]["vendorCost"] * BUYCAP
            finalData.update({product: {"buyFor": totalCost, "sellFor": totalSale, "profit": totalSale - totalCost}})
        elif product in sellerItems:
            if product == "IRON_INGOT" or product == "GOLD_INGOT":
                totalCost = sellerItems[product]["vendorCost"] * 1280
                totalSale = data[product]['sellPrice'] * 1280
                finalData.update({product: {"buyFor": totalCost,
                                            "sellFor": totalSale,
                                            "profit": totalSale - totalCost}})
            else:
                totalCost = sellerItems[product]["vendorCost"] * BUYCAP
                totalSale = data[product]['sellPrice'] * BUYCAP
                finalData.update(
                    {product: {"buyFor": totalCost,
                               "sellFor": totalSale,
                               "profit": totalSale - totalCost}})

    return finalData


'''
Made to help people with minion mules,
Gives you information on whether its more profit to vendor the minion items or post on the bazaar.
Returns A dictionary; NOTE The product name is the key for each entry

item: {"instaSell": Estimated price to sell Instantly on the bazaar, 
        "slowSell": Estimated price when slow selling on the bazaar,
        "vendorSell": Guaranteed profit selling to the in-game NPC Vendors.}
'''


def merchant_minion_shuffle(data: dict) -> dict:
    minionItems = {"SNOW_BALL": 1, "ENCHANTED_SNOW_BLOCK": 600,
                   "DIAMOND": 8, "ENCHANTED_DIAMOND": 1280,
                   "CLAY_BALL": 3, "ENCHANTED_CLAY_BALL": 480}
    finalResults = {}
    for item in minionItems:
        if item in data:
            instaSell = data[item]["sellPrice"]
            slowSell = data[item]["buyPrice"]
            vendorSell = minionItems[item]
            finalResults.update({item: {"instaSell": instaSell, "slowSell": slowSell,
                                        "vendorSell": vendorSell}})
    return finalResults


'''
Gathers all of the auctions on the Hypixel Auction house Requires your API_KEY
Returns a dictionary KEY is the page Number 
'auctions' is all of the auctions from that page.
'''


def gather_pages(API_KEY: str) -> dict:
    buyData = {}
    data = requests.get("https://api.hypixel.net/skyblock/auctions?key=" + API_KEY).json()
    totalPages = data['totalPages']
    for page in range(totalPages + 1):
        data = requests.get("https://api.hypixel.net/skyblock/auctions?page=" + str(page) + "&key=" + API_KEY).json()
        auctions = data['auctions']
        buyData.update({page: auctions})

    return buyData


'''
Used to clean the DateTime on the Data
Helpful to keep things uniform and 'pretty'
'''


def clean_times(milliseconds: int or str) -> str:
    millis = int(milliseconds)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24
    return "%d:%d:%d" % (hours, minutes, seconds)


'''
Determines whether an item is currently reforged or not (The 'LORE' portion of each Auction is hideous from the API)
Returns the name (uppercase) of the reforge OR that the item is 'Not Reforged'
'''


def get_reforge(extra: str) -> dict or str:
    reforgeDict = {'gentle': ['Weapons', "bad"], 'odd': ["Weapons", "bad"], 'fast': ["Weapons", "bad"],
                   'fair': ["Weapons", "bad"], 'epic': ["Weapons", "eh"], 'sharp': ["Weapons", "eh"],
                   'heroic': ["Weapons", "eh"], 'spicy': ["Weapons", "good"], 'legendary': ["Weapons", "eh"],
                   'fabled': ["Unique Weapons", "idk"], 'suspicious': ["Unique Weapons", "idk"],
                   'gilded': ["Unique Weapons", "idk"], 'salty': ["Unique Fishing Rod", "idk"],
                   'treacherous': ["Unique Fishing Rod", "idk"], 'deadly': ["Ranged", "idk"], 'fine': ["Ranged", "idk"],
                   'grand': ["Ranged", "idk"], 'hasty': ["Ranged", "idk"], 'neat': ["Ranged", "idk"],
                   'rapid': ["Ranged", "idk"], 'unreal': ["Ranged", "idk"], 'awkward': ["Ranged", "idk"],
                   'rich': ["Ranged", "idk"], 'precise': ["Unique Ranged", "idk"],
                   'spiritual': ["Unique Ranged", "idk"], 'clean': ["Armor", "idk"], 'fierce': ["Armor", "idk"],
                   'heavy': ["Armor", "idk"], 'light': ["Armor", "idk"], 'mythic': ["Armor", "idk"],
                   'pure': ["Armor", "idk"], 'smart': ["Armor", "idk"], 'titanic': ["Armor", "idk"],
                   'wise': ["Armor", "idk"], 'perfect': ["Unique Armor", "idk"], 'necrotic': ["Unique Armor", "idk"],
                   'spiked': ["Unique Armor", "idk"], 'renowned': ["Unique Armor", "idk"],
                   'cubic': ["Unique Armor", "idk"], 'warped': ["Unique Armor", "idk"],
                   'reinforced': ["Unique Armor", "idk"], 'loving': ["Unique Armor", "idk"],
                   'ridiculous': ["Unique Armor", "idk"], 'godly': ["Armor", "idk"]}

    d = extra.split(" ")[0].lower()
    if d in reforgeDict.keys():
        return d.upper()
    else:
        return "Not Reforged"


'''
Munges an auctions data and determines from the "Lore" feature of each auction what enchants are on it.
This part is ugly I tried to make it clean looking, but there is only so much that could be done.

Returns a list of all enchants on an item

'''


def get_enchants(itemLore: str) -> list:
    romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
    enchants = []
    splitLore = (itemLore.split("§"))

    for index in splitLore:
        for k in romanNumerals:
            if k in index and "9" in index:
                index = index.replace(",", "")
                index = index.replace("9", "")
                ench = index

                if ench[-1] == " " and ench not in enchants:
                    enchants.append(ench[0:-2].rstrip("\n"))
                else:
                    if ench not in enchants:
                        enchants.append(ench.rstrip("\n"))

    return enchants


'''
Requests AH Data from the API (REQUIRES your API KEY currently)

Gathers are important information about each item. SUPPORTS only BUY IT NOW for now, Low bid items are bid up too fast.

Returns a dictionary; NOTE Key is just the count of the item parsed.
count: {'bin': 1 ALWAYS TRUE only Buy it Now is currently supported AH bids are bid up too fast to be worth checking. 
        'auctionStart': Time the auction started. 
        'auctionEnd': Time the auction will end.
        'uuid': User id that is selling the item.
        'profileId': Profile ID that is selling the item.
        'itemName': Name of the item being sold.
        'category': Category the item resides in (Enchant, Weapon, Armor etc.) 
        'tier': Tier of the item (Legendary, Rare etc..) 
        'itemStars': Upgrades to an item up to 5 stars in game.
        'enchants': Enchants that are on the item.
        'reforge': Reforge that is on an item.
        'itemCost': The current cost to purchase the item.}
'''


def gather_auction_data(API_KEY: str) -> dict:
    dirty_data = {}
    data = requests.get("https://api.hypixel.net/skyblock/auctions?key=" + API_KEY).json()
    totalPages = data['totalPages']
    for page in range(totalPages + 1):
        data = requests.get("https://api.hypixel.net/skyblock/auctions?page=" + str(page) + "&key=" + API_KEY).json()
        auctions = data['auctions']
        dirty_data.update({page: auctions})

    # Stops unnecessary parsing and only checks for enchants/reforges on items that can actually have them applied.
    enchantCategories = ['armor', 'weapon', 'consumables']

    reforgeCategories = ['armor', 'weapon', 'accessories']
    # Used as the key for each item I used it to see total items, and never changed it.
    count = 0
    auctions = {}

    for page in dirty_data:
        for item in dirty_data[page]:

            itemCost = item['starting_bid']
            auctionStart = clean_times(item['start'])
            auctionEnd = clean_times(item['end'])
            uuid = item['uuid']
            profileId = item['profile_id']
            itemName = item['item_name']
            category = item['category']
            tier = item['tier']
            itemLore = item['item_lore']
            extra = item['extra']

            if category in enchantCategories:
                enchants = get_enchants(itemLore)
            else:
                enchants = 0

            if category in reforgeCategories:
                reforge = get_reforge(extra)
            else:
                reforge = 0
            # checks for foreign characters in the lore for each item (the api gets ALL data from the AH)
            # Some items sold by a russian user are posted in russian, same for Japanese ETC.
            if "◆" in itemName:
                itemName = itemName[2:]
            elif itemName.isascii() is False:
                itemName = "Enchanted Book"
            # Get the upgrade count on an item.
            if "✪" in itemName:
                itemStars = itemName.count("✪")
                itemName = itemName[:-itemStars - 1]
            else:
                itemStars = 0
            # Only appends item if it is a Buy it Now auction.
            if 'bin' in item:
                auctions.update({count: {'bin': 1, 'auctionStart': auctionStart, 'auctionEnd': auctionEnd,
                                         'uuid': uuid, 'profileId': profileId, 'itemName': itemName,
                                         'category': category, 'tier': tier, 'itemStars': itemStars,
                                         'enchants': enchants, 'reforge': reforge, 'itemCost': itemCost}})
                count += 1

    return auctions


'''
Saves the AH Data (I personally save AH data every 5-7minutes and drop duplicate data later on.)
'''


def save_auction_data(data: dict) -> None:
    try:
        file = csv.writer(open("auctionData.csv", "a+", newline='', encoding='utf-8'))

        for k, v in data.items():
            file.writerow([v['bin'], v['auctionStart'], v['auctionEnd'], v['uuid'], v['profileId'], v['itemName'],
                           v['category'], v['tier'], v['itemStars'], v['enchants'], v['reforge'], v['maxBid'],
                           v['itemCost']])

    # First time saving AH Data? Let's create the file.
    except FileNotFoundError:
        file = open('auctionData.csv', 'w')
        file.close()
        save_auction_data(data)


'''
Used to find desirable enchanted books.
'''


def check_books(data: dict) -> list:
    books = []

    for k in data:
        if data[k]["category"] == "consumables":
            books.append(data[k])

    return books


'''
Takes in book data and a list of enchants you want

returns a list of the enchant and it's cost on the Auction House currently.

Kind of hacky approach, but there are not  >20 enchants so the item is skipped over entirely.
'''


def find_books(book_data: dict, requestedEnchants: list) -> dict:
    requestedBooks = {}

    for book in book_data:

        count = 0
        if book["enchants"] != 0:

            for ench in book["enchants"]:

                if ench in requestedEnchants:
                    count += 1
                else:
                    count = -20

                if count == 1 and ench not in requestedBooks:
                    requestedBooks.update({ench: [book["itemCost"]]})

                elif count == 1 and ench in requestedBooks:
                    requestedBooks[ench].append(book["itemCost"])

    return requestedBooks
