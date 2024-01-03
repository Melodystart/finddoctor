from mysql.connector import pooling
from dotenv import get_key
from elasticsearch import Elasticsearch
import time
from datetime import datetime, timedelta
import json

es = Elasticsearch(["http://localhost:9200/"], basic_auth=(get_key(".env", "es_user"), get_key(".env", "es_password")))

conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
    ".env", "password"), host='finddoctor.collqfqpnilo.us-west-2.rds.amazonaws.com', database='finddoctor', pool_name='findConPool', pool_size=17,  auth_plugin='mysql_native_password')

toDay = datetime.today().date()
expiredDay = toDay - timedelta(days=7)  # 設定快取資料期限為7天

def get_thank(keyword):
    T1 = time.perf_counter()
    res = es.options(opaque_id=keyword.encode("utf-8").decode("latin1")).search(index='thank', body={"size": 100, "query": {
        "match_phrase": {
            "content": keyword
        }
    }, "sort": {
        "month.keyword": {
            "order": "desc"
        }
    }})
    T2 = time.perf_counter()
    print(keyword+"Elastic Search："+'%s毫秒' % ((T2 - T1)*1000))
    data = res['hits']['hits']
    return data

def get_review(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT author, star, timestamp, review, link, location FROM review WHERE doctor=%s;", (inputtext, ))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def check_no_review(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT * FROM review WHERE doctor=%s;", (inputtext,))
    data = cursor.fetchall()
    if len(data) == 0:
        cursor.execute(
            "INSERT INTO review (doctor, review) VALUES (%s, %s)", (inputtext, ""))
    con.commit()
    cursor.close()
    con.close()

def save_review(inputtext, author, review_rating, review_timestamp, review, review_link, location):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO review (doctor, author, star, timestamp, review, link, location ) VALUES (%s, %s,%s, %s, %s,%s,%s)", (inputtext, author, review_rating, review_timestamp, review, review_link, location))
    con.commit()
    cursor.close()
    con.close()

def get_business(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor(buffered=True)
    cursor.execute(
        "SELECT author, timestamp, comment, createdAt, link, location FROM businessComment WHERE doctor=%s;", (inputtext, ))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def save_business(inputtext, author, timestamp, comment, link, location):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO businessComment (doctor, author, timestamp, comment, link, location) VALUES (%s, %s,%s, %s,%s, %s)", (inputtext, author, timestamp, comment, link, location))
    con.commit()
    cursor.close()
    con.close()

def get_judgment(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title FROM judgment WHERE doctor=%s;", (inputtext, ))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def save_judgment(inputtext, link, title):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO judgment (doctor, link, title) VALUES (%s, %s,%s)", (inputtext, link, title))
    con.commit()
    cursor.close()
    con.close()

def get_ptt(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title, text FROM Ptt WHERE doctor=%s;", (inputtext,))
    data = cursor.fetchall()
    cursor.execute(
        "SELECT board FROM PttBoard;")
    data_board = cursor.fetchall()
    cursor.close()
    con.close()
    return data, data_board

def save_ptt(inputtext, link, title, text):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO Ptt (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
    con.commit()
    cursor.close()
    con.close()

def get_search(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title, text FROM search WHERE doctor=%s;", (inputtext, ))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def save_search(inputtext, link, title, text):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO search (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
    con.commit()
    cursor.close()
    con.close()

def get_dcard(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title, text FROM Dcard WHERE doctor=%s;", (inputtext, ))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def save_dcard(inputtext, link, title, text):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO Dcard (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
    con.commit()
    cursor.close()
    con.close()

def get_blog(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT link, title, text FROM blog WHERE doctor=%s;", (inputtext,))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def save_blog(inputtext, link, title, text):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO blog (doctor, link, title, text) VALUES (%s, %s,%s,%s)", (inputtext, link, title, text))
    con.commit()
    cursor.close()
    con.close()

def get_most():
    result = {}
    result["data"] = []

    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT doctor FROM record WHERE createdAt >= %s group by(doctor) ORDER BY count(doctor) DESC LIMIT 10;", (expiredDay,))
    data = cursor.fetchall()
    cursor.close()
    con.close()

    for d in data:
        result["data"].append(d[0])
    return result

def get_doctor():
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT department, name FROM doctor;")
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def delete_expired_data():
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute("DELETE FROM record WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM review WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute(
        "DELETE FROM businessComment WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM judgment WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM Ptt WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM search WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.execute("DELETE FROM blog WHERE createdAt<=%s;", (expiredDay,))
    con.commit()
    cursor.close()
    con.close()

def get_mostsearched():
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT doctor, count(doctor) AS counter FROM record WHERE createdAt >= %s group by(doctor) ORDER BY counter DESC LIMIT 10;", (expiredDay,))
    data = cursor.fetchall()
    cursor.close()
    con.close()
    return data

def save_searchedrecord(inputtext):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO record (doctor) VALUES (%s)", (inputtext, ))
    con.commit()
    cursor.close()
    con.close()

def create_table():
    con = conPool.get_connection()
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
    cursor.execute("DROP table IF EXISTS doctor;")
    cursor.execute("DROP table IF EXISTS PttBoard;")

    cursor.execute(
        "CREATE table PttBoard (id BIGINT PRIMARY KEY auto_increment,board VARCHAR(255));")
    cursor.execute(
        "CREATE table doctor (id BIGINT PRIMARY KEY auto_increment,department VARCHAR(255) NOT NULL,name VARCHAR(255) NOT NULL,url TEXT NOT NULL);")
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
    cursor.close()
    con.close()

def save_doctor(department, doctor, url):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO doctor (department, name, url) VALUES (%s, %s,%s)", (department, doctor, url))
    con.commit()
    cursor.close()
    con.close()

def save_pttboard(board):
    con = conPool.get_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO PttBoard (board) VALUES (%s)", (board.text,))
    con.commit()
    cursor.close()
    con.close()

def Redis(cache):
    result={}
    result["data"] = []
    for item in cache:
        result["data"].append(json.loads(item))
    return result