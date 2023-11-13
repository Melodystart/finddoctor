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
# import threading

conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
    ".env", "password"), host='localhost', database='finddoctor', pool_name='findConPool', pool_size=10,  auth_plugin='mysql_native_password')


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

    for i in range(len(data["items"])):
        if (query+"醫師介紹和評價") in data["items"][i]["title"]:
            url = data["items"][i]["link"]
            result["url"] = url
            result["title"] = data["items"][i]["title"]
            with urllib.request.urlopen(url) as response:
                html = response.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            messages = soup.find_all("div", class_="commentbody")
            for message in messages:
                posttime = message.find("div", class_="posttime").text
                commentPart = message.find("p", class_="commentcont-part").text
                commentAll = message.find("p", class_="commentcont-all").text
                if len(commentAll) == 0:
                    comment = commentPart
                else:
                    comment = commentAll
                item = {}
                item["posttime"] = posttime
                item["comment"] = comment
                result["data"].append(item)
            return result
        else:
            pass


def readReview(inputtext):
    def getReviews(keyword, result):
        Title = driver.find_element(By.CSS_SELECTOR, "h1").text
        # if "Hospital" in Title or "Clinic" in Title or "醫" in Title or "診所" in Title:
        print("函數中")
        Btn = driver.find_element(By.XPATH, "//button[2]")  # 點選評論
        Btn.click()
        time.sleep(1)
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
        time.sleep(5)
        print("輸入搜尋")
        print(Input)
        # sort = driver.find_element(
        #     By.XPATH, "//*[contains(text(), '排序')]")  # 選擇排序
        # sort.click()
        # time.sleep(1)

        # new = driver.find_elements(By.CLASS_NAME, 'fxNQSd')[1]  # 選擇最新
        # new.click()
        count = 0
        for i in range(10):
            try:
                container = driver.find_element(By.CLASS_NAME, 'DxyBCb')
                print(container)
                driver.execute_script(
                    "arguments[0].scrollBy(0, arguments[0].scrollHeight);", container)
                mores = driver.find_elements(By.CLASS_NAME, 'w8nwRe')
                for more in mores:
                    more.click()
            except:
                break
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

    linkLength = len(Links) - i

    if linkLength > 3:
        linkLength = 3

    for j in range(i, linkLength):
        Link = Links[j].get_attribute("href")
        print(Link)
        Linkst.append(Link)

    result = {}
    result["data"] = []
    try:
        if len(Linkst) == 0:
            getReviews(keyword, result)
        else:
            for link in Linkst:
                if len(result["data"]) == 0:
                    driver.get(link)
                    print("外開視窗")
                    getReviews(keyword, result)
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

    for link in links:
        item = {}
        item["url"] = link.get_attribute("href")
        item["title"] = link.text
        result["data"].append(item)

    driver.close()
    driver.quit()

    return result


def readThank(keyword):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT thankUrl.url, thank.target, thank.content FROM thank LEFT JOIN thankUrl ON thank.month = thankUrl.month WHERE content LIKE %s;", ("%" + keyword + "%",))
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
        result["data"].append(item)
    return result


def readPtt(keyword):
    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_PTT = get_key(".env", "SEARCH_ENGINE_ID_PTT")
    query = keyword
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
                        if ("徵才" not in data["items"][i]["title"] and "新聞" not in data["items"][i]["title"] and "新聞" not in data["items"][i]["snippet"]):
                            item = {}
                            item["url"] = data["items"][i]["link"]
                            item["title"] = data["items"][i]["title"]
                            item["text"] = data["items"][i]["snippet"]
                            result["data"].append(item)

            page += 1
        except:
            break
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
                item = {}
                item["url"] = data["items"][i]["link"]
                item["title"] = data["items"][i]["title"]
                item["text"] = data["items"][i]["snippet"]
                result["data"].append(item)
    except:
        item = {}
        item["url"] = ""
        item["title"] = ""
        item["text"] = ""
        result["data"].append(item)

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
                    item = {}
                    item["url"] = data["items"][i]["link"]
                    item["title"] = data["items"][i]["title"]
                    item["text"] = data["items"][i]["snippet"]
                    result["data"].append(item)
    except:
        item = {}
        item["url"] = ""
        item["title"] = ""
        item["text"] = ""
        result["data"].append(item)

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
    result = readBusiness(keyword)
    return result, 200


app.run(host="0.0.0.0", port=8080)
