import urllib.request
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
        f = open("test.pdf", "wb")
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
        # cursor.execute(
        #     "INSERT INTO thank (month, target, content) VALUES (%s, %s,%s)", (title, r[0], r[1]))
        # con.commit()

        res = es.index(index="thank", document={
            "month": title,
            "target": r[0],
            "content": r[1],
        })

    pdf.close()
    # os.remove("test.pdf")


thankPDF("105年11月感謝函", "https://www.vghtpe.gov.tw/vghtpe/files/PDF/thank/105%E5%B9%B411%E6%9C%88%E6%84%9F%E8%AC%9D%E5%87%BD.pdf")
