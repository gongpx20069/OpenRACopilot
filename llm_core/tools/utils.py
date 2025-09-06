from OpenRA_Copilot_Library.models import TargetsQueryParam
from .. import game_api
from OpenRA_Copilot_Library.models import Actor
from typing import Dict, List
from collections import defaultdict
from functools import wraps
import time
import logging

logger = logging.getLogger("AgentSystem")


def print_tool_io(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"[Tool Log] {func.__name__} - Input: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        # logger.info(f"[Tool Log] {func.__name__} - Output: {result}")
        return result
    return wrapper


def tool_sleep(seconds: float):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            logger.info(f"[Tool Sleep] {func.__name__} - {seconds}s")
            time.sleep(seconds)
            return result
        return wrapper
    return decorator


def validate_actor_ids(actor_ids: List[Actor]) -> List[Actor]:
    actors = game_api.query_actor(TargetsQueryParam(faction="自己"))
    # logger.info("validate_actor_ids result: ", actors)
    our_actor_ids = set([actor.actor_id for actor in actors])
    validated_actors = []
    for actor_id in actor_ids:
        if actor_id in our_actor_ids:
            validated_actors.append(Actor(actor_id=actor_id))
    return validated_actors


def classify_different_faction_actors(actors: List[Actor], factions = ["己方", "敌方"]) -> Dict[str, Dict[str, List[Actor]]]:
    output = defaultdict(lambda: defaultdict(list))
    for actor in actors:
        if actor.faction in factions and actor.type != "mpspawn":
            output[actor.faction][actor.type].append(actor)
    return output


def convert_byte_to_str(byte_data:memoryview) -> str:
    byte_data = bytes(byte_data)
    # Decode the bytes back to a string (using UTF-8)
    return byte_data.decode('utf-8').rstrip('\x00')
