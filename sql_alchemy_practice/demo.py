import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


# 先從 declarative_base 這個 factory class 中，創建一個 BASE 的 class
BASE = declarative_base()

# 用 object 來當 table
# object 內的 property


class User(BASE):
    # table name
    __tablename__ = 'user'

    # columns
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.String(64), unique=True)  # varchar64
    password = sa.Column(sa.String(64))
    email = sa.Column(sa.String(128), unique=True)
    create_at = sa.Column(sa.DateTime, server_default=sa.func.now())  # 自動插入時間

    # print 這個 object 的時候，要他 print 這些東西
    def __repr__(self):
        res = f"id={self.id}, username={self.username}, email={self.email}"
        return res


# 建立 session, 和 DBMS 連結
# 和 mysql 內的 mydev 這個 db 連結;
engine = sa.create_engine(
    "mysql+pymysql://root:my-secret-pw@localhost:3307/mydev")
Session = sa.orm.sessionmaker(bind=engine)  # 此時的 Session 是個 class，
# 之後還要用 session = Session() 來實例化一個當前的 session
s = Session()  # instance 一個當前的 session
s.close()

# mapping
BASE.metadata.create_all(engine)  # 把 BASE 這個 class 底下的所有子類，都去建立 mapping
# 所以現在 BASE 下面有 User 這個 class，他就會幫你把 User 的 object，當成 table，插入到 DB 中

"""
* 這邊有重要觀念
* 這個 py 檔，如果重複執行，DB中並不會重複一直插入 User 這張表。他只有第一次(DB中沒有 table 能和此 object 對應時)，才會啟用
* 所以，就算我現在去改 User 這個 object 裡面的內容 (例如: 新增一個 column 叫 update_at)，在執行這個 py 檔，他也不會更動
* 若要更動，涉及到 "migration"，這之後會講
"""

# -------------------------------------------------------------------------------------
# CRUD
# -------------------------------------------------------------------------------------

'''
* 這邊提醒一下，sqlalchemy 是把 python 的物件，和 DBMS 中的 table 做 mapping，所以：  
  * User class 會對應到 DB 中的 user table  
  * User 的一個 instance (i.e. user object)，對應到 DB 中 user table 的一個 record (i.e. row)
  * 所以：
    * [Create]: 當我想新增一個 row 到 DB 的 user table 時，我會先實例化一個 user object (就等於 table 裡的一個 row)，再加進去
    * [Read]: 我如果查詢 DB 中的多個 row (e.g. select * from table)，那他回傳給我的會是一個 iterable 的 user object，每 next 一次，就等於取一個 row，等於取到一個 user object
    * [Read]: 如果查詢結果只有一筆 (e.g. select * from table where id = xxx)，他還是回傳給我一個 iterable 的 user object(同上)，只是長度為1而已
    * [Update]: 先用查詢語句取出該 user object，再透過改 object 屬性 (就等於改欄位value) 的方式，達到 update  
    * [Delete]:
'''


# -------------------------------------------------------------------------------------
# [C]: create, 插入一筆數據 or 多筆數據
# -------------------------------------------------------------------------------------

user1 = User(username='test1', password='test1',
             email='test1@test1.com')  # user1就是一個 instance 了

s.add(user1)  # 就是在做 insert 了，append 一筆資料進去
s.commit()  # 確定 commit 出去

user2 = User(username='test2', password='test2', email='test2@test2.com')
user3 = User(username='test3', password='test3', email='test3@test3.com')
s.add_all([user2, user3])
s.commit()

# -------------------------------------------------------------------------------------
# [R]: read
# -------------------------------------------------------------------------------------


users = s.query(User)  # 這就是 select * from User 的意思了
# 但 User 是 python 的物件， mappping 到 DB 裡的 user table
# 回傳的結果，也是物件。所以現在 users 是一個物件，而且是一個 iterable 的物件
# 如果原本查詢結果，table 中有 10 個 row 符合，那這邊就會是 10 個 user object 所組成的 users 物件
# 我們用 for 迴圈，去看每個 row 的 object，並 print 出他的屬性 (aka 欄位)
u = next(iter(users))
print(type(u))
print(u.id)
print(u.username)
print(u.password)
print(u.email)

# 或用 for 迴圈逐一看完
for u in users:
    print(u.username)

for u in users:
    print(u)  # print 一個物件，會用到 class 中定義的 __repr__ method，這邊上面有特別寫


# 取前 n 筆
users = s.query(User).limit(2)
for u in users:
    print(u)

# 可以用 .all() 這個 method，叫 sqlalchemy 幫我迭代，並整理成 list
# 但要小心使用，因為如果結果有 100 萬條，那等於一次灌進 100 萬的資料進到 ram
users = s.query(User).all()
print(users)


# filter
users = s.query(User).filter(User.username == 'test1')
for u in users:
    print(u)
# 總共有這些可用
users = s.query(User).filter(User.username == 'test1')  # equal
users = s.query(User).filter(User.username != 'test1')  # not equal
users = s.query(User).filter(User.username.like(
    '%es%'))  # like, username 中間出現 es 的
users = s.query(User).filter(User.username.in_(['ed', 'wendy', 'jack']))  # in
users = s.query(User).filter(
    ~User.username.in_(['ed', 'wendy', 'jack']))  # not in
users = s.query(User).filter(User.username == None)  # NULL
users = s.query(User).filter(User.username != None)  # not NULL
users = s.query(User).filter(User.username ==
                             'ed').filter(User.age == 27)  # AND
users = s.query(User).filter(
    sa.or_(User.username == 'ed', User.username == 'wendy'))  # OR


# 用 first() 取第一個，但最常是拿來確認篩選結果存不存在
# 只取第一個
users = s.query(User).first()
print(users)
users = s.query(User).filter(User.username == 'test1').first()
print(users)
users = s.query(User).filter(User.username == 'test3345678').first()
print(users)  # None, 用這招來快速確認，資料庫裡面有沒有這個 name 了

# select column
s = Session()
u2 = s.query(User.id, User.username)
for u in u2:
    print(u, type(u))  # 每個 u, 是 tuple, 不是 object 了！

# order_by
users = s.query(User).order_by(User.id)
for u in users:
    print(u)

users = s.query(User).order_by(User.id.desc())
for u in users:
    print(u)

# -------------------------------------------------------------------------------------
# [U]: update
# -------------------------------------------------------------------------------------

# 舉例來說，我想改 username 為 test1 的這個人的密碼
s = Session()
u = s.query(User).filter(User.username == 'test1').first()
print(u.password)
u.passowrd = 'test111'
s.commit()

# -------------------------------------------------------------------------------------
# [D]: delete
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# debug
# -------------------------------------------------------------------------------------

# 建立 engine 時，開啟 echo (dev 階段可開啟，正式部署時要關閉)
engine = sa.create_engine(
    "mysql+pymysql://root:my-secret-pw@localhost:3307/mydev",
    echo=True)  # 打開 echo
Session = sa.orm.sessionmaker(bind=engine)
s = Session()

# 現在做任何操作，他都會自動 print 出 sqlalchemy 幫你翻譯好的 sql 語句，就知道自己實際是傳什麼指令給 DBMS
users = s.query(User).filter(User.username == 'test1')
for u in users:
    print(u)  # 可以看到 sql 查詢語句
