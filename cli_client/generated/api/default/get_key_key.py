from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from typing import Dict
from typing import cast, List
from typing import cast
from ...models.code_response import CodeResponse
from ...models.unprocessable_entity import UnprocessableEntity
from ...models.get_response import GetResponse



def _get_kwargs(
    key: str,
    *,
    client: Client,

) -> Dict[str, Any]:
    url = "{}/key/{key}".format(
        client.base_url,key=key)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    

    

    

    

    

    return {
	    "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, client: Client, response: httpx.Response) -> Optional[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetResponse.from_dict(response.json())



        return response_200
    if response.status_code == HTTPStatus.NOT_FOUND:
        response_404 = CodeResponse.from_dict(response.json())



        return response_404
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = []
        _response_422 = response.json()
        for response_422_item_data in (_response_422):
            response_422_item = UnprocessableEntity.from_dict(response_422_item_data)



            response_422.append(response_422_item)

        return response_422
    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        response_500 = cast(Any, None)
        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(f"Unexpected status code: {response.status_code}")
    else:
        return None


def _build_response(*, client: Client, response: httpx.Response) -> Response[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    key: str,
    *,
    client: Client,

) -> Response[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]:
    """
    Args:
        key (str): key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]
    """


    kwargs = _get_kwargs(
        key=key,
client=client,

    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    key: str,
    *,
    client: Client,

) -> Optional[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]:
    """
    Args:
        key (str): key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]
    """


    return sync_detailed(
        key=key,
client=client,

    ).parsed

async def asyncio_detailed(
    key: str,
    *,
    client: Client,

) -> Response[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]:
    """
    Args:
        key (str): key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]
    """


    kwargs = _get_kwargs(
        key=key,
client=client,

    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(
            **kwargs
        )

    return _build_response(client=client, response=response)

async def asyncio(
    key: str,
    *,
    client: Client,

) -> Optional[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]:
    """
    Args:
        key (str): key

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, CodeResponse, GetResponse, List['UnprocessableEntity']]]
    """


    return (await asyncio_detailed(
        key=key,
client=client,

    )).parsed

