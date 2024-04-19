"""
This is a boilerplate pipeline 'data_science'
generated using Kedro 0.19.3
"""

from kedro.pipeline import Pipeline, node, pipeline

from healthcare_chatbot.pipelines.data_science.nodes import (
    generate_wordcloud,
    get_responses,
)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=generate_wordcloud,
                inputs="queries_file",
                outputs="wordcloud",
                name="generate_wordcloud_node",
            ),
            node(
                func=get_responses,
                inputs=[
                    "queries_file",
                    "params:api",
                    "params:start_index",
                    "params:end_index",
                ],
                outputs="responses_file",
                name="get_responses_node",
            ),
        ]
    )
