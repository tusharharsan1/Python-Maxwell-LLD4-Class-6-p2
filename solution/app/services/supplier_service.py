"""Talking to the supplier. (Finished version.)"""
import httpx

from app.core.errors import SupplierError
from app.schemas.supplier import SupplierProduct

# The one sentence the client is allowed to see when the supplier is the problem.
SUPPLIER_DOWN_MESSAGE = "The supplier is not available right now"


def read_response(response: httpx.Response) -> dict | None:
    """Read the supplier's answer (a response that has already arrived).

    - Status 404: the supplier has no such product. Return None.
    - Status 200 and a good product in the JSON: return the product as a dict, in OUR names.
    - Anything else is a problem: another 4xx or 5xx status, a body that is not JSON,
      or JSON that is not a good product. Then a SupplierError comes out.

    The try/except below turns every problem into a SupplierError.
    """
    # A 404 is a normal answer, not a problem: the supplier simply has no such product.
    # We check it BEFORE the try, so that it never becomes a SupplierError.
    if response.status_code == 404:
        return None

    try:
        # Step 1: a 4xx or 5xx status raises an httpx.HTTPStatusError.
        response.raise_for_status()
        # Step 2: response.json() raises a ValueError when the body is not JSON.
        # model_validate raises a ValidationError (also a ValueError) when the JSON is not a good product.
        item = SupplierProduct.model_validate(response.json())
        # Step 3: a plain dictionary, in OUR names.
        return item.model_dump()
    except (httpx.HTTPError, ValueError) as exc:
        raise SupplierError(SUPPLIER_DOWN_MESSAGE) from exc


class SupplierService:
    def __init__(self, base_url: str, client: httpx.AsyncClient):
        """`base_url` is the supplier's address, with no "/" at the end, for example "https://dummyjson.com".

        `client` is given to us: we use it to send the request. (The tests give a pretend one.)
        """
        self.base_url = base_url
        self.client = client

    async def get_by_id(self, product_id: int) -> dict | None:
        """Ask the supplier for one product, and give back what read_response says."""
        url = f"{self.base_url}/products/{product_id}"
        try:
            # Send the GET request. `await` waits for the answer, and other requests can run meanwhile.
            response = await self.client.get(url)
        except httpx.HTTPError as exc:
            # The call itself broke (a timeout, no connection). The client sees one safe sentence.
            raise SupplierError(SUPPLIER_DOWN_MESSAGE) from exc

        # The answer has arrived. read_response decides what it means.
        return read_response(response)
