from logging import Logger
import redis
import requests
from typing import Annotated, Optional, Union
from fastapi import Depends
from pydantic import BaseModel, SecretStr
from sqlalchemy.orm import Session

from app import config, utils, tokenizer, main

from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from langchain_community.chat_message_histories import RedisChatMessageHistory


import os
import openai
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core import PromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.selectors import LLMSingleSelector

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from llama_index.core import QueryBundle
from langchain_core.chat_history import BaseChatMessageHistory

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

    custom_prompt = PromptTemplate(
        """\
    Given a conversation (between Human and Assistant) and a follow up message from Human, \
    rewrite the message to be a standalone question that flows better and has more detail. \

    <Chat History>
    {chat_history}

    <Follow Up Message>
    {question}

    <Standalone question>
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

    system_message = f"""You are a supportive therapist for reflective journaling, focusing on daily life, emotions, and personal events. You emphasize emotional exploration by asking specific, open-ended questions that help users understand and process their feelings deeply. The tone is empathetic, encouraging reflection and fostering self-discovery, without offering direct advice or solutions, instead facilitating personal insights and growth through thoughtful questioning. Keep the responses under 4 sentences and keep it to one question for a response.
    Here is a list of all of the past messages provided by the user:
    {' '.join(redis_history)}"""  # type: ignore

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
    ])
    logger.info(prompt)

    # Create the chain for the second chatbot
    chain = prompt | langchain_model

    # Choices for routing
    choices = [
        """This choice involves making an explicit statement about wanting to reflect on specific past events in your life where you experienced strong emotions or challenges. It prompts you to recall and describe moments when you felt lost, alone, inadequate, or not good enough. For example, you might ask, "Give me a time where I felt lost and alone in my life," "Tell me a time where I felt like I was not enough," or "Describe a time where I felt like I was not good enough." """,
        """This choice focuses on articulating the current thoughts and feelings that are on your mind. It involves expressing the emotions or mental states you are experiencing in the present moment, such as anxiety, difficulty concentrating, restlessness, or inability to focus. Examples of phrases that might be used include "feeling anxious," "not able to focus," "feeling restless," or "not able to concentrate." """,
    ]

    selector = LLMSingleSelector.from_defaults()

    # Use the selector to choose the chatbot
    selector_result = selector.select(choices, query=user_input)
    # selected_choice = selector_result.selections[0].index
    selected_choice = 1

    if selected_choice == 0:
        # Use the first chatbot (RAG enabled)
        response = str(chat_engine.chat(user_input))
    else:
        # Use the second chatbot (RAG disabled)
        response = chain.invoke(
            {"\"message\"": user_input})
        response = response.content

    return response  # type: ignore


# todo: what you're gonna wanna work on Varun
def generate_response(user_phone: str, content: str, date_sent: str, logger: Logger, settings: config.Settings, db: Session, redis_client: redis.Redis):
    return user_phone + " " + initialize_and_get_response(user_phone, content, logger, settings.openai_api_key, settings.langchain_api_key, settings.cohere_api_key, True, db, redis_client)


async def send_message(user_phone: str, response: str, settings: config.Settings):
    headers = {
        "sb-api-key-id": settings.sendblue_apikey,
        "sb-api-secret-key": settings.sendblue_apisecret,
        "Content-Type": "application/json"
    }
    data = {
        "number": user_phone,
        "content": response,
    }
    sendblue_response = requests.post(
        settings.sendblue_apiurl, headers=headers, json=data)
    return sendblue_response.json
