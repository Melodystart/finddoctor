import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import pdfplumber
import os
from elasticsearch import Elasticsearch
es = Elasticsearch("http://localhost:9200/")


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
                pass

    for r in result:
        # 感謝函月份、感謝對象、感謝內容
        res = es.index(index="thank", document={
            "month": title,
            "target": r[0],
            "content": r[1],
        })

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
                    res = es.index(index="thank", document={
                        "month": title,
                        "target": target,
                        "content": content,
                    })
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
                        res = es.index(index="thank", document={
                            "month": title,
                            "target": target,
                            "content": content,
                        })
                except:
                    pass
    except:
        pass


def crawl_letter():
    try:
        es.indices.create(index="thank",
                          body={"settings": {
                              "index": {"number_of_replicas": 0}}})

        es.indices.create(index="thankurl",
                          body={"settings": {
                              "index": {"number_of_replicas": 0}}})
    except:
        pass

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

            # 確認感謝函月份是否已存於資料庫
            res = es.search(index='thankurl', query={
                "match_phrase": {
                    "month": title
                }
            })

            if len(res['hits']['hits']) == 0:

                if "../" in url:
                    url = "https://www.vghtpe.gov.tw/" + url.replace("../", "")
                    thankPDF(title, url)
                elif ".pdf" in url:
                    thankPDF(title, url)
                else:
                    thankWEB(title, url)

                # 感謝函名稱、URL存放於資料庫
                res = es.index(index="thankurl", document={
                    "month": title,
                    "url": url,
                })
            else:
                break

crawl_letter()