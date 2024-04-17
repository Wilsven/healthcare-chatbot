# What is this for?

This folder should be used to store configuration files used by Kedro or by separate tools.

This file can be used to provide users with instructions for how to reproduce local configuration with their own credentials. For more information, refer to the sections under **Instructions**.

## Local configuration

The `local` folder should be used for configuration that is either user-specific (e.g. IDE configuration) or protected (e.g. security keys).

> _Note:_ Please do not check in any local configuration to version control.

### Instructions

Create a configuration file for your credentials named `credentials.yml`. Inside, place your `OPENAI_API_KEY`.

```yml
OPENAI_API_KEY: <OPENAI_API_KEY>
```

## Base configuration

The `base` folder is for shared configuration, such as non-sensitive and project-related configuration that may be shared across team members.

> _Warning:_ Please do not put access credentials in the base configuration folder.

### Instructions

#### [`catalog.yml`](conf/base/catalog.yml)

The `catalog.yml` contains the configurations for the saved data containing the chunks that will be indexed into the vector database in JSON format.

#### [`parameters.yml`](conf/base/parameters_data_processing.yml)

The `parameters.yml` file contains the configurations for the path to the vector database and name of the collection. The default location for the vector database will be at the root of the project and the default collection name will be _healthcare_.

#### [`parameters_data_processing.yml`](conf/base/parameters.yml)

The `parameters_data_processing.yml` file contains the configurations for the URLs to websites and path to the directory containing the PDF files to index into the vector database.

It also contains configurations for the chunking strategy such as the:

1. Chunk Size
2. Chunk Overlap
3. Separators

Lastly, it contains the embedding model that is used to transform the chunks into dense vector representations which will be stored in the vector database.

## Find out more

You can find out more about configuration from the [user guide documentation](https://docs.kedro.org/en/stable/configuration/configuration_basics.html).
