from http.client import HTTPException
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field
from typing import Optional


# DB setting
from database import engine, SessionLocal
import models
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Todo(BaseModel):
    title: str
    description: Optional[str]
    # priority 只能是 1 ~ 5
    priority: int = Field(
        gt=0, lt=6, description="The priority must be between 1-5")
    complete: bool


# start api ----

app = FastAPI()

# error handling


def http_exception():
    return HTTPException(status_code=404, detail="Todo not found")


def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction': 'Successful'
    }

# ------------------------------------------------------------------------
# [C]: create
# ------------------------------------------------------------------------


@app.post("/")
async def create_todo(todo: Todo, db: Session = Depends(get_db)):
    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete

    db.add(todo_model)
    db.commit()

    return {
        'status': 201,
        'transaction': 'Successful'
    }

# ------------------------------------------------------------------------
# [R]: read
# ------------------------------------------------------------------------


@app.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Todos).all()

# ------------------------------------------------------------------------
# [U]: update
# ------------------------------------------------------------------------


@app.put("/{todo_id}")
async def update_todo(todo_id: int, todo: Todo, db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos)\
        .filter(models.Todos.id == todo_id)\
        .first()

    if todo_model is None:
        raise http_exception()

    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete

    db.commit()

    return successful_response(status_code=201)


# ------------------------------------------------------------------------
# [D]: delete
# ------------------------------------------------------------------------

@app.delete("/{todo_id")
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos)\
        .filter(models.Todos.id == todo_id)\
        .first()

    if todo_model is None:
        raise http_exception()

    todo_model = db.query(models.Todos)\
        .filter(models.Todos.id == todo_id)\
        .delete()

    db.commit()

    return successful_response(status_code=200)


# [cmd]
# cd TodoApp
# uvicorn main:app --reload
