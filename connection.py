from dotenv import get_key
from mysql.connector import pooling


conPool = pooling.MySQLConnectionPool(user=get_key(".env", "user"), password=get_key(
    ".env", "password"), host='finddoctor.collqfqpnilo.us-west-2.rds.amazonaws.com', database='finddoctor', pool_name='findConPool', pool_size=17,  auth_plugin='mysql_native_password')
