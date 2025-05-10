# from auth.basic_auth import get_authenticated_user

from fastapi.security import HTTPAuthorizationCredentials  # , HTTPBearer

from auth.jwt_auth import get_authenticated_user

from fastapi import Depends, APIRouter

from fastapi.security import APIKeyHeader



router = APIRouter(tags=["pages"], prefix="/pages")

header_scheme = APIKeyHeader(name="x-key")


@router.get("/public", tags=["Auth Test"])
def public_route():
    return {"message": "This is a public route"}


@router.get("/private", tags=["Auth Test"])  # Token authentication
def private_route(user: HTTPAuthorizationCredentials = Depends(get_authenticated_user)):
    print(user.username)

    return {"message": "This is a private page"}


# @router.get("/private", tags=["Auth Test"]) # Http authorize
# def private_route(
# credentials: HTTPAuthorizationCredentials= Depends(security)
# ):
#     print(credentials)
#     return {"message": "This is a private page"}

# @router.get("/private", tags=["Auth Test"]) # Old basic user pass method
# def private_route(user: UsersModel = Depends(get_authenticated_user)):
#     print(user)
#     return {"message": "This is a private page"}

# @router.get("/private", tags=["Auth Test"]) # APIkey Header auth
# def private_route(api_key = Depends(header_scheme)):
#     print(api_key)
#     return {"message": "This is a private page"}

# from fastapi.security import APIKeyQuery

# query_scheme = APIKeyQuery(name="api_key")

# @router.get("/private", tags=["Auth Test"]) # APIkey Query auth
# def private_route(api_key = Depends(header_scheme)):
#     print(api_key)
#     return {"message": "This is a private page"}