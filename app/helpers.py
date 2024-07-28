from logging import Logger
import requests
from typing import Annotated, Optional, Union
from fastapi import Depends
from pydantic import BaseModel, SecretStr
from sqlalchemy.orm import Session

from app import config, utils, tokenizer, main

from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore


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
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from llama_index.core import QueryBundle

# Global variable to store chat histories
store = {}

# Function to initialize the CustomSQLRetriever


def initialize_custom_retriever(db: Session):
    return utils.CustomSQLRetriever(db=db, embed_model=tokenizer)


def initialize_and_get_response(session_id: str, user_input: str, logger: Logger,
                                openai_apikey: str, langchain_apikey: str, cohere_api_key: str, enable_tracing: bool, db: Session) -> str:
    # Set environment variables
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if enable_tracing else "false"
    os.environ["LANGCHAIN_API_KEY"] = langchain_apikey

    # Initialize the model
    langchain_model = ChatOpenAI(
        model="gpt-3.5-turbo", api_key=openai_apikey)  # type: ignore

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    # Create a Runnable with message history
    with_message_history = RunnableWithMessageHistory(
        langchain_model, get_session_history)

    # Define the prompt template for the second chatbot
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a supportive therapist for reflective journaling, focusing on daily life, emotions, and personal events. You emphasize emotional exploration by asking specific, open-ended questions that help users understand and process their feelings deeply. The tone is empathetic, encouraging reflection and fostering self-discovery, without offering direct advice or solutions, instead facilitating personal insights and growth through thoughtful questioning. Keep the responses under 4 sentences and keep it to one question for a response."),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # Create the chain for the second chatbot
    chain = prompt | langchain_model

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

    # Create chat engine for the first chatbot
    chat_history = [
        ChatMessage(
            role=MessageRole.USER,
            content="You are an assistant who specializes in helping me reflect on past events in my life. Use specific examples from the entries to explain the specifics behind the event that I am trying to reflect on.",
        ),
    ]

    chat_engine = CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        condense_question_prompt=custom_prompt,
        chat_history=chat_history,
        verbose=True,
    )

    # Choices for routing
    choices = [
        """This choice involves making an explicit statement about wanting to reflect on specific past events in your life where you experienced strong emotions or challenges. It prompts you to recall and describe moments when you felt lost, alone, inadequate, or not good enough. For example, you might ask, "Give me a time where I felt lost and alone in my life," "Tell me a time where I felt like I was not enough," or "Describe a time where I felt like I was not good enough." """,
        """This choice focuses on articulating the current thoughts and feelings that are on your mind. It involves expressing the emotions or mental states you are experiencing in the present moment, such as anxiety, difficulty concentrating, restlessness, or inability to focus. Examples of phrases that might be used include "feeling anxious," "not able to focus," "feeling restless," or "not able to concentrate." """,
    ]

    selector = LLMSingleSelector.from_defaults()

    # Manage session history
    if session_id not in store:
        store[session_id] = ChatMessageHistory()

    # Use the selector to choose the chatbot
    chat_history = store[session_id].messages
    selector_result = selector.select(choices, query=user_input)
    selected_choice = selector_result.selections[0].index

    if selected_choice == 0:
        # Use the first chatbot
        chat_history.append(ChatMessage(
            role=MessageRole.USER, content=user_input))
        response = str(chat_engine.chat(user_input))
        chat_history.append(ChatMessage(
            role=MessageRole.ASSISTANT, content=response))
    else:
        # Use the second chatbot
        response = chain.invoke(
            {"messages": [HumanMessage(content=user_input)]})
        chat_history.append(ChatMessage(
            role=MessageRole.ASSISTANT, content=response.content))
        response = response.content

    return response  # type: ignore


# todo: what you're gonna wanna work on Varun
def generate_response(user_phone: str, content: str, date_sent: str, logger: Logger, settings: config.Settings, db: Session):
    return user_phone + " " + initialize_and_get_response('1', content, logger, settings.openai_api_key, settings.langchain_api_key, settings.cohere_api_key, True, db)


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
