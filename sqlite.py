import sqlite3

dbname = 'test.db'
conn = sqlite3.connect(dbname, isolation_level=None)

cursor = conn.cursor()

sql = """CREATE TABLE IF NOT EXISTS test(id, name, date)"""

cursor.execute(sql)
conn.commit()

sql = """SELECT name FROM sqlite_master WHERE TYPE='table'"""

for t in cursor.execute(sql):#for文で作成した全テーブルを確認していく
    print(t)