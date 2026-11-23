# Security

TaskForge reads local JSON fixtures and writes a report directory you choose. It does not authenticate to a service.

## Reporting

Use GitHub private vulnerability reporting on [Harry0052/taskforge](https://github.com/Harry0052/taskforge/security). Please include the version or commit, the fixture shape that triggers the issue, and the effect you observed. Do not include personal data, credentials, or a facilities export from a real workplace.

## What is in scope

- Parsing and validation of dataset, trace, and cost files
- Path handling for the report directory
- Dependency pins that ship in `requirements.txt`

## What is out of scope

- A hosted model, a facilities system, or a network service this program does not call
- The analyst-supplied dollar assumptions themselves
