from fastapi import APIRouter, Depends

from app.db.models import Farm
from app.deps import get_current_farm
from app.services.scheme_matcher import match_schemes

router = APIRouter(prefix="/api/schemes", tags=["schemes"])


@router.get("/match")
def schemes_match(language: str = "en", farm: Farm = Depends(get_current_farm)):
    return match_schemes(farm.crop_type, farm.field_area_hectare, language)
