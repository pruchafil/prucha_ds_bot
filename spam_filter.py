from collections import deque
from sys import maxsize

import discord
import time
from cachetools import TTLCache
from enum import IntEnum

short_message_history = TTLCache(maxsize=100, ttl=60)
ping_message_history = TTLCache(maxsize=100, ttl=300)
repeated_spam_history = TTLCache(maxsize=10000, ttl=300)
annoyance_antidote = TTLCache(maxsize=10000, ttl=60*20)

LIMIT = 5
INTERVAL = 10.0
PING_INTERVAL = 300.0

class SpamType(IntEnum):
    NONE = 0
    SMALL = 1
    REPEATED = 2
    REPEATED_PING = 2
    SABOTEUR = 3

def ping(user_id: int):
    now = time.time()

    history = ping_message_history.get(user_id)
    if history is None:
        history = deque(maxlen=3)

    if len(history) == history.maxlen:
        history[-1] = now
    else:
        history.append(now)

    while now - history[0] > PING_INTERVAL:
        history.popleft()

    ping_message_history[user_id] = history

    if len(history) == 2:
        return SpamType.REPEATED_PING
    if len(history) == 3:
        return SpamType.SABOTEUR

    return SpamType.NONE

def non_ping(user_id: int):
    now = time.time()

    history = short_message_history.get(user_id)
    if history is None:
        history = deque(maxlen=LIMIT + 1)

    if len(history) == history.maxlen:
        history[-1] = now
    else:
        history.append(now)

    while now - history[0] > INTERVAL:
        history.popleft()

    short_message_history[user_id] = history

    spam_detected = len(history) > LIMIT
    spam_type = SpamType.NONE

    if spam_detected:
        spam_type = SpamType.SMALL

        repeated = repeated_spam_history.get(user_id)
        if repeated is None or len(repeated) == 0:
            repeated = deque(maxlen=3)

        repeated.append(user_id)

        if len(repeated) > 1:
            spam_type = SpamType.REPEATED

            annoyance = annoyance_antidote.get(user_id)
            if annoyance is not None and len(annoyance) > 0:
                spam_type = SpamType.SABOTEUR

            annoyance_antidote[user_id] = [user_id]

        repeated_spam_history[user_id] = repeated

    return spam_type

def check_spam(message: discord.Message):
    user_id = message.author.id

    if len(message.mentions) == 0:
        return non_ping(user_id)
    else:
        return ping(user_id)
