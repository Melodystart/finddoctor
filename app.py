from function import *
from elastic import *
import time
from flask import *
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(
    __name__,
    static_folder="public",
    static_url_path="/"
)

crawlerletter()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/thank")
def thankPage():
    return render_template("thank.html")


@app.route("/Ptt")
def PttPage():
    return render_template("Ptt.html")


@app.route("/search")
def searchPage():
    return render_template("search.html")


@app.route("/Dcard")
def DcardPage():
    return render_template("Dcard.html")


@app.route("/blog")
def blogPage():
    return render_template("blog.html")


@app.route("/judgment")
def judgmentPage():
    return render_template("judgment.html")


@app.route("/review")
def reviewPage():
    return render_template("review.html")


@app.route("/business")
def businessPage():
    return render_template("business.html")


@app.route("/api/doctor")
def getDoctor():
    result = Doctor()
    return result


@app.route("/api/mostsearch/<inputtext>")
def getMost(inputtext):
    if inputtext != "default":
        con = conPool.get_connection()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO record (doctor) VALUES (%s)", (inputtext, ))
        con.commit()
        cursor.close()
        con.close()
    result = Most()
    return result


@app.route("/api/thank/<inputtext>")
def getthank(inputtext):
    T1 = time.perf_counter()
    data = Thank(inputtext)
    result = viewThank(data)
    T2 = time.perf_counter()
    print(inputtext+"感謝函好了："+'%s毫秒' % ((T2 - T1)*1000))
    return result


@app.route("/api/Ptt/<inputtext>")
def getPtt(inputtext):
    T1 = time.perf_counter()
    result = Ptt(inputtext, T1, expiredDay)
    return result


@app.route("/api/Dcard/<inputtext>")
def getDcard(inputtext):
    T1 = time.perf_counter()
    result = Dcard(inputtext, T1, expiredDay)
    return result


@app.route("/api/search/<inputtext>")
def getSearch(inputtext):
    T1 = time.perf_counter()
    result = Search(inputtext, T1, expiredDay)
    return result


@app.route("/api/blog/<inputtext>")
def getBlog(inputtext):
    T1 = time.perf_counter()
    result = Blog(inputtext, T1, expiredDay)
    return result


@app.route("/api/judgment/<inputtext>")
def getJudgment(inputtext):
    T1 = time.perf_counter()
    result = Judgment(inputtext, T1, expiredDay)
    return result


@app.route("/api/review/<inputtext>")
def getReview(inputtext):
    T1 = time.perf_counter()
    result = Review(inputtext, T1, expiredDay)
    return result


@app.route("/api/business/<inputtext>")
def getBusiness(inputtext):
    T1 = time.perf_counter()
    result = Business(inputtext, T1, expiredDay)
    return result


@app.route("/api/all/<inputtext>")
def all(inputtext):
    result = getAll(inputtext)
    return result


# 1. 指定BackgroundScheduler不會阻塞主程式app的執行 v.s BlockingScheduler
scheduler = BackgroundScheduler(timezone="Asia/Taipei")

# 2-1. interval 固定間隔模式：每10秒執行自訂的hi函式
# scheduler.add_job(hi, 'interval', seconds=10)

# 2-2. cron 指定某時段執行： 每天 0點00分執行updatedata函式
scheduler.add_job(updatedata, 'cron',
                  day_of_week="mon-sun", hour=0, minute=00)

scheduler.add_job(crawlerletter, 'cron',
                  day_of_week="sun", hour=0, minute=00)

# 3. 排程開始
scheduler.start()

app.run(host="0.0.0.0", port=8080)
