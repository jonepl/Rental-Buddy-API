from enum import Enum


# enum of context request types
class OperationType(Enum):
    SALES = "sale"
    RENTALS = "rental"
    GEOCODING = "geocoding"
