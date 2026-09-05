from fastapi import APIRouter, Depends

from app.db.models import Farm
from app.deps import get_current_farm
from app.services.dealer_directory import get_dealer_links
from app.services.mandi_price_service import get_mandi_prices

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/overview")
def market_overview(farm: Farm = Depends(get_current_farm)):
    return {
        "state": farm.state,
        "crop": farm.crop_type,
        "mandi": get_mandi_prices(farm.crop_type, farm.state),
        "dealers": get_dealer_links(farm.latitude, farm.longitude),
    }
