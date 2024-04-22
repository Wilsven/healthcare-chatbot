"""
This is a boilerplate pipeline 'model_evaluation'
generated using Kedro 0.19.3
"""

from kedro.pipeline import Pipeline, node, pipeline

from healthcare_chatbot.pipelines.model_evaluation.nodes import (
    generate_barplot,
    get_evaluations,
)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=get_evaluations,
                inputs=[
                    "responses_file",
                    "params:eval_api",
                    "params:start_eval_index",
                    "params:end_eval_index",
                ],
                outputs="evaluations_file",
                name="get_evaluations_node",
            ),
            node(
                func=generate_barplot,
                inputs=[
                    "evaluations_file",
                    "params:criterion",
                    "params:labelled_criterion",
                ],
                outputs="barplot",
                name="generate_barplot_node",
            ),
        ]
    )
