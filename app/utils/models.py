import re
from datetime import datetime
from typing import List, Optional, Annotated

from fastapi.exceptions import ValidationException, HTTPException

from pydantic import BaseModel, Field, constr, conint, condate, field_validator

countryAlpha2 = Annotated[Optional[constr(max_length=2, pattern=r'^[a-zA-Z]{2}$')], Field(
    title="Country Alpha2 Code",
    description="Двухбуквенный код, уникально идентифицирующий страну",
    max_length=2,
    pattern=r'^[a-zA-Z]{2}$',
    default=None,
    examples=['RU']
)]

countryRegion = Annotated[str, Field(
    title="Country Region",
    description="Географический регион, к которому относится страна",
    default=None
)]


class CountryModel(BaseModel):
    """
    Информация о стране из стандарта ISO 3166

    example: OrderedMap { "name": "Burkina Faso", "alpha2": "BF", "alpha3": "BFA", "region": "Africa" }
    """

    name: Annotated[constr(max_length=100), Field(
        title="Country Name",
        description="Полное название страны",
        max_length=100
    )]
    alpha2: countryAlpha2
    alpha3: Annotated[constr(max_length=3, pattern=r'^[a-zA-Z]{3}$'), Field(
        title="Country Alpha3 Code",
        description="Трехбуквенный код страны",
        max_length=3,
        pattern=r'^[a-zA-Z]{3}$'
    )]
    region: countryRegion


userLogin = Annotated[constr(max_length=30, pattern=r'^[a-zA-Z0-9-]+$'), Field(
    title="User Login",
    description="Логин пользователя",
    max_length=30,
    pattern=r'^[a-zA-Z0-9-]+$',
    examples=['yellowMonkey']
)]

userEmail = Annotated[constr(min_length=1, max_length=50), Field(
    title="User Email",
    description="E-mail пользователя",
    min_length=1,
    max_length=50,
    examples=['yellowstone1980@you.ru']
)]

userPassword = Annotated[constr(min_length=6, max_length=100), Field(
    title="User Password",
    description="""
    Пароль пользователя, к которому предъявляются следующие требования:

    Длина пароля не менее 6 символов.
    Присутствуют латинские символы в нижнем и верхнем регистре.
    Присутствует минимум одна цифра.
    """,
    min_length=6,
    max_length=100,
    examples=['$aba4821FWfew01#.fewA$']
)]

userIsPublic = Annotated[bool, Field(
    title="User Is Public",
    description="""
    Является ли данный профиль публичным.

    Публичные профили доступны другим пользователям: если профиль публичный, любой пользователь платформы сможет получить информацию о пользователе.
    """,
    examples=['true']
)]

userPhone = Annotated[Optional[constr(max_length=200)], Field(
    title="User Phone",
    description="Номер телефона пользователя в формате +123456789",
    pattern=r'^\+[\d]+$',
    max_length=20,
    default=None,
    examples=['+74951239922']
)]

userImage = Annotated[Optional[constr(min_length=1, max_length=200)], Field(
    title="User Image Url",
    description="Ссылка на фото для аватара пользователя",
    min_length=1,
    max_length=200,
    default=None,
    examples=['https://http.cat/images/100.jpg']
)]


class UserModel(BaseModel):
    """
    Информация о профиле пользователя
    """

    login: userLogin
    email: userEmail
    password: userPassword
    countryCode: countryAlpha2
    isPublic: userIsPublic
    phone: userPhone
    image: userImage


    @field_validator('login', mode='before')
    def validate_login(cls, login):
        if not login:
            raise HTTPException(status_code=400, detail="Логин не указан.")
        elif len(login) < 3:
            raise HTTPException(status_code=400, detail="Длина логина слишком маленькая.")
        elif len(login) > 30:
            raise HTTPException(status_code=400, detail="Длина логина превышает допустимый лимит.")
        elif not re.search(pattern=r'^[a-zA-Z0-9-]+$', string=login):
            raise HTTPException(status_code=400, detail="Логин не соответствует шаблону.")

        return login

    @field_validator('password', mode='before')
    def validate_password(cls, password):
        if not password:
            raise HTTPException(status_code=400, detail="Пароль не указан.")
        elif len(password) < 6:
            raise HTTPException(status_code=400, detail="Недостаточно надежный пароль.")
        elif len(password) > 100:
            raise HTTPException(status_code=400, detail="Длина пароля превышает допустимый лимит.")

        return password

    @field_validator('email', mode='before')
    def validate_email(cls, email):
        if not email:
            raise HTTPException(status_code=400, detail="E-mail не указан.")
        elif not re.search(pattern=r'^[-\w\.]+@([-\w]+\.)+[-\w]{2,4}$', string=email):
            raise HTTPException(status_code=400, detail="E-mail не валидный.")
        elif len(email) > 50:
            raise HTTPException(status_code=400, detail="Длина e-mail превышает допустимый лимит.")

        return email

    @field_validator('countryCode', mode='before')
    def validate_country_code(cls, countryCode):
        if not countryCode:
            raise HTTPException(status_code=400, detail="Поле countryCode не указано.")
        elif not re.search(pattern=r'^[a-zA-Z]{2}$', string=countryCode):
            raise HTTPException(status_code=400, detail="Код страны не соответствует шаблону.")

        return countryCode

    @field_validator('isPublic', mode='before')
    def validate_is_public(cls, isPublic):
        if isPublic is None:
            raise HTTPException(status_code=400, detail="Поле isPublic не указано.")
        elif not isinstance(isPublic, bool):
            raise HTTPException(status_code=400, detail="В поле isPublic передан не boolean.")

        return isPublic

    @field_validator('phone', mode='before')
    def validate_phone(cls, phone):
        if not phone:
            return phone

        if not re.search(pattern=r'^\+[\d]+$', string=phone):
            raise HTTPException(status_code=400, detail="Номер телефона не соответствует шаблону.")
        elif len(phone) > 20:
            raise HTTPException(status_code=400, detail="Длина номера телефона превышает допустимый лимит.")
        elif len(phone) < 5:
            raise HTTPException(status_code=400, detail="Длина номера телефона слишком маленькая")

        return phone

    @field_validator('image', mode='before')
    def validate_image(cls, image):
        if not image:
            return image

        if len(image) > 200:
            raise HTTPException(status_code=400, detail="Длина ссылки на аватар пользователя превышает допустимый лимит.")
        elif len(image) < 5:
            raise HTTPException(status_code=400, detail="Длина ссылки на аватар пользователя слишком маленькая.")

        return image


class UserResponseModel(BaseModel):
    """
    Информация о профиле пользователя без пароля
    """

    login: userLogin
    email: userEmail
    countryCode: countryAlpha2
    isPublic: userIsPublic
    phone: userPhone
    image: userImage


class UserProfileResponseModel(BaseModel):
    profile: UserResponseModel


class EditUserModel(BaseModel):
    """
    Данные пользователя, которые можно изменить
    """

    countryCode: countryAlpha2
    isPublic: Annotated[Optional[bool], Field(
        title="User Is Public",
        description="""
        Является ли данный профиль публичным.
    
        Публичные профили доступны другим пользователям: если профиль публичный, любой пользователь платформы сможет получить информацию о пользователе.
        """,
        default=None,
        examples=['true']
    )]
    phone: userPhone
    image: userImage

    @field_validator('phone', mode='before')
    def validate_phone(cls, phone):
        if not phone:
            return phone

        if not re.search(pattern=r'^\+[\d]+$', string=phone):
            raise HTTPException(status_code=400, detail="Номер телефона не соответствует шаблону.")
        elif len(phone) > 20:
            raise HTTPException(status_code=400, detail="Длина номера телефона превышает допустимый лимит.")
        elif len(phone) < 5:
            raise HTTPException(status_code=400, detail="Длина номера телефона слишком маленькая")

        return phone

    @field_validator('image', mode='before')
    def validate_image(cls, image):
        if not image:
            return image

        if len(image) > 200:
            raise HTTPException(status_code=400,
                                detail="Длина ссылки на аватар пользователя превышает допустимый лимит.")
        elif len(image) < 5:
            raise HTTPException(status_code=400, detail="Длина ссылки на аватар пользователя слишком маленькая.")

        return image


class UpdatePasswordModel(BaseModel):
    """
    Обновление пароля
    """

    oldPassword: userPassword
    newPassword: userPassword

    @field_validator('newPassword', mode='before')
    def validate_password(cls, newPassword):
        if not newPassword:
            raise HTTPException(status_code=400, detail="Пароль не указан.")
        elif len(newPassword) < 6:
            raise HTTPException(status_code=400, detail="Недостаточно надежный пароль.")
        elif len(newPassword) > 100:
            raise HTTPException(status_code=400, detail="Длина пароля превышает допустимый лимит.")

        return newPassword


class FriendLoginModel(BaseModel):
    login: userLogin


class FriendResponseModel(BaseModel):
    login: userLogin
    addedAt: str


postId = Annotated[constr(max_length=100), Field(
    title="Post Id",
    description="Уникальный идентификатор публикации, присвоенный сервером.",
    max_length=100,
    examples=['550e8400-e29b-41d4-a716-446655440000']
)]

postContent = Annotated[constr(max_length=1000), Field(
    title="Post Content Text",
    description="Текст публикации.",
    max_length=1000,
    examples=['Свеча на 400! Покупаем, докупаем и фиксируем прибыль.']
)]

postTag = Annotated[constr(max_length=20), Field(
    title="Post Tag",
    description="Значение тега.",
    max_length=20,
    examples=['тинькофф']
)]

postTags = Annotated[List[postTag], Field(
    title="Post Tags List",
    description="Список тегов публикации.",
    default=[],
    examples=['List [ "тинькофф", "спббиржа", "moex" ]']
)]


class PostModel(BaseModel):
    """
    Пользовательская публикация.
    """

    id: postId
    content: postContent
    author: userLogin
    tags: postTags
    createdAt: str = Field(
        title="Post Created At Date",
        description="Серверная дата и время в момент, когда пользователь отправил данную публикацию. Передается в формате RFC3339.",
        examples=['2006-01-02T15:04:05Z07:00']
    )
    likesCount: Optional[conint(ge=0)] = Field(
        title="Post Likes Count",
        description="Число лайков, набранное публикацией.",
        ge=0,
        default=0
    )
    dislikesCount: Optional[conint(ge=0)] = Field(
        title="Post Dislikes Count",
        description="Число дизлайков, набранное публикацией.",
        ge=0,
        default=0
    )


class AddPostModel(BaseModel):
    """
    Данные для добавления нового поста
    """

    content: postContent
    tags: postTags


class ErrorResponse(BaseModel):
    """
    Используется для возвращения ошибки пользователю

    example: OrderedMap { "reason": "<объяснение, почему запрос пользователя не может быть обработан>" }
    """

    reason: constr(min_length=5) = Field(
        title="Error Response Reason",
        description="Описание ошибки в свободной форме",
        min_length=5,
        examples=["<объяснение, почему запрос пользователя не может быть обработан>"]
    )


class ResponseStatusModel(BaseModel):
    status: Annotated[Optional[str], Field(
        title="Response Status",
        description="Статус ответа",
        default=False,
        examples=["ok"]
    )]


class OAuthForm(BaseModel):
    login: userLogin
    password: userPassword


class Token(BaseModel):
    token: str = Field(
        title="Access Token",
        default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
