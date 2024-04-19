# What is this for?

This folder should be used to store configuration files used by Kedro or by separate tools.

This file can be used to provide users with instructions for how to reproduce local configuration with their own credentials. For more information, refer to the sections under **Instructions**.

## Local configuration

The `local` folder should be used for configuration that is either user-specific (e.g. IDE configuration) or protected (e.g. security keys).

> **Note:** Please do not check in any local configuration to version control.

### Instructions

Create a configuration file for your credentials named `credentials.yml`. Inside, place your `OPENAI_API_KEY`.

```yml
OPENAI_API_KEY: <OPENAI_API_KEY>
```

## Base configuration

The `base` folder is for shared configuration, such as non-sensitive and project-related configuration that may be shared across team members.

> **Warning:** Please do not put access credentials in the base configuration folder.

### Instructions

#### [`catalog.yml`](conf/base/catalog.yml)

The `catalog.yml` contains the configurations to saved data containing the chunks that will be indexed into the vector database in JSON format.

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

# Some visualisation reporting to show the
# most frequent words in the form of a word cloud
# from the queries.
wordcloud:
  type: matplotlib.MatplotlibWriter
  filepath: data/08_reporting/wordcloud.png
```

#### [`parameters.yml`](conf/base/parameters.yml)

The `parameters.yml` file contains the configurations for the path to the vector database and name of the collection. The default location for the vector database will be at the root of the project and the default collection name will be _healthcare_.

```yml
# Contains the path to the vector database with respect
# to the root of the project and the collection name
vector_db:
  path: db
  collection_name: healthcare
```

#### [`parameters_data_processing.yml`](conf/base/parameters_data_processing.yml)

The `parameters_data_processing.yml` file contains the configurations for the URLs to websites and path to the directory containing the PDF files to index into the vector database.

It also contains configurations for the chunking strategy such as the:

1. Chunk Size
2. Chunk Overlap
3. Separators

Lastly, it contains the name of the embedding model that is used to transform the chunks into dense vector representations which will be stored in the vector database, the model used to power the chatbot and its hyperparameters like:

1. `temperature`: Determines how diverse the responses will be. In general, you want a low value for topics like healthcare related. For creative writing, a higher temperature value is usually used.
2. `max_tokens`: Controls the length of the generated responses

```yml
# This is a boilerplate parameters config generated for pipeline 'data_processing'
# using Kedro 0.19.3.
#
# Documentation for this file format can be found in "Parameters"
# Link: https://docs.kedro.org/en/0.19.3/configuration/parameters.html
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

#### [`parameters_data_science.yml`](conf/base/parameters_data_science.yml)

The `parameters_data_science.yml` file contains the configurations for the API endpoints as well as the configurations to determine the window size of queries to send to the chatbot. This setting helps mitigate rate limit errors when we call the API too often in a short time.

```yml
# This is a boilerplate parameters config generated for pipeline 'data_science'
# using Kedro 0.19.3.
#
# Documentation for this file format can be found in "Parameters"
# Link: https://docs.kedro.org/en/0.19.3/configuration/parameters.html
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
