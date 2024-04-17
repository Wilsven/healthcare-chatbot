from pydantic import BaseModel, Field


class Message(BaseModel):
    query: str = Field(description="The content of the message which is the query.")
