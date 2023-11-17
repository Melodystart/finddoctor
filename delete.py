from mysql.connector import pooling
from datetime import datetime, timedelta
from dotenv import get_key

# expiredDay = datetime.today().date() - timedelta(days=7)
expiredDay = datetime.today().date() + timedelta(days=7)

conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
    ".env", "password"), host='localhost', database='finddoctor', pool_name='findConPool', pool_size=10,  auth_plugin='mysql_native_password')

con = conPool.get_connection()
cursor = con.cursor()
cursor.execute("DELETE FROM newest WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.execute("DELETE FROM review WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.execute(
    "DELETE FROM businessComment WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.execute("DELETE FROM businessLink WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.execute("DELETE FROM judgment WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.execute("DELETE FROM Ptt WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.execute("DELETE FROM search WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.execute("DELETE FROM blog WHERE createdAt<%s;", (expiredDay,))
con.commit()
cursor.close()
con.close()
