import mysql.connector
import urllib.request
from bs4 import BeautifulSoup
from dotenv import get_key
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

con = mysql.connector.connect(
    host='finddoctor.collqfqpnilo.us-west-2.rds.amazonaws.com',
    user=get_key(".env", "user"),
    password=get_key(
        ".env", "password")
)
cursor = con.cursor()

cursor.execute("DROP database IF EXISTS finddoctor;")
cursor.execute("CREATE database finddoctor;")
cursor.execute("USE finddoctor;")
cursor.execute("DROP table IF EXISTS review;")
cursor.execute("DROP table IF EXISTS businessComment;")
cursor.execute("DROP table IF EXISTS judgment;")
cursor.execute("DROP table IF EXISTS Ptt;")
cursor.execute("DROP table IF EXISTS Dcard;")
cursor.execute("DROP table IF EXISTS search;")
cursor.execute("DROP table IF EXISTS blog;")
cursor.execute("DROP table IF EXISTS record;")

cursor.execute(
    "CREATE table record (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255), createdAt DATE DEFAULT (CURRENT_DATE));")
cursor.execute(
    "CREATE table review (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255), author VARCHAR(255),star BIGINT, timestamp TEXT,review TEXT, link TEXT, location VARCHAR(255), createdAt DATE DEFAULT (CURRENT_DATE));")
cursor.execute(
    "CREATE table businessComment (id BIGINT PRIMARY KEY auto_increment, doctor VARCHAR(255), author VARCHAR(255), timestamp TEXT, comment TEXT, createdAt DATE DEFAULT (CURRENT_DATE),link TEXT,location TEXT);")
cursor.execute(
    "CREATE table judgment (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, createdAt DATE DEFAULT (CURRENT_DATE));")
cursor.execute(
    "CREATE table Ptt (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, text TEXT, createdAt DATE DEFAULT (CURRENT_DATE));")
cursor.execute(
    "CREATE table search (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, text TEXT, createdAt DATE DEFAULT (CURRENT_DATE));")
cursor.execute(
    "CREATE table blog (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, text TEXT, createdAt DATE DEFAULT (CURRENT_DATE));")
cursor.execute(
    "CREATE table Dcard (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, text TEXT, createdAt DATE DEFAULT (CURRENT_DATE));")


# 取得榮總醫生掛號名單
def getDoctorList():
    def getSoupDoctor(url):
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("big5-hkscs")
            return BeautifulSoup(html, "html.parser")

    def getUrl(words):
        first = words.index("'")+1
        end = words.index("'", first)
        return words[slice(first, end)]

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


getPttBoard()
getDoctorList()

cursor.close()
con.close()
