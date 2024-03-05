from datetime import datetime

from sqlalchemy import Column, Integer, Boolean, String, ARRAY, ForeignKey, DateTime, Enum

from app.db.base import Base
from app.utils.enums import ReactionType



class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    name = Column(String(100), nullable=False)
    alpha2 = Column(String(2), nullable=False, unique=True)
    alpha3 = Column(String(3), nullable=False)
    region = Column(Enum('Europe', 'Africa', 'Americas', 'Oceania', 'Asia', '', name="continents"), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    login = Column(String(30), nullable=False)
    email = Column(String(50), nullable=False)
    password = Column(String(100), nullable=False)

    country_code = Column(String(2), ForeignKey("countries.alpha2"), nullable=False)
    is_public = Column(Boolean, nullable=False)

    phone = Column(String(20), nullable=True)
    image = Column(String(200), nullable=True)


class Post(Base):
    __tablename__ = "posts"

    id = Column(String(100), primary_key=True, unique=True, nullable=False)

    content = Column(String(1000), nullable=False)
    author = Column(Integer, ForeignKey("users.id"), nullable=False)
    tags = Column(ARRAY(String(20)), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    likes_count = Column(Integer, nullable=False, default=0)
    dislikes_count = Column(Integer, nullable=False, default=0)


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    added_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(String(100), ForeignKey("posts.id"), nullable=False)

    reaction_type = Column(Enum(ReactionType), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
