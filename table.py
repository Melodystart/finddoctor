import urllib.request
from bs4 import BeautifulSoup
import ssl
from model import *
from py_test import *

ssl._create_default_https_context = ssl._create_unverified_context

# 取得榮總醫生掛號名單
def getDoctorList():
    def getSoupDoctor(url):
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("big5-hkscs")
            return BeautifulSoup(html, "html.parser")

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
                            save_doctor(department, doctor, url)

# 取得PTT醫療板及地區板
def getPttBoard():
    def getsoup(link):
        request = urllib.request.Request(link, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })

        with urllib.request.urlopen(request) as response:
            html = response.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        return soup

    url_taiwan = "https://www.ptt.cc/cls/9217"
    soup = getsoup(url_taiwan)
    areas = soup.find_all("a", class_="board")

    for area in areas:
        url_location = "https://www.ptt.cc"+area.get("href")
        soup1 = getsoup(url_location)
        boards = soup1.find_all("div", class_="board-name")
        for board in boards:
            save_pttboard(board)

    url_health = "https://www.ptt.cc/cls/7957"
    soup2 = getsoup(url_health)
    boards = soup2.find_all("div", class_="board-name")
    for board in boards:
        save_pttboard(board)


create_table()
getPttBoard()
getDoctorList()