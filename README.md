# Lifelong Learning Logger (L2Logger)

[![DOI](https://zenodo.org/badge/298137550.svg)](https://zenodo.org/badge/latestdoi/298137550)

![APL Logo](https://github.com/lifelong-learning-systems/l2logger/raw/release/docs/apl_small_horizontal_blue.png)

## Table of Contents

- [Introduction](#introduction)
- [Logger Term Definitions/Glossary](#logger-term-definitionsglossary)
- [Logger Output Format](#logger-output-format)
- [Interface/Usage](#interfaceusage)
- [Examples](#examples)
- [Tests](#tests)
- [Log Aggregation](#log-aggregation)
  - [Example](#aggregation-example)
  - [Usage](#aggregation-usage)
- [Log Validation](#log-validation)
  - [Example](#validation-example)
  - [Usage](#validation-usage)
- [Changelog](#changelog)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Introduction

The Lifelong Learning Logger is a utility library provided for
producing logs in a convenient format for the provided l2metrics module,
but can also be used independently.

## Logger Term Definitions/Glossary

Strongly recommend starting here, detailed explanation of the terms used
throughout: [docs/definitions.md](https://github.com/lifelong-learning-systems/l2logger/blob/release/docs/definitions.md).

## Logger Output Format

Detailed explanations of the logging output structure/format can be seen via
[docs/log_format.md](https://github.com/lifelong-learning-systems/l2logger/blob/release/docs/log_format.md).

## Interface/Usage

At a high level, the library is used simply by creating an
instance of the logger object, then by invoking the `log_record`
 member function on it at least once per experience.

For a detailed explanation of the provided functions, see
[docs/interface.md](https://github.com/lifelong-learning-systems/l2logger/blob/release/docs/interface.md).

## Examples

See documentation in the examples folder at [examples/README.md](https://github.com/lifelong-learning-systems/l2logger/blob/release/examples/README.md).

## Tests

See documentation in the test folder at [test/README.md](https://github.com/lifelong-learning-systems/l2logger/blob/release/test/README.md).

## Log Aggregation

L2Logger provides a module for exporting an aggregated data table from an
L2Logger directory as a TSV, CSV, or Feather file.

### Aggregation Example

The following is a simple example for how to aggregate a log directory into a single TSV file:

```bash
python -m l2logger.aggregate <path/to/log_directory>
```

### Aggregation Usage

```text
usage: python -m l2logger.aggregate [-h] [-f {tsv,csv,feather}] [-o OUTPUT] log_dir

Aggregate data within a log directory from the command line

positional arguments:
  log_dir               Log directory of scenario

optional arguments:
  -h, --help            show this help message and exit
  -f {tsv,csv,feather}, --format {tsv,csv,feather}
                        Output format of data table
  -o OUTPUT, --output OUTPUT
                        Output filename
```

## Log Validation

Logs generated by L2Logger should already be in the proper format for ingestion by the Metrics Framework. However, log validation can also be done manually using the provided `validate.py` module.

### Validation Example

```bash
python -m l2logger.validate <path/to/log_directory>
```

### Validation Usage

```text
usage: python -m l2logger.validate [-h] log_dir

Validate log format from the command line

positional arguments:
  log_dir     Log directory of scenario

optional arguments:
  -h, --help  show this help message and exit
```

Note: This script only validates one instance of a scenario output; it does not run recursively on a directory containing multiple scenario logs.

## Changelog

See [CHANGELOG.md](https://github.com/lifelong-learning-systems/l2logger/blob/release/CHANGELOG.md) for a list of notable changes to the project.

## License

See [LICENSE](https://github.com/lifelong-learning-systems/l2logger/blob/release/LICENSE) for license information.

## Acknowledgements

Primary development of Lifelong Learning Logger (L2Logger) was funded by the DARPA Lifelong Learning Machines (L2M) Program.

© 2021-2022The Johns Hopkins University Applied Physics Laboratory LLC
