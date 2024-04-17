"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.19.3
"""

from kedro.pipeline import Pipeline, node, pipeline

from healthcare_chatbot.pipelines.data_processing.nodes import (index_pdfs,
                                                                index_websites)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=index_websites,
                inputs=[
                    "params:websites",
                    "params:embedding_model_name",
                    "params:vector_db",
                    "params:splitter",
                ],
                outputs="docs_dict",
                name="index_websites_node",
            ),
            node(
                func=index_pdfs,
                inputs=[
                    "params:pdfs_dir_path",
                    "params:embedding_model_name",
                    "params:vector_db",
                    "params:splitter",
                ],
                outputs="pdfs_dict",
                name="index_pdfs_node",
            ),
        ]
    )
