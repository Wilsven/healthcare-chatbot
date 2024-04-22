"""
This is a boilerplate pipeline 'model_evaluation'
generated using Kedro 0.19.3
"""

from pathlib import Path
from matplotlib import pyplot as plt
import pandas as pd
import requests
from kedro.framework.session import KedroSession
from tqdm import tqdm


def get_evaluations(
    responses_df: pd.DataFrame,
    eval_api_params: dict,
    start_eval_index: int,
    end_eval_index: int,
) -> list[dict]:
    """
    A function to get evaluations based on responses data, API parameters, and evaluation indices.

    Args:
        responses_df (pd.DataFrame): DataFrame containing responses data.
        eval_api_params (dict): Dictionary of evaluation API parameters.
        start_eval_index (int): The starting index for evaluation.
        end_eval_index (int): The ending index for evaluation.

    Returns:
        list[dict]: List of evaluation results in dictionary format.
    """
    # Get JSON already saved to be updated with new documents
    with KedroSession.create(project_path=Path.cwd()) as session:
        context = session.load_context()
        catalog = context.catalog

    domain = eval_api_params["domain"]
    eval_endpoint = eval_api_params["eval_endpoint"]
    eval_url = domain + eval_endpoint

    queries = responses_df["queries"].to_list()
    responses = responses_df["responses"].to_list()
    page_contents = responses_df["page_contents"].to_list()

    assert start_eval_index is not None and end_eval_index is not None

    queries = queries[start_eval_index : end_eval_index + 1]
    responses = responses[start_eval_index : end_eval_index + 1]
    page_contents = page_contents[start_eval_index : end_eval_index + 1]

    assert len(queries) == len(responses) == len(page_contents)

    qrp = tqdm(zip(queries, responses, page_contents))
    criterion_responses = []

    for query, response, page_content in qrp:
        qrp.set_description(f"Getting criterion evaluation for query: {query}")

        try:
            criterion_response = requests.post(
                eval_url,
                json={
                    "query": query,
                    "response": response,
                    "page_content": page_content,
                },
            )

            if criterion_response.status_code == 200:
                criterion_responses.append(criterion_response.json())
        except:
            break

    try:
        evaluations_file = catalog.load("evaluations_file")
        new_evaluations_file = criterion_responses
        evaluations_file.extend(new_evaluations_file)

    except Exception:
        print(
            "There is no existing evaluations.json file. Creating new evaluations.json file."
        )
        evaluations_file = criterion_responses

    return evaluations_file


def generate_barplot(
    evaluations_file: list[dict], criterion: list[str], labelled_criterion: list[str]
) -> plt.Figure:
    """
    Generate a barplot of the mean scores of evaluation criteria over all responses.

    Args:
        evaluations_file (list[dict]): A list of dictionaries containing evaluation data.
        criterion (list[str]): A list of strings representing the evaluation criteria.
        labelled_criterion (list[str]): A list of strings representing the labelled evaluation criteria.

    Returns:
        plt.Figure: The generated barplot figure.
    """
    eval_df = pd.DataFrame(
        columns=[
            "queries",
            "responses",
            "page_contents",
            *criterion,
            *labelled_criterion,
        ]
    )

    for i, eval in enumerate(evaluations_file):
        eval_df.at[i, "queries"] = eval["query"]
        eval_df.at[i, "responses"] = eval["response"]
        eval_df.at[i, "page_contents"] = eval["page_content"]

        for criteria in criterion:
            eval_df.at[i, criteria] = eval[criteria]["score"]

        for labelled_criteria in labelled_criterion:
            eval_df.at[i, labelled_criteria] = eval[labelled_criteria]["score"]

    eval_df[[*criterion, *labelled_criterion]] = eval_df[
        [*criterion, *labelled_criterion]
    ].astype(int)

    meta_df = eval_df[[*criterion, *labelled_criterion]].describe().T

    fig = plt.figure()
    fig.set_figheight(4.5)
    fig.set_figwidth(4.5 * 2)
    plt.barh(meta_df.index[::-1], meta_df["mean"][::-1])
    plt.xlabel("Mean Scores")
    plt.ylabel("Criteria")
    plt.title("Mean Scores of Evaluation Criteria over All Responses")
    plt.show()

    return fig
