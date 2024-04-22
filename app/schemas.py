from pydantic import BaseModel, Field


class Message(BaseModel):
    query: str = Field(description="The content of the message which is the query.")


class EvalMessage(Message):
    response: str = Field(description="The response from the chatbot.")
    page_content: str = Field(
        description="The page content that makes up the context to the chatbot."
    )
