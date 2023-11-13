import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import pdfplumber
import os
import mysql.connector
from mysql.connector import pooling

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
)
cursor = con.cursor()

# 建立table
cursor.execute("DROP database IF EXISTS finddoctor;")
cursor.execute("CREATE database finddoctor;")
cursor.execute("USE finddoctor;")
cursor.execute("DROP table IF EXISTS thank;")
cursor.execute("DROP table IF EXISTS thankUrl;")
cursor.execute(
    "CREATE table thank (id BIGINT PRIMARY KEY auto_increment,month VARCHAR(255),target TEXT,content TEXT NOT NULL);")
cursor.execute(
    "CREATE table thankUrl (id BIGINT PRIMARY KEY auto_increment,month VARCHAR(255),url TEXT NOT NULL);")


def thankPDF(title, url):

    try:
        urllib.request.urlopen(url)
    except:
        first = url.index("thank/") + 6
        needTranscode = url[slice(first, len(url))]
        url = "https://www.vghtpe.gov.tw/vghtpe/files/PDF/thank/" + \
            urllib.parse.quote(needTranscode)

    with urllib.request.urlopen(url) as response:
        f = open(os.path.join("test.pdf"), "wb")
        f.write(response.read())
        f.close()

    pdf = pdfplumber.open('test.pdf')
    pages = pdf.pages
    result = []

    for i in range(len(pages)):
        page = pdf.pages[i]
        try:
            tables = page.extract_tables()[0]
        except:
            tables = page.extract_tables()
            print("表格異常")
            print(tables)

        for j in range(len(tables)):
            item = []
            orginText = tables[j][0]

            while None in tables[j]:
                tables[j].remove(None)
            while "" in tables[j]:
                tables[j].remove("")

            if len(tables[j]) == 2:
                target = tables[j][0].replace("\n", "")
                content = tables[j][1].replace("\n", "")
                if (orginText == None or orginText == ""):
                    result[(len(result)-1)][0] += target
                    result[(len(result)-1)][1] += content
                else:
                    item.append(target)
                    item.append(content)
                    result.append(item)

            elif len(tables[j]) == 3:
                target = tables[j][1].replace("\n", "")
                content = tables[j][2].replace("\n", "")
                if (target != "摘要" and content != "內容"):
                    item.append(target)
                    item.append(content)
                    result.append(item)

            elif len(tables[j]) == 1:
                content = tables[j][0].replace("\n", "")
                result[(len(result)-1)][1] += content

            else:
                print("-----------資料異常，需另處理------------")
                print(url)
                print(tables[j])

    for r in result:
        # 感謝函月份、感謝對象、感謝內容
        cursor.execute(
            "INSERT INTO thank (month, target, content) VALUES (%s, %s,%s)", (title, r[0], r[1]))
        con.commit()

    pdf.close()
    os.remove("test.pdf")


def thankWEB(title, url):
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        result = soup.find_all('tr')

        for tr in result:
            try:
                td = tr.find_all("td")
                target = td[1].find("span").text
                if target == "":
                    target = td[1].text
                content = ""
                span = td[2].find_all(string=True)
                for sentence in span:
                    content += sentence.strip()
                if target != "摘要":
                    # 感謝函月份、感謝對象、感謝內容
                    cursor.execute(
                        "INSERT INTO thank (month, target, content) VALUES (%s, %s,%s)", (title, target, content))
                    con.commit()
            except:
                try:
                    td = tr.find_all("td")
                    target = td[1].text
                    content = ""
                    span = td[2].find_all(string=True)
                    for sentence in span:
                        content += sentence.strip()
                    if target != "摘要":
                        # 感謝函月份、感謝對象、感謝內容
                        cursor.execute(
                            "INSERT INTO thank (month, target, content) VALUES (%s, %s,%s)", (title, target, content))
                        con.commit()
                except:
                    print("我是122")
                    print(title)
                    print("感謝對象"+target)
                    print("感謝內容"+content)
                    print(url)
    except:
        print("我是128")
        print(title, url)


url = "https://www.vghtpe.gov.tw/Fpage.action?muid=6231"

with urllib.request.urlopen(url) as response:
    html = response.read().decode("utf-8")
soup = BeautifulSoup(html, "html.parser")

result = soup.find_all('td')

for td in result:
    item = td.find_all('a')
    if len(item) != 0:
        title = item[0].find('span').text
        url = item[0].get("href")

        if "../" in url:
            url = "https://www.vghtpe.gov.tw/" + url.replace("../", "")
            thankPDF(title, url)
        elif ".pdf" in url:
            thankPDF(title, url)
        else:
            thankWEB(title, url)

        # 每月感謝函名稱、URL
        cursor.execute(
            "INSERT INTO thankUrl (month, url) VALUES (%s, %s)", (title, url))
        con.commit()

cursor.close()
con.close()
