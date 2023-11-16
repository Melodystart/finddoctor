import mysql.connector
from mysql.connector import pooling

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
)
cursor = con.cursor()

# 建立table
cursor.execute("USE finddoctor;")
cursor.execute("DROP table IF EXISTS review;")
cursor.execute("DROP table IF EXISTS businessComment;")
cursor.execute("DROP table IF EXISTS businessLink;")
cursor.execute("DROP table IF EXISTS judgment;")
cursor.execute("DROP table IF EXISTS Ptt;")
cursor.execute("DROP table IF EXISTS search;")
cursor.execute("DROP table IF EXISTS blog;")


cursor.execute(
    "CREATE table review (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255), author VARCHAR(255),star BIGINT, timestamp VARCHAR(255),review TEXT, link TEXT, location VARCHAR(255));")
cursor.execute(
    "CREATE table businessComment (id BIGINT PRIMARY KEY auto_increment, doctor VARCHAR(255), author VARCHAR(255), timestamp VARCHAR(255), comment TEXT);")
cursor.execute(
    "CREATE table businessLink (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT);")
cursor.execute(
    "CREATE table judgment (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT);")
cursor.execute(
    "CREATE table Ptt (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, text TEXT);")
cursor.execute(
    "CREATE table search (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, text TEXT);")
cursor.execute(
    "CREATE table blog (id BIGINT PRIMARY KEY auto_increment,doctor VARCHAR(255),link TEXT,title TEXT, text TEXT);")
