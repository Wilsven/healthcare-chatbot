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
def index() -> dict:
    """
    Get the index page.

    This function is a route handler for the root URL ("/") of the API.
    It returns a JSON response with a "response" key containing the string "Hello World!".
    The HTTP status code of the response is set to 200 (OK).

    Returns:
        dict: A dictionary with a single key-value pair, where the key is "response" and the value is the string "Hello World!".
    """
    return {"response": "Hello World!"}


@app.post("/chat", status_code=status.HTTP_201_CREATED)
def ask(question: Message) -> dict:
    """
    Endpoint for asking a question and getting a response.

    Args:
        question (Message): The question to be asked.

    Returns:
        dict: A dictionary containing the query, response, and source documents.
            - query (str): The query string.
            - response (str): The response string.
            - source_documents (List[dict]): A list of dictionaries representing the source documents.
    """

    query = question.query
    response = qa.invoke(question.query)
    result = response["result"].replace("\n", " ")
    source_documents = response["source_documents"]
    source_documents = [dict(doc) for doc in source_documents]

    return {
        "query": query,
        "response": result,
        "source_documents": source_documents,
    }
