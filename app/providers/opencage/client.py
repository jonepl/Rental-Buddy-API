from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.domain.enums.context_request import ContextRequest

class OpenCageClient: 
  def __init__(self):
    self.api_key = settings.opencage_api_key
    self.base_url = settings.opencage_url
    self.timeout = settings.request_timeout_seconds

  async def geocode_address(self, params: Dict[str, Any]) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    return await self._get(self.base_url, params, ContextRequest.GEOCODING)