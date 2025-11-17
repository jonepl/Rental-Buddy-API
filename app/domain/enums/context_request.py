from enum import Enum


# enum of context request types
class ContextRequest(Enum):
    SALES = "sales"
    RENTALS = "rentals"
    GEOCODING = "geocoding"
