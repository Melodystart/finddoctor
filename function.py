from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent
import requests
import urllib.request
from bs4 import BeautifulSoup
from outscraper import ApiClient
from datetime import datetime, timedelta
from dotenv import get_key
import time
from mysql.connector import pooling
import threading
from elasticsearch import Elasticsearch
from function_test import *
import redis
import json
pool = redis.BlockingConnectionPool(timeout=10,host='localhost', port=6379, max_connections=40, decode_responses=True)
r = redis.Redis(connection_pool=pool)

es = Elasticsearch("http://localhost:9200/")

# conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
#     ".env", "password"), host='finddoctor.collqfqpnilo.us-west-2.rds.amazonaws.com', database='finddoctor', pool_name='findConPool', pool_size=17,  auth_plugin='mysql_native_password')

conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
    ".env", "password"), host='localhost', database='finddoctor', pool_name='findConPool', pool_size=17,  auth_plugin='mysql_native_password')

toDay = datetime.today().date()
expiredDay = toDay - timedelta(days=7)  # 設定快取資料期限為7天
selenium_counts = 0


def error(result, message):
    result["error"] = True
    result["message"] = message
    return result


def Review(inputtext, expiredDay):
    def callReviewAPI(place_id, keyword, result):
        api_client = ApiClient(
            api_key=get_key(".env", "review_api_key"))
        results = api_client.google_maps_reviews(
            place_id, reviews_limit=1, reviews_query=keyword, sort="newest", language="zh-TW", region="TW")
        try:
            T3 = time.perf_counter()
            reviews = results[0]["reviews_data"]

            if len(reviews) > 0:
                location = results[0]["name"]
                result["title"] = location

                for i in range(len(reviews)):
                    author = reviews[i]["author_title"]
                    review = reviews[i]["review_text"]
                    review_rating = reviews[i]["review_rating"]
                    review_timestamp = reviews[i]["review_timestamp"]
                    review_until = untilNow(review_timestamp)
                    review_link = reviews[i]["review_link"]

                    item = {}
                    item["location"] = location
                    item["name"] = author
                    item["star"] = review_rating
                    item["when"] = review_until
                    item["review"] = review
                    item["link"] = review_link
                    result["data"].append(item)

                    try:
                        con = conPool.get_connection()
                        cursor = con.cursor()
                        cursor.execute(
                            "INSERT INTO review (doctor, author, star, timestamp, review, link, location ) VALUES (%s, %s,%s, %s, %s,%s,%s)", (inputtext, author, review_rating, review_timestamp, review, review_link, location))
                        con.commit()
                        cursor.close()
                        con.close()
                    except:
                        pass
                T4 = time.perf_counter()

            else:
                T4 = time.perf_counter()
                pass
        except:
            pass

    try:
        keyword = inputtext.split()[0]
        location = inputtext.split()[1]
        query = location
    except:
        keyword = inputtext
        query = inputtext + "醫"

    result = {}
    result["data"] = []

    try:
        con = conPool.get_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT author, star, timestamp, review, link, location FROM review WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
        data = cursor.fetchall()
        cursor.close()
        con.close()
    except:
        pass

    if len(data) != 0:
        for d in data:
            item = {}
            item["name"] = d[0]
            item["star"] = d[1]
            try:
                item["when"] = untilNow(float(d[2]))
            except:
                pass
            item["review"] = d[3]
            item["link"] = d[4]
            item["location"] = d[5]
            result["data"].append(item)
            r.rpush("Review-"+inputtext,json.dumps(item))
        r.expire("Review-"+inputtext, time=60*60*24*7)
        return result
    else:
        API_KEY = get_key(".env", "API_KEY")

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query=" + \
            query+"&key="+API_KEY+"&language=zh-TW&region=TW"
        data = requests.get(url).json()

        try:
            places_dict = {}
            for i in range(len(data["results"])):
                if ("醫院" in data["results"][i]["name"]) or ("診所" in data["results"][i]["name"]):
                    places_dict[data["results"][i]["place_id"]
                                ] = data["results"][i]["user_ratings_total"]
            places = list(places_dict.keys())
            counts = len(places)
            if counts > 1:
                counts = 1

            threads = []

            for i in range(counts):
                threads.append(threading.Thread(
                    target=callReviewAPI, args=(places[i], keyword, result)))
                T2 = time.perf_counter()
                threads[i].start()

            timeout = 60
            for i in range(counts):
                threads[i].join(timeout)
        except:
            pass

        try:
            con = conPool.get_connection()
            cursor = con.cursor()
            cursor.execute(
                "SELECT * FROM review WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
            data = cursor.fetchall()
            if len(data) == 0:
                cursor.execute(
                    "INSERT INTO review (doctor, review) VALUES (%s, %s)", (inputtext, ""))
                con.commit()
            cursor.close()
            con.close()
        except:
            pass
        return result, 200


def Business(inputtext, expiredDay):
    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_BUSINESS = get_key(".env", "SEARCH_ENGINE_ID_BUSINESS")

    query = inputtext + "醫師介紹和評價"
    page = 1
    result = {}
    result["data"] = []

    try:
        con = conPool.get_connection()
        cursor = con.cursor(buffered=True)
        cursor.execute(
            "SELECT author, timestamp, comment, createdAt, link, location FROM businessComment WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
        data = cursor.fetchall()
        cursor.close()
        con.close()
    except:
        pass

    if len(data) != 0:
        for d in data:
            item = {}
            item["name"] = d[0]
            item["posttime"] = untilNow(float(d[1]))
            item["comment"] = d[2]
            item["createdAt"] = d[3]
            item["link"] = d[4]
            item["location"] = d[5]
            result["data"].append(item)
            r.rpush("Business-"+inputtext,json.dumps(item, default=str))
        r.expire("Business-"+inputtext, time=60*60*24*7)
        return result
    else:
        start = (page - 1) * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_BUSINESS}&q={query}&start={start}"

        data = requests.get(url).json()
        try:
            for i in range(len(data["items"])):
                if (inputtext+"醫師介紹和評價") in data["items"][i]["title"]:

                    link = data["items"][i]["link"]
                    request = urllib.request.Request(link, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                    })

                    with urllib.request.urlopen(request) as response:
                        html = response.read().decode("utf-8")
                    soup = BeautifulSoup(html, "html.parser")
                    messages = soup.find_all("div", class_="commentbody")
                    location = soup.find(
                        "li", class_="clearfix").find("a").text
                    for message in messages:
                        posttime = message.find("div", class_="posttime").text
                        commentPart = message.find(
                            "p", class_="commentcont-part").text
                        commentAll = message.find(
                            "p", class_="commentcont-all").text
                        if len(commentAll) == 0:
                            comment = commentPart
                        else:
                            comment = commentAll
                        posttime = posttime.split()
                        author = posttime[0].replace("發表於", "")
                        timestamp = time.mktime(datetime.strptime(
                            posttime[1], "%Y/%m/%d").timetuple())

                        item = {}
                        item["name"] = author
                        item["posttime"] = untilNow(timestamp)
                        item["comment"] = comment
                        item["link"] = link
                        item["location"] = location
                        result["data"].append(item)

                        try:
                            con = conPool.get_connection()
                            cursor = con.cursor()
                            cursor.execute(
                                "INSERT INTO businessComment (doctor, author, timestamp, comment, link, location) VALUES (%s, %s,%s, %s,%s, %s)", (inputtext, author, timestamp, comment, link, location))
                            con.commit()
                            cursor.close()
                            con.close()
                        except:
                            pass
                else:
                    pass
        except:
            pass
        return result, 200


def Judgment(inputtext, expiredDay):
    global selenium_counts
    result = {}
    result["data"] = []

    try:
        con = conPool.get_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT link, title FROM judgment WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
        data = cursor.fetchall()
        cursor.close()
        con.close()
    except:
        pass

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            result["data"].append(item)
            r.rpush("Judgment-"+inputtext,json.dumps(item, default=str))
        r.expire("Judgment-"+inputtext, time=60*60*24*7)
        return result
    else:
        if selenium_counts < 20:
            selenium_counts += 1
            service = Service(executable_path=ChromeDriverManager().install())
            options = Options()
            ua = UserAgent()
            user_agent = ua.random  # 偽裝隨機產生瀏覽器、作業系統
            options.add_argument(f'--user-agent={user_agent}')
            options.add_argument('headless')
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('start-maximized')
            options.add_argument("--disable-extensions")
            options.add_argument('--disable-browser-side-navigation')
            options.add_argument('enable-automation')
            options.add_argument('--disable-infobars')
            options.add_argument('enable-features=NetworkServiceInProcess')
            options.add_argument('--disable-dev-shm-usage')
            options.add_experimental_option("detach", True)  # 加入後不會閃退
            options.page_load_strategy = 'normal'
            driver = webdriver.Chrome(service=service, options=options)
            driver.maximize_window()
            try:
                inputList = inputtext.split()
                keyword = inputtext.split()[0]
            except:
                keyword = inputtext

            query = '(被告'+keyword+'+被上訴人'+keyword+'+相對人' + \
                keyword+'+被告醫院之履行輔助人'+keyword+')&(醫生+醫師)'

            for i in range(1, len(inputList)):
                query += '&'+inputList[i]

            try:
                driver.get(
                    "https://judgment.judicial.gov.tw/FJUD/default.aspx")
                Input = driver.find_element(By.ID, 'txtKW')
                Input.send_keys(query)
                Btn = driver.find_element(By.ID, 'btnSimpleQry')
                Btn.send_keys(Keys.ENTER)
                driver.switch_to.frame('iframe-data')

                time.sleep(1)
                links = driver.find_elements(By.CLASS_NAME, 'hlTitle_scroll')
                if len(links) == 0:
                    try:
                        con = conPool.get_connection()
                        cursor = con.cursor()
                        cursor.execute(
                            "INSERT INTO judgment (doctor, link, title) VALUES (%s, %s,%s)", (inputtext, "", "搜尋不到資料：關鍵字可嘗試僅輸入醫生名稱，例如：王大明"))
                        con.commit()
                        cursor.close()
                        con.close()
                    except:
                        pass
                else:
                    for l in links:
                        link = l.get_attribute("href")
                        title = l.text

                        item = {}
                        item["url"] = link
                        item["title"] = title
                        result["data"].append(item)

                        try:
                            con = conPool.get_connection()
                            cursor = con.cursor()
                            cursor.execute(
                                "INSERT INTO judgment (doctor, link, title) VALUES (%s, %s,%s)", (inputtext, link, title))
                            con.commit()
                            cursor.close()
                            con.close()
                        except:
                            pass
            except:
                pass
            driver.close()

            selenium_counts -= 1
            return result, 200
        else:
            result["busy"] = True
            return result, 200


def Thank(keyword):
    T1 = time.perf_counter()
    res = es.options(opaque_id=keyword.encode("utf-8").decode("latin1")).search(index='thank', body={"size": 100, "query": {
        "match_phrase": {
            "content": keyword
        }
    }, "sort": {
        "month.keyword": {
            "order": "desc"
        }
    }})
    T2 = time.perf_counter()
    print(keyword+"Elastic Search："+'%s毫秒' % ((T2 - T1)*1000))
    data = res['hits']['hits']
    return data


def viewThank(data,inputtext):
    result = {}
    result["data"] = []
    for d in data:
        res = es.search(index='thankurl', query={
            "match_phrase": {
                "month": d['_source']['month']
            }
        })

        item = {}
        item["url"] = res['hits']['hits'][0]['_source']['url']
        item["title"] = d['_source']['target']
        item["text"] = d['_source']['content']
        item["when"] = d['_source']['month']
        result["data"].append(item)
        r.rpush("Thank-"+inputtext,json.dumps(item))
    r.expire("Thank-"+inputtext, time=60*60*24*7)
    return result


def Ptt(inputtext, expiredDay):
    result = {}
    result["data"] = []

    try:
        con = conPool.get_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT link, title, text FROM Ptt WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
        data = cursor.fetchall()
        cursor.execute(
            "SELECT board FROM PttBoard;")
        data_board = cursor.fetchall()
        cursor.close()
        con.close()
        boards = ["Nurse", "BabyMother", "GoodPregnan", "Laser_eye",
                  "hair_loss", "facelift", "teeth_salon", "KIDs", "Preschooler"]
        for d in data_board:
            boards.append(d[0])
    except:
        pass

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
            r.rpush("Ptt-"+inputtext,json.dumps(item))
        r.expire("Ptt-"+inputtext, time=60*60*24*7)
        return result
    else:
        try:
            inputList = inputtext.split()
            keyword = inputtext.split()[0]
        except:
            keyword = inputtext
        query = '"'+keyword+'"'+'+醫生'+'+醫師'

        for i in range(1, len(inputList)):
            query += '+'+inputList[i]

        API_KEY = get_key(".env", "API_KEY")
        SEARCH_ENGINE_ID_PTT = get_key(".env", "SEARCH_ENGINE_ID_PTT")
        page = 1
        while page < 6:
            start = (page - 1) * 10 + 1
            url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_PTT}&q={query}&start={start}"

            data = requests.get(url).json()
            try:
                for i in range(len(data["items"])):
                    for board in boards:
                        if board in data["items"][i]["link"]:
                            if ("徵才" not in data["items"][i]["title"] and "新聞" not in data["items"][i]["title"] and (keyword in data["items"][i]["title"] or keyword in data["items"][i]["snippet"])):

                                link = data["items"][i]["link"]
                                title = data["items"][i]["title"]
                                text = data["items"][i]["snippet"]

                                item = {}
                                item["url"] = link
                                item["title"] = title
                                item["text"] = text
                                result["data"].append(item)

                                try:
                                    con = conPool.get_connection()
                                    cursor = con.cursor()
                                    cursor.execute(
                                        "INSERT INTO Ptt (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                                    con.commit()
                                    cursor.close()
                                    con.close()
                                except:
                                    pass

                page += 1
            except:
                break
        return result, 200


def Search(inputtext, expiredDay):
    result = {}
    result["data"] = []

    try:
        con = conPool.get_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT link, title, text FROM search WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
        data = cursor.fetchall()
        cursor.close()
        con.close()
    except:
        pass

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
            r.rpush("Search-"+inputtext,json.dumps(item))
        r.expire("Search-"+inputtext, time=60*60*24*7)
        return result
    else:
        try:
            inputList = inputtext.split()
            keyword = inputtext.split()[0]
        except:
            keyword = inputtext
        query = '"'+keyword+'"'+'+醫生'+'+醫師'+'+"感謝函"'

        for i in range(1, len(inputList)):
            query += '+'+inputList[i]

        API_KEY = get_key(".env", "API_KEY")
        SEARCH_ENGINE_ID_ALL = get_key(".env", "SEARCH_ENGINE_ID_ALL")
        page = 1

        start = (page - 1) * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_ALL}&q={query}&start={start}"

        data = requests.get(url).json()
        try:
            for i in range(len(data["items"])):
                if keyword in data["items"][i]["title"] or keyword in data["items"][i]["snippet"]:

                    link = data["items"][i]["link"]
                    title = data["items"][i]["title"]
                    text = data["items"][i]["snippet"]

                    item = {}
                    item["url"] = link
                    item["title"] = title
                    item["text"] = text
                    result["data"].append(item)

                    try:
                        con = conPool.get_connection()
                        cursor = con.cursor()
                        cursor.execute(
                            "INSERT INTO search (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                        con.commit()
                        cursor.close()
                        con.close()
                    except:
                        pass
        except:
            pass
        return result, 200


def Dcard(inputtext, expiredDay):
    result = {}
    result["data"] = []

    try:
        con = conPool.get_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT link, title, text FROM Dcard WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
        data = cursor.fetchall()
        cursor.close()
        con.close()
    except:
        pass

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
            r.rpush("Dcard-"+inputtext,json.dumps(item))
        r.expire("Dcard-"+inputtext, time=60*60*24*7)
        return result
    else:
        try:
            inputList = inputtext.split()
            keyword = inputtext.split()[0]
        except:
            keyword = inputtext
        query = '"'+keyword+'"'+'+醫生'+'+醫師'

        for i in range(1, len(inputList)):
            query += '+'+inputList[i]

        API_KEY = get_key(".env", "API_KEY")
        SEARCH_ENGINE_ID_Dcard = get_key(".env", "SEARCH_ENGINE_ID_Dcard")
        page = 1
        while page < 6:
            start = (page - 1) * 10 + 1
            url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_Dcard}&q={query}&start={start}"

            data = requests.get(url).json()
            try:
                for i in range(len(data["items"])):
                    if ("徵才" not in data["items"][i]["title"] and "新聞" not in data["items"][i]["title"] and (keyword in data["items"][i]["title"] or keyword in data["items"][i]["snippet"])):

                        link = data["items"][i]["link"]
                        title = data["items"][i]["title"]
                        text = data["items"][i]["snippet"]

                        item = {}
                        item["url"] = link
                        item["title"] = title
                        item["text"] = text
                        result["data"].append(item)

                        try:
                            con = conPool.get_connection()
                            cursor = con.cursor()
                            cursor.execute(
                                "INSERT INTO Dcard (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                            con.commit()
                            cursor.close()
                            con.close()
                        except:
                            pass

                page += 1
            except:
                break
        return result, 200


def Blog(inputtext, expiredDay):
    result = {}
    result["data"] = []

    try:
        con = conPool.get_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT link, title, text FROM blog WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
        data = cursor.fetchall()
        cursor.close()
        con.close()
    except:
        pass

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
            r.rpush("Blog-"+inputtext,json.dumps(item))
        r.expire("Blog-"+inputtext, time=60*60*24*7)
        return result
    else:
        try:
            inputList = inputtext.split()
            keyword = inputtext.split()[0]
        except:
            keyword = inputtext
        query = '"'+keyword+'"'+'+醫生'+'+醫師'

        for i in range(1, len(inputList)):
            query += '+'+inputList[i]

        API_KEY = get_key(".env", "API_KEY")
        SEARCH_ENGINE_ID_BLOG = get_key(".env", "SEARCH_ENGINE_ID_BLOG")
        page = 1
        while page < 3:
            start = (page - 1) * 10 + 1
            url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_BLOG}&q={query}&start={start}"
            data = requests.get(url).json()
            filters = get_key(".env", "filters").split(",")
            try:
                for i in range(len(data["items"])):
                    if any(filter in data["items"][i]["title"] for filter in filters):
                        pass
                    else:
                        if keyword in data["items"][i]["title"] or keyword in data["items"][i]["snippet"]:

                            link = data["items"][i]["link"]
                            title = data["items"][i]["title"]
                            text = data["items"][i]["snippet"]

                            item = {}
                            item["url"] = link
                            item["title"] = title
                            item["text"] = text
                            result["data"].append(item)

                            try:
                                con = conPool.get_connection()
                                cursor = con.cursor()
                                cursor.execute(
                                    "INSERT INTO blog (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                                con.commit()
                                cursor.close()
                                con.close()
                            except:
                                pass
                page += 1
            except:
                break
        return result, 200


def Most():
    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT doctor FROM record WHERE createdAt >= %s group by(doctor) ORDER BY count(doctor) DESC LIMIT 10;", (expiredDay,))
    data = cursor.fetchall()
    cursor.close()
    con.close()

    for d in data:
        result["data"].append(d[0])
    return result


def Doctor():
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT department, name FROM doctor;")
    data = cursor.fetchall()
    cursor.close()
    con.close()

    result = {}
    for d in data:
        if d[0] not in result:
            result[d[0]] = []
        result[d[0]].append(d[1])
    return result


def getAll(inputtext):
    T1 = time.perf_counter()
    threads = []
    threads.append(threading.Thread(target=Review,
                   args=(inputtext, T1, expiredDay)))
    threads.append(threading.Thread(target=Business,
                   args=(inputtext, T1, expiredDay)))
    # threads.append(threading.Thread(target=readJudgment,
    #                args=(inputtext, T1, expiredDay)))
    threads.append(threading.Thread(target=Ptt,
                   args=(inputtext, T1, expiredDay)))
    threads.append(threading.Thread(target=Search,
                   args=(inputtext, T1, expiredDay)))
    threads.append(threading.Thread(target=Blog,
                   args=(inputtext, T1, expiredDay)))
    threads.append(threading.Thread(target=Dcard,
                   args=(inputtext, T1, expiredDay)))

    for i in range(6):
        threads[i].start()

    for i in range(6):
        threads[i].join()

    result = {}
    result["ok"] = True
    T2 = time.perf_counter()
    print(inputtext+"全部："+'%s毫秒' % ((T2 - T1)*1000))
    return result


def updatedata():
    T1 = time.perf_counter()
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute("DELETE FROM record WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM review WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute(
        "DELETE FROM businessComment WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM judgment WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM Ptt WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM search WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM blog WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    print("刪除過期資料")
    cursor.execute(
        "SELECT doctor, count(doctor) AS counter FROM record WHERE createdAt >= %s group by(doctor) ORDER BY counter DESC LIMIT 10;", (expiredDay,))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    for d in data:
        keyword = d[0]
        getAll(keyword)
    print("更新過去一周熱搜前十名資料")


def getDoctorList():
    def getSoupDoctor(url):
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("big5-hkscs")
            return BeautifulSoup(html, "html.parser")

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute("DROP table IF EXISTS doctor;")
    cursor.execute(
        "CREATE table doctor (id BIGINT PRIMARY KEY auto_increment,department VARCHAR(255) NOT NULL,name VARCHAR(255) NOT NULL,url TEXT NOT NULL);")

    url = "https://www6.vghtpe.gov.tw/reg/sectList.do?type=return"

    departmentList = getSoupDoctor(url).find_all('a')
    doctorNameList = {}
    for i in range(len(departmentList)):
        if "opdTimetable" in departmentList[i].get("href"):
            url_1 = "https://www6.vghtpe.gov.tw/reg/" + \
                departmentList[i].get("href")
            url_2 = url_1.replace("page=1", "page=2")
            urlList = [url_1, url_2]
            department = departmentList[i].text
            if department not in doctorNameList.keys():
                doctorNameList[department] = []

            for url in urlList:
                doctorList = getSoupDoctor(url).find_all("a")

                for i in range(len(doctorList)):
                    if "javascript:CreateWindow(" in doctorList[i].get("href"):
                        url = getUrl(doctorList[i].get("href"))
                        doctor = doctorList[i].text.strip()

                        if (doctor not in doctorNameList[department]) & len(doctor) > 0:
                            doctorNameList[department].append(doctor)
                            cursor.execute(
                                "INSERT INTO doctor (department, name, url) VALUES (%s, %s,%s)", (department, doctor, url))
                            con.commit()
    cursor.close()
    con.close()


def getPttBoard():
    def getsoup(link):
        request = urllib.request.Request(link, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })

        with urllib.request.urlopen(request) as response:
            html = response.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        return soup

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute("DROP table IF EXISTS PttBoard;")
    cursor.execute(
        "CREATE table PttBoard (id BIGINT PRIMARY KEY auto_increment,board VARCHAR(255));")

    url_taiwan = "https://www.ptt.cc/cls/9217"
    soup = getsoup(url_taiwan)
    areas = soup.find_all("a", class_="board")

    for area in areas:
        url_location = "https://www.ptt.cc"+area.get("href")
        soup1 = getsoup(url_location)
        boards = soup1.find_all("div", class_="board-name")
        for board in boards:
            cursor.execute(
                "INSERT INTO PttBoard (board) VALUES (%s)", (board.text,))
            con.commit()

    url_health = "https://www.ptt.cc/cls/7957"
    soup2 = getsoup(url_health)
    boards = soup2.find_all("div", class_="board-name")
    for board in boards:
        cursor.execute(
            "INSERT INTO PttBoard (board) VALUES (%s)", (board.text,))
        con.commit()

    cursor.close()
    con.close()
