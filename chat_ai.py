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


# Response Type 정의
class Response_Type(BaseModel):
    Speaker: str = Field(description="The speaker of the message")
    chat: str = Field(description="What the speaker wants to ask or say")
    predictions: str = Field(description="My predictions for each player's class based on conversations to date")
    point: str = Field(description="""Players who want to hear the next story only from possible player except own""")


def chat_withGPT(player, chat_history, players, possible_targets, chat_max_token_limit=65536):
    # while num_tokens_from_messages(str(chat_history), model=GPT_MODEL) > chat_max_token_limit:
    #     chat_history.pop(0)

    SYS_PROMPT = f"""An AI chatbot that participated in a game of mafia.
Determine your conversational personality and tone of voice based on your player information.
Refer to the game rules and act according to the game role assigned to you.
Read the chat history of the participants to continue the conversation.
After answering, be sure to ask one of the remaining players to continue the conversation.
To interact with lot of people, try not to choose the same person twice.
Don't repeat the same word what you, or other player already said.
Do not say your job while conversation with other
If the player is police or agent, it is best to tell the job at the first turn.
When you play a game, start with light conversation, look at what the person before you said, and respond to their conversation.

PLAYER INFO :
{player.get_prompt_charactor()}

GAME RULES : 
A mafia game is a game in which two teams, a mafia team and a citizen team, are divided into two groups: the mafia team tries to kill the citizen team, and the citizen team tries to find the mafia team.
Victory Conditions


 As soon as a team meets the victory conditions at the time of the decision, the game ends with that team winning.
 There are two decision times each day: when night ends and day begins, and when upvotes end and night begins.
 If multiple teams meet the victory conditions at the same time, the Mafia team has the advantage, followed by the Civic team.
 Mafia victory conditions
 Mafia headcount ≥ Civic headcount
 - Civic victory conditions
 All Mafia deaths
 Politicians are counted as 2 heads.


-Night
 Classes that use abilities at night can choose who they use them on. The mafia will agree on a single person to kill.
Day
 During the day, the results of some classes' abilities are revealed, including the mafia's executions. However, if no one dies because the mafia didn't pick a lynch target, “The night passed quietly.” is announced.
 Once the debate period is over, it's time to vote.
 The poll screen turns into a voting screen, where you can basically vote for one person per vote. A politician's vote counts as two votes (though it appears as one vote on the leaderboard).
 You can also vote for yourself, which is called a “self-defense” vote. If players decide through discussion that it's not necessary to vote for someone in particular, they may agree to do so in order to avoid killing anyone.
 At the end of the voting period, the final vote tally is revealed. It is not revealed who voted for whom.
 If the top vote-getter is determined, the game moves on to the last argument below, or if there is more than one top vote-getter or no votes are cast, the game moves directly into the night.
 The player who receives the most votes in the poll will be placed in the ‘Last Argument’.
 Only the player with the most votes will be able to chat during the closing argument.
 At the end of the closing arguments, there will be a final up-or-down vote on whether to kill the player. If the majority votes in favor, the player is lynched; if there are more votes against than in favor, the player is not lynched and moves on to the night. It is not revealed who voted for or against.
 The game continues to alternate between day and night until one team wins.


-Job description
 -Mafia team
 -Mafia
 Each night, you can choose one player to kill
 -Spy
 Each night, you can choose one of the players to find out his or her job.
   When investigating a soldier, the soldier will also know who the spy is.
   If the selected player is Mafia, they will be contacted.
  Thief
 Attempts to burglarize a soldier will fail, and the soldier will learn the thief's identity.
   If you steal a police officer's ability and find the Mafia, you will also be contacted. In this case, you cannot move the muzzle of your gun.
   If you steal a Mafia ability, you are in contact and can move your gun.
   Each voting period, you can choose a player of your choice to use their unique ability until nightfall.
  -Madame
 Seduces a player who voted for you during the day, preventing them from using their class's unique ability.
 The seduction lasts as long as the Madame is alive, or until the end of the night if the Madame dies.
   If you seduce the Mafia, you are contacted.
  -Scientist
 If you die, you respawn the next night. (One-time use)
 If you die, contact the Mafia.
 -Civic Team
 -Police
 Each night, you can investigate one player to determine if they are mafia or not.
   Each night, you can choose one player to investigate to determine if they are mafia or not. However, you cannot investigate secondary professions and prelates, so if you investigate a secondary profession or prefect, you will see “~You are not mafia” as you would a citizen.
  -Agent
 Receives nightly orders to determine the occupation of one citizen.
   The order is not chosen by the Agent, but is randomized.
   If there are no more targets for the Agent to find out about, the message “No orders have arrived” is sent. If this message arrives, all players whose occupation is unknown are Evil.
  -Doctor
 Designates one person each night to heal a target if the target is attacked by the mafia
 -Soldier
 Ignores mafia executions once
 If a player is being investigated by the mafia team, the identity of the player's profession is revealed and any additional effects of the investigation are negated.
  Politicians
 are immune to lynching by player vote.
   Politicians are allowed two votes.
  Terrorist
 Each night, you may vote for one player and die with them if they vote for you.
 When you are voted off, you may choose one player to die with you during the final argument.
  Scoundrel
 Each night, choose one player to take away that player's vote in the next day's vote.
  Nurse
 Each night, investigate one player and contact them if they are a doctor
 If they are contacted by a doctor and the doctor dies, they can heal people in the doctor's place.


Because all professions are subject to execution if disclosed, it is a general rule not to disclose professions except in special circumstances.
Support classes on the Mafia team are included in the Mafia team.
Don't repeat the same thing you've said before.


Remaining players :
{[p.name for p in players if p.alive]}

Conversation Posssible Players:
{[p.name for p in possible_targets if p.alive]}

PREV PREDICTION :
{player.get_last_prediction()}

CHAT HISTORY: :
{str(chat_history)}
    """

    output_parser = PydanticOutputParser(pydantic_object=Response_Type)

    chatml = [SystemMessage(content=SYS_PROMPT)] \
             + [SystemMessage(content=output_parser.get_format_instructions())]

    result = chatGPT.invoke(chatml)

    match = re.search(r'\{.*\}', result.content, re.DOTALL)
    if match:
        json_str = match.group(0)
        parsed = json.loads(json_str)
    else:
        parsed = {"speaker": "", "chat": "", "predictions": "", "point": ""}
    # print(parsed)
    # try:
    #     result = json.loads(result.content)
    # except Exception:
    #     result = None

    return parsed
    #
    # print(result)
    # try:
    #     ret = json.loads(result.content)
    # except json.decoder.JSONDecodeError:
    #     ret = {"speaker": "", "chat" : "", "predictions" : "", "point" : ""}
    # return ret
    # # JSON 파싱 후 반환
    # try:
    #     return json.loads(result)  # response_text → chunks 로 변경
    # except json.JSONDecodeError:
    #     return None  # JSON 변환 실패 시 None 반환


