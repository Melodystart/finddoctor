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
from datetime import datetime
import time
import threading
from model import *
from view import *

selenium_counts = 0

def call_reviewAPI(place_id, keyword, result, inputtext):
    api_client = ApiClient(
        api_key=get_key(".env", "review_api_key"))
    results = api_client.google_maps_reviews(
        place_id, reviews_limit=1, reviews_query=keyword, sort="newest", language="zh-TW", region="TW")
    try:
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

                item = view_setitem_review(location,author,review_rating,review_until,review,review_link)
                result["data"].append(item)

                # try:
                save_review(inputtext, author, review_rating, review_timestamp, review, review_link, location)
                # except:
                #     pass
    except:
        pass

def Review(inputtext):
    cache = r.lrange("Review-"+inputtext,0,-1)
    if len(cache) != 0:
        return Redis(cache)

    try:
        keyword = inputtext.split()[0]
        location = inputtext.split()[1]
        query = location
    except:
        keyword = inputtext
        query = inputtext + "醫"

    data = get_review(inputtext)

    result = {}
    result["data"] = []
    
    if len(data) != 0:
        result = view_redis_review(data, inputtext, result)
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
                    target=call_reviewAPI, args=(places[i], keyword, result,inputtext)))
                threads[i].start()

            timeout = 60
            for i in range(counts):
                threads[i].join(timeout)
        except:
            pass

        check_no_review(inputtext)
    return result, 200

def Business(inputtext):
    cache = r.lrange("Business-"+inputtext,0,-1)
    if len(cache) != 0:
        return Redis(cache)

    API_KEY = get_key(".env", "API_KEY")
    SEARCH_ENGINE_ID_BUSINESS = get_key(".env", "SEARCH_ENGINE_ID_BUSINESS")

    query = inputtext + "醫師介紹和評價"
    page = 1
    result = {}
    result["data"] = []

    data = get_business(inputtext)

    if len(data) != 0:
        result = view_redis_business(data, inputtext, result)
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

                        item = view_setitem_business(author,timestamp,comment,link,location)
                        result["data"].append(item)

                        save_business(inputtext, author, timestamp, comment, link, location)
        except:
            pass
    return result, 200

def Judgment(inputtext):
    cache = r.lrange("Judgment-"+inputtext,0,-1)
    if len(cache) != 0:
        return Redis(cache)

    global selenium_counts
    result = {}
    result["data"] = []

    data = get_judgment(inputtext)

    if len(data) != 0:
        result = view_redis_judgment(data,inputtext, result)
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
                    save_judgment(inputtext, "", "搜尋不到資料：關鍵字可嘗試僅輸入醫生名稱，例如：王大明")
                else:
                    for l in links:
                        link = l.get_attribute("href")
                        title = l.text

                        item = view_setitem_judgment(link, title)
                        result["data"].append(item)
                        save_judgment(inputtext, link, title)
            except:
                pass
            driver.close()
            selenium_counts -= 1
        else:
            result["busy"] = True
    return result, 200

def Ptt(inputtext):
    cache = r.lrange("Ptt-"+inputtext,0,-1)
    if len(cache) != 0:
        return Redis(cache)

    result = {}
    result["data"] = []
    data, data_board = get_ptt(inputtext)
    boards = ["Nurse", "BabyMother", "GoodPregnan", "Laser_eye",
                "hair_loss", "facelift", "teeth_salon", "KIDs", "Preschooler"]
    for d in data_board:
        boards.append(d[0])

    if len(data) != 0:
        result = view_redis_ptt(data, inputtext, result)
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

                                item = view_setitem_ptt(link,title,text)
                                result["data"].append(item)
                                save_ptt(inputtext, link, title, text)
                page += 1
            except:
                break
    return result, 200

def Search(inputtext):
    cache = r.lrange("Search-"+inputtext,0,-1)
    if len(cache) != 0:
        return Redis(cache)

    result = {}
    result["data"] = []
    data = get_search(inputtext)

    if len(data) != 0:
        result = view_redis_search(data, inputtext, result)
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

                    item = view_setitem_search(link, title, text)
                    result["data"].append(item)
                    save_search(inputtext, link, title, text)
        except:
            pass
    return result, 200

def Dcard(inputtext):
    cache = r.lrange("Dcard-"+inputtext,0,-1)
    if len(cache) != 0:
        return Redis(cache)

    result = {}
    result["data"] = []
    data = get_dcard(inputtext)

    if len(data) != 0:
        result = view_redis_dcard(data, inputtext, result)
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

                        item = view_setitem_dcard(link,title,text)
                        result["data"].append(item)
                        save_dcard(inputtext, link, title, text)
                page += 1
            except:
                break
    return result, 200

def Blog(inputtext):
    cache = r.lrange("Blog-"+inputtext,0,-1)
    if len(cache) != 0:
        return Redis(cache)

    result = {}
    result["data"] = []
    data = get_blog(inputtext)

    if len(data) != 0:
        result = view_redis_blog(data, inputtext, result)
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

                            item = view_setitem_blog(link,title,text)
                            result["data"].append(item)
                            save_blog(inputtext, link, title, text)
                page += 1
            except:
                break
    return result, 200

def get_all(inputtext):
    T1 = time.perf_counter()
    threads = []
    threads.append(threading.Thread(target=Review,
                   args=(inputtext,)))
    threads.append(threading.Thread(target=Business,
                   args=(inputtext,)))
    threads.append(threading.Thread(target=Ptt,
                   args=(inputtext,)))
    threads.append(threading.Thread(target=Search,
                   args=(inputtext,)))
    threads.append(threading.Thread(target=Blog,
                   args=(inputtext,)))
    threads.append(threading.Thread(target=Dcard,
                   args=(inputtext,)))

    for i in range(6):
        threads[i].start()

    for i in range(6):
        threads[i].join()

    result = {}
    result["ok"] = True
    T2 = time.perf_counter()
    print(inputtext+"全部："+'%s毫秒' % ((T2 - T1)*1000))
    return result

def update_data():
    data = get_expired_searched()
    # 刪除7日前搜尋計數
    for d in data:
        r.zincrby('search_count', -1, d[0])
    delete_expired_data()
    data = get_mostsearched()
    for d in data:
        keyword = d[0]
        get_all(keyword)
