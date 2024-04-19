import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

conf_path = str(str(Path(os.getcwd()) / settings.CONF_SOURCE))
conf_loader = OmegaConfigLoader(conf_source=conf_path)
credentials = conf_loader["credentials"]

# Load the OpenAI API key
OPENAI_API_KEY = credentials["OPENAI_API_KEY"]

# Load the configurations required for the embedding model and LLM
embedding_model_name = conf_loader["parameters"]["embedding_model_name"]
model_name = conf_loader["parameters"]["model_name"]
temperature = conf_loader["parameters"]["temperature"]
max_tokens = conf_loader["parameters"]["max_tokens"]

# Specify path to vector store
persist_directory = conf_loader["parameters"]["vector_db"]["path"]

# Specify collection name
collection_name = conf_loader["parameters"]["vector_db"]["collection_name"]

client = chromadb.Client(
    Settings(
        is_persistent=True,
        persist_directory=persist_directory,
    )
)

embedding_model = OpenAIEmbeddings(
    model=embedding_model_name, openai_api_key=OPENAI_API_KEY
)
store = Chroma(
    client=client,
    collection_name=collection_name,
    embedding_function=embedding_model,
)

llm = ChatOpenAI(
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
    model_name=model_name,
    temperature=temperature,
    openai_api_key=OPENAI_API_KEY,
    max_tokens=max_tokens,
)

template = """
You are a helpful conversational chatbot. Your goal is to provide accurate and helpful information about healthcare.
You should answer user inquiries based on the context provided and avoid making up answers.

The context are multiple articles containing healthcare facts, information, and tips published by a local healthcare
company. You should answer readers' queries using only the information from the published articles.

If you don't know the answer, simply state that you don't know. It is not required to acknowledge that information was
provided in the articles. 

Remember to be appropriate and adopt an empathetic and understanding tone.

{context}
=========
Question: {question}
"""

PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=store.as_retriever(
        search_type="mmr", search_kwargs={"k": 3, "fetch_k": 20, "lambda_mult": 0.5}
    ),
    chain_type_kwargs={"prompt": PROMPT},
    return_source_documents=True,
)
