import mysql.connector
from mysql.connector import pooling
import urllib.request
from bs4 import BeautifulSoup

#網頁編碼有utf8 就用utf8
#若為big5 則轉換為 big5-hkscs
#https://sjkou.net/2017/01/06/python-requests-encoding/


con = mysql.connector.connect(
    host='localhost',           
    user='root',                
    password='password',
)
cursor = con.cursor()

# 建立資料庫、table
cursor.execute("DROP database IF EXISTS finddoctor;")
cursor.execute("CREATE database finddoctor;")
cursor.execute("USE finddoctor;")
cursor.execute("CREATE table doctor (id BIGINT PRIMARY KEY auto_increment,department VARCHAR(255) NOT NULL,name VARCHAR(255) NOT NULL,url TEXT NOT NULL);")

def getSoup(url):
  with urllib.request.urlopen(url) as response:
    html = response.read().decode("big5-hkscs")
    return BeautifulSoup(html,"html.parser")

def getUrl(words):
  first = words.index("'")+1
  end = words.index("'",first)
  return words[slice(first, end)]

url ="https://www6.vghtpe.gov.tw/reg/sectList.do?type=return"

departmentList = getSoup(url).find_all('a')

for i in range(len(departmentList)):
  if "opdTimetable" in departmentList[i].get("href"):
    url_1 = "https://www6.vghtpe.gov.tw/reg/" +departmentList[i].get("href")
    url_2 = url_1.replace("page=1","page=2")
    urlList = [url_1, url_2]
    department = departmentList[i].text
    doctorNameList = []

    for url in urlList:
      doctorList = getSoup(url).find_all("a")

      for i in range(len(doctorList)):
        if "javascript:CreateWindow(" in doctorList[i].get("href"):
          url = getUrl(doctorList[i].get("href"))
          doctor = doctorList[i].text.strip()

          if (doctor not in doctorNameList) & len(doctor)>0:
            doctorNameList.append(doctor)
            cursor.execute("INSERT INTO doctor (department, name, url) VALUES (%s, %s,%s)",(department, doctor, url))
            con.commit()

cursor.close()
con.close()
