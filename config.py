import pymysql

db_address = "localhost"
db_username = "root"
db_password = "123456"
db_name = "live_viewer"

def connect_db():
    return pymysql.connect(db_address, db_username, db_password, db_name, charset='utf8')
