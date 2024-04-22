# What is this for? <a id="what-is-this-for"></a>

This folder should be used to store configuration files used by Kedro or by separate tools.

This file can be used to provide users with instructions for how to reproduce local configuration with their own credentials. For more information, refer to the sections under **Instructions**.

## Overview

- [Local Configuration](#local-configuration)
  - [Instructions](#instructions)
    - [`credentials.yml`](#credentials)
- [Base Configuration](#base-configuration)
  - [Instructions](#base-instructions)
    - [`catalog.yml`](#catalog)
    - [`parameters.yml`](#parameters)
    - [`parameters_data_processing.yml`](#parameters_data_processing)
    - [`parameters_data_science.yml`](#parameters_data_science)
    - [`parameters_model_evaluation.yml`](#parameters_model_evaluation)

## Local Configuration <a id="local-configuration"></a>

The `local` folder should be used for configuration that is either user-specific (e.g. IDE configuration) or protected (e.g. security keys).

> **Note:** Please do not check in any local configuration to version control.

### Instructions <a id="local-instructions"></a>

#### `credentials.yml` <a id="credentials"></a>

Create a configuration file for your credentials named `credentials.yml`. Inside, place your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`.

> **Note:** GPT-3.5 powers the chatbot while either GPT-4 and/or Claude 3 can be used to evaluate the responses of the chatbot.

```yml
OPENAI_API_KEY: <OPENAI_API_KEY>
ANTHROPIC_API_KEY: <ANTHROPIC_API_KEY>
```

## Base Configuration <a id="base-configuration"></a>

The `base` folder is for shared configuration, such as non-sensitive and project-related configuration that may be shared across team members.

> **Warning:** Please do not put access credentials in the base configuration folder.

### Instructions <a id="base-instructions"></a>

#### [`catalog.yml`](conf/base/catalog.yml) <a id="catalog"></a>

The `catalog.yml` contains the configurations to save data containing the chunks that will be indexed into the vector database in JSON format. It also contains the configurations to load and save the queries, responses and evaluations.

```yml
# Contains the document chunks before indexing
# into the vector database. Review these JSON files
# to discover any relevant information to take note of.
docs_dict:
  type: json.JSONDataset
  filepath: data/02_intermediate/websites.json

pdfs_dict:
  type: json.JSONDataset
  filepath: data/02_intermediate/pdfs.json

# Contains the queries to evaluate the reponses from.
queries_file:
  type: pandas.CSVDataset
  filepath: data/03_primary/queries.csv

# This is where the responses from the chatbot will be
# saved. It also saves the most relevant document extracted
# from the vector database used as part of the context.
responses_file:
  type: pandas.CSVDataset
  filepath: data/07_model_output/responses.csv
  load_args:
    encoding: latin_1

# Some visualisation reporting to show the
# most frequent words in the form of a word cloud
# from the queries.
wordcloud:
  type: matplotlib.MatplotlibWriter
  filepath: data/08_reporting/wordcloud.png

# Stores the evaluation results over multiple criterion
# in a JSON file
evaluations_file:
  type: json.JSONDataset
  filepath: data/07_model_output/evaluations.json

# Some visualisation reporting to show the
# most evaluation scores for both criterion and
# labelled criterion
barplot:
  type: matplotlib.MatplotlibWriter
  filepath: data/08_reporting/barplot.png
```

#### [`parameters.yml`](conf/base/parameters.yml) <a id="parameters"></a>

The `parameters.yml` file contains the configurations for the path to the vector database and name of the collection. The default location for the vector database will be at the root of the project and the default collection name will be _healthcare_.

```yml
# Contains the path to the vector database with respect
# to the root of the project and the collection name
vector_db:
  path: db
  collection_name: healthcare
```

#### [`parameters_data_processing.yml`](conf/base/parameters_data_processing.yml) <a id="parameters_data_processing"></a>

The `parameters_data_processing.yml` file contains the configurations for the URLs to websites and path to the directory containing the PDF files to index into the vector database.

It also contains configurations for the chunking strategy such as the:

1. Chunk Size
2. Chunk Overlap
3. Separators

Lastly, it contains the name of the embedding model that is used to transform the chunks into dense vector representations which will be stored in the vector database, the model used to power the chatbot and its hyperparameters like:

1. `temperature`: Determines how diverse the responses will be. In general, you want a low value for topics like healthcare related. For creative writing, a higher temperature value is usually used.
2. `max_tokens`: Controls the length of the generated responses

```yml
websites:
  - https://www.healthhub.sg/a-z/diseases-and-conditions/diabetes-treatment-capsules--tablets
  - https://www.healthhub.sg/a-z/diseases-and-conditions/diabetic_foot_ttsh
  - https://www.healthhub.sg/a-z/diseases-and-conditions/diabetic-ulcer
  - https://www.healthhub.sg/a-z/diseases-and-conditions/diabetes-treatment-insulin
  - https://www.healthxchange.sg/diabetes/living-well-diabetes/diabetes-recommended-vaccinations-children-adults

pdfs_dir_path: data/01_raw/pdfs

splitter:
  chunk_size: 1000
  chunk_overlap: 100
  separators:
    - "\n\n"
    - "\n"
    - "."
    - "!"
    - "?"
    - ","
    - " "
    - ""

embedding_model_name: text-embedding-ada-002
model_name: gpt-3.5-turbo-0125
temperature: 0
max_tokens: 1024
```

#### [`parameters_data_science.yml`](conf/base/parameters_data_science.yml) <a id="parameters_data_science"></a>

The `parameters_data_science.yml` file contains the configurations for the chat API endpoints as well as the configurations to determine the window size of queries to send to the chatbot. This setting helps mitigate rate limit errors when we call the API too often in a short time.

```yml
# Chat API endpoint
api:
  domain: http://127.0.0.1:8000
  test_endpoint: /
  chat_endpoint: /chat

# Hint: Look inside response.csv file to see the index of the latest
# data. Subtract 1 from it and that would be your new `start_index`.

# For example:
# If the index of the last row in response.csv is 52. Then the new
#  `start_index` will be 52 - 1 = 51.

# Note: While the maximum value of `end_index` can be some arbitrarily large
# number, look inside queries.csv to see the the total number of rows.

# For example:
# If the last index in queries.csv is 238, you have a total of 237 queries since
# the first row is the header. Then the new `end_index` will be 237 - 1 = 236
# because Python is a 0-indexing language.
start_index: 0
end_index: 10
```

#### [`parameters_model_evaluation.yml`](conf/base/parameters_model_evaluation.yml) <a id="parameters_model_evaluation"></a>

The `parameters_model_evaluation.yml` file contains the configurations for the evaluation API endpoints as well as the configurations to determine the window size of queries-responses pair for evaluation. This setting helps mitigate rate limit errors when we call the API too often in a short time.

```yml
# Evaluation API endpoint
eval_api:
  domain: http://127.0.0.1:8000
  eval_endpoint: /evaluate

# Simply change this between "openai" or "anthropic" to use
# either GPT-4 or Claude 3 Sonnet model respectively
# to evaluate the responses
eval_model: openai

# Change this if you'd want to use another model for evaluation
# For example, you can swap out Claude 3 Sonnet with Claude 3 Opus
# or Claude 3 Haiku should you prioritize a higher capaibility vs speed respectively
eval_model_name:
  openai: gpt-4
  anthropic: claude-3-sonnet-20240229

# The criterion to evaluate
# Refer here for more info: https://python.langchain.com/docs/guides/productionization/evaluation/string/criteria_eval_chain/
criterion:
  - coherence
  - helpfulness

labelled_criterion:
  - correctness
  - relevance

start_eval_index: 0
end_eval_index: 10
```
