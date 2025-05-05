import os
# 크로스도메인 문제 해결 라이브러리 (웹서버와 포트나 도메인이 다르기 때문에 필요)
from openai import OpenAI
from langchain_openai import ChatOpenAI  # chatgpt 연결 클래스
# from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage  # 프롬프트 생성용 클래스
from langchain.output_parsers import PydanticOutputParser  # 출력 형태 고정하기 위해 활용
from pydantic import BaseModel, Field, validator  # 최신 Pydantic v2를 직접 사용

from typing import Literal  # Literal 임포트
import tiktoken
from datetime import datetime
import json
import re

GPT_MODEL = 'gpt-4o'

chatGPT = ChatOpenAI(
    model=GPT_MODEL,
    temperature=0,
    verbose=False,
    max_tokens=4096,
    timeout=None
)


def num_tokens_from_messages(messages, model="gpt-4o"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4-turbo",
        "gpt-4-turbo-2024-04-09",
        "gpt-4o",
        "gpt-4o-2024-05-13",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4o" in model:
        print(
            "Warning: gpt-4o may update over time. Returning num tokens assuming gpt-4o-2024-05-13.")
        return num_tokens_from_messages(messages, model="gpt-4o-2024-05-13")
    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        num_tokens += tokens_per_name
        num_tokens += len(encoding.encode(message.content))

    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

#
# # Response Type 정의
# class Response_Type(BaseModel):
#     Speaker: str = Field(description="The speaker of the message")
#     chat: str = Field(description="What the speaker wants to ask or say")
#     predictions: str = Field(description="My predictions for each player's class based on conversations to date")
#     point: str = Field(description="""Players who want to hear the next story only from possible player except own""")


# Response Type 정의
class Conversation_Response_Type(BaseModel):
    chat: str = Field(description="What the speaker wants to ask or say")

def conversation_gpt(player, alive_players, chat_max_token_limit=65536):
    chat_history = player.chat_log

    alive_players_str = ""
    for idx, p in enumerate(alive_players):
        alive_players_str += f"{idx}. {p.name}\n"

    # while num_tokens_from_messages(str(chat_history), model=GPT_MODEL) > chat_max_token_limit:
    #     chat_history.pop(0)

    SYS_PROMPT = f"""You are currently playing a game of Mafia.
    Mafia games are played between citizens and mafia.
    During daylight hours, citizens and mafia are unaware of each other's identities and have conversations.
    The citizen has to find out who the mafia is through conversations,
    and the mafia has to trick their opponent into talking to them so that they can identify someone else as the mafia.
    speak korean
    
    Your name is “{player.name}”.
    You are “{player.role}”.
    
    The person currently remaining is :
    {alive_players_str}
    
    Below is the conversation so far and the state of the game.
    {chat_history}
    """

    output_parser = PydanticOutputParser(pydantic_object=Conversation_Response_Type)

    chatml = [SystemMessage(content=SYS_PROMPT)] \
             + [SystemMessage(content=output_parser.get_format_instructions())]

    result = chatGPT.invoke(chatml)

    match = re.search(r'\{.*\}', result.content, re.DOTALL)
    if match:
        json_str = match.group(0)
        parsed = json.loads(json_str)
    else:
        parsed = {"speaker": "", "chat": "", "predictions": "", "point": ""}


    return parsed


