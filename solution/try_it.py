"""Run this file to see what your code does:   python try_it.py

You do not need to change anything in this file. It uses a pretend supplier, so no internet is needed.
"""
import asyncio

import httpx

from app.services.supplier_service import SupplierService, read_response
from samples import SUPPLIER_PRODUCT_1

URL = "https://pretend.supplier.test/products/1"


def make_response(status, **content):
    """A response built by hand. It has a request attached, as a real one has."""
    return httpx.Response(status, request=httpx.Request("GET", URL), **content)


def describe(result):
    if isinstance(result, dict):
        return f"product {result['id']}, {result['title']}"
    return str(result)


def try_sync(call):
    try:
        return describe(call())
    except NotImplementedError:
        raise
    except Exception as error:
        return f"raises {type(error).__name__}"


async def try_async(call):
    try:
        return describe(await call())
    except NotImplementedError:
        raise
    except Exception as error:
        return f"raises {type(error).__name__}"


print("Task 1: read_response")
try:
    print("  200, a good product  :", try_sync(lambda: read_response(make_response(200, json=SUPPLIER_PRODUCT_1))))
    print("  404                  :", try_sync(lambda: read_response(make_response(404, json={"message": "not found"}))))
    print("  500                  :", try_sync(lambda: read_response(make_response(500, json={}))))
    print("  429                  :", try_sync(lambda: read_response(make_response(429, json={}))))
    print("  200, but a web page  :", try_sync(lambda: read_response(make_response(200, text="<html>Maintenance</html>"))))
    print("  200, but a bad shape :", try_sync(lambda: read_response(make_response(200, json={"id": 1}))))
except NotImplementedError as error:
    print("  not done yet ->", error)

asked = []


def pretend_supplier(request):
    """Plays the supplier. It writes down every address it is asked for."""
    asked.append(str(request.url))
    path = request.url.path
    if path == "/products/1":
        return httpx.Response(200, json=SUPPLIER_PRODUCT_1)
    if path == "/products/500":
        return httpx.Response(500, json={"message": "Something broke"})
    if path == "/products/408":
        raise httpx.ReadTimeout("The supplier is too slow", request=request)
    return httpx.Response(404, json={"message": "Product not found"})


async def task_2():
    async with httpx.AsyncClient(transport=httpx.MockTransport(pretend_supplier)) as client:
        service = SupplierService("https://pretend.supplier.test", client)
        print("  product 1            :", await try_async(lambda: service.get_by_id(1)))
        print("  product 9999         :", await try_async(lambda: service.get_by_id(9999)))
        print("  address asked first  :", asked[0] if asked else "(nothing was asked)")
        print("  supplier answers 500 :", await try_async(lambda: service.get_by_id(500)))
        print("  supplier too slow    :", await try_async(lambda: service.get_by_id(408)))


print("Task 2: SupplierService.get_by_id (a pretend supplier, no internet)")
try:
    asyncio.run(task_2())
except NotImplementedError as error:
    print("  not done yet ->", error)
