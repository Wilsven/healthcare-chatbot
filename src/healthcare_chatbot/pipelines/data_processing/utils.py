import re
import uuid
from enum import Enum
from io import BytesIO
from pathlib import Path

import chromadb
from chromadb.api.client import Client
from chromadb.utils import embedding_functions
from kedro.framework.session import KedroSession
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents.base import Document
from pypdf import PdfReader
from tqdm import tqdm


def strip_content(page_content: str) -> str:
    """A function that strips excess whitespace from the input page content.

    Args:
        page_content (str): The content of the page to strip whitespace from.

    Returns:
        str: he page content with excess whitespace removed.
    """
    new_content = re.sub("\s+", " ", page_content).strip()
    return new_content


def websites_to_docs(
    websites: list[str], chunk_size: int, chunk_overlap: int, separators: list[str]
) -> tuple[list[Document], dict]:
    """
    Indexes websites into a vector database by loading the content of each website,
    stripping excess whitespace from the content, splitting the content into chunks,
    and converting the resulting documents into a JSON serializable format.

    Args:
        websites (list[str]): A list of website URLs to index.
        chunk_size (int): The maximum length of each chunk.
        chunk_overlap (int): The number of characters that each chunk overlaps with
            the previous and next chunk.
        separators (list[str]): A list of strings that are used to separate the content
            into chunks.

    Returns:
        tuple[list[Document], dict]: A tuple containing two elements:
            - A list of Document objects representing the split documents.
            - A dictionary representing the split documents in a JSON serializable format.
    """
    loader = WebBaseLoader(websites)
    data = loader.load()

    for d in data:
        new_content = strip_content(d.page_content)
        d.page_content = new_content

    # Define text chunk strategy
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=separators
    )
    # Split documents into chunks
    data_split = splitter.split_documents(data)
    # Convert to JSON serializable format
    docs_dict = [dict(ds) for ds in data_split]

    return data_split, docs_dict


def parse_pdf(file: BytesIO) -> tuple[list[str], BytesIO]:
    """
    Parses a PDF file and returns a list of strings representing the extracted text from each page of the PDF.

    Args:
        file (BytesIO): A BytesIO object containing the PDF file to be parsed.

    Returns:
        tuple[list[str], BytesIO]: A tuple containing two elements:
            - A list of strings representing the extracted text from each page of the PDF.
            - The original BytesIO object containing the PDF file.
    """
    source = file
    pdf = PdfReader(source)
    output = []
    for page in pdf.pages:
        text = page.extract_text()
        # Merge hyphenated words
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        # Fix newlines in the middle of sentences (use negative look behind and look ahead)
        text = re.sub(r"(?<!\n\s)\n(?!\n\s)", " ", text.strip())
        # Remove multiple newlines
        text = re.sub(r"\n\s*\n", "\n\n", text)
        output.append(text)

    return output, source


def text_to_docs(
    text: str | list[str],
    source: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
) -> list[Document]:
    """
    Converts text data into a list of Document objects by splitting the text into pages, adding metadata to each page,
    and then splitting the documents into chunks based on specified parameters.

    Args:
        text (Union[str, List[str]]): The input text as a single string or a list of strings.
        source (str): The source of the text data.
        chunk_size (int): The size of each chunk.
        chunk_overlap (int): The number of characters each chunk overlaps.
        separators (List[str]): List of strings used to split the text into chunks.

    Returns:
        List[Document]: A list of Document objects representing the split documents.
    """
    if isinstance(text, str):
        # Take a single string as one page
        text = [text]

    page_docs = [Document(page_content=page) for page in text]

    # Add page as metadata
    for i, doc in enumerate(page_docs):
        doc.metadata["source"] = source
        doc.metadata["page"] = i + 1

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )

    # Split documents into chunks
    data_split = splitter.split_documents(page_docs)

    return data_split


def pdfs_to_docs(
    pdfs_paths: list[str], chunk_size: int, chunk_overlap: int, separators: list[str]
) -> tuple[list[Document], dict]:
    """
    Converts a list of PDF paths into a list of Document objects and a dictionary of JSON serializable data.

    Args:
        pdfs_paths (list[str]): A list of paths to PDF files.
        chunk_size (int): The maximum size of each chunk in characters.
        chunk_overlap (int): The number of characters to overlap between chunks.
        separators (list[str]): A list of strings to use as separators between chunks.

    Returns:
        tuple[list[Document], dict]: A tuple containing a list of Document objects and a dictionary of JSON serializable data.
            - The list of Document objects contains the parsed and split text from each PDF file.
            - The dictionary of JSON serializable data contains the same information as the list of Document objects, but in a JSON serializable format.
    """
    all_data_splits = []

    t = tqdm(pdfs_paths)

    for pdf_path in t:
        t.set_description("Parsing and splitting PDF into document chunks")
        output, source = parse_pdf(pdf_path)
        data_split = text_to_docs(output, source, chunk_size, chunk_overlap, separators)
        all_data_splits.extend(data_split)

    # Convert to JSON serializable format
    pdfs_dict = [dict(ds) for ds in all_data_splits]

    return all_data_splits, pdfs_dict


class SourceType(Enum):
    WEBSITE = "website"
    PDF = "pdf"


def check_sources(
    input_sources: list[str],
    client: Client,
    collection_name: str,
) -> tuple[chromadb.Collection, list[str] | None]:
    """
    Check the sources provided against the collection of documents already indexed in ChromaDB.

    Args:
        input_sources (list[str]): A list of sources to check against the collection.
        source_type (SourceType): An enum representing the type of sources being checked.
        client (Client): A ChromaDB client object.
        collection_name (str): The name of the collection to check against.

    Returns:
        tuple[chromadb.Collection, list[str] | None]: A tuple containing the ChromaDB collection and a list of sources to index.
            - The ChromaDB collection.
            - A list of sources to index, or None if there are no new sources to index.

    Raises:
        TypeError: If source_type is not an instance of the SourceType enum.
    """
    collection = client.get_collection(name=collection_name)
    # Get all the sources already in collection
    sources = set([metadata["source"] for metadata in collection.get()["metadatas"]])

    # From the input sources, only keep those which do not already appear in
    # the collection AKA not in the sources (we do not want to index the same
    # website or PDF twice)
    new_sources = [
        input_source for input_source in input_sources if input_source not in sources
    ]

    return collection, new_sources if new_sources else None


def index_new_documents(
    new_sources: list[str],
    source_type: SourceType,
    collection: chromadb.Collection,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
    embedding_model_name: str,
    api_key: str,
) -> dict:
    """
    Indexes new documents into a collection based on the source type.

    Args:
        new_sources (list[str]): List of new sources to be indexed.
        source_type (SourceType): Enum indicating the type of source (website or pdf).
        collection (chromadb.Collection): The collection to index the new documents into.
        chunk_size (int): The size of each chunk for processing.
        chunk_overlap (int): The overlap between each chunk for processing.
        separators (list[str]): List of separators for splitting the data.
        embedding_model_name (str): The name of the embedding model to be used.
        api_key (str): The API key for embedding functions.

    Returns:
        dict: A dictionary containing the indexed documents based on the source type.
    """

    def _index_new_documents(
        original: list[dict],
        new: list[dict],
        data_split: list[Document],
        collection: chromadb.Collection,
    ) -> dict:
        """
        Indexes new documents into a collection based on the source type.

        Args:
            original (list[dict]): The original list of documents to be updated.
            new (list[dict]): The new list of documents to be added.
            data_split (list[Document]): The list of Document objects to be split.
            collection (chromadb.Collection): The collection to index the new documents into.

        Returns:
            dict: A dictionary containing the indexed documents based on the source type.
        """
        print(f"Before updating: {len(original)}")
        # Extend the original with the new documents
        original.extend(new)
        print(f"After updating: {len(original)}")

        # The embedding function
        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            model_name=embedding_model_name, api_key=api_key
        )

        # Extract the page content from the document objects
        documents = [ds.page_content for ds in data_split]
        # Extract the metadata from the document objects
        metadatas = [ds.metadata for ds in data_split]
        # Create embeddings from the page contents
        embeddings = embedding_function(documents)
        # Randomly generate UUIDs (chromadb is kinda dumb for not auto-incrementing ids)
        ids = [str(uuid.uuid4()) for _ in embeddings]

        # Add the new documents into the collection
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        return original

    print(f"Indexing {len(new_sources)} new documents into collection.")
    # Get JSON already saved to be updated with new documents
    with KedroSession.create(project_path=Path.cwd()) as session:
        context = session.load_context()
        catalog = context.catalog

    if source_type.value == "website":
        data_split, new_docs_dict = websites_to_docs(
            new_sources, chunk_size, chunk_overlap, separators
        )

        try:
            docs_dict = catalog.load("docs_dict")
        except:
            docs_dict = []

        docs_dict = _index_new_documents(
            docs_dict, new_docs_dict, data_split, collection
        )
        return docs_dict

    elif source_type.value == "pdf":
        all_data_splits, new_pdfs_dict = pdfs_to_docs(
            new_sources, chunk_size, chunk_overlap, separators
        )

        try:
            pdfs_dict = catalog.load("pdfs_dict")
        except:
            pdfs_dict = []

        pdfs_dict = _index_new_documents(
            pdfs_dict, new_pdfs_dict, all_data_splits, collection
        )
        return pdfs_dict


def update_json(source_type: SourceType) -> dict:
    """
    Updates the JSON file based on the source type.

    Args:
        source_type (SourceType): The type of source (website or pdf).

    Returns:
        dict: The loaded JSON data based on the source type.
    """
    print("There are no new documents to index.")
    # Get JSON already saved to be updated with new documents
    with KedroSession.create(project_path=Path.cwd()) as session:
        context = session.load_context()
        catalog = context.catalog

    return (
        catalog.load("docs_dict")
        if source_type.value == "website"
        else catalog.load("pdfs_dict")
    )
