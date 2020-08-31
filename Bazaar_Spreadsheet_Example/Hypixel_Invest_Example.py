import gspread
import time
from datetime import datetime
import HypixelBazaar
import sys

'''
Updates all product data on google spreadsheet.
Limit 100 Writes per 100 seconds, so we cap it to 50 viable investments and 15 possible market crashes.
takes the newestData (currentData), crashData(getCrashData) and the location of our google spreadsheet api "###.json"
'''


def updateShuffleSheet(newData, gsheetAPI, sheetName):
    # Create connection to Google Spreadsheet api
    gc = gspread.service_account(gsheetAPI)
    # Name of the sheet we want to interact with.
    wks = gc.open(sheetName).get_worksheet(3)
    # Updating the "Last Updated" date time in the sheet.
    wks.update('A1', [['Spreadsheet Last Updated ', str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" EST"]])

    n = 4

    gc.login()
    for prod in newData:
        product = prod[0]
        buyFor = prod[1]["buyFor"]
        sellFor = prod[1]["sellFor"]
        profit = prod[1]["profit"]

        wks.update('A'+str(n)+":D"+str(n), [[product, (round(buyFor, 2)),
                                             round(sellFor, 2),
                                             round(profit, 2)]])
        n += 1
    print("Done with Merchant Shuffles")


def updateInsightGoogleSheet(insight, gsheetAPI, sheetName):
    gc = gspread.service_account(gsheetAPI)
    # Name of the sheet we want to interact with.
    wks = gc.open(sheetName).get_worksheet(2)
    # Updating the "Last Updated" date time in the sheet.

    gc.login()
    n = 2
    wks.update('A1', [['Spreadsheet Last Updated ', str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " EST"]])
    for k in insight:

        products = k['insight']
        entireCost = k['entireCost']
        entireSoldFor = k['entireSoldFor']
        playerAmount = k['playerAmount']

        n += 1
        wks.update('I' + str(n) + ":L" + str(n), [[(round(entireCost)),
                                                   (round(entireSoldFor)),
                                                   (round(entireSoldFor - entireCost, 2)),
                                                   playerAmount]])
        for product in products:

            wks.update('A' + str(n) + ":H" + str(n), [[product, (products[product]['itemQuantity']),
                                                       (round(products[product]['totalCost'])),
                                                       (round(products[product]['totalSold'])),
                                                       (round(products[product]['totalProfit'])),
                                                       (products[product]['productWeight']),
                                                       (products[product]['sellMovingWeek']),
                                                       (products[product]['buyMovingWeek'])]])

            n += 1

        n += 2

    print("Finished Updating Insights")


def updateCrashesGoogleSheet(crashData, gsheetAPI, sheetName):
    gc = gspread.service_account(gsheetAPI)
    # Name of the sheet we want to interact with.
    wks = gc.open(sheetName).get_worksheet(1)
    # Updating the "Last Updated" date time in the sheet.

    gc.login()
    wks.update('A1', [['Spreadsheet Last Updated ', str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + " EST"]])

    n = 3
    for crashIndex in crashData:
        for crash in crashIndex:

            wks.update('A' + str(n) + ":F" + str(n), [[crash[0], round(crash[4], 2), round(crash[3], 2),
                                                       str(round(crash[5] * 100, 3)) + "%",
                                                       str(round(crash[1] * 100, 3)) + "%",
                                                       str(round(crash[2] * 100, 3)) + "%"]])
            n += 1

        # Wipes old crash data that may be sitting in the spreadsheet.
        while n <= 15:
            wks.update('A' + str(n) + ":F" + str(n), [['', '', '', '', '', '']])
            n += 1

    print("Done with updating Crashes")


def updateGoogleSheet(newData, gsheetAPI, sheetName):
    # Create connection to Google Spreadsheet api
    gc = gspread.service_account(gsheetAPI)
    # Name of the sheet we want to interact with.
    wks = gc.open(sheetName).get_worksheet(0)
    # Updating the "Last Updated" date time in the sheet.
    wks.update('A1', [['Spreadsheet Last Updated ', str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" EST"]])

    n = 2
    count = 0
    gc.login()
    for product in newData:
        if product[1]['reliability'] >= 7 and count <= 40 and product[1]['RoI'] >= 2:
            count += 1
            n += 1

            wks.update('A'+str(n)+":J"+str(n), [[product[0], (round(product[1]['RoI'], 2)/100),
                                                 round(product[1]['margin'], 2),
                                                 float(product[1]['reliability']), round(product[1]['buyPrice'], 2),
                                                 round(product[1]['sellPrice'], 2), product[1]['buyOrders'],
                                                 product[1]['sellOrders'], product[1]['sellMovingWeek'],
                                                 product[1]['buyMovingWeek']]])

    # Wipes old investment data that may be sitting in the spreadsheet.
    while n <= 55:
        n += 1
        wks.update('A'+str(n)+":J"+str(n), [['', '', '', '', '', '', '', '', '', '']])

    # Add percentage format to a column I needed it for, you can do this within google spreadsheets manually.
    wks.format("B3:B53", {"numberFormat": {"type": "PERCENT"}})
    print("Done with Investments")


'''
finally, the example of it all working, I do not have user input as this was intended to be a script used on one rig
and have the information posted to a public interface(Google Spreadsheets or Possibly Discord, etc.)
'''


def main(count):
    with open('env.txt', 'r') as file:
        line = file.readline()
        line = eval(line)
        API_KEY = line["API_KEY"]
        gsheetAPI1 = line["gsheetAPI1"]
        gsheetAPI2 = line["gsheetAPI2"]
        gsheetAPI3 = line["gsheetAPI3"]
        sheet = "HypixelInvest"
        file.close()

    while True:

        try:

            # Clean the data and create predictions on the data
            currentData = HypixelBazaar.gather_bazaar_data(API_KEY=API_KEY, modelFile="finalized_multiclass_model.sav")

            # Sort the data by margin, change this if you want by changing the string 'margin' to something else
            reliability_sort = HypixelBazaar.sortData(data=currentData, dataFeature='margin')

            # Updates the google sheet based on all of the data above
            updateGoogleSheet(newData=reliability_sort, gsheetAPI=gsheetAPI1, sheetName=sheet)

            # Gather insight and update The insight spreadsheet
            amounts = [10e6, 5e6, 1e6, 500e3, 125e3]
            insightData = []
            for amount in amounts:
                insightData.append(HypixelBazaar.giveInsight(currentData, amount))

            updateInsightGoogleSheet(insight=insightData, gsheetAPI=gsheetAPI2, sheetName=sheet)

            # Gather Merchant data from bazaar and update Merchant Spreadsheet

            testShuffle = HypixelBazaar.sellerShuffle(currentData)

            profitSort = HypixelBazaar.sortData(data=testShuffle, dataFeature="profit")
            updateShuffleSheet(newData=profitSort, gsheetAPI=gsheetAPI3, sheetName=sheet)

            # Saves the currentData in our CrashData file, ensuring it becomes the next "previous" data
            crashes = []
            crashes.append(HypixelBazaar.checkCrashData(currentData))
            HypixelBazaar.saveCrashData(data=currentData)
            count += 1
            time.sleep(80)

            if count % 3 == 0:
                updateCrashesGoogleSheet(crashData=crashes, gsheetAPI=gsheetAPI1, sheetName=sheet)
                crashes = []
                time.sleep(45)

            # Saves data every 10 iterations
            if count % 10 == 0:
                HypixelBazaar.saveBazaarData(currentData)
                time.sleep(40)

            print("Sheet last updated on", datetime.now())

        # Catches the only error we end up hitting, an api error with gspread that randomly occurs (I don't know)
        except:
            print(sys.exc_info())
            time.sleep(60)
            main(count)


# Call main initializing count to 0
main(count=0)
