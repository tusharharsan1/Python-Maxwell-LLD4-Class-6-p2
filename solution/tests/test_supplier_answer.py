import inspect
import os
import sys
import unittest
from unittest.mock import patch

import httpx

# Lets this file run directly (python tests/test_supplier_answer.py) from any folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.errors import SupplierError
from app.services import supplier_service
from app.services.supplier_service import SupplierService, read_response

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

# The nine names of OUR product, and the supplier's keys that we require.
OUR_NAMES = {
    "id", "title", "description", "category", "price", "stock",
    "image_url", "discount_percentage", "dimensions",
}
REQUIRED_SUPPLIER_KEYS = [
    "id", "title", "description", "category", "price", "stock", "thumbnail", "discountPercentage",
]

# A web page that a broken supplier might send instead of JSON.
WEB_PAGE = "<html><body>Down for maintenance</body></html>"


# ---------------------------------------------------------------------------
# Helpers: keep the tests short and readable
# ---------------------------------------------------------------------------

def _supplier_json(**changes):
    """A product as the supplier sends it: 22 fields, in the supplier's own spelling."""
    product = {
        "id": 1,
        "title": "Essence Mascara Lash Princess",
        "description": "A popular mascara known for its volumizing and lengthening effects.",
        "category": "beauty",
        "price": 9.99,
        "discountPercentage": 10.48,
        "rating": 2.56,
        "stock": 99,
        "tags": ["beauty", "mascara"],
        "brand": "Essence",
        "sku": "BEA-ESS-ESS-001",
        "weight": 4,
        "dimensions": {"width": 15.14, "height": 13.08, "depth": 22.99},
        "warrantyInformation": "1 week warranty",
        "shippingInformation": "Ships in 3-5 business days",
        "availabilityStatus": "In Stock",
        "reviews": [{"rating": 3, "comment": "Would not recommend!", "reviewerName": "Eleanor Collins"}],
        "returnPolicy": "No return policy",
        "minimumOrderQuantity": 48,
        "meta": {"createdAt": "2025-04-30T09:41:02.053Z", "barcode": "5784719087687"},
        "images": ["https://cdn.example.test/products/1/1.webp"],
        "thumbnail": "https://cdn.example.test/products/1/thumbnail.webp",
    }
    product.update(changes)
    return product


def _without(product, *keys):
    """A copy of `product` that has no key from `keys`."""
    return {key: value for key, value in product.items() if key not in keys}


def _product_1_in_our_names():
    """Product 1 exactly as read_response must give it back."""
    return {
        "id": 1,
        "title": "Essence Mascara Lash Princess",
        "description": "A popular mascara known for its volumizing and lengthening effects.",
        "category": "beauty",
        "price": 9.99,
        "stock": 99,
        "image_url": "https://cdn.example.test/products/1/thumbnail.webp",
        "discount_percentage": 10.48,
        "dimensions": {"width": 15.14, "height": 13.08, "depth": 22.99},
    }


def _response(status, **content):
    """A response built by hand. It has a request attached, as a real one has."""
    return httpx.Response(status, request=httpx.Request("GET", "https://supplier.test/products/1"), **content)


def _product_for(product_id):
    """The supplier's JSON for the product with this id. Each id gives a different product."""
    return _supplier_json(
        id=product_id, title=f"Product number {product_id}", price=product_id + 0.5, stock=product_id,
        thumbnail=f"https://cdn.example.test/products/{product_id}/thumbnail.webp",
    )


# Three more products with their expected answers, all different (so a hard-coded answer fails).
OTHER_PRODUCTS = [
    (
        _supplier_json(id=9, title="Dolce Shine Eau de", description="A fruity fragrance.", category="fragrances",
                       price=69.99, stock=4, discountPercentage=0.62,
                       dimensions={"width": 27.28, "height": 29.88, "depth": 18.3},
                       thumbnail="https://cdn.example.test/products/9/thumbnail.webp"),
        {"id": 9, "title": "Dolce Shine Eau de", "description": "A fruity fragrance.", "category": "fragrances",
         "price": 69.99, "stock": 4, "image_url": "https://cdn.example.test/products/9/thumbnail.webp",
         "discount_percentage": 0.62, "dimensions": {"width": 27.28, "height": 29.88, "depth": 18.3}},
    ),
    (
        _without(_supplier_json(id=26, title="Green Chili Pepper", description="Hot and fresh.", category="groceries",
                                price=0.99, stock=3, discountPercentage=1.5,
                                thumbnail="https://cdn.example.test/products/26/thumbnail.webp"), "dimensions"),
        {"id": 26, "title": "Green Chili Pepper", "description": "Hot and fresh.", "category": "groceries",
         "price": 0.99, "stock": 3, "image_url": "https://cdn.example.test/products/26/thumbnail.webp",
         "discount_percentage": 1.5, "dimensions": None},
    ),
    (
        _supplier_json(id=500, title="Mug", description="A big mug.", category="kitchen", price=4.5, stock=0,
                       discountPercentage=0.0, dimensions=None, thumbnail="https://example.test/mug.webp"),
        {"id": 500, "title": "Mug", "description": "A big mug.", "category": "kitchen", "price": 4.5, "stock": 0,
         "image_url": "https://example.test/mug.webp", "discount_percentage": 0.0, "dimensions": None},
    ),
]


# ===========================================================================
# Test Suite 1: Task 1, read_response, answers that are fine
# ===========================================================================

class TestReadResponseGoodAnswers(unittest.TestCase):
    """Tests that a 200 answer with a good product gives back OUR product."""

    def test_a_good_product_in_our_names(self):
        """Status 200 and a good product: the answer is the product in our names (see the README)."""
        self.assertEqual(read_response(_response(200, json=_supplier_json())), _product_1_in_our_names())

    def test_other_products(self):
        """Anti-bypass: three different products each give their own answer."""
        for raw, expected in OTHER_PRODUCTS:
            with self.subTest(product=expected["id"]):
                self.assertEqual(read_response(_response(200, json=raw)), expected)

    def test_the_answer_has_exactly_our_nine_names(self):
        """The supplier's spelling ('thumbnail', 'discountPercentage') and its other keys are not in the answer."""
        for raw in [_supplier_json()] + [raw for raw, _ in OTHER_PRODUCTS]:
            with self.subTest(product=raw["id"]):
                self.assertEqual(set(read_response(_response(200, json=raw))), OUR_NAMES)

    def test_unknown_keys_are_ignored(self):
        """Keys we have never seen are not an error."""
        raw = _supplier_json(newFeature="yes", another={"deep": [1, 2, 3]})
        self.assertEqual(read_response(_response(200, json=raw)), _product_1_in_our_names())

    def test_dimensions_is_none_when_missing_or_null(self):
        """No dimensions at all, or null, gives dimensions None."""
        for label, raw in [("missing", _without(_supplier_json(), "dimensions")),
                           ("null", _supplier_json(dimensions=None))]:
            with self.subTest(dimensions=label):
                answer = read_response(_response(200, json=raw))
                self.assertIn("dimensions", answer)
                self.assertIsNone(answer["dimensions"])

    def test_the_answer_is_a_plain_dict(self):
        """The answer is a dict (not a model), and its dimensions are a dict too."""
        answer = read_response(_response(200, json=_supplier_json()))
        self.assertIs(type(answer), dict)
        self.assertIs(type(answer["dimensions"]), dict)


# ===========================================================================
# Test Suite 2: Task 1, read_response, a 404 is a normal answer
# ===========================================================================

class TestReadResponseNotFound(unittest.TestCase):
    """Tests that a 404 gives None, whatever the body is."""

    def test_a_404_gives_none(self):
        """The supplier says 404 with its usual note: there is no such product, so the answer is None."""
        self.assertIsNone(read_response(_response(404, json={"message": "Product with id '9999' not found"})))

    def test_the_status_is_looked_at_before_the_body(self):
        """Anti-bypass: a 404 gives None even if the body is a web page, is empty, or looks like a product."""
        bodies = [
            ("a web page", {"text": WEB_PAGE}),
            ("an empty body", {"content": b""}),
            ("plain text", {"text": "not found"}),
            ("a good product", {"json": _supplier_json()}),
            ("an empty list", {"json": []}),
        ]
        for label, body in bodies:
            with self.subTest(body=label):
                self.assertIsNone(read_response(_response(404, **body)))


# ===========================================================================
# Test Suite 3: Task 1, read_response, answers that are a problem
# ===========================================================================

class TestReadResponseProblems(unittest.TestCase):
    """Tests that every problem gives a SupplierError, and nothing else."""

    def _assert_supplier_error(self, response):
        """The call must raise a SupplierError (exactly this kind of error, and nothing else)."""
        with self.assertRaises(SupplierError) as context:
            read_response(response)
        self.assertIs(type(context.exception), SupplierError)

    def test_error_statuses_raise_a_supplier_error(self):
        """Any 4xx or 5xx status except 404 is a problem."""
        for status in (400, 401, 403, 408, 429, 500, 502, 503, 504):
            with self.subTest(status=status):
                self._assert_supplier_error(_response(status, json={"message": "Something is wrong"}))

    def test_an_error_status_wins_over_a_good_body(self):
        """Anti-bypass: a 500 is an error even when its body looks like a good product."""
        for status in (400, 429, 500, 503):
            with self.subTest(status=status):
                self._assert_supplier_error(_response(status, json=_supplier_json()))

    def test_a_body_that_is_not_json_raises_a_supplier_error(self):
        """A 200 with a web page, an empty body, or plain text is not JSON."""
        bodies = [("a web page", {"text": WEB_PAGE}), ("an empty body", {"content": b""}), ("plain text", {"text": "OK"})]
        for label, body in bodies:
            with self.subTest(body=label):
                self._assert_supplier_error(_response(200, **body))

    def test_json_that_is_not_a_product_raises_a_supplier_error(self):
        """A 200 with JSON that is not a good product: a list, null, a word, a number, an empty dict, or only a note."""
        not_products = [[], None, "text", 5, {}, {"id": 1}, {"message": "Product with id '9999' not found"}]
        for value in not_products:
            with self.subTest(json=value):
                self._assert_supplier_error(_response(200, json=value))

    def test_a_missing_key_raises_a_supplier_error(self):
        """Without any one of the eight required keys, the product is not good."""
        for key in REQUIRED_SUPPLIER_KEYS:
            with self.subTest(missing=key):
                self._assert_supplier_error(_response(200, json=_without(_supplier_json(), key)))

    def test_a_wrong_kind_of_value_raises_a_supplier_error(self):
        """A word where a number belongs (and similar) makes the product not good."""
        wrong_values = [("price", "cheap"), ("stock", "many"), ("id", "abc"), ("discountPercentage", "big"),
                        ("title", 12345), ("category", None), ("thumbnail", None)]
        for key, value in wrong_values:
            with self.subTest(key=key, value=value):
                self._assert_supplier_error(_response(200, json=_supplier_json(**{key: value})))


# ===========================================================================
# Test Suite 4: Task 2, SupplierService.get_by_id
# ===========================================================================

class TestGetById(unittest.IsolatedAsyncioTestCase):
    """Tests that get_by_id sends the right request and gives back what read_response says.

    The supplier is a pretend one: a small function that plays the supplier (httpx.MockTransport).
    """

    def setUp(self):
        self.requests = []   # every request that reached the pretend supplier

    def _service(self, handler, base_url="https://supplier.test"):
        """A SupplierService whose client talks to a pretend supplier. `handler` plays the supplier."""
        def recording_handler(request):
            self.requests.append(request)
            return handler(request)

        client = httpx.AsyncClient(transport=httpx.MockTransport(recording_handler))
        self.addAsyncCleanup(client.aclose)
        return SupplierService(base_url, client)

    @staticmethod
    def _always(status, **content):
        """A pretend supplier that gives the same answer to every request."""
        return lambda request: httpx.Response(status, **content)

    @staticmethod
    def _product_id_in(request):
        """The id at the end of the address that was asked."""
        return int(request.url.path.rsplit("/", 1)[1])

    # --- The request that is sent ---

    async def test_it_asks_the_right_address_with_a_get(self):
        """The request is a GET to {base_url}/products/{product_id}."""
        cases = [
            ("https://supplier.test", 5, "https://supplier.test/products/5"),
            ("https://dummyjson.com", 194, "https://dummyjson.com/products/194"),
            ("http://localhost:8000", 1, "http://localhost:8000/products/1"),
        ]
        for base_url, product_id, expected_address in cases:
            with self.subTest(address=expected_address):
                self.requests.clear()
                service = self._service(self._always(404, json={"message": "not found"}), base_url)
                await service.get_by_id(product_id)
                self.assertEqual(len(self.requests), 1)
                self.assertEqual(self.requests[0].method, "GET")
                self.assertEqual(str(self.requests[0].url), expected_address)

    async def test_one_call_sends_one_request(self):
        """No repeats and no retries, whatever the supplier answers."""
        answers = [self._always(200, json=_supplier_json()), self._always(404, json={}),
                   self._always(500, json={}), self._always(200, text=WEB_PAGE)]
        for handler in answers:
            with self.subTest(answer=handler):
                self.requests.clear()
                service = self._service(handler)
                try:
                    await service.get_by_id(1)
                except SupplierError:
                    pass
                self.assertEqual(len(self.requests), 1)

    # --- What comes back ---

    async def test_a_good_product_comes_back_in_our_names(self):
        """Anti-bypass: each id gets its own product back, translated to our names."""
        service = self._service(lambda request: httpx.Response(200, json=_product_for(self._product_id_in(request))))
        for product_id in (3, 17, 250):
            with self.subTest(product_id=product_id):
                answer = await service.get_by_id(product_id)
                self.assertEqual(answer["id"], product_id)
                self.assertEqual(answer["title"], f"Product number {product_id}")
                self.assertEqual(answer["price"], product_id + 0.5)
                self.assertEqual(answer["image_url"], f"https://cdn.example.test/products/{product_id}/thumbnail.webp")
                self.assertEqual(set(answer), OUR_NAMES)

    async def test_product_1_comes_back_exactly(self):
        """The product from the README comes back exactly as the README shows."""
        service = self._service(self._always(200, json=_supplier_json()))
        self.assertEqual(await service.get_by_id(1), _product_1_in_our_names())

    async def test_a_404_gives_none(self):
        """The supplier has no such product: the answer is None, and no error."""
        service = self._service(self._always(404, json={"message": "Product with id '9999' not found"}))
        self.assertIsNone(await service.get_by_id(9999))

    async def test_a_problem_gives_a_supplier_error(self):
        """An error status, a web page, a bad product, or a body that is not JSON: SupplierError."""
        problems = [
            ("a 500", self._always(500, json={"message": "broke"})),
            ("a 429", self._always(429, json={})),
            ("a 503 with a good body", self._always(503, json=_supplier_json())),
            ("a web page", self._always(200, text=WEB_PAGE)),
            ("an empty body", self._always(200, content=b"")),
            ("a bad product", self._always(200, json={"id": 1})),
            ("a list", self._always(200, json=[])),
        ]
        for label, handler in problems:
            with self.subTest(problem=label):
                service = self._service(handler)
                with self.assertRaises(SupplierError) as context:
                    await service.get_by_id(1)
                self.assertIs(type(context.exception), SupplierError)

    async def test_a_broken_call_gives_a_supplier_error(self):
        """The supplier is too slow, or cannot be reached: SupplierError (and no httpx error comes out)."""
        def too_slow(request):
            raise httpx.ReadTimeout("The supplier is too slow", request=request)

        def cannot_connect_in_time(request):
            raise httpx.ConnectTimeout("No connection in time", request=request)

        def no_connection(request):
            raise httpx.ConnectError("No connection", request=request)

        def hangs_up(request):
            raise httpx.RemoteProtocolError("The supplier hung up", request=request)

        for label, handler in [("too slow", too_slow), ("no connection in time", cannot_connect_in_time),
                               ("no connection", no_connection), ("hung up", hangs_up)]:
            with self.subTest(problem=label):
                service = self._service(handler)
                with self.assertRaises(SupplierError) as context:
                    await service.get_by_id(1)
                self.assertIs(type(context.exception), SupplierError)

    # --- How it is built ---

    async def test_it_gives_the_response_to_read_response(self):
        """Anti-bypass: get_by_id hands the response to read_response, and returns what it says."""
        service = self._service(self._always(200, json=_product_for(5)))
        with patch.object(supplier_service, "read_response", return_value="what read_response said") as fake:
            result = await service.get_by_id(5)
        self.assertEqual(result, "what read_response said")
        fake.assert_called_once()
        response = fake.call_args.args[0]
        self.assertIsInstance(response, httpx.Response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 5)

    async def test_it_uses_the_client_it_was_given(self):
        """Anti-bypass: two services with two clients each use their own client."""
        first = self._service(self._always(200, json=_supplier_json(title="From the first supplier")))
        second = self._service(self._always(200, json=_supplier_json(title="From the second supplier")))
        self.assertEqual((await first.get_by_id(1))["title"], "From the first supplier")
        self.assertEqual((await second.get_by_id(1))["title"], "From the second supplier")

    def test_get_by_id_is_an_async_method(self):
        """get_by_id is written with `async def`, so the caller has to use `await`."""
        self.assertTrue(inspect.iscoroutinefunction(SupplierService.get_by_id))


# ===========================================================================
# Run all tests
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
