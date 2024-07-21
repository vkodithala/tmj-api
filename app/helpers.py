import requests
from typing import Annotated, Optional
from fastapi import Depends
from pydantic import BaseModel, SecretStr

from app import config

import os
import openai
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor, TimeWeightedPostprocessor
from llama_index.core import PromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.tools import ToolMetadata
from llama_index.core.selectors import LLMSingleSelector

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore


class MessagePayload(BaseModel):
    accountEmail: str
    content: str
    media_url: str
    is_outbound: bool
    status: str
    error_code: Optional[int]
    error_message: Optional[str]
    message_handle: str
    date_sent: str
    date_updated: str
    from_number: str
    number: str
    was_downgraded: Optional[bool]
    plan: str


# Rebuild storage context and load index for the first chatbot

def main(user_input, settings: config.Settings):

    # Set environment variables
    # Initialize the model
    langchain_model = ChatOpenAI(
        # type: ignore
        # type: ignore
        model="gpt-4o", api_key=settings.openai_api_key)  # type: ignore
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
    choices = [
        """This choice involves making an explicit statement about wanting to reflect on specific past events in your life where you experienced strong emotions or challenges. It prompts you to recall and describe moments when you felt lost, alone, inadequate, or not good enough. For example, you might ask, "Give me a time where I felt lost and alone in my life," "Tell me a time where I felt like I was not enough," or "Describe a time where I felt like I was not good enough.""",
        """This choice focuses on articulating the current thoughts and feelings that are on your mind. It involves expressing the emotions or mental states you are experiencing in the present moment, such as anxiety, difficulty concentrating, restlessness, or inability to focus. Examples of phrases that might be used include "feeling anxious," "not able to focus," "feeling restless," or "not able to concentrate.""",
    ]

    selector = LLMSingleSelector.from_defaults()

    # Store chat history
    store = {}

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    # Create a Runnable with message history
    with_message_history = RunnableWithMessageHistory(
        langchain_model, get_session_history)  # type: ignore

    # Define the prompt template for the second chatbot
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a supportive therapist for reflective journaling, focusing on daily life, emotions, and personal events. You emphasize emotional exploration by asking specific, open-ended questions that help users understand and process their feelings deeply. The tone is empathetic, encouraging reflection and fostering self-discovery, without offering direct advice or solutions, instead facilitating personal insights and growth through thoughtful questioning. Keep the responses under 4 sentences and keep it to one question for a response.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    # Create the chain for the second chatbot
    chain = prompt | langchain_model  # type: ignore

    # Create chat engine for the first chatbot

    # cohere_rerank = CohereRerank(api_key=cohere_api_key, top_n=3)

    # Configure retriever

   # retriever = VectorIndexRetriever(
    #    index=index,  # type: ignore
    #    similarity_top_k=10,
    # )
    # chat_history = [
    #   ChatMessage(
    #      role=MessageRole.USER,
    # content="You are an assistant who specializes in helping me reflect on past events in my life. Use specific examples from the entries to explain the specifics behind the event that I am trying to reflect on.",
    # ),
    # ]

    """"
    # Assemble query engine
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        node_postprocessors=[
            SimilarityPostprocessor(
                similarity_cutoff=0.6,
            ),
            # cohere_rerank,
        ]
    )
    """

    """""
    chat_engine = CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        condense_question_prompt=custom_prompt,
        chat_history=chat_history,
        verbose=True,
    )
    """

    session_id = "default_session"
    guidedJournal = False
    while True:
        if user_input.lower() == '!exit':
            print("Goodbye!")
            break
        # Use the selector to choose the chatbot
        if not guidedJournal:
            selector_result = selector.select(choices, query=user_input)
            selected_choice = selector_result.selections[0].index
            if selected_choice == 1:
                guidedJournal = True
        else:
            selected_choice = 1

        # print(f"\n{Colors.WARNING}Routing Agent: {
            # selector_result}{Colors.ENDC}")  # type: ignore
        # print()

        if selected_choice == 0:
            # Use the first chatbot

            return "rag hiit"
        else:
            # Use the second chatbot
            response = chain.invoke(
                {"messages": [HumanMessage(content=user_input)]})
            # print(f"{Colors.FAIL}Journaling Agent: {response.content}{Colors.FAIL}")
            # print()
            return response.content


# todo: what you're gonna wanna work on Varun
def generate_response(user_phone: str, content: str, date_sent: str, settings: config.Settings):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    return main(content, settings)


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
