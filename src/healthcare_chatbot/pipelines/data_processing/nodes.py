"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.19.3
"""

import glob
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from kedro.config import OmegaConfigLoader
from kedro.framework.project import settings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from healthcare_chatbot.pipelines.data_processing.utils import (
    SourceType,
    check_sources,
    index_new_documents,
    pdfs_to_docs,
    update_json,
    websites_to_docs,
)


def index_websites(
    websites: list[str],
    embedding_model_name: str,
    db_params: dict,
    splitter_params: dict,
) -> dict:
    """Indexes websites into a vector database.

    This function takes a list of website URLs, an embedding model, vector database parameters,
    and splitter parameters as input. It loads the OpenAI API key, creates an embedding model,
    and loads vector database parameters. It then checks if the collection exists in the vector database.
    If the collection does not exist, it creates the collection and indexes all documents.
    If the collection exists, it checks for new documents to index into the collection.
    It gets all the website URLs already in the collection, and from the websites,
    it keeps those which do not already appear in the collection.
    If there are new websites, it indexes them into the collection.

    Args:
        websites (list[str]): A list of website URLs to index.
        embedding_model_name (str): The name of the embedding model to use.
        db_params (dict): A dictionary containing the path and collection name of the vector database.
        splitter_params (dict): A dictionary containing the chunk size and chunk overlap.

    Returns:
        dict: A dictionary containing the split documents in a JSON serializable format.
    """
    conf_path = str(str(Path(os.getcwd()) / settings.CONF_SOURCE))
    conf_loader = OmegaConfigLoader(conf_source=conf_path)
    credentials = conf_loader["credentials"]

    # Load the OpenAI API key
    OPENAI_API_KEY = credentials["OPENAI_API_KEY"]
    embedding_model = OpenAIEmbeddings(
        model=embedding_model_name, openai_api_key=OPENAI_API_KEY
    )

    # Load vector database parameters
    db_path = db_params["path"]
    collection_name = db_params["collection_name"]

    # Load splitter parameters
    chunk_size = splitter_params["chunk_size"]
    chunk_overlap = splitter_params["chunk_overlap"]
    separators = splitter_params["separators"]

    client = chromadb.Client(
        Settings(
            is_persistent=True,
            persist_directory=str(Path(os.getcwd()) / db_path),
        )
    )

    # Check collections
    collections = [collection.name for collection in client.list_collections()]

    # If collection doesn't exist, we create the collection and index all documents
    if collection_name not in collections:
        print(
            f"Collection: {collection_name} does not exist. Creating collection and indexing all documents."
        )

        data_split, docs_dict = websites_to_docs(
            websites, chunk_size, chunk_overlap, separators
        )

        _ = Chroma.from_documents(
            data_split,
            embedding_model,
            collection_name=collection_name,
            persist_directory=str(Path(os.getcwd()) / db_path),
        )

        print(f"Indexing {len(docs_dict)} documents from website(s).")

        return docs_dict

    # If the collection exists, we want to check if there are
    # any new documents. If so, we want to add them to the collection
    else:
        print(
            f"Collection: {collection_name} already exists. Checking for new documents to index into collection."
        )

        # Check for new websites to index
        collection, new_websites = check_sources(websites, client, collection_name)

        # If there are new websites, index them into the collection
        if new_websites is not None:
            docs_dict = index_new_documents(
                new_websites,
                SourceType.WEBSITE,
                collection,
                chunk_size,
                chunk_overlap,
                separators,
                embedding_model_name,
                OPENAI_API_KEY,
            )

            print(f"Indexing {len(docs_dict)} documents from website(s).")

            return docs_dict

        # If there aren't any new websites to index, we can skip to avoid repeated indexing
        else:
            print(f"No new documents to index for websites.")

            docs_dict = update_json(SourceType.WEBSITE)
            return docs_dict


def index_pdfs(
    dir_path: str, embedding_model_name: str, db_params: dict, splitter_params: dict
) -> dict:
    """
    Indexes PDFs into a vector database collection.

    Args:
        dir_path (str): The directory path containing the PDFs to be indexed.
        embedding_model_name (str): The name of the embedding model to be used.
        db_params (dict): The parameters for the vector database collection.
        splitter_params (dict): The parameters for splitting the PDFs into chunks.

    Returns:
        dict: A dictionary containing information about the indexed PDFs.
    """
    conf_path = str(str(Path(os.getcwd()) / settings.CONF_SOURCE))
    conf_loader = OmegaConfigLoader(conf_source=conf_path)
    credentials = conf_loader["credentials"]

    # Load the OpenAI API key
    OPENAI_API_KEY = credentials["OPENAI_API_KEY"]
    embedding_model = OpenAIEmbeddings(
        model=embedding_model_name, openai_api_key=OPENAI_API_KEY
    )

    # Load vector database parameters
    db_path = db_params["path"]
    collection_name = db_params["collection_name"]

    # Load splitter parameters
    chunk_size = splitter_params["chunk_size"]
    chunk_overlap = splitter_params["chunk_overlap"]
    separators = splitter_params["separators"]

    # Load all the PDF paths
    pdfs_paths = glob.glob(os.path.join(dir_path, "*.pdf"))

    client = chromadb.Client(
        Settings(
            is_persistent=True,
            persist_directory=str(Path(os.getcwd()) / db_path),
        )
    )

    # Check collections
    collections = [collection.name for collection in client.list_collections()]

    if collection_name not in collections:
        print(
            f"Collection: {collection_name} does not exist. Creating collection and indexing all documents."
        )

        all_data_splits, pdfs_dict = pdfs_to_docs(
            pdfs_paths, chunk_size, chunk_overlap, separators
        )

        _ = Chroma.from_documents(
            all_data_splits,
            embedding_model,
            collection_name=collection_name,
            persist_directory=str(Path(os.getcwd()) / db_path),
        )

        print(f"Indexing {len(pdfs_dict)} documents from PDF(s).")

        return pdfs_dict

    # If the collection exists, we want to check if there are
    # any new documents. If so, we want to add them to the collection
    else:
        print(
            f"Collection: {collection_name} already exists. Checking for new documents to index into collection."
        )

        # Check for new PDFs to index
        collection, new_pdfs = check_sources(pdfs_paths, client, collection_name)

        # If there are new PDFs, index them into the collection
        if new_pdfs is not None:
            pdfs_dict = index_new_documents(
                new_pdfs,
                SourceType.PDF,
                collection,
                chunk_size,
                chunk_overlap,
                separators,
                embedding_model_name,
                OPENAI_API_KEY,
            )

            print(f"Indexing {len(pdfs_dict)} documents from PDF(s).")

            return pdfs_dict

        # If there aren't any new PDFs to index, we can skip to avoid repeated indexing
        else:
            print(f"No new documents to index for PDFs.")

            pdfs_dict = update_json(SourceType.PDF)
            return pdfs_dict
