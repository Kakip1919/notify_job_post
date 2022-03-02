import sqlite3

dbname = 'lancers.db'
conn = sqlite3.connect(dbname, isolation_level=None)

cursor = conn.cursor()

sql = """CREATE TABLE IF NOT EXISTS lancers_data(id real, title, body text,price text, date)"""

cursor.execute(sql)
conn.commit()

sql = """SELECT title FROM lancers_data WHERE TYPE='table'"""

for t in cursor.execute(sql):#for文で作成した全テーブルを確認していく
    print(t)