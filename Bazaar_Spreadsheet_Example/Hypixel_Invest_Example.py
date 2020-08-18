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


def updateCrashesGoogleSheet(crashData, gsheetAPI, sheetName):
    gc = gspread.service_account(gsheetAPI)
    # Name of the sheet we want to interact with.
    wks = gc.open(sheetName).sheet1
    # Updating the "Last Updated" date time in the sheet.

    gc.login()
    n = 3
    for crashIndex in crashData:
        for crash in crashIndex:

            wks.update('K' + str(n) + ":P" + str(n), [[crash[0], round(crash[4], 2), round(crash[3], 2),
                                                       str(round(crash[5] * 100, 3)) + "%",
                                                       str(round(crash[1] * 100, 3)) + "%",
                                                       str(round(crash[2] * 100, 3)) + "%"]])
            n += 1

        # Wipes old crash data that may be sitting in the spreadsheet.
        while n <= 15:
            wks.update('K' + str(n) + ":P" + str(n), [['', '', '', '', '', '']])
            n += 1


def updateGoogleSheet(newData, gsheetAPI, sheetName):
    # Create connection to Google Spreadsheet api
    gc = gspread.service_account(gsheetAPI)
    # Name of the sheet we want to interact with.
    wks = gc.open(sheetName).sheet1
    # Updating the "Last Updated" date time in the sheet.
    wks.update('A1', [['Spreadsheet Last Updated ', str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+" EST"]])

    n = 2
    count = 0
    gc.login()
    for product in newData:
        if product[1]['reliability'] >= 1 and count <= 50 and product[1]['RoI'] >= 2:
            count += 1
            n += 1

            wks.update('A'+str(n)+":J"+str(n), [[product[0], (round(product[1]['RoI'], 2)/100),
                                                 round(product[1]['margin'], 2), product[1]['reliability'],
                                                 round(product[1]['buyPrice'], 2), round(product[1]['sellPrice'], 2),
                                                 product[1]['buyOrders'], product[1]['sellOrders'],
                                                 product[1]['sellMovingWeek'], product[1]['buyMovingWeek']]])

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
        gsheetAPI = line["gsheetAPI"]
        sheet = "HypixelInvest"
        file.close()

    while True:

        try:

            # Clean the data and create predictions on the data
            currentData = HypixelBazaar.gather_bazaar_data(API_KEY=API_KEY, modelFile="finalized_model.sav")

            # Sort the data by margin, change this if you want by changing the string 'margin' to something else
            reliability_sort = HypixelBazaar.sortData(data=currentData, dataFeature='margin')

            # Checks the currentData against the previous data to look for massive spikes (Market Crashes)
            crashes = []
            crashes.append(HypixelBazaar.checkCrashData(currentData))
            # Updates the google sheet based on all of the data above
            updateGoogleSheet(newData=reliability_sort, gsheetAPI=gsheetAPI, sheetName=sheet)

            # Increment count since I want to save data about every 20 minutes.
            count += 1

            # Saves the currentData in our CrashData file, ensuring it becomes the next "previous" data
            HypixelBazaar.saveCrashData(data=currentData)
            print("Sheet last updated on", datetime.now())

            if count % 3 == 0:
                updateCrashesGoogleSheet(crashData=crashes, gsheetAPI=gsheetAPI, sheetName=sheet)
                crashes = []

            # If count/10 has no remainder it saves the data.
            if count % 10 == 0:
                HypixelBazaar.saveBazaarData(currentData)
                time.sleep(100)

            else:

                # Rest so we don't hit API limit on google spreadsheets, can be removed if you don't use gspread.
                time.sleep(100)

        # Catches the only error we end up hitting, an api error with gspread that randomly occurs (I don't know)
        except:
            print(sys.exc_info())
            time.sleep(60)
            main(count)


# Call main initializing count to 0
main(count=0)
