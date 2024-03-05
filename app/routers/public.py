from typing import Iterable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, ValidationException

from app.utils.scripts import get_countries_list
from app.utils.security import create_access_token
from app.utils.models import (ResponseStatusModel, UserModel, UserResponseModel, UserProfileResponseModel, CountryModel,
                              countryAlpha2, countryRegion, OAuthForm, Token)
from app.db.functions import (get_countries_by_region, get_all_countries, get_country_by_alpha2, authenticate_user,
                              get_users_by, add_new_user)


public_router = APIRouter(prefix="/api")


@public_router.get('/ping', response_model=ResponseStatusModel)
async def send_status():
    return JSONResponse(status_code=200, content=ResponseStatusModel(status="ok").dict())


@public_router.get('/countries', response_model=Iterable[CountryModel])
async def send_countries_by_region(request: Request, region: countryRegion = None):
    db_session = request.state.db_session

    if region:
        if region not in ['Europe', 'Africa', 'Americas', 'Oceania', 'Asia']:
            raise ValidationException(
                errors="Формат входного запроса не соответствует формату либо переданы неверные значения.")

        countries = await get_countries_by_region(region=region, db_session=db_session)
    else:
        countries = await get_all_countries(db_session=db_session)

    countries_list = get_countries_list(countries=countries)

    return JSONResponse(status_code=200, content=countries_list)


@public_router.get('/countries/{alpha}', response_model=CountryModel)
async def send_country_by_alpha2(request: Request, alpha: countryAlpha2):
    db_session = request.state.db_session

    if not alpha:
        raise HTTPException(status_code=400, detail="Код страны не соответствует шаблону.")

    alpha = alpha.upper()
    country = await get_country_by_alpha2(alpha2=alpha, db_session=db_session)
    if not country:
        raise HTTPException(status_code=404, detail=f"Страна с кодом {alpha} не найдена.")

    return JSONResponse(status_code=200, content=CountryModel(
        name=country.name,
        alpha2=country.alpha2,
        alpha3=country.alpha3,
        region=country.region
    ).dict())


@public_router.post('/auth/register', response_model=UserProfileResponseModel)
async def register_new_user(request: Request, user_data: UserModel):
    db_session = request.state.db_session

    user_data.countryCode = user_data.countryCode.upper()

    check_country_code = await get_country_by_alpha2(alpha2=user_data.countryCode, db_session=db_session)
    if not check_country_code:
        raise HTTPException(status_code=400, detail="Страна с указанным кодом не найдена.")

    check_user = await get_users_by(user_data=user_data, db_session=db_session)
    if check_user:
        raise HTTPException(status_code=409,
                            detail="Пользователь с таким e-mail, номером телефона или логином уже зарегистрирован.")

    new_user = await add_new_user(user_data=user_data, db_session=db_session)

    return JSONResponse(status_code=201, content=UserProfileResponseModel(profile=UserResponseModel(
        login=new_user.login,
        email=new_user.email,
        countryCode=new_user.country_code,
        isPublic=new_user.is_public,
        phone=new_user.phone,
        image=new_user.image,
    )).dict())


@public_router.post('/auth/sign-in', response_model=Token)
async def send_access_token(request: Request, form_data: OAuthForm):
    db_session = request.state.db_session

    user = await authenticate_user(form_data=form_data, db_session=db_session)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь с указанным логином и паролем не найден")

    access_token_expire = None
    access_token = create_access_token(data={"sub": form_data.login}, expire_delta=access_token_expire)

    response = JSONResponse(status_code=200, content=Token(token=access_token).dict())

    return response
