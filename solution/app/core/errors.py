"""Our own errors. They know nothing about HTTP. EXAMPLES, already finished.

Each class holds a number (`status_code`). The handler in app/core/handlers.py uses it.
"""


class AppError(Exception):
    status_code = 500


class ProductNotFoundError(AppError):
    status_code = 404


class SupplierError(AppError):
    status_code = 502
