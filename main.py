import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pymongo
import configparser
import logging
import re
from mapping_enum import *

config = configparser.ConfigParser()
config.read("config.ini")
connStr = config.get("database", "connStr")

logging.basicConfig(filename=config.get("logging", "filename"),
                    encoding='utf-8',
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

baseurl = "https://bet.hkjc.com/football/odds/odds_{}.aspx?lang=en&tournid={}"


def start():
    client = pymongo.MongoClient(connStr, serverSelectionTimeoutMS=10000)
    db = client["football-betting"]
    collection = db["odds"]

    try:
        logging.info("Connected to DB server: " + client.server_info())
    except Exception:
        logging.error("Unable to connect to the server.")

    urls = [baseurl.format(OddTypeEnum.HomeAwayDraw.value, CompetitionEnum.UEChampions.value)]
    odds = []

    for url in urls:
        try:
            logging.info("start scrapping data from url: " + url)

            oddType = re.findall("odds_[a-z]{3}", url)[0].lstrip("odds_")

            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.maximize_window()
            driver.get(url)
            time.sleep(0.5)

            dates = driver.find_elements(By.CLASS_NAME, "couponTable")
            for date in dates:
                events = date.text.split("\n")
                competition = events[0]
                for i in range(1, len(events)):
                    information = events[i].split(' ')
                    sellingDate = datetime.datetime.strptime(information[0], "%d/%m/%Y").strftime("%Y-%m-%d")
                    sellingTime = datetime.datetime.strptime(information[1], "%H:%M").strftime("%H:%M:%S")
                    expectedStopSellingTime = datetime.datetime.strptime("{0}T{1}.000Z".format(sellingDate, sellingTime),
                                                                         "%Y-%m-%dT%H:%M:%S.000Z")

                    if oddType in [OddTypeEnum.HomeAwayDraw.value, OddTypeEnum.HandicapHAD.value]:
                        teams = " ".join(information[3:-3]).split("vs")

                        odds.append(
                            {
                                "type": oddType,
                                "competition": competition,
                                "expectedStopSellingTime": expectedStopSellingTime,
                                "eventId": information[2],
                                "home": teams[0].strip(),
                                "away": teams[1].strip(),
                                "homeOdd": information[-3],
                                "drawOdd": information[-2],
                                "awayOdd": information[-1],
                                "createdAt": datetime.datetime.now()
                            }
                        )
                    elif oddType == OddTypeEnum.Handicap.value:
                        teams = " ".join(information[3:-2]).split("vs")

                        odds.append(
                            {
                                "type": oddType,
                                "competition": competition,
                                "expectedStopSellingTime": expectedStopSellingTime,
                                "eventId": information[2],
                                "home": teams[0].strip(),
                                "away": teams[1].strip(),
                                "homeOdd": information[-2],
                                "awayOdd": information[-1],
                                "createdAt": datetime.datetime.now()
                            }
                        )
                    elif oddType == OddTypeEnum.HiLo.value:
                        logging.info(OddTypeEnum.HiLo.value)
                        # not yet ready
        except Exception as ex:
            logging.error(ex)
        finally:
            driver.quit()

    logging.info("insert scrapped data to: " + collection.name)
    if odds == [] or len(odds) == 0:
        logging.warning("empty odd list")
    else:
        logging.info(odds)
        collection.insert_many(odds)


if __name__ == '__main__':
    start()


