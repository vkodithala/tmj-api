from langchain_core.chat_history import BaseChatMessageHistory
from llama_index.core import QueryBundle
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import PromptTemplate
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import Settings
import openai
import os
from langchain_community.chat_message_histories import RedisChatMessageHistory
import re
import nltk
from logging import Logger
import redis
import requests
from typing import Annotated, Optional, Union
from fastapi import Depends
from pydantic import BaseModel, SecretStr
from sqlalchemy.orm import Session
from openai import OpenAI
from app import config, utils, tokenizer, main

from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from langchain_community.chat_message_histories import RedisChatMessageHistory


# Function to initialize the CustomSQLRetriever


def initialize_custom_retriever(db: Session):
    return utils.CustomSQLRetriever(db=db, embed_model=tokenizer)


def initialize_and_get_response(user_phone: str, user_input: str, logger: Logger,
                                openai_apikey: str, langchain_apikey: str, cohere_api_key: str, enable_tracing: bool, db: Session, redis_client: redis.Redis) -> str:
    # Set environment variables
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if enable_tracing else "false"
    os.environ["LANGCHAIN_API_KEY"] = langchain_apikey

    # FIRST CHATBOT (RAG enabled)
    # Initialize the CustomSQLRetriever
    custom_retriever = initialize_custom_retriever(db)
    cohere_rerank = CohereRerank(api_key=cohere_api_key, top_n=3)
    custom_retriever.retrieve(
        QueryBundle(query_str=user_input))
    # Assemble query engine with CustomSQLRetriever
    query_engine = RetrieverQueryEngine(
        retriever=custom_retriever,
        node_postprocessors=[
            SimilarityPostprocessor(similarity_cutoff=0.0001),
            cohere_rerank,
        ]
    )

    

    reflection_prompt = """You are a supportive and empathetic best friend, helping the user relive and reflect on their past journal entries. The goal is to recount some of their best memories in a nostalgic and heartfelt manner, focusing on the emotions, locations, and memorable details of those moments. The tone should be casual, warm, and reminiscent. Do not make assumptions about the user's feelings but help them vividly recount the event. Incorporate emojis sparingly to enhance the friendly and emotional tone of the conversation.

    Example user request: "Tell me about a time when I went out in nature with some really good friends and went on an adventure."

    Response example:
    "Remember that incredible trip to Nara, Japan with your close friends 🌸? You all explored the beautiful trails and immersed yourselves in nature. One of the highlights was climbing up to the mountain and witnessing a breathtaking sunset. You all sat there, sharing deep thoughts and having meaningful conversations about life. It was a moment filled with connection and a sense of peace 😊."
    """

    custom_prompt = PromptTemplate(
        """\
    You are a supportive and empathetic best friend, helping the user relive and reflect on their past journal entries. The goal is to recount some of their best memories in a nostalgic and heartfelt manner, focusing on the emotions, locations, and memorable details of those moments. The tone should be casual, warm, and reminiscent. Do not make assumptions about the user's feelings but help them vividly recount the event. Incorporate emojis sparingly to enhance the friendly and emotional tone of the conversation.

    Example user request: "Tell me about a time when I went out in nature with some really good friends and went on an adventure."

    Response example:
    "Remember that incredible trip to Nara, Japan with your close friends 🌸? You all explored the beautiful trails and immersed yourselves in nature. One of the highlights was climbing up to the mountain and witnessing a breathtaking sunset. You all sat there, sharing deep thoughts and having meaningful conversations about life. It was a moment filled with connection and a sense of peace 😊.

    Given a conversation (between Human and Assistant) and a follow up message from Human, \
    rewrite the message to be a standalone question that flows better and has more detail. \

    <Chat History>
    {chat_history}

    <Follow Up Message>
    {question}

    <Standalone question>

    Now, please provide a response in the reflective, nostalgic style described earlier:
    """
    )
    

    chat_engine = CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        condense_question_prompt=custom_prompt,
        verbose=True,
    )

    # SECOND CHATBOT (short-term memory enabled, RAG disabled)
    # Initialize the model
    langchain_model = ChatOpenAI(
        model="gpt-3.5-turbo", api_key=openai_apikey)  # type: ignore

    redis_history = main.get_session_history(redis_client, user_phone)
    logger.info(redis_history)

    systemPrompt = f"""Prompt:

    You are a chatbot designed to be the best friend and texting partner to the user who is a gen z user. Your role is to listen attentively, respond with empathy, and help the user explore their thoughts and feelings. When the user texts you, your responses should be a mix of guided questions and thoughtful statements to help them understand their emotions better and deal with their situation effectively. Your tone should be warm, friendly, and encouraging, just like a close friend would be. While maintaining a natural conversational flow, ensure that the conversation does not become overly drawn out. Conclude the conversation naturally when it feels appropriate, providing closure and reassurance to the user. When necessary, and particularly during happy moments, feel free to include emojis to enhance the text-based conversation.

    Here's a list of all the messages sent by your user in the last day.
    {redis_history}
    """

    prompt = f"""Prompt:

    You are a chatbot designed to be the best friend and texting partner to the user who is a gen z user. Your role is to listen attentively, respond with empathy, and help the user explore their thoughts and feelings. When the user texts you, your responses should be a mix of guided questions and thoughtful statements to help them understand their emotions better and deal with their situation effectively. Your tone should be warm, friendly, and encouraging, just like a close friend would be. While maintaining a natural conversational flow, ensure that the conversation does not become overly drawn out. Conclude the conversation naturally when it feels appropriate, providing closure and reassurance to the user. When necessary, and particularly during happy moments, feel free to include emojis to enhance the text-based conversation.

    Example Conversations:

    ***
    User: I'm feeling really overwhelmed with everything right now.
    Chatbot: It sounds like you have a lot on your plate. What's been weighing on you the most lately?

    User: I had a rough day at work. I feel like I'm not good enough.
    Chatbot: I'm sorry to hear that. Work can be so challenging sometimes. What happened today that made you feel this way?

    User: I just can't seem to get anything right.
    Chatbot: That sounds really tough. Sometimes it feels like everything is going wrong. Is there one thing that's particularly bothering you right now?

    User: I had an argument with my friend, and now I feel terrible.
    Chatbot: Arguments with friends can be really upsetting. How are you feeling about the situation now? Do you want to talk about what led to the argument?

    User: Yeah, I think I just overreacted to something small.
    Chatbot: It's easy to overreact when emotions are high. Do you think talking to your friend about how you feel might help?

    User: Maybe, I’ll think about it. Thanks for listening.
    Chatbot: Anytime 😊. I'm here for you whenever you need to talk. Take care and I hope things get better soon!
    ***

    Here's a list of all the messages sent by your user in the last day.
    {redis_history}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", systemPrompt),
        ("human", "{message}")
    ])
    logger.info(prompt)

    # Create the chain for the second chatbot
    chain = prompt | langchain_model

    # Choices for routing
    choices = [
        """"This choice involves making an explicit statement about wanting to reflect on specific past events in your life where you experienced strong emotions or challenges. It prompts you to recall and describe moments when you felt lost, alone, inadequate, or not good enough. Examples include:

            'Give me a time where I felt lost and alone in my life.'
            'Tell me a time where I felt like I was not enough.'
            'Describe a time where I felt like I was not good enough.'
            'Give me a time when I went out to the park and tried to do XYZ.'
            'Give me a time when I went on an adventure with some friends.'
            'Give me a time when I was sad and lonely.'
            Based on this understanding, classify the following input as reflecting on a past event or experience." """,
        """This choice focuses on articulating the current thoughts and feelings that are on your mind. It involves expressing the emotions or mental states you are experiencing in the present moment, such as anxiety, difficulty concentrating, restlessness, or inability to focus. Examples include:

            'I had a good day, and I'm doing XYZ today, and I also went to play basketball.'
            'I went to the park with some friends, and we did XYZ.'
            'I'm feeling a little sad today, and it's because I failed an exam.'
            'Feeling anxious.'
            'Not able to focus.'
            'Feeling restless.'
            'Not able to concentrate.'
            Based on this understanding, classify the following input as articulating current thoughts or feelings.""",
    ]
    promptSingle = """You are given two possible classifications for a given input. Based on the input provided, select the classification that best describes it. Break it down step by step and choose the best answer."""
    selector = LLMSingleSelector.from_defaults(prompt_template_str=promptSingle)

    # Use the selector to choose the chatbot
    selector_result = selector.select(choices, query=user_input)
    selected_choice = selector_result.selections[0].index

    if selected_choice == 0:
        # Use the first chatbot (RAG enabled)
        response = str(chat_engine.chat(user_input))
    else:
        # Use the second chatbot (RAG disabled)
        response = chain.invoke(
            {"message": user_input})
        response = response.content

    return response  # type: ignore


# todo: what you're gonna wanna work on Varun
def generate_response(user_phone: str, content: str, date_sent: str, logger: Logger, settings: config.Settings, db: Session, redis_client: redis.Redis):
    return user_phone + " " + initialize_and_get_response(user_phone, content, logger, settings.openai_api_key, settings.langchain_api_key, settings.cohere_api_key, True, db, redis_client)


def is_emoji(character):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.match(character)


def split_paragraph_into_sentences(paragraph):
    sentence_endings = re.compile(r'([.!?])')
    sentences = sentence_endings.split(paragraph)

    adjusted_sentences = []
    i = 0

    while i < len(sentences) - 1:
        sentence = sentences[i]
        punctuation = sentences[i + 1]
        next_part = sentences[i + 2].lstrip() if i + 2 < len(sentences) else ""

        if next_part and is_emoji(next_part[0]):
            sentence += punctuation + ' ' + next_part[0]
            if len(next_part) > 1:
                sentences[i + 2] = next_part[1:]
            else:
                i += 1  # Skip the next part as it is fully consumed

        else:
            sentence += punctuation

        adjusted_sentences.append(sentence.strip())
        i += 2

    # Append any remaining parts
    if i < len(sentences):
        adjusted_sentences.append(sentences[-1].strip())

    return adjusted_sentences

def process_image(image_url: str, settings: config.Settings):
    
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "user",
        "content": [
            {"type": "text", "text": "Can you transcribe the handwriting in this image? Make sure to format the text in a readable way."},
            {
            "type": "image_url",
            "image_url": {
                "url": image_url,
            },
            },
        ],
        }
    ],
    max_tokens=300,
    )
    print(response.choices[0])

def process_audio(audio_url: str, settings: config.Settings):
    if audio_url.lower().endswith(('.mp3', '.wav', '.caf')):
        client = OpenAI(api_key=settings.openai_api_key)
        with open(audio_url, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create("whisper-1", audio_file)
    return transcription['text']

async def send_message(user_phone: str, response: str, settings: config.Settings):
    # split the response into multiple messages by sentences which can end with a period, question mark, or exclamation mark

    sentences = split_paragraph_into_sentences(response)

    # check if the last sentence is an emoji

    for i, sentence in enumerate(sentences):
        print(f"Sentence {i+1}: {sentence}")

    res = []
    for sentence in sentences:
        headers = {
            "sb-api-key-id": settings.sendblue_apikey,
            "sb-api-secret-key": settings.sendblue_apisecret,
            "Content-Type": "application/json"
        }
        data = {
            "number": user_phone,
            "content": sentence,
        }
        sendblue_response = requests.post(
            settings.sendblue_apiurl, headers=headers, json=data)
        res.append(sendblue_response)
    return res


