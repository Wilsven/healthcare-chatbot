# https://github.com/jina-ai/langchain-serve

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import qa
from app.schemas import Message

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", status_code=status.HTTP_200_OK)
def index():
    return {"response": "Hello World!"}


@app.post("/chat", status_code=status.HTTP_201_CREATED)
def ask(question: Message) -> dict:
    return {"query": question.query, "response": qa.invoke(question.query)["result"]}
