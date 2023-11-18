import mysql.connector
from mysql.connector import pooling

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
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
