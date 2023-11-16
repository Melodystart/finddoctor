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

conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
    ".env", "password"), host='localhost', database='finddoctor', pool_name='findConPool', pool_size=10,  auth_plugin='mysql_native_password')


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


def readReview(inputtext):
    T1 = time.perf_counter()

    def callReviewAPI(place_id, keyword, result):
        def viewReview(i, location):
            author = reviews[i]["author_title"]
            review = reviews[i]["review_text"]
            review_rating = int(reviews[i]["review_rating"])
            # review_timestamp = untilNow(reviews[i]["review_timestamp"])
            review_timestamp = reviews[i]["review_timestamp"]
            review_link = reviews[i]["review_link"]

            item = {}
            item["name"] = author
            item["star"] = review_rating
            item["when"] = review_timestamp
            item["review"] = review
            item["link"] = review_link
            item["location"] = location
            result["data"].append(item)

            con = conPool.get_connection()
            cursor = con.cursor()
            cursor.execute(
                "INSERT INTO review (doctor, author, star, timestamp, review, link, location ) VALUES (%s, %s,%s, %s, %s,%s,%s)", (keyword, author, review_rating, review_timestamp, review, review_link, location))
            con.commit()
            cursor.close()
            con.close()

        api_client = ApiClient(
            api_key=get_key(".env", "review_api_key"))
        results = api_client.google_maps_reviews(
            place_id, reviews_limit=1, reviews_query=keyword, sort="newest", language="zh-TW", region="TW")
        try:
            reviews = results[0]["reviews_data"]
            if len(reviews) > 0:
                location = results[0]["name"]
                print(location)
                result["title"] = location
                threads2 = []
                for i in range(len(reviews)):
                    threads2.append(threading.Thread(
                        target=viewReview, args=(i, location)))
                    threads2[i].start()
                for i in range(len(reviews)):
                    threads2[i].join()

                # for i in range(len(reviews)):
                #     author = reviews[i]["author_title"]
                #     review = reviews[i]["review_text"]
                #     review_rating = reviews[i]["review_rating"]
                #     review_timestamp = untilNow(reviews[i]["review_timestamp"])
                #     review_link = reviews[i]["review_link"]

                #     item = {}
                #     item["location"] = location
                #     item["name"] = author
                #     item["star"] = review_rating
                #     item["when"] = review_timestamp
                #     item["comment"] = review
                #     item["link"] = review_link
                #     result["data"].append(item)
        except:
            pass
        return result
    try:
        keyword = inputtext.split()[0]
        location = inputtext.split()[1]
    except:
        keyword = inputtext
        location = ""
    query = inputtext + "醫"
    API_KEY = get_key(".env", "API_KEY")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query=" + \
        query+"&key="+API_KEY+"&language=zh-TW"
    data = requests.get(url).json()

    places = []
    for i in range(len(data["results"])):
        if "醫院" in data["results"][i]["name"] or "診所" in data["results"][i]["name"]:
            print(data["results"][i]["name"])
            places.append(data["results"][i]["place_id"])

    counts = len(data["results"])
    if counts > 2:  # 僅取前二個搜尋地點
        counts = 2

    # -----------------未處理若找不到place情形
    result = {}
    result["data"] = []
    # 使用threading 7.5~29毫秒
    threads = []
    for i in range(counts):
        threads.append(threading.Thread(
            target=callReviewAPI, args=(places[i], keyword, result)))
        threads[i].start()

    for i in range(counts):
        threads[i].join()

    # 沒有使用threading 19毫秒
    # for i in range(counts):
    #     callReviewAPI(data["results"][i]["place_id"], keyword)
    print(result)
    T2 = time.perf_counter()
    print('%s毫秒' % ((T2 - T1)*1000))
    print("review好了")
    return result


def readBusiness(keyword):
    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_BUSINESS = get_key(".env", "SEARCH_ENGINE_ID_BUSINESS")
    query = keyword
    page = 1
    result = {}
    result["data"] = []

    start = (page - 1) * 10 + 1
    url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_BUSINESS}&q={query}&start={start}"

    data = requests.get(url).json()
    try:
        for i in range(len(data["items"])):
            if (query+"醫師介紹和評價") in data["items"][i]["title"]:
                link = data["items"][i]["link"]
                title = data["items"][i]["title"]
                result["url"] = link
                result["title"] = title

                con = conPool.get_connection()
                cursor = con.cursor()
                cursor.execute(
                    "INSERT INTO businessLink (doctor, link, title) VALUES (%s, %s,%s)", (keyword, link, title))
                con.commit()
                cursor.close()
                con.close()

                request = urllib.request.Request(link, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                })

                with urllib.request.urlopen(request) as response:
                    html = response.read().decode("utf-8")
                soup = BeautifulSoup(html, "html.parser")
                messages = soup.find_all("div", class_="commentbody")
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
                    result["data"].append(item)

                    con = conPool.get_connection()
                    cursor = con.cursor()
                    cursor.execute(
                        "INSERT INTO businessComment (doctor, author, timestamp, comment) VALUES (%s, %s,%s, %s)", (keyword, author, timestamp, comment))
                    con.commit()
                    cursor.close()
                    con.close()
                print("商周好了")
                return result
            else:
                pass
    except:
        pass
    return result


def crawlReview(inputtext):
    def getReviews(keyword, result):
        Title = driver.find_element(By.CSS_SELECTOR, "h1").text
        # if "Hospital" in Title or "Clinic" in Title or "醫" in Title or "診所" in Title:
        print("函數中")
        Btn = driver.find_elements(By.CLASS_NAME, "Gpq6kf")[1]  # 點選評論
        Btn.click()
        time.sleep(1)
        print(Btn.text)
        print("點選評論")
        print(Btn)
        Search = driver.find_elements(By.CLASS_NAME, "g88MCb")[1]  # 點選搜尋
        Search.click()
        time.sleep(1)
        print("點選搜尋")
        print(Search)
        Input = driver.find_element(By.CLASS_NAME, 'LCTIRd')
        Input.send_keys(keyword)  # 輸入搜尋
        Input.send_keys(Keys.ENTER)
        time.sleep(3)
        print("輸入搜尋")
        # sort = driver.find_element(
        #     By.XPATH, "//*[contains(text(), '排序')]")  # 選擇排序
        # sort.click()
        # time.sleep(1)

        # new = driver.find_elements(By.CLASS_NAME, 'fxNQSd')[1]  # 選擇最新
        # new.click()
        count = 0
        container = driver.find_element(By.CLASS_NAME, 'DxyBCb')
        print("在小框框內")
        print(container)
        print("迴圈即將開始")
        print(container.text)
        for i in range(5):
            print(i)
            driver.execute_script(
                "arguments[0].scrollBy(0, arguments[0].scrollHeight);", container)
            print("下滑視窗")
            try:
                mores = driver.find_elements(By.CLASS_NAME, 'w8nwRe')
                for more in mores:
                    more.click()
                print("下滑視窗")
            except:
                pass
            time.sleep(3)
            reviews = driver.find_elements(By.CLASS_NAME, 'jJc9Ad')
            for review in reviews:
                name = review.find_element(By.CLASS_NAME, 'd4r55 ').text
                print(name)
        print("下滑資料")
        reviews = driver.find_elements(By.CLASS_NAME, 'jJc9Ad')
        for review in reviews:
            count += 1
            name = review.find_element(By.CLASS_NAME, 'd4r55 ').text

            star = review.find_element(
                By.CLASS_NAME, 'kvMYJc').get_attribute("aria-label")

            when = review.find_element(By.CLASS_NAME, 'rsqaWe').text

            try:
                comment = review.find_element(By.CLASS_NAME, 'wiI7pd').text
            except:
                comment = ""
            result["title"] = Title

            item = {}
            item["location"] = Title
            item["name"] = name
            item["star"] = star
            item["when"] = when
            item["comment"] = comment
            result["data"].append(item)
            print("裝入資料")
        return result

    options = Options()
    ua = UserAgent()
    user_agent = ua.random  # 偽裝隨機產生瀏覽器、作業系統
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('start-maximized')
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-browser-side-navigation')
    options.add_argument('enable-automation')
    options.add_argument('--disable-infobars')
    options.add_argument('enable-features=NetworkServiceInProcess')
    options.add_experimental_option("detach", True)  # 加入後不會閃退
    options.add_argument('--lang=zh-tw')
    options.page_load_strategy = 'normal'
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    try:
        keyword = inputtext.split()[0]
        location = inputtext.split()[1]
    except:
        keyword = inputtext
        location = ""

    if location == "":
        driver.get("https://www.google.com.tw/maps/search/"+keyword+"醫")
        print(keyword)
        print("https://www.google.com.tw/maps/search/"+keyword+"醫")
    else:
        driver.get("https://www.google.com.tw/maps/search/"+location+"醫院")
        print(location)
    # driver.get("https://www.google.com.tw/maps/search/"+inputtext+"醫")

    time.sleep(1)
    Linkst = []

    i = 0
    sponsors = driver.find_elements(By.CLASS_NAME, 'jHLihd')
    for sponsor in sponsors:
        i += 1
        print(sponsor.text)
    Links = driver.find_elements(By.CLASS_NAME, 'hfpxzc')
    print(str(len(Links))+"個連結")

    try:
        linkLength = len(Links) - i
        if linkLength > 3:
            linkLength = 3
        for j in range(i, linkLength):
            Link = Links[j].get_attribute("href")
            print("連結")
            print(Link)
            if "&entry=ttu" not in Link:
                Link = Link + "&entry=ttu"
                print("更新後的連結")
                print(Link)
            Linkst.append(Link)
    except:
        pass

    result = {}
    result["data"] = []
    try:
        if len(Linkst) == 0:
            print("沒有其他連結")
            Title = driver.find_element(By.CSS_SELECTOR, "h1").text
            print(Title)
            getReviews(keyword, result)
        else:
            for link in Linkst:
                if len(result["data"]) == 0:
                    driver.get(link)
                    print("外開視窗")
                    while True:
                        try:
                            driver.find_elements(By.CLASS_NAME, "Gpq6kf")[
                                1]  # 點選評論
                            getReviews(keyword, result)
                            break
                        except:
                            driver.get(link)
                else:
                    print("已經有資料了")
                    break
    except:
        print("exception")

    driver.close()
    driver.quit()
    return result


def readJudgment(keyword):
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
    options.add_argument('--remote-debugging-port=8080')

    options.add_experimental_option("detach", True)  # 加入後不會閃退
    options.page_load_strategy = 'normal'
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    driver.get("https://judgment.judicial.gov.tw/FJUD/default.aspx")
    Input = driver.find_element(By.ID, 'txtKW')
    Input.send_keys('(被告'+keyword+'+被上訴人'+keyword+'+相對人' +
                    keyword+'+被告醫院之履行輔助人'+keyword+')&(醫生+醫師)')
    Btn = driver.find_element(By.ID, 'btnSimpleQry')
    Btn.send_keys(Keys.ENTER)
    driver.switch_to.frame('iframe-data')

    time.sleep(1)
    links = driver.find_elements(By.CLASS_NAME, 'hlTitle_scroll')
    # tags = driver.find_elements(By.CLASS_NAME, 'tdCut')
    result = {}
    result["data"] = []

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
            "INSERT INTO judgment (doctor, link, title) VALUES (%s, %s,%s)", (keyword, link, title))
        con.commit()
        cursor.close()
        con.close()

    driver.close()
    driver.quit()
    print("司法院好了")
    return result


def readThank(keyword):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT thankUrl.url, thank.target, thank.content, thank.month FROM thank LEFT JOIN thankUrl ON thank.month = thankUrl.month WHERE content LIKE %s;", ("%" + keyword + "%",))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data


def viewThank(data):
    result = {}
    result["data"] = []
    for d in data:
        item = {}
        item["url"] = d[0]
        item["title"] = d[1]
        item["text"] = d[2]
        item["when"] = d[3]
        result["data"].append(item)
    return result


def readPtt(keyword):
    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_PTT = get_key(".env", "SEARCH_ENGINE_ID_PTT")
    query = keyword + "醫生"
    page = 1
    result = {}
    result["data"] = []

    while True:
        start = (page - 1) * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID_PTT}&q={query}&start={start}"

        data = requests.get(url).json()
        try:
            for i in range(len(data["items"])):
                boards = ["Doctor-Info", "allergy", "Anti-Cancer", "Nurse",
                          "BabyMother", "BigPeitou", "BigShiLin", "GoodPregnan", ]
                for board in boards:
                    if board in data["items"][i]["link"]:
                        if ("徵才" not in data["items"][i]["title"] and "新聞" not in data["items"][i]["title"] and keyword in data["items"][i]["snippet"]):

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
                                "INSERT INTO Ptt (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (keyword, link, title, text))
                            con.commit()
                            cursor.close()
                            con.close()

            page += 1
        except:
            break
    print("Ptt好了")
    return result


def readSearch(keyword):
    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_ALL = get_key(".env", "SEARCH_ENGINE_ID_ALL")
    query = keyword+"醫"+"感謝"
    page = 1
    result = {}
    result["data"] = []

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
                    "INSERT INTO search (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (keyword, link, title, text))
                con.commit()
                cursor.close()
                con.close()

    except:
        item = {}
        item["url"] = ""
        item["title"] = ""
        item["text"] = ""
        result["data"].append(item)
    print("Search好了")
    return result


def readBlog(keyword):
    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_BLOG = get_key(".env", "SEARCH_ENGINE_ID_BLOG")
    query = '"'+keyword+'"+"醫"'
    page = 1
    result = {}
    result["data"] = []

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
                        "INSERT INTO blog (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (keyword, link, title, text))
                    con.commit()
                    cursor.close()
                    con.close()

    except:
        pass
    print("Blog好了")
    return result


mysql_user = get_key(".env", "user")
mysql_password = get_key(".env", "password")

app = Flask(
    __name__,
    static_folder="public",
    static_url_path="/"
)


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
    data = readThank(keyword)
    result = viewThank(data)
    return result, 200


@app.route("/api/Ptt/<keyword>")
def getPtt(keyword):
    result = readPtt(keyword)
    return result, 200


@app.route("/api/search/<keyword>")
def getSearch(keyword):
    result = readSearch(keyword)
    return result, 200


@app.route("/api/blog/<keyword>")
def getBlog(keyword):
    result = readBlog(keyword)
    return result, 200


@app.route("/api/judgment/<keyword>")
def getJudgment(keyword):
    result = readJudgment(keyword)
    return result, 200


@app.route("/api/review/<inputtext>")
def getReview(inputtext):
    result = readReview(inputtext)
    return result, 200


@app.route("/api/business/<keyword>")
def getBusiness(keyword):
    result = readBusiness(keyword)
    return result, 200


@app.route("/api/<keyword>")
def getAll(keyword):
    T3 = time.perf_counter()
    threads = []
    threads.append(threading.Thread(target=readReview,
                   args=(keyword,)))
    threads.append(threading.Thread(target=readBusiness,
                   args=(keyword,)))
    threads.append(threading.Thread(target=readJudgment,
                   args=(keyword,)))
    threads.append(threading.Thread(target=readPtt,
                   args=(keyword,)))
    threads.append(threading.Thread(target=readSearch,
                   args=(keyword,)))
    threads.append(threading.Thread(target=readBlog,
                   args=(keyword,)))
    for i in range(6):
        threads[i].start()

    for i in range(6):
        threads[i].join()
    result = {}
    result["ok"] = True
    T4 = time.perf_counter()
    print("全都好了")
    print('%s毫秒' % ((T4 - T3)*1000))
    return result, 200


app.run(host="0.0.0.0", port=8080)
