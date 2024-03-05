from datetime import datetime
from typing import Iterable, Union

from sqlalchemy import or_, and_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.enums import ReactionType
from app.utils.scripts import Hasher, generate_uuid4
from app.db.models import Country, User, Post, Friendship, Reaction
from app.utils.models import (countryAlpha2, countryRegion, UserModel, userLogin, OAuthForm, UserResponseModel,
                              userPhone, EditUserModel, userPassword, AddPostModel, postId)


async def get_countries_by_region(region: countryRegion, db_session: AsyncSession) -> Iterable[Country]:
    query = select(Country).where(Country.region == region).order_by(Country.alpha2)
    result = await db_session.execute(query)
    countries = result.scalars().all()

    return countries


async def get_all_countries(db_session: AsyncSession) -> Iterable[Country]:
    query = select(Country).order_by(Country.alpha2)
    result = await db_session.execute(query)
    countries = result.scalars().all()

    return countries


async def get_country_by_alpha2(alpha2: countryAlpha2, db_session: AsyncSession) -> Country:
    query = select(Country).where(Country.alpha2 == alpha2)
    result = await db_session.execute(query)
    country = result.scalars().one_or_none()

    return country


async def get_users_by(user_data: UserModel, db_session: AsyncSession) -> Union[Iterable[User], None]:
    query = select(User).where(
        or_(User.login == user_data.login, User.email == user_data.email, User.phone == user_data.phone)
    )
    result = await db_session.execute(query)
    user = result.scalars().all()

    return user


async def get_user_by_login(login: userLogin, db_session: AsyncSession) -> Union[User, None]:
    if not login:
        return None

    query = select(User).where(User.login == login)
    result = await db_session.execute(query)
    user = result.scalars().one_or_none()

    return user


async def get_user_by_id(user_id: int, db_session: AsyncSession) -> Union[User, None]:
    if not user_id:
        return None

    query = select(User).where(User.id == user_id)
    result = await db_session.execute(query)
    user = result.scalars().one_or_none()

    return user


async def get_public_user_by_login(login: userLogin, db_session: AsyncSession) -> Union[User, None]:
    if not login:
        return None

    query = select(User).where(and_(User.is_public, User.login == login))
    result = await db_session.execute(query)
    user = result.scalars().one_or_none()

    return user


async def get_user_by_phone(phone: userPhone, db_session: AsyncSession) -> Union[User, None]:
    if not phone:
        return None

    query = select(User).where(User.phone == phone)
    result = await db_session.execute(query)
    user = result.scalars().one_or_none()

    return user


async def authenticate_user(form_data: OAuthForm, db_session: AsyncSession) -> Union[User, bool]:
    user = await get_user_by_login(login=form_data.login, db_session=db_session)

    if not user:
        return False
    if not Hasher.verify_password(plain_password=form_data.password, hashed_password=user.password):
        return False

    return user


async def add_new_user(user_data: UserModel, db_session: AsyncSession) -> User:
    user_data.password = Hasher.get_password_hash(password=user_data.password)

    new_user = User(
        login=user_data.login,
        email=user_data.email,
        password=user_data.password,
        country_code=user_data.countryCode,
        is_public=user_data.isPublic,
        phone=user_data.phone,
        image=user_data.image,
    )

    db_session.add(new_user)
    await db_session.commit()

    return new_user


async def edit_user_data(old_user: User, new_user_data: EditUserModel, db_session: AsyncSession):
    new_country_code = new_user_data.countryCode if new_user_data.countryCode is not None else old_user.country_code
    new_is_public = new_user_data.isPublic if new_user_data.isPublic is not None else old_user.is_public
    new_phone = new_user_data.phone if new_user_data.phone is not None else old_user.phone
    new_image = new_user_data.image if new_user_data.image is not None else old_user.image

    old_user.country_code = new_country_code.upper()
    old_user.is_public = new_is_public
    old_user.phone = new_phone
    old_user.image = new_image

    await db_session.commit()
    await db_session.refresh(old_user)

    return old_user


async def update_user_password(user: User, old_password: userPassword, new_password: userPassword,
                               db_session: AsyncSession) -> bool:
    if not Hasher.verify_password(plain_password=old_password, hashed_password=user.password):
        return False

    new_password = Hasher.get_password_hash(new_password)

    user.password = new_password

    await db_session.commit()

    return True


async def get_user_all_friends(user_id: int, db_session: AsyncSession) -> Iterable[User]:
    query = select(Friendship.friend_id).where(Friendship.user_id == user_id)
    result = await db_session.execute(query)
    friend_ids = result.scalars().all()

    query = select(User).where(User.id.in_(friend_ids))
    result = await db_session.execute(query)
    friends = result.scalars().all()

    return friends


async def get_user_friends_for_pagination(user_id: int, offset: int, limit: int,
                                          db_session: AsyncSession) -> Iterable[User]:
    query = select(Friendship.friend_id).where(Friendship.user_id == user_id)
    result = await db_session.execute(query)
    friend_ids = result.scalars().all()

    query = select(User).where(User.id.in_(friend_ids)).offset(offset).limit(limit)
    result = await db_session.execute(query)
    friends = result.scalars().all()

    return friends


async def get_user_friends_added_at_for_pagination(user_id: int, offset: int, limit: int,
                                                   db_session: AsyncSession) -> Iterable[datetime]:
    query = select(Friendship.added_at).where(Friendship.user_id == user_id).offset(offset).limit(limit)
    result = await db_session.execute(query)
    added_ats = result.scalars().all()

    return added_ats


async def get_user_friend(user_id: int, friend_id: int, db_session: AsyncSession) -> Union[Friendship, None]:
    query = select(Friendship).where(and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id))
    result = await db_session.execute(query)
    friendship = result.scalars().one_or_none()

    return friendship


async def add_friend(user_id: int, friend_id: int, db_session: AsyncSession) -> Friendship:
    new_friendship = Friendship(user_id=user_id, friend_id=friend_id)

    db_session.add(new_friendship)
    await db_session.commit()

    return new_friendship


async def remove_friend(friendship: Friendship, db_session: AsyncSession) -> None:
    await db_session.delete(friendship)
    await db_session.commit()


async def add_post(post_data: AddPostModel, author: User, db_session: AsyncSession) -> Post:
    new_post = Post(
        id=generate_uuid4(),
        content=post_data.content,
        author=author,
        tags=post_data.tags,
    )

    db_session.add(new_post)
    await db_session.commit()

    return new_post


async def get_post_by_id(post_id: postId, db_session: AsyncSession) -> Union[Post, None]:
    query = select(Post).where(Post.id == post_id)
    result = await db_session.execute(query)
    post = result.scalars().one_or_none()

    return post


async def get_all_user_posts_for_pagination(user_id: int, offset: int, limit: int,
                                            db_session: AsyncSession) -> Iterable[Post]:
    query = select(Post).where(Post.author == user_id).offset(offset).limit(limit)
    result = await db_session.execute(query)
    posts = result.scalars().all()

    return posts


async def get_user_reaction_to_post(user_id: int, post_id: postId, db_session: AsyncSession) -> Reaction:
    query = select(Reaction).where(and_(Reaction.post_id == post_id, Reaction.user_id == user_id))
    result = await db_session.execute(query)
    reaction = result.scalars().one_or_none()

    return reaction


async def add_new_user_reaction(user_id: int, post_id: postId, db_session: AsyncSession) -> Reaction:
    new_reaction = Reaction(
        user_id=user_id,
        post_id=post_id,
    )

    db_session.add(new_reaction)
    await db_session.commit()

    return new_reaction


async def add_like_to_post(post: Post, reaction: Reaction, db_session: AsyncSession) -> Post:
    if reaction.reaction_type == ReactionType.dislike:
        post.likes_count += 1
        post.dislikes_count -= 1

    elif not reaction.reaction_type:
        post.likes_count += 1

    reaction.reaction_type = ReactionType.like

    await db_session.commit()
    await db_session.refresh(post)

    return post


async def add_dislike_to_post(post: Post, reaction: Reaction, db_session: AsyncSession) -> Post:
    if reaction.reaction_type == ReactionType.like:
        post.dislikes_count += 1
        post.likes_count -= 1

    elif not reaction.reaction_type:
        post.dislikes_count += 1

    reaction.reaction_type = ReactionType.dislike

    await db_session.commit()
    await db_session.refresh(post)

    return post
