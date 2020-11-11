import requests
import time
import csv


def gather_page_amount(API_KEY):
    buyData = {}
    data = requests.get("https://api.hypixel.net/skyblock/auctions?key=" + API_KEY).json()
    totalPages = data['totalPages']
    for page in range(totalPages+1):
        data = requests.get("https://api.hypixel.net/skyblock/auctions?page=" + str(page) + "&key=" + API_KEY).json()
        auctions = data['auctions']
        buyData.update({page: auctions})

    return buyData


def cleanTimes(milliseconds):
    millis = int(milliseconds)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24
    return "%d:%d:%d" % (hours, minutes, seconds)


def getReforge(extra):
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


def getEnchants(itemLore):
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


def gatherAuctionData(dirty_data):

    enchantCategories = ['armor', 'weapon', 'consumables']
    reforgeCategories = ['armor', 'weapon', 'accessories']
    count = 0
    auctions = {}

    for page in dirty_data:
        for item in dirty_data[page]:

            itemCost = item['starting_bid']
            auctionStart = cleanTimes(item['start'])
            auctionEnd = cleanTimes(item['end'])
            uuid = item['uuid']
            profileId = item['profile_id']
            itemName = item['item_name']
            category = item['category']
            tier = item['tier']
            itemLore = item['item_lore']
            extra = item['extra']

            if category in enchantCategories:
                enchants = getEnchants(itemLore)
            else:
                enchants = 0

            if category in reforgeCategories:
                reforge = getReforge(extra)
            else:
                reforge = 0

            if "◆" in itemName:
                itemName = itemName[2:]
            elif itemName.isascii() is False:
                itemName = "Enchanted Book"

            if "✪" in itemName:
                itemStars = itemName.count("✪")
                itemName = itemName[:-itemStars-1]
            else:
                itemStars = 0

            if 'bin' in item:
                auctions.update({count: {'bin': 1, 'auctionStart': auctionStart, 'auctionEnd': auctionEnd,
                                         'uuid': uuid, 'profileId': profileId, 'itemName': itemName,
                                         'category': category, 'tier': tier, 'itemStars': itemStars,
                                         'enchants': enchants, 'reforge': reforge, 'itemCost': itemCost}})
                count += 1



    return auctions


def saveAuctionData(data):
    file = csv.writer(open("auctionData.csv", "a+", newline='', encoding='utf-8'))

    for k, v in data.items():

        file.writerow([v['bin'], v['auctionStart'], v['auctionEnd'], v['uuid'], v['profileId'], v['itemName'],
                       v['category'], v['tier'], v['itemStars'], v['enchants'], v['reforge'], v['maxBid'],
                       v['itemCost']])

    print("Done Updating CSV.")


def checkBooks(data):
    books = []

    for k in data:
        if data[k]["category"] == "consumables":
            books.append(data[k])

    return books


def findBooks(book_data, requestedEnchants):

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
