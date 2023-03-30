# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai,config,urllib.request,os,sys
from os import environ

from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from os.path import exists

from langchain import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def construct_index(directory_path):
    path = 'index.json'
    file_exists = exists(path)
    if file_exists == False:
        max_input_size = 8096
        num_outputs = 1024
        max_chunk_overlap = 20
        chunk_size_limit = 600

        prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

        llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.7, model_name="text-davinci-003", max_tokens=num_outputs))

        documents = SimpleDirectoryReader(directory_path).load_data()
        index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)

        index.save_to_disk('index.json')
    else:
        index = 'index.json'
    return index

def chatbot(query):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    answer = index.query(query, response_mode="compact")
    answer = answer.response
    return answer

index = construct_index("docs")
