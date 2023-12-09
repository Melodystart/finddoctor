from function import *
import mysql.connector
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

getDoctorList()
getPttBoard()


cursor.close()
con.close()
