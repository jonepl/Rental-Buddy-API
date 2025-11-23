from app.providers.rentcast.client import RentCastClient
from app.providers.rentcast.adapter import RentCastAdapter
from app.services.listings_service import ListingsService

def get_listings_service() -> ListingsService:
  client = RentCastClient()
  adapter = RentCastAdapter(client)
  return ListingsService(listings_port=adapter)
