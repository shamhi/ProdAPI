import uuid
from typing import Iterable
from datetime import datetime

from passlib.context import CryptContext

from app.db.models import Country, User, Post
from app.utils.models import PostModel, FriendResponseModel, CountryModel, userLogin, userPassword

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_countries_list(countries: Iterable[Country]):
    return [
        CountryModel(
            name=country.name,
            alpha2=country.alpha2,
            alpha3=country.alpha3,
            region=country.region
        ).dict()
        for country in countries
    ]


def get_friends_list(friends: Iterable[User], added_ats: Iterable[datetime]):
    return [
        FriendResponseModel(
            login=friend.login,
            addedAt=added_at.isoformat()
        ).dict()
        for friend, added_at in zip(friends, added_ats)
    ]


def get_posts_list(posts: Iterable[Post], author: userLogin):
    return [
        PostModel(
            id=post.id,
            content=post.content,
            author=author,
            tags=post.tags,
            createdAt=post.created_at.isoformat(),
            likesCount=post.likes_count,
            dislikesCount=post.likes_count
        ).dict()
        for post in posts
    ]


def generate_uuid4():
    return str(uuid.uuid4())


class Hasher:
    @staticmethod
    def get_password_hash(password: userPassword) -> str:
        return pwd_context.hash(secret=password)

    @staticmethod
    def verify_password(plain_password: userPassword, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
