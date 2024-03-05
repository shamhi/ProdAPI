from typing import Annotated, Iterable

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException

from app.db.models import User
from app.utils.security import decode_access_token
from app.utils.scripts import get_friends_list, get_posts_list
from app.utils.models import (UserResponseModel, EditUserModel, FriendResponseModel, Token, UpdatePasswordModel,
                              ResponseStatusModel, FriendLoginModel, PostModel, AddPostModel, userLogin, postId)
from app.db.functions import (get_country_by_alpha2, get_user_by_login, get_public_user_by_login, get_user_by_phone,
                              edit_user_data, update_user_password, add_friend, get_user_all_friends, remove_friend,
                              get_user_friend, get_user_friends_for_pagination, get_post_by_id, add_new_user_reaction,
                              add_like_to_post, add_dislike_to_post, add_post, get_user_friends_added_at_for_pagination,
                              get_user_by_id, get_all_user_posts_for_pagination, get_user_reaction_to_post)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/sign-in")


async def get_current_user_by_token(request: Request, token: Annotated[Token, Depends(oauth2_scheme)]) -> User:
    db_session = request.state.db_session

    UnauthorizedResponse = HTTPException(status_code=401, detail="Переданный токен не существует либо некорректен.")

    payload = decode_access_token(token=token)
    if not payload:
        raise UnauthorizedResponse

    user_login = payload.get("sub")
    if not user_login:
        raise UnauthorizedResponse

    user = await get_user_by_login(login=user_login, db_session=db_session)
    if not user:
        raise UnauthorizedResponse

    return user


private_router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user_by_token)])


@private_router.get('/me/profile', response_model=UserResponseModel)
async def send_my_profile(user: Annotated[User, Depends(get_current_user_by_token)]):
    return JSONResponse(status_code=200, content=UserResponseModel(
        login=user.login,
        email=user.email,
        countryCode=user.country_code,
        isPublic=user.is_public,
        phone=user.phone,
        image=user.image,
    ).dict())


@private_router.patch('/me/profile', response_model=UserResponseModel)
async def edit_my_profile(request: Request, old_user: Annotated[User, Depends(get_current_user_by_token)],
                          new_user_data: EditUserModel):
    db_session = request.state.db_session

    if new_user_data.countryCode:
        check_country_code = await get_country_by_alpha2(alpha2=new_user_data.countryCode.upper(),
                                                         db_session=db_session)
        if not check_country_code:
            raise HTTPException(status_code=400, detail="Страна с указанным кодом не найдена.")

    if old_user.phone != new_user_data.phone:
        check_user = await get_user_by_phone(phone=new_user_data.phone, db_session=db_session)
        if check_user:
            raise HTTPException(status_code=409,
                                detail="Пользователь с таким номером телефона уже зарегистрирован.")

    new_user = await edit_user_data(old_user=old_user, new_user_data=new_user_data, db_session=db_session)

    return JSONResponse(status_code=200, content=UserResponseModel(
        login=new_user.login,
        email=new_user.email,
        countryCode=new_user.country_code,
        isPublic=new_user.is_public,
        phone=new_user.phone,
        image=new_user.image,
    ).dict())


@private_router.get('/profiles/{login}', response_model=UserResponseModel)
async def send_profile_by_login(request: Request, login: userLogin,
                                current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    if current_user.login == login:
        user = current_user
    else:
        user_friends = await get_user_all_friends(user_id=current_user.id, db_session=db_session)
        user_friend_logins = [friend.login for friend in user_friends]
        if login not in user_friend_logins:
            user = await get_public_user_by_login(login=login, db_session=db_session)
            if not user:
                raise HTTPException(status_code=403,
                                    detail="Профиль не может быть получен: либо пользователь с указанным логином не существует, либо у отправителя запроса нет доступа к запрашиваемому профилю.")
        else:
            user = await get_user_by_login(login=login, db_session=db_session)

    return JSONResponse(status_code=200, content=UserResponseModel(
        login=user.login,
        email=user.email,
        countryCode=user.country_code,
        isPublic=user.is_public,
        phone=user.phone,
        image=user.image,
    ).dict())


@private_router.post('/me/updatePassword', response_model=ResponseStatusModel)
async def update_my_password(request: Request, passwords: UpdatePasswordModel,
                             current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    status = await update_user_password(user=current_user,
                                        old_password=passwords.oldPassword,
                                        new_password=passwords.newPassword,
                                        db_session=db_session)

    if status is False:
        raise HTTPException(status_code=403, detail="Указанный пароль не совпадает с действительным.")

    return JSONResponse(status_code=200, content=ResponseStatusModel(status="ok").dict())


@private_router.post('/friends/add', response_model=ResponseStatusModel)
async def add_new_friend(request: Request, login: FriendLoginModel,
                         current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    success_response = JSONResponse(status_code=200, content=ResponseStatusModel(status="ok").dict())

    if current_user.login == login.login:
        return success_response

    friend = await get_user_by_login(login=login.login, db_session=db_session)
    if not friend:
        raise HTTPException(status_code=404, detail="Пользователь с указанным логином не найден.")

    current_user_friends = await get_user_all_friends(user_id=current_user.id, db_session=db_session)
    current_user_friend_ids = [friend.id for friend in current_user_friends]
    if friend.id in current_user_friend_ids:
        return success_response

    await add_friend(user_id=current_user.id, friend_id=friend.id, db_session=db_session)

    return success_response


@private_router.post('/friends/remove', response_model=ResponseStatusModel)
async def remove_my_friend(request: Request, login: FriendLoginModel,
                           current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    success_response = JSONResponse(status_code=200, content=ResponseStatusModel(status="ok").dict())

    if current_user.login == login.login:
        return success_response

    friend = await get_user_by_login(login=login.login, db_session=db_session)
    if not friend:
        return success_response

    current_user_friends = await get_user_all_friends(user_id=current_user.id, db_session=db_session)
    current_user_friend_ids = [friend.id for friend in current_user_friends]

    if friend.id not in current_user_friend_ids:
        return success_response

    friendship = await get_user_friend(user_id=current_user.id, friend_id=friend.id, db_session=db_session)
    await remove_friend(friendship=friendship, db_session=db_session)

    return success_response


@private_router.get('/friends', response_model=Iterable[FriendResponseModel])
async def send_my_friends(request: Request, current_user: Annotated[User, Depends(get_current_user_by_token)],
                          offset: int = 0, limit: int = 5):
    db_session = request.state.db_session

    friends = await get_user_friends_for_pagination(user_id=current_user.id,
                                                    offset=offset,
                                                    limit=limit,
                                                    db_session=db_session)
    added_ats = await get_user_friends_added_at_for_pagination(user_id=current_user.id,
                                                               offset=offset,
                                                               limit=limit,
                                                               db_session=db_session)

    friends_list = get_friends_list(friends=friends, added_ats=added_ats)

    return JSONResponse(status_code=200, content=friends_list)


@private_router.post('/posts/new', response_model=PostModel)
async def add_new_post(request: Request, post_data: AddPostModel,
                       current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    new_post = await add_post(post_data=post_data, author=current_user.id, db_session=db_session)

    return JSONResponse(status_code=200, content=PostModel(
        id=new_post.id,
        content=new_post.content,
        author=current_user.login,
        tags=new_post.tags,
        createdAt=new_post.created_at.isoformat(),
        likesCount=new_post.likes_count,
        dislikesCount=new_post.dislikes_count
    ).dict())


@private_router.get('/posts/{postId}', response_model=PostModel)
async def send_post(request: Request, postId: postId,
                    current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    post = await get_post_by_id(post_id=postId, db_session=db_session)
    if not post:
        raise HTTPException(status_code=404, detail="Указанный пост не найден либо к нему нет доступа.")

    post_author = await get_user_by_id(user_id=post.author, db_session=db_session)
    if current_user.id != post_author.id:
        if not post_author.is_public:
            post_author_friends = await get_user_all_friends(user_id=post_author.id, db_session=db_session)
            post_author_friend_ids = [friend.id for friend in post_author_friends]
            if current_user.id not in post_author_friend_ids:
                raise HTTPException(status_code=404, detail="Указанный пост не найден либо к нему нет доступа.")

    return JSONResponse(status_code=200, content=PostModel(
        id=post.id,
        content=post.content,
        author=post_author.login,
        tags=post.tags,
        createdAt=post.created_at.isoformat(),
        likesCount=post.likes_count,
        dislikesCount=post.dislikes_count
    ).dict())


@private_router.get('/posts/feed/my', response_model=Iterable[PostModel])
async def send_my_posts(request: Request, current_user: Annotated[User, Depends(get_current_user_by_token)],
                        offset: int = 0, limit: int = 5):
    db_session = request.state.db_session

    my_posts = await get_all_user_posts_for_pagination(user_id=current_user.id,
                                                       offset=offset,
                                                       limit=limit,
                                                       db_session=db_session)

    my_posts_list = get_posts_list(posts=my_posts, author=current_user.login)

    return JSONResponse(status_code=200, content=my_posts_list)


@private_router.get('/posts/feed/{login}', response_model=Iterable[PostModel])
async def send_user_posts_by_login(request: Request, current_user: Annotated[User, Depends(get_current_user_by_token)],
                                   login: userLogin, offset: int = 0, limit: int = 5):
    db_session = request.state.db_session

    post_author = await get_user_by_login(login=login, db_session=db_session)
    if not post_author:
        raise HTTPException(status_code=404, detail="Пользователь не найден либо к нему нет доступа.")

    if current_user.id != post_author.id:
        if not post_author.is_public:
            post_author_friends = await get_user_all_friends(user_id=post_author.id, db_session=db_session)
            post_author_friend_ids = [friend.id for friend in post_author_friends]
            if current_user.id not in post_author_friend_ids:
                raise HTTPException(status_code=404, detail="Указанный пост не найден либо к нему нет доступа.")

    user_posts = await get_all_user_posts_for_pagination(user_id=post_author.id,
                                                         offset=offset,
                                                         limit=limit,
                                                         db_session=db_session)

    user_posts_list = get_posts_list(posts=user_posts, author=login)

    return JSONResponse(status_code=200, content=user_posts_list)


@private_router.post('/posts/{postId}/like', response_model=PostModel)
async def send_like(request: Request, postId: postId,
                    current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    post = await get_post_by_id(post_id=postId, db_session=db_session)

    reaction = await get_user_reaction_to_post(user_id=current_user.id,
                                               post_id=postId,
                                               db_session=db_session)

    if not reaction:
        reaction = await add_new_user_reaction(user_id=current_user.id,
                                               post_id=postId,
                                               db_session=db_session)

    post = await add_like_to_post(post=post, reaction=reaction, db_session=db_session)

    post_author = await get_user_by_id(user_id=post.author, db_session=db_session)

    return JSONResponse(PostModel(
        id=post.id,
        content=post.content,
        author=post_author.login,
        tags=post.tags,
        createdAt=post.created_at.isoformat(),
        likesCount=post.likes_count,
        dislikesCount=post.dislikes_count
    ).dict())


@private_router.post('/posts/{postId}/dislike', response_model=PostModel)
async def send_dislike(request: Request, postId: postId,
                       current_user: Annotated[User, Depends(get_current_user_by_token)]):
    db_session = request.state.db_session

    post = await get_post_by_id(post_id=postId, db_session=db_session)

    reaction = await get_user_reaction_to_post(user_id=current_user.id,
                                               post_id=postId,
                                               db_session=db_session)

    if not reaction:
        reaction = await add_new_user_reaction(user_id=current_user.id,
                                               post_id=postId,
                                               db_session=db_session)

    post = await add_dislike_to_post(post=post, reaction=reaction, db_session=db_session)

    post_author = await get_user_by_id(user_id=post.author, db_session=db_session)

    return JSONResponse(PostModel(
        id=post.id,
        content=post.content,
        author=post_author.login,
        tags=post.tags,
        createdAt=post.created_at.isoformat(),
        likesCount=post.likes_count,
        dislikesCount=post.dislikes_count
    ).dict())
