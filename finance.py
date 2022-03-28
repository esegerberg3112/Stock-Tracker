# module to handle returning Financial data from Yahoo Finance based on user input/searches

import requests
import json
import sys
import re

# function to return headers JSON object for Yahoo finance API calls
# storing API key outside of program on local computer
def get_headers():
    file_path = "/Users/esegerberg/PycharmProjects/Stock Tracker/yahoo_api.json"
    try:
        with open(file_path, 'r') as file:
            api_keys = json.loads(file.read())

    # catch an error here if can't find file or not valid JSON
    except (ValueError, OSError):
        print("There was an issue reading in the API Key file:" + file_path)
        sys.exit()

    header = {
        'x-api-key': api_keys['YAHOO_KEY']
    }
    return header

# function to return financial info about a given stock ticker
def get_quote(tickr):
    # remove any special characters or numbers or spaces from search
    search = re.sub('[^A-Za-z]+', '', tickr)

    # define parameters for API call
    base_url = "https://yfapi.net/v6/finance/quote"
    query = {
        "symbols": search
    }
    headers = get_headers()

    # make request, save desired output in a JSON object
    response = requests.request("GET", base_url, headers=headers, params=query)
    output = json.loads(response.text)
    result = output['quoteResponse']['result']
    # return None if ticker doesn't exist
    if not result:
        return None

    # need to catch if tickr has not bid price
    try:
        result[0]['bid']
    except KeyError:
        return None

    response_obj = {
        "currentPrice": result[0]['bid'],
        "lastClose": result[0]['regularMarketPreviousClose'],
        "analystRating": result[0]['averageAnalystRating'],
        "percentChangeSinceClose": round(((int(result[0]['bid']) - int(
            result[0]['regularMarketPreviousClose'])) / int(
            result[0]['regularMarketPreviousClose'])) * 100, 2),
        "companyName": result[0]['shortName']
    }
    return response_obj

# function to get insights for a given stock sticker
def get_insights(tickr):
    return