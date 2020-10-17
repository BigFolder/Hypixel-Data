import HypixelBazaar
import HypixelAuctions


def getCheapestLog(data):
    logs = {}
    scuffNames = {"LOG:1": "Spruce Wood", "LOG:3": "Jungle Wood", "LOG:2": "Birch Wood",
                  "LOG": "Oak Wood", "LOG_2": "Acacia Wood", "LOG_2:1": "Dark Oak Wood"}
    for prod in data:
        if prod in scuffNames:
            logs.update({scuffNames[prod]: data[prod]["sellPrice"]})

    return min(logs.items())


def bazaarPart():
    enchShuffle = {
        "Critical V": {"paper": 48, "ENCHANTED_DIAMOND": 16},
        "Cubism V": {"paper": 48, "PUMPKIN": 64},
        "Ender Slayer V": {"paper": 48, "ENCHANTED_ENDER_PEARL": 16},
        "Execute V": {"paper": 48, "FLINT": 80},
        "Experience III": {"paper": 12, "INK_SACK:4": 4},
        "First Strike IV": {"paper": 24, "ENCHANTED_FLINT": 8},
        "Giant Killer V": {"paper": 48, "GHAST_TEAR": 16},
        "Impaling III": {"paper": 12, "PRISMARINE_SHARD": 40},
        "Lethality V": {"paper": 48, "OBSIDIAN": 48},
        "Looting III": {"paper": 12, "GOLD_INGOT": 72},
        "Life Steal III": {"paper": 48, "GOLD_INGOT": 144, "apple": 2},
        "Luck V": {"paper": 48, "RABBIT_HIDE": 16},
        "Scavenger III": {"paper": 12, "GOLD_INGOT": 4, "stick": 2},
        "Sharpness V": {"paper": 48, "FLINT": 16, "IRON_INGOT": 4, "STRING": 2},
        "Thunderlord V": {"paper": 48, "ENCHANTED_GUNPOWDER": 16},
        "Vampirism V": {"paper": 48, "ENCHANTED_GHAST_TEAR": 16},
        "Protection V": {"paper": 48, "IRON_INGOT": 16},
        "Growth V": {"paper": 48, "ENCHANTED_DARK_OAK_LOG": 16},
        "Power V": {"paper": 48, "BONE": 80},
        "Punch I": {"paper": 6, "SLIME_BALL": 2, "stick": 2, "FEATHER": 2, "FLINT": 2},
        "Infinite Quiver V": {"paper": 48, "stick": 6, "STRING": 6}
    }
    bazaarData = HypixelBazaar.gather_bazaar_data("", modelFile="finalized_multiclass_model.sav")

    scuffNames = {"LOG:1": "Spruce Wood", "LOG:3": "Jungle Wood", "LOG:2": "Birch Wood", "CARROT_ITEM": "Carrot",
                  "LOG": "Oak Wood", "POTATO_ITEM": "Potato", "INK_SACK:3": "Cocoa Bean", "LOG_2": "Acacia Wood",
                  "LOG_2:1": "Dark Oak Wood", "ENDER_STONE": "End Stone", "NETHER_STALK": "Nether Wart",
                  "RAW_FISH:3": "Pufferfish", "RAW_FISH:1": "Raw Salmon", "RAW_FISH:2": "Clownfish", "INK_SACK:4": "Lapis Lazuli"}

    sumCost = {}

    for ench in enchShuffle:
        chantCost = []
        for prod in bazaarData:
            if prod in enchShuffle[ench]:
                if ench in scuffNames:
                    chantCost.append([scuffNames[prod],
                                      round(bazaarData[prod]["sellPrice"] * enchShuffle[ench][prod], 2),
                                      enchShuffle[ench][prod]])
                else:
                    chantCost.append([prod,
                                      round(bazaarData[prod]["sellPrice"] * enchShuffle[ench][prod], 2),
                                      enchShuffle[ench][prod]])

        if "paper" in enchShuffle[ench]:
            chantCost.append(["SUGAR_CANE",
                              round(bazaarData["SUGAR_CANE"]["sellPrice"] * enchShuffle[ench]["paper"], 2),
                              enchShuffle[ench]["paper"]])

        if "stick" in enchShuffle[ench]:
            cheapestLog = getCheapestLog(bazaarData)
            if enchShuffle[ench]["stick"] == 2:
                chantCost.append([cheapestLog[0], round(cheapestLog[1] * 2, 2), 2])
            else:
                chantCost.append([cheapestLog[0], round(cheapestLog[1] * 4, 2), 4])

        if "apple" in enchShuffle[ench]:
            chantCost.append(["apple", 0, 2])

        sumCost.update({ench: chantCost})

    final = {}

    for item in sumCost:
        total = 0

        for prod in sumCost[item]:
            total += prod[1]

        final.update({item: {"items": sumCost[item], "totalCost": round(total, 2)}})

    return final


def auctionPart():
    dirty_data = HypixelAuctions.gather_page_amount(API_KEY="")
    data = HypixelAuctions.gatherAuctionData(dirty_data)

    bookData = HypixelAuctions.checkBooks(data)

    enchShuffle = {
        "Critical V": {"paper": 48, "ENCHANTED_DIAMOND": 16},
        "Cubism V": {"paper": 48, "PUMPKIN": 64},
        "Ender Slayer V": {"paper": 48, "ENCHANTED_ENDER_PEARL": 16},
        "Execute V": {"paper": 48, "FLINT": 80},
        "Experience III": {"paper": 12, "INK_SACK:4": 4},
        "First Strike IV": {"paper": 24, "ENCHANTED_FLINT": 8},
        "Giant Killer V": {"paper": 48, "GHAST_TEAR": 16},
        "Impaling III": {"paper": 12, "PRISMARINE_SHARD": 40},
        "Lethality V": {"paper": 48, "OBSIDIAN": 48},
        "Looting III": {"paper": 12, "GOLD_INGOT": 72},
        "Life Steal III": {"paper": 48, "GOLD_INGOT": 144, "apple": 2},
        "Luck V": {"paper": 48, "RABBIT_HIDE": 16},
        "Scavenger III": {"paper": 12, "GOLD_INGOT": 4, "stick": 2},
        "Sharpness V": {"paper": 48, "FLINT": 16, "IRON_INGOT": 4, "STRING": 2},
        "Thunderlord V": {"paper": 48, "ENCHANTED_GUNPOWDER": 16},
        "Vampirism V": {"paper": 48, "ENCHANTED_GHAST_TEAR": 16},
        "Protection V": {"paper": 48, "IRON_INGOT": 16},
        "Growth V": {"paper": 48, "ENCHANTED_DARK_OAK_LOG": 16},
        "Power V": {"paper": 48, "BONE": 80},
        "Punch I": {"paper": 6, "SLIME_BALL": 2, "stick": 2, "FEATHER": 2, "FLINT": 2},
        "Infinite Quiver V": {"paper": 48, "stick": 6, "STRING": 6}
    }

    requestedEnchants = [ench for ench in enchShuffle]

    myBooks = HypixelAuctions.findBooks(bookData, requestedEnchants)
    # print("Books", len(myBooks))
    finalBooks = {}

    for book in myBooks:
        minPrice = min(myBooks[book])
        avgPrice = round(sum(myBooks[book]) / len(myBooks[book]), 2)

        finalBooks.update({book: {"minPrice": minPrice, "avgPrice": avgPrice}})

    return finalBooks


'''
bzData, item : items is a list of all items needed to craft by name [0] and the total cost[1] and the quantity [2] 
'''


def compareData(bzData, ahData):
    completeData = {}
    for item in bzData:

        if item in bzData and item in ahData:
            minProfit = round(ahData[item]["minPrice"] - bzData[item]["totalCost"], 2)
            #avgProfit = round(ahData[item]["avgPrice"] - bzData[item]["totalCost"], 2)

            completeData.update({item: {"bzCost": bzData[item]["totalCost"],
                                        "ahCost": ahData[item]["minPrice"],
                                        "minProfit": minProfit,
                                        "items": bzData[item]["items"]}})
        else:

            completeData.update({item: {"bzCost": bzData[item]["totalCost"],
                                        "ahCost": "None On the AH",
                                        "items": bzData[item]["items"],
                                        "minProfit": -1}})

    return completeData

