from __future__ import annotations                  #Implemented in Python 3.10. See: https://stackoverflow.com/a/52631754
import csv
from time import sleep
from datetime import datetime
import requests
import json
import tokens                                       #local file that stores api keys
import twitter                                      #pip install python-twitter

WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

TARGET_TEMP = 69

delay = .25

class City:
    name: str
    temp: float

    def __init__(self, name: str, temp: float) -> None:
        self.name = name
        self.temp = temp

    '''
    Sort from closest to TARGET_TEMP to farthest
    '''
    def __lt__(self, other: City):
        return abs(self.temp - TARGET_TEMP) < abs(other.temp - TARGET_TEMP)

    def __str__(self) -> str:
        return f"{self.name}: {self.temp}"

twttr = twitter.Api(consumer_key=tokens.TWTTR_API_KEY,
                        consumer_secret=tokens.TWTTR_API_SECRET,
                        access_token_key=tokens.TWTTR_USER_TOKEN,
                        access_token_secret=tokens.TWTTR_USER_SECRET)

'''
Send a DM to Admin account notifying them of the error
'''
def LogException(error: Exception, additionalMessage: str = ""):
    now = datetime.now()
    twttr.PostDirectMessage(f"{now}\n\n{error}\n\n{additionalMessage}", tokens.ADMIM_ACCOUNT_ID)

'''
Returns whether temp is equal to the target temp, with given tolerance
'''
def isTargertTemp(temp: float, tolerance: float = 0.5) -> bool:
    return temp > (TARGET_TEMP - tolerance) and temp < (TARGET_TEMP + tolerance)

'''
returns a list of cities where the current temp in Fahrenheit is equal to the target temp
'''
def getMatchingCities() -> list[City]:
    global delay
    matchingCities = []

    with open('cityList.csv') as csvfile:
        reader = csv.reader(csvfile)
        reader.__next__()                                               # skip header row
        for row in reader:
            cityName = row[1]

            try:
                query = {
                    'q': cityName,
                    'key' : tokens.WEATHER_API_TOKEN,
                }
                response = requests.get(WEATHER_API_URL, query)
                response.raise_for_status()
                data = response.json()
                temp = data["current"]["temp_f"]
                print(f"WEATHER API: {cityName}: {temp}")
                if isTargertTemp(temp):
                    matchingCities.append(City(cityName, temp))
            except requests.exceptions.HTTPError as error:
                print("WEATHER API", cityName, error)
            except Exception as error:
                LogException(error, "Probably being rate limited by API. Increasing delay")
                delay += .25

            sleep(delay)                                                  # so the api doesnt get mad

    return matchingCities

def main() -> None:
    try:
        print(twttr.VerifyCredentials())
        matchingCities = getMatchingCities()
        matchingCities.sort()
        print(f"It is currently {TARGET_TEMP} degrees in the following cities")
        for city in matchingCities:
            print(city)

        #tweet the city closest to TARGET_TEMP
        if len(matchingCities) > 0:
            status = twttr.PostUpdate(f"It is currently {TARGET_TEMP} degrees in {matchingCities[0].name}")
            print(status.text)
    except Exception as error:
        LogException(error, "Exception in main")


if __name__ == "__main__":
    main()
else:
    raise ImportError(f"{__file__} must be called directly and not imported")