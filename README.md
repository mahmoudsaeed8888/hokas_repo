# mini-rag

This is a minimal implementatin of the RAG model for question answering.

## Requirements 

- python 3.8 or later

### Install python using Miniconda 

1) Download and install Miniconda from [here](https://docs.anaconda.com/free/miniconda/#quick-command-line-install)

2) Create a new environment using the following command : 
```bash
$ conda create -n mini-rag python=3.8 
````

3) Activate the environment : 
```bash
$ conda activate mini-rag
```

#### (optional) setup you command line for better readability

```bash 
export PS1="\[\033[01;32m\]\u@\h:\w\n[\033[00m\]\$"
```

## INSTALLATION

### Install the required packages 
```bash
$ pip install -r requirements.txt
```

### SETUP THE ENVIRONMENT VARIABLES
```bash
$ cp .env.example .env
```
set your environment variable  in the `.env` file . like `OPENAI_API_KEY` value

## Run the FastAPI server 
```bash
$ uvicron main:app --reload --host 0.0.0.0 --port 5000 
```
### POSTMAN COLLECTION 

Download the POSTMAN collection from [/assets/mini-rag-app.postman_collection.json](/assets/mini-rag-app.postman_collection.json)

## Install pydantic-settings==2.2.1
```bash 
cd src 
pip install -r Rquirements.txt
```
