from app.domain.dto.listings import Center
from app.providers.opencage.models import GeocodeResponse


def normalize_response(response: GeocodeResponse) -> Center:
    return Center(
        lat=response.results[0].geometry.lat, lon=response.results[0].geometry.lng
    )
