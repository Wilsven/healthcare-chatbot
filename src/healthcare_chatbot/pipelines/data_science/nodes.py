"""
This is a boilerplate pipeline 'data_science'
generated using Kedro 0.19.3
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests
from kedro.framework.session import KedroSession
from tqdm import tqdm
from wordcloud import STOPWORDS, WordCloud


def generate_wordcloud(queries_df: pd.DataFrame) -> plt.Figure:
    """
    Generate a word cloud image from a DataFrame of queries.

    Args:
        queries_df (pd.DataFrame): A DataFrame containing queries.

    Returns:
        plt.Figure: The generated word cloud figure.
    """
    queries = " ".join(query for query in queries_df.queries)
    print(f"There are {len(queries)} words in the combination of all queries.")

    # Create stopword list
    stopwords = set(STOPWORDS)

    # Generate a word cloud image
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(
        queries
    )

    fig = plt.figure()
    fig.set_figheight(4.5)
    fig.set_figwidth(4.5 * 2)
    # Display the generated image:
    # the matplotlib way:
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

    return fig


def get_responses(
    queries_df: pd.DataFrame,
    api_params: dict,
    start_index: int,
    end_index: int,
) -> pd.DataFrame:
    """
    Retrieves responses from an API based on a list of queries.

    Args:
        queries_df (pd.DataFrame): A DataFrame containing a column of queries.
        api_params (dict): A dictionary containing the API parameters.
        start_index (int): The start index of the queries to retrieve.
        end_index (int): The end index of the queries to retrieve.

    Returns:
        pd.DataFrame: A DataFrame containing the retrieved responses.
    """
    # Get dataframe already saved to be updated with new documents
    with KedroSession.create(project_path=Path.cwd()) as session:
        context = session.load_context()
        catalog = context.catalog

    domain = api_params["domain"]
    chat_endpoint = api_params["chat_endpoint"]
    chat_url = domain + chat_endpoint

    questions = []
    responses = []
    page_contents = []
    sources = []

    queries = queries_df["queries"].to_list()
    assert start_index is not None and end_index is not None
    queries = queries[start_index : end_index + 1]

    q = tqdm(queries)

    for query in q:
        q.set_description(f"Getting response from LLM for query: {query}")

        try:
            response = requests.post(chat_url, json={"query": query})

            if response.status_code == 201:
                response = response.json()
                questions.append(response["query"])
                responses.append(response["response"])
                # Get only the first most relevant document
                page_contents.append(response["source_documents"][0]["page_content"])
                sources.append(response["source_documents"][0]["metadata"]["source"])
        except:
            break

    try:
        responses_file = catalog.load("responses_file")
        new_responses_file = pd.DataFrame(
            {
                "queries": questions,
                "responses": responses,
                "page_contents": page_contents,
                "sources": sources,
            }
        )
        responses_file = pd.concat(
            [responses_file, new_responses_file], axis=0, ignore_index=True
        )

    except Exception:
        print("There is no existing response.csv file. Creating new response.csv file.")
        responses_file = pd.DataFrame(
            {
                "queries": questions,
                "responses": responses,
                "page_contents": page_contents,
                "sources": sources,
            }
        )

    return responses_file
