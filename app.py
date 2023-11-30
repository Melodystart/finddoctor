from selenium import webdriver
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from flask import *
from mysql.connector import pooling
from dotenv import get_key
import requests
import urllib.request
from bs4 import BeautifulSoup
import threading
from outscraper import ApiClient
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.background import BackgroundScheduler
from elasticsearch import Elasticsearch
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry

es = Elasticsearch("http://localhost:9200/")

conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
    ".env", "password"), host='finddoctor.collqfqpnilo.us-west-2.rds.amazonaws.com', database='finddoctor', pool_name='findConPool', pool_size=32,  auth_plugin='mysql_native_password')

toDay = datetime.today().date()
expiredDay = toDay - timedelta(days=1)  # 設定資料期限為1天前到期

selenium_counts = 0

app = Flask(
    __name__,
    static_folder="public",
    static_url_path="/"
)

# session = requests.Session()
# # session.keep_alive = False
# retry = Retry(total=5, backoff_factor=0.1)
# adapter = HTTPAdapter(max_retries=retry)
# session.mount('http://', adapter)
# session.mount('https://', adapter)


def error(result, message):
    result["error"] = True
    result["message"] = message
    return result


def untilNow(ts):
    # 設定utc時區
    past_utc = datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)
    now_utc = datetime.now(tz=timezone.utc)

    # 設定utc+8時區
    # utf8 = timezone(timedelta(hours=8))
    # past_utc8 = past_utc.astimezone(utf8)
    # now_utc8 = now_utc.astimezone(utf8)

    until_now = relativedelta(now_utc, past_utc)

    years = until_now.years
    months = until_now.months
    days = until_now.days
    hours = until_now.hours
    minutes = until_now.minutes

    if years == 0:
        if months == 0:
            if days == 0:
                if hours == 0:
                    return (str(minutes) + "分鐘前")
                else:
                    return (str(hours) + "小時前")
            else:
                return (str(days) + "天前")
        else:
            return (str(months) + "個月前")
    else:
        return (str(years) + "年前")


def readReview(inputtext, T1, expiredDay):
    def callReviewAPI(place_id, keyword, result):
        api_client = ApiClient(
            api_key=get_key(".env", "review_api_key"))
        results = api_client.google_maps_reviews(
            place_id, reviews_limit=1, reviews_query=keyword, sort="newest", language="zh-TW", region="TW")
        try:
            T3 = time.perf_counter()
            reviews = results[0]["reviews_data"]
            # print("API回應了 ："+results[0]["name"])
            # print('%s毫秒' % ((T3 - T1)*1000))

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

                    con = conPool.get_connection()
                    cursor = con.cursor()
                    cursor.execute(
                        "INSERT INTO review (doctor, author, star, timestamp, review, link, location ) VALUES (%s, %s,%s, %s, %s,%s,%s)", (inputtext, author, review_rating, review_timestamp, review, review_link, location))
                    con.commit()
                    cursor.close()
                    con.close()

                T4 = time.perf_counter()
                # print("資料append好了："+location)
                # print('%s毫秒' % ((T4 - T1)*1000))

            else:
                T4 = time.perf_counter()
                # print("無資料："+results[0]["name"])
                # print('%s毫秒' % ((T4 - T1)*1000))
        except:
            pass

    try:
        keyword = inputtext.split()[0]
    except:
        keyword = inputtext

    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT author, star, timestamp, review, link, location FROM review WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
    data = cursor.fetchall()
    cursor.close()
    con.close()

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
            print(keyword+"回傳先前review資料")
        return result
    else:
        print(keyword+"開始連線reviewAPI")
        query = inputtext + "醫"

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
            # print(places_dict)
            # places_sort = dict(sorted(places_dict.items(),
            #                           key=lambda x: x[1], reverse=True))
            # print(places_sort)
            places = list(places_dict.keys())
            counts = len(places)
            if counts > 1:  # 僅取前1個搜尋地點
                counts = 1

            # 使用threading
            threads = []

            for i in range(counts):
                threads.append(threading.Thread(
                    target=callReviewAPI, args=(places[i], keyword, result)))
                T2 = time.perf_counter()
                threads[i].start()
                # print("開始呼叫API："+places[i])
                # print('%s毫秒' % ((T2 - T1)*1000))

            timeout = 60
            for i in range(counts):
                threads[i].join(timeout)
        except:
            print(keyword+"review有錯誤")
            pass

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

        T5 = time.perf_counter()
        print(keyword+"review好了："+'%s毫秒' % ((T5 - T1)*1000))
        return result, 200


def readBusiness(keyword, T1, expiredDay):
    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_BUSINESS = get_key(".env", "SEARCH_ENGINE_ID_BUSINESS")

    query = keyword + "醫師介紹和評價"
    page = 1
    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor(buffered=True)

    cursor.execute(
        "SELECT author, timestamp, comment, createdAt, link, location FROM businessComment WHERE doctor=%s AND createdAt>%s;", (keyword, expiredDay))
    data = cursor.fetchall()

    cursor.close()
    con.close()

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
        return result
    else:
        start = (page - 1) * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_BUSINESS}&q={query}&start={start}"

        data = requests.get(url).json()
        try:
            for i in range(len(data["items"])):
                if (keyword+"醫師介紹和評價") in data["items"][i]["title"]:

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

                        con = conPool.get_connection()
                        cursor = con.cursor()
                        cursor.execute(
                            "INSERT INTO businessComment (doctor, author, timestamp, comment, link, location) VALUES (%s, %s,%s, %s,%s, %s)", (keyword, author, timestamp, comment, link, location))
                        con.commit()
                        cursor.close()
                        con.close()
                else:
                    pass
        except:
            print(keyword+"有錯誤，商周找不到資料")
        T2 = time.perf_counter()
        print(keyword+"商周好了："+'%s毫秒' % ((T2 - T1)*1000))
        return result, 200


def readJudgment(inputtext, T1, expiredDay):
    global selenium_counts
    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title FROM judgment WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
    data = cursor.fetchall()
    cursor.close()
    con.close()

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            result["data"].append(item)
        return result
    else:
        if selenium_counts < 20:
            selenium_counts += 1
            print("第"+str(selenium_counts)+"個爬蟲開始爬")
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
            driver = webdriver.Chrome(options=options)
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
                    con = conPool.get_connection()
                    cursor = con.cursor()
                    cursor.execute(
                        "INSERT INTO judgment (doctor, link, title) VALUES (%s, %s,%s)", (inputtext, "", "搜尋不到資料：關鍵字可嘗試僅輸入醫生名稱，例如：王大明"))
                    con.commit()
                    cursor.close()
                    con.close()
                else:
                    for l in links:
                        link = l.get_attribute("href")
                        title = l.text

                        item = {}
                        item["url"] = link
                        item["title"] = title
                        result["data"].append(item)

                        con = conPool.get_connection()
                        cursor = con.cursor()
                        cursor.execute(
                            "INSERT INTO judgment (doctor, link, title) VALUES (%s, %s,%s)", (inputtext, link, title))
                        con.commit()
                        cursor.close()
                        con.close()

                # driver.quit()
            except:
                print(keyword+"：司法院資料異常")
                # driver.quit()
            driver.close()
            selenium_counts -= 1
            print(keyword+"：爬蟲結束，剩下"+str(selenium_counts)+"個爬蟲")
            T2 = time.perf_counter()
            print(keyword+"司法院好了："+'%s毫秒' % ((T2 - T1)*1000))
            return result, 200
        else:
            print("因忙碌中，先不取司法院資料")
            result["busy"] = True
            return result, 200


def readThank(keyword):
    res = es.search(index='thank', body={"size": 100, "query": {
        "match_phrase": {
            "content": keyword
        }
    }})
    data = res['hits']['hits']
    return data


def viewThank(data):
    result = {}
    result["data"] = []
    for d in data:
        res = es.search(index='thankurl', query={
            "match": {
                "month": d['_source']['month']
            }
        })

        item = {}
        item["url"] = res['hits']['hits'][0]['_source']['url']
        item["title"] = d['_source']['target']
        item["text"] = d['_source']['content']
        item["when"] = d['_source']['month']
        result["data"].append(item)
    return result


def readPtt(inputtext, T1, expiredDay):
    result = {}
    result["data"] = []

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

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
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

                                con = conPool.get_connection()
                                cursor = con.cursor()
                                cursor.execute(
                                    "INSERT INTO Ptt (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                                con.commit()
                                cursor.close()
                                con.close()

                page += 1
            except:
                break

        T2 = time.perf_counter()
        print(keyword+"Ptt好了："+'%s毫秒' % ((T2 - T1)*1000))
        return result, 200


def readSearch(inputtext, T1, expiredDay):
    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title, text FROM search WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
    data = cursor.fetchall()
    cursor.close()
    con.close()

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
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

                    con = conPool.get_connection()
                    cursor = con.cursor()
                    cursor.execute(
                        "INSERT INTO search (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                    con.commit()
                    cursor.close()
                    con.close()
        except:
            pass

        T2 = time.perf_counter()
        print(keyword+"Search好了："+'%s毫秒' % ((T2 - T1)*1000))
        return result, 200


def readDcard(inputtext, T1, expiredDay):
    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title, text FROM Dcard WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
    data = cursor.fetchall()
    cursor.close()
    con.close()

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
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

                        con = conPool.get_connection()
                        cursor = con.cursor()
                        cursor.execute(
                            "INSERT INTO Dcard (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                        con.commit()
                        cursor.close()
                        con.close()

                page += 1
            except:
                break

        T2 = time.perf_counter()
        print(keyword+"Dcard好了："+'%s毫秒' % ((T2 - T1)*1000))
        return result, 200


def readBlog(inputtext, T1, expiredDay):
    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title, text FROM blog WHERE doctor=%s AND createdAt>%s;", (inputtext, expiredDay))
    data = cursor.fetchall()
    cursor.close()
    con.close()

    if len(data) != 0:
        for d in data:
            item = {}
            item["url"] = d[0]
            item["title"] = d[1]
            item["text"] = d[2]
            result["data"].append(item)
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

        start = (page - 1) * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_BLOG}&q={query}&start={start}"

        data = requests.get(url).json()
        try:
            for i in range(len(data["items"])):
                if "580913" not in data["items"][i]["title"]:
                    if keyword in data["items"][i]["title"] or keyword in data["items"][i]["snippet"]:

                        link = data["items"][i]["link"]
                        title = data["items"][i]["title"]
                        text = data["items"][i]["snippet"]

                        item = {}
                        item["url"] = link
                        item["title"] = title
                        item["text"] = text
                        result["data"].append(item)

                        con = conPool.get_connection()
                        cursor = con.cursor()
                        cursor.execute(
                            "INSERT INTO blog (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
                        con.commit()
                        cursor.close()
                        con.close()

        except:
            pass
        T2 = time.perf_counter()
        print(keyword+"Blog好了："+'%s毫秒' % ((T2 - T1)*1000))
        return result, 200


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/thank")
def thank():
    return render_template("thank.html")


@app.route("/Ptt")
def Ptt():
    return render_template("Ptt.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/Dcard")
def Dcard():
    return render_template("Dcard.html")


@app.route("/blog")
def blog():
    return render_template("blog.html")


@app.route("/judgment")
def judgment():
    return render_template("judgment.html")


@app.route("/review")
def review():
    return render_template("review.html")


@app.route("/business")
def business():
    return render_template("business.html")


@app.route("/api/thank/<keyword>")
def getthank(keyword):
    T1 = time.perf_counter()
    data = readThank(keyword)
    result = viewThank(data)
    T2 = time.perf_counter()
    print(keyword+"感謝函好了："+'%s毫秒' % ((T2 - T1)*1000))
    return result


@app.route("/api/Ptt/<inputtext>")
def getPtt(inputtext):
    T1 = time.perf_counter()
    result = readPtt(inputtext, T1, expiredDay)
    return result


@app.route("/api/Dcard/<inputtext>")
def getDcard(inputtext):
    T1 = time.perf_counter()
    result = readDcard(inputtext, T1, expiredDay)
    return result


@app.route("/api/search/<inputtext>")
def getSearch(inputtext):
    T1 = time.perf_counter()
    result = readSearch(inputtext, T1, expiredDay)
    return result


@app.route("/api/blog/<inputtext>")
def getBlog(inputtext):
    T1 = time.perf_counter()
    result = readBlog(inputtext, T1, expiredDay)
    return result


@app.route("/api/judgment/<inputtext>")
def getJudgment(inputtext):
    T1 = time.perf_counter()
    result = readJudgment(inputtext, T1, expiredDay)
    return result


@app.route("/api/review/<inputtext>")
def getReview(inputtext):
    T1 = time.perf_counter()
    result = readReview(inputtext, T1, expiredDay)
    return result


@app.route("/api/business/<keyword>")
def getBusiness(keyword):
    T1 = time.perf_counter()
    result = readBusiness(keyword, T1, expiredDay)
    return result


@app.route("/api/<keyword>")
def getAll(keyword):
    T1 = time.perf_counter()

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO record (doctor) VALUES (%s)", (keyword, ))
    con.commit()
    cursor.execute(
        "INSERT INTO newest (doctor) VALUES (%s)", (keyword, ))
    con.commit()
    cursor.close()
    con.close()

    threads = []
    threads.append(threading.Thread(target=readReview,
                   args=(keyword, T1, expiredDay)))
    threads.append(threading.Thread(target=readBusiness,
                   args=(keyword, T1, expiredDay)))
    threads.append(threading.Thread(target=readJudgment,
                   args=(keyword, T1, expiredDay)))
    threads.append(threading.Thread(target=readPtt,
                   args=(keyword, T1, expiredDay)))
    threads.append(threading.Thread(target=readSearch,
                   args=(keyword, T1, expiredDay)))
    threads.append(threading.Thread(target=readBlog,
                   args=(keyword, T1, expiredDay)))
    threads.append(threading.Thread(target=readDcard,
                   args=(keyword, T1, expiredDay)))

    for i in range(7):
        threads[i].start()

    for i in range(7):
        threads[i].join()

    result = {}
    result["ok"] = True
    T2 = time.perf_counter()
    print(keyword+"全都好了："+'%s毫秒' % ((T2 - T1)*1000))
    return result


def updatedata():
    T1 = time.perf_counter()
    con = conPool.get_connection()
    cursor = con.cursor()
    # 刪除過期資料
    cursor.execute("DELETE FROM newest WHERE createdAt<=%s;", (expiredDay,))
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
    # 更新過去一周熱搜前十名資料
    cursor.execute(
        "SELECT doctor, count(doctor) AS counter FROM record WHERE createdAt < %s AND createdAt >= %s group by(doctor) ORDER BY counter DESC LIMIT 10;", (toDay, expiredDay))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    for d in data:
        print(d)
        keyword = d[0]
        getAll(keyword)


# def hi():
#     print("Hi apscheduler")


# 1. 指定BackgroundScheduler不會阻塞主程式app的執行 v.s BlockingScheduler
scheduler = BackgroundScheduler(timezone="Asia/Taipei")

# 2-1. interval 固定間隔模式：每1秒執行hi函式
# scheduler.add_job(hi, 'interval', seconds=10)

# 2-2. cron 指定某時段執行： 每天 0點00分執行updatedata函式
scheduler.add_job(updatedata, 'cron',
                  day_of_week="mon-sun", hour=0, minute=00)

# 3. 排程開始
scheduler.start()

app.run(host="0.0.0.0", port=8080)
