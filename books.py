from fastapi import FastAPI
# 回傳 http error 的 status code 和 detail, header 給 user
from fastapi import HTTPException
from fastapi import Request, status, Form, Header

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

from uuid import UUID

from starlette.responses import JSONResponse

'''
purpose: 做一個 CRUD 的 api
  - C: create, 每次可以輸入一本書的 title 和 author，他會幫你發 post ，加到資料庫(這邊就是個 temp 的 list 而已)
  - R: read, 用 get 方法，可以讀取資料庫中所有的書，或查找特定的書的資訊
  - U: update, 用 put/post 方法，可以更新某本書的資訊 (title, author, ...)
  - D: delete, 用 delete/post 方法，幫你把某本書刪除
'''

# temp 的 資料庫 ----
BOOKS = []

# 自己寫幾本書進去的 function


def create_books_no_api():
    book_1 = Book(id="71f4c2ea-1340-41f4-89f7-2852347bb0d1",
                  title="Title 1",
                  author="Author 1",
                  description="Description 1",
                  rating=60)
    book_2 = Book(id="21f4c2ea-1340-41f4-89f7-2852347bb0d1",
                  title="Title 2",
                  author="Author 2",
                  description="Description 2",
                  rating=70)
    book_3 = Book(id="31f4c2ea-1340-41f4-89f7-2852347bb0d1",
                  title="Title 3",
                  author="Author 3",
                  description="Description 3",
                  rating=80)
    book_4 = Book(id="41f4c2ea-1340-41f4-89f7-2852347bb0d1",
                  title="Title 4",
                  author="Author 4",
                  description="Description 4",
                  rating=90)
    BOOKS.append(book_1)
    BOOKS.append(book_2)
    BOOKS.append(book_3)
    BOOKS.append(book_4)


# schema ----
# Query 時， post body 的 schema (其實就是 db 的 schema 啦)
class Book(BaseModel):
    '''
    remark:
      * BaseModel 其實就是以前熟悉的 Enum, 你等等列出的所有 key，就是 user 能輸入的所有 key 了，不能超過
      * 這邊，一本書需要的 key 包括  
        * id: 
        * title
        * author
        * description: 選填
        * rating:
    '''
    id: UUID
    title: str = Field(min_length=1)  # 所以 user 不可以上傳 "" 這種 title, 因為字數不夠
    author: str = Field(min_length=1, max_length=100)  # 通常都會設上界，避免 user 寫太多字
    description: Optional[str] = Field(title="Description of the book",  # title 這個 arg 的 value，會顯示在 Swagger UI 上;
                                       # Optional[str] 則表示此欄位 user 可以不填，那到時候會用 null 傳入
                                       max_length=100,
                                       min_length=1)
    rating: int = Field(gt=-1, lt=101)

    class Config:
        schema_extra = {
            "example": {
                "id": "11f4c2ea-1340-41f4-89f7-2852347bb0d1",
                "title": "Computer Science Pro",
                "author": "awsome author",
                "description": "A very nice description of a book",
                "rating": 75
            }
        }

# response 給 user 時， response body 用的 schema
# 這邊提醒一下他的好處: 如果我的 data table 有 10 個欄位，但我最終想給 user 看到的只有 4 個
# 那我可以寫這個 schema 後，我還時照傳原始 table 給 user，但他只會看到我這邊規範好的 4 個欄位而已
# 那好處就是，我只要寫一次 response 用的模板，後續我不管寫多少 function，回多少 response，他的 body 都會是我限定的這版


class BookNoRating(BaseModel):
    id: UUID
    title: str = Field(min_length=1)
    author: str
    description: Optional[str] = Field(
        None, title="description of the Book",
        max_length=100,
        min_length=1
    )

# 還是小孩子的時候，用的是 Enum


class DirectionName(str, Enum):
    north = "North"
    south = "South"
    east = "East"
    west = "West"

# Error handling ----
# 這個 HTTPException 可以回傳給 user, 包括 status_code 和 訊息 (detail)


def raise_item_cannot_be_found_exception():
    return HTTPException(status_code=404,
                         detail="Book not found",
                         headers={"X-Header_Error":
                                  "Nothing to be seen at the UUID"})

# custom exception class
# 這等等要搭配


class NegativeNumberException(Exception):
    def __init__(self, books_to_return):
        self.books_to_return = books_to_return


# 開始 app ----
# app
app = FastAPI()

# error handling


@app.exception_handler(NegativeNumberException)
async def negative_number_exception_handler(request: Request,
                                            exception: NegativeNumberException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Hey, why do you want {exception.books_to_return} "
                            f"books? You need to read more!"}
    )


# [C] create book
# 原本 request 成功，會回 200，這邊改成回 201，因為這是 create 資料成功的 convention
@app.post("/", status_code=status.HTTP_201_CREATED)
async def create_book(book: Book):
    BOOKS.append(book)
    return book


# [R] read
# 列出前 N 本書 (query parameter 的好處是(比起 path parameter)，是他可以設成 optional)
@app.get("/")
async def read_all_books(books_to_return: Optional[int] = None):

    # 先確認輸入進來的 books_to_return 是合法的 (前 N 本書的話， N 應該 > 0)
    # 這邊其實也可以直接在 arg 直接用 books_to_return: Query(gt = 0)，表示要 greater than 0，否則直接回傳 error 訊息回來
    # 但現在故意練習自己寫一個 custom exception
    if books_to_return and books_to_return < 0:
        raise NegativeNumberException(books_to_return=books_to_return)

    # 如果目前資料庫裡面沒有書，那我就自己新增四本進去 (create_books_no_api())
    if len(BOOKS) < 1:
        create_books_no_api()

    if books_to_return and len(BOOKS) >= books_to_return > 0:
        i = 1
        new_books = []
        while i <= books_to_return:
            new_books.append(BOOKS[i - 1])
            i += 1
        return new_books
    return BOOKS

# 用 ID 來查書


@app.get("/book/{book_id}")
async def read_book(book_id: UUID):
    for x in BOOKS:
        if x.id == book_id:
            return x
    raise raise_item_cannot_be_found_exception()

# 用 ID 來查書，但我有限定 response 是我規範好的 class, 所以只會回我想給 user 看的欄位


@app.get("/book/rating/{book_id}", response_model=BookNoRating)
async def read_book_no_rating(book_id: UUID):
    for x in BOOKS:
        if x.id == book_id:
            return x
    raise raise_item_cannot_be_found_exception()


# 用 row index 來查書 + 要通過認證才讓你查書
@app.post("/books/login/")
async def book_login(book_id: int, username: Optional[str] = Header(default=None), password: Optional[str] = Header(default=None)):
    """
    remark:
        * 每個參數，都有他的角色。例如 
            * book_id 啥都沒寫，會被認為是 query parameter，所以 user 查詢時，要放在 url 裡面用 ?book_id=xxx 來傳遞給我們
            * 之前下 post 時，參數後面會指定一個寫好的 BaseModel class，fastAPI看到這個，就會認為他是 body parameter，所以 user 要把資訊放在 request body 傳過來
            * username 和 password 被 declare 為 Header()，表示 user 傳 username 和 password 時，要包在 header 裡面傳過來
            * 其他的 parameter 還有 Cookie()。至於 Header() 和 Cookie() 的使用時機，去參考官網範例
    example:
        curl -X 'POST' \
            'http://localhost:8000/books/login/?book_id=1' \
            -H 'accept: application/json' \
            -H 'username: FastAPIUser' \
            -H 'password: test1234!' \
            -d ''
    """
    if username == "FastAPIUser" and password == "test1234!":
        return BOOKS[book_id]
    return "Invalid User"

# @app.get("/directions/{direction_name}")
# async def get_direction(direction_name: DirectionName):
#     if direction_name == DirectionName.north:
#         return {"Direction": direction_name, "sub": "Up"}
#     if direction_name == DirectionName.south:
#         return {"Direction": direction_name, "sub": "Down"}
#     if direction_name == DirectionName.east:
#         return {"Direction": direction_name, "sub": "Right"}
#     return {"Direction": direction_name, "sub": "Left"}


# [U] update ----
@app.put("/{book_id}")
async def update_book(book_id: UUID, book: Book):
    counter = 0

    for x in BOOKS:
        counter += 1
        if x.id == book_id:
            BOOKS[counter - 1] = book
            return BOOKS[counter - 1]
    raise raise_item_cannot_be_found_exception()

# [D] delete ----


@app.delete("/{book_id}")
async def delete_book(book_id: UUID):
    counter = 0

    for x in BOOKS:
        counter += 1
        if x.id == book_id:
            del BOOKS[counter - 1]
            return f'ID:{book_id} deleted'
    raise raise_item_cannot_be_found_exception()

# [cmd]
# uvicorn books:app --reload

# 瀏覽
# localhost:8000/openapi.json # 可以看到 openapi 的 schema
# localhost:8000/doc

# [git]
# https://github.com/codingwithroby/fastapi-the-complete-course.git
