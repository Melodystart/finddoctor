import mysql.connector
from mysql.connector import pooling

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
)
cursor = con.cursor()

cursor.execute("USE test;")
cursor.execute(
    "INSERT INTO hello (text) VALUES (%s)", ("Hello crontab", ))
con.commit()
cursor.close()
con.close()


# 1. 編輯排程
# crontab -e

# 2. 指令
# ┌──分鐘（0 - 59）
# │ ┌──小時（0 - 23）
# │ │ ┌──日（1 - 31）
# │ │ │ ┌─月（1 - 12）
# │ │ │ │ ┌─星期（0 - 6 => 周日到周六）
# * * * * * 執行的任務

# 每分鐘執行hello.py檔
# */1 * * * * python3 /home/ubuntu/finddoctor/hello.py

# 每周日7:30 cd到資料夾finddoctor後，再執行thank.py檔爬蟲網頁/pdf檔
# 30 07 * * 0 cd /home/ubuntu/finddoctor && python3 /home/ubuntu/finddoctor/thank.py

# 3. 編輯後重啟排程
# sudo service cron restart

# 4. 查看排程日誌
# grep CRON /var/log/syslog
