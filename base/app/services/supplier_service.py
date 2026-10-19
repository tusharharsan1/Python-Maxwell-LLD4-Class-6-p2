"""Talking to the supplier.

Read README.md first. Your job is to finish the TODOs: three in `read_response` and two in `get_by_id`.
Do not rename the functions, the class or their parameters.
"""
import httpx

from app.core.errors import SupplierError
from app.schemas.supplier import SupplierProduct

# The one sentence the client is allowed to see when the supplier is the problem.
SUPPLIER_DOWN_MESSAGE = "The supplier is not available right now"


def read_response(response: httpx.Response) -> dict | None:
    """TASK 1: read the supplier's answer (a response that has already arrived).

    - Status 404: the supplier has no such product. Return None.
    - Status 200 and a good product in the JSON: return the product as a dict, in OUR names.
    - Anything else is a problem: another 4xx or 5xx status, a body that is not JSON,
      or JSON that is not a good product. Then a SupplierError must come out.

    The try/except below is already finished. It turns every problem into a SupplierError.
    """
    # TODO 1: if the status code is 404, return None.
    #         Do this BEFORE the try, because a 404 is a normal answer, not a problem.

    try:
        # TODO 2: raise an error when the status is 4xx or 5xx.
        # TODO 3: turn the JSON into a SupplierProduct, then return it as a dict (OUR names).
        raise NotImplementedError("TODO 2 and TODO 3 are not done yet")  # delete this line when both are done
    except (httpx.HTTPError, ValueError) as exc:
        # EXAMPLE, already finished.
        raise SupplierError(SUPPLIER_DOWN_MESSAGE) from exc


class SupplierService:
    def __init__(self, base_url: str, client: httpx.AsyncClient):
        """EXAMPLE, already finished.

        `base_url` is the supplier's address, with no "/" at the end, for example "https://dummyjson.com".
        `client` is given to you: use it to send the request. (The tests give a pretend one.)
        """
        self.base_url = base_url
        self.client = client

    async def get_by_id(self, product_id: int) -> dict | None:
        """TASK 2: ask the supplier for one product, and give back what read_response says.

        - Send a GET request to  {base_url}/products/{product_id}  with self.client (use `await`).
        - Give the response to read_response and return its result.
        - If the call itself breaks (a timeout, no connection), httpx raises an httpx.HTTPError.
          The try/except below is already finished. It turns that into a SupplierError.
        """
        url = f"{self.base_url}/products/{product_id}"  # EXAMPLE, already finished
        try:
            # TODO 4: send the GET request with `await self.client.get(url)` and keep the answer in `response`.
            raise NotImplementedError("TODO 4 is not done yet")  # delete this line when it is done
        except httpx.HTTPError as exc:
            # EXAMPLE, already finished.
            raise SupplierError(SUPPLIER_DOWN_MESSAGE) from exc
        # TODO 5: give `response` to read_response and return what it says.
        raise NotImplementedError("TODO 5 is not done yet")  # delete this line when it is done
