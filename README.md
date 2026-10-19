# Reading the Supplier's Answer at ShopNest

> **Where the files are:** the finished files in the `solution/` folder. Every path below (such as `app/services/supplier_service.py`, `tests/` and `try_it.py`) is inside `solution/`. Open a terminal in `solution/` to run the commands.

## Problem Statement
Our catalog asks the supplier (dummyjson) for one product at a time. In class we learned that the supplier's answer is not always a product. `httpx` hands back a `404` as a normal answer (it does **not** raise an error), and the supplier can also answer with an error status, send a web page instead of JSON, or be too slow to answer. Our service must turn every one of these into something the rest of the project can handle: a **product**, `None` (which means "there is no such product"), or our own **`SupplierError`**. Finish two small pieces. Together they need only about 7 lines of code.

## Requirements
### Reading an answer that has arrived (`read_response`)
`read_response` receives the supplier's response (it has already arrived) and decides what it means.

| The supplier's answer | What `read_response` does |
|---|---|
| status `404` | returns `None` |
| status `200`, with a good product in the JSON | returns the product as a `dict`, in **our** names (use `SupplierProduct`: `model_validate`, then `model_dump`) |
| any other `4xx` or `5xx` status (for example `400`, `429`, `500`, `503`) | raises `SupplierError` |
| status `200`, but the body is not JSON (for example a web page) | raises `SupplierError` |
| status `200`, JSON, but not a good product (a key is missing, or the JSON is a list) | raises `SupplierError` |

Rules to remember:
- **Look at the status first.** A `404` is a normal answer, so it returns `None` even if its body is not JSON.
- **An error status always wins.** A `500` is an error even if its body looks like a good product.
- Only `SupplierError` may come out. The `try/except` that is already written in the starter turns every other problem into a `SupplierError`, so you only have to write the lines inside the `try`.

### Asking the supplier (`SupplierService.get_by_id`)
`get_by_id` asks the supplier for one product, and then gives the response to `read_response`.

| What happens at the supplier | What `get_by_id` does |
|---|---|
| answers `200` with a good product | returns the product as a `dict`, in our names |
| answers `404` | returns `None` |
| answers with an error status, a web page, or a bad product | raises `SupplierError` |
| is too slow, or cannot be reached | raises `SupplierError` (the `try/except` that is already written does this for you) |

More rules:
- The request is a `GET` to `{base_url}/products/{product_id}`. For example `https://dummyjson.com/products/1`. The starter already builds this address for you (`url`).
- Use `self.client` (it is given to you) with `await`, as in class.
- One call to `get_by_id` sends **one** request.

To achieve these requirements we need to do 2 things:
- Complete `read_response`, which decides what the supplier's answer means.
- Complete `SupplierService.get_by_id`, which sends the request and uses `read_response`.

## Instructions
1. We need to implement `read_response` inside `app/services/supplier_service.py`. There are three TODO notes in it (`TODO 1`, `TODO 2` and `TODO 3`).
2. We need to implement `get_by_id` inside the class `SupplierService` in the same file. There are two TODO notes in it (`TODO 4` and `TODO 5`).
3. Check the status `404` **before** the `try`, as in class: a `404` must not become an error.
4. Do not modify the existing code: `SUPPLIER_DOWN_MESSAGE`, the `try/except` parts that are already written, `SupplierService.__init__`, the file `app/core/errors.py`, the file `app/schemas/supplier.py`, the file `samples.py`, or the names and parameters of the functions. Feel free to add new methods or new functions if required.
5. When a TODO is finished, delete the `raise NotImplementedError(...)` line that belongs to it.
6. Run `python try_it.py` from this folder (the one that contains `app/` and `try_it.py`) to see what your code does. When both tasks are finished, you should see exactly this:
   ```
   Task 1: read_response
     200, a good product  : product 1, Essence Mascara Lash Princess
     404                  : None
     500                  : raises SupplierError
     429                  : raises SupplierError
     200, but a web page  : raises SupplierError
     200, but a bad shape : raises SupplierError
   Task 2: SupplierService.get_by_id (a pretend supplier, no internet)
     product 1            : product 1, Essence Mascara Lash Princess
     product 9999         : None
     address asked first  : https://pretend.supplier.test/products/1
     supplier answers 500 : raises SupplierError
     supplier too slow    : raises SupplierError
   ```
   If you see `not done yet`, a task still has its `raise` line.
7. Your code will be checked with the test file `tests/test_supplier_answer.py`. It checks the cases in the Requirements above, and the rules in instructions 3 and 4. While you write your code, use `python try_it.py` (instruction 6) to check your work.
8. You do not need a server, an internet connection or a key for this assignment. The supplier is a **pretend supplier** (`httpx` can be given one, and that is what `try_it.py` and the tests do). The packages `httpx` and `pydantic` are already installed (they came with `pip install "fastapi[standard]"` in Class 4). Use Python 3.10 or newer.
9. Hints (all of these use ideas from class):
    - **What a response tells you.** `response.status_code` is the number (404, 500, and so on). `response.json()` gives the data. `response.raise_for_status()` raises an error when the status is `4xx` or `5xx`.
    - **TODO 1.** One `if` that returns `None`:
      ```python
      if response.status_code == 404:
          return None
      ```
    - **TODO 2 and TODO 3.** Inside the `try`, first check the status, then make the product:
      ```python
      response.raise_for_status()
      item = SupplierProduct.model_validate(response.json())
      return item.model_dump()
      ```
      (`model_validate` reads the supplier's JSON. `model_dump()` gives a plain dictionary, in our names.)
    - **TODO 4.** Sending a request with the client you were given:
      ```python
      response = await self.client.get(url)
      ```
    - **TODO 5.** Give the response to `read_response` and return its result: `return read_response(response)`.
    - **If something looks wrong.** If the good product shows `raises AttributeError`, you probably forgot `await` in TODO 4. If the `404` line shows `raises SupplierError`, check that TODO 1 comes **before** the `try`.
