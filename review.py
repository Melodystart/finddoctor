# 取得地址ID
# url = f"https://maps.googleapis.com/maps/api/place/textsearch/xml?query={query}&key={key}"
# https://maps.googleapis.com/maps/api/place/textsearch/xml?query=陳威明&key={key}

# https://places.googleapis.com/v1/places:searchText/xml?query=陳威明&key={key}

# 只有5個reviews
# url = "https://maps.googleapis.com/maps/api/place/details/json?place_id=ChIJq6q6AoquQjQRk27N2_Y8tWE&key={key}"

# https://places.googleapis.com/v1/places/ChIJq6q6AoquQjQRk27N2_Y8tWE?fields=id,displayName,reviews&key={key}

# data = requests.get(url).json()

# print(data)

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.options import Options
# import time
# from fake_useragent import UserAgent


# def getReviews(keyword):
#     Title = driver.find_element(By.CSS_SELECTOR, "h1").text

#     if "醫" in Title or "診所" in Title:
#         print(Title)
#         Btn = driver.find_element(By.XPATH, "//button[2]")  # 點選評論
#         Btn.click()
#         time.sleep(1)

#         Search = driver.find_elements(By.CLASS_NAME, "g88MCb")[1]  # 點選搜尋
#         Search.click()
#         time.sleep(1)

#         Input = driver.find_element(By.CLASS_NAME, 'LCTIRd')
#         Input.send_keys(keyword)  # 輸入搜尋
#         Input.send_keys(Keys.ENTER)

#         sort = driver.find_element(
#             By.XPATH, "//*[contains(text(), '排序')]")  # 選擇排序
#         sort.click()
#         time.sleep(1)

#         new = driver.find_elements(By.CLASS_NAME, 'fxNQSd')[1]  # 選擇最新
#         new.click()
#         count = 0
#         for i in range(10):
#             try:
#                 container = driver.find_element(By.CLASS_NAME, 'DxyBCb')
#                 driver.execute_script(
#                     "arguments[0].scrollBy(0, arguments[0].scrollHeight);", container)
#                 mores = driver.find_elements(By.CLASS_NAME, 'w8nwRe')
#                 for more in mores:
#                     more.click()
#             except:
#                 break

#         reviews = driver.find_elements(By.CLASS_NAME, 'jJc9Ad')
#         for review in reviews:
#             count += 1
#             name = review.find_element(By.CLASS_NAME, 'd4r55 ')
#             print(name.text)

#             star = review.find_element(
#                 By.CLASS_NAME, 'kvMYJc').get_attribute("aria-label")
#             print(star)

#             when = review.find_element(By.CLASS_NAME, 'rsqaWe')
#             print(when.text)

#             try:
#                 comment = review.find_element(By.CLASS_NAME, 'wiI7pd')
#                 print(comment.text)
#             except:
#                 pass
#             print("---counts:"+str(count) +
#                   "-------------------------------------------------")
#     else:
#         pass

# options = Options()
# ua = UserAgent()
# user_agent = ua.random  # 偽裝隨機產生瀏覽器、作業系統
# options.add_argument(f'--user-agent={user_agent}')
# options.add_argument('headless')

# options.add_argument('--headless')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('start-maximized')
# options.add_argument("--disable-extensions")
# options.add_argument('--disable-browser-side-navigation')
# options.add_argument('enable-automation')
# options.add_argument('--disable-infobars')
# options.add_argument('enable-features=NetworkServiceInProcess')
# options.add_argument('--disable-dev-shm-usage')

# options.add_experimental_option("detach", True)  # 加入後不會閃退
# options.page_load_strategy = 'normal'
# driver = webdriver.Chrome(options=options)
# driver.maximize_window()

# keyword = "陳威明"
# driver.get("https://www.google.com.tw/maps/search/"+keyword)

# time.sleep(1)
# Linkst = []

# try:
#     for i in range(3):
#         Link = driver.find_elements(By.CLASS_NAME, 'hfpxzc')[
#             i].get_attribute("href")
#         Linkst.append(Link)
# except:
#     pass

# try:
#     if len(Linkst) == 0:
#         getReviews(keyword)
#     else:
#         for link in Linkst:
#             driver.get(link)
#             getReviews(keyword)
# except:
#     print("I am here")

# driver.close()
# driver.quit()

# import urllib.request
# import urllib.parse
# from bs4 import BeautifulSoup


# url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?query="陳威明"+"醫"&key={MAP_KEY}'

from serpapi import GoogleSearch

params = {
    "engine": "google_maps_reviews",
    "place_id": "ChIJq6q6AoquQjQRk27N2_Y8tWE",
    "api_key": "2bbe87bdc30b92ff1e70918a097cd5824459f84ed4cd81b5df68b49f9f178985"
}

search = GoogleSearch(params)
results = search.get_dict()
reviews = results["reviews"]
print(reviews)
print(results)
