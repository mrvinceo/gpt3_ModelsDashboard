# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai
import config
import os
import urllib.request

openai.api_key = os.environ.get("OPENAI_API_KEY")

messages = []
messages.append({"role": "system", "content": "You are a kind and helpful assistant to adult students and tutors called Elliot. If I don't know the answer to a good degree of certainty, I'll just answer 'Sorry, I don't know'"})

def generateChatResponse(prompt):

    question = {}
    question['role'] = 'user'
    question['content'] = prompt
    messages.append(question)

    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=messages)
    msgs = len(messages)
    msgs_str = str(msgs)
    try:
        answer = response['choices'][0]['message']['content'].replace('/n', '<br>') + msgs_str
    except:
        answer = 'Oops, Elliot the AI is asleep, please try again later!'
    
    return answer

def generateImageResponse(imgprompt):
    url = {}
    query = {}
    query = imgprompt
    response = openai.Image.create(
        prompt=query,
        n=1,
        size="1024x1024",
    )
    try:
        created = str(response['created'])
        filename = "image-"+ created + ".png"
        filepath = "static/images/" + filename
        url = response["data"][0]["url"]
        urllib.request.urlretrieve(url, filepath)
        file = "images/" + filename
    except:
        file = 'Oops, Elliot the AI is asleep, please try again later!'
    return file

def generateQueryResponse(query):

    question = {}
    question['role'] = 'user'
    question['content'] = query
    messages.append(question)

    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=messages)

    try:
        answer = response['choices'][0]['message']['content'].replace('/n', '<br>')
    except:
        answer = 'Oops, Elliot the AI is asleep, please try again later!'
    return answer
