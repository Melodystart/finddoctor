import mysql.connector
from mysql.connector import pooling
from dotenv import get_key
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
cursor.execute("DROP table IF EXISTS thank;")
cursor.execute("DROP table IF EXISTS thankUrl;")
cursor.execute(
    "CREATE table thank (id BIGINT PRIMARY KEY auto_increment,month VARCHAR(255),target TEXT,content TEXT NOT NULL);")
cursor.execute(
    "CREATE table thankUrl (id BIGINT PRIMARY KEY auto_increment,month VARCHAR(255),url TEXT NOT NULL);")
cursor.close()
con.close()
