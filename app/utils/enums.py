from enum import Enum


class ReactionType(str, Enum):
    like = "like"
    dislike = "dislike"
