"""
AgriNova — Nearest agri-input dealer linkage.

Deliberately not a hardcoded list of dealer names/addresses — with ~700+
Krishi Vigyan Kendras and countless licensed seed/fertilizer shops across
India, a static directory would either be too sparse to be useful or risk
presenting guessed/stale contact details as fact. Instead this builds two
always-correct links from data AgriNova already has:

- a Google Maps search centered on the farm's own stored GPS coordinates,
  so results are genuinely nearby rather than approximated by state/region.
- the official ICAR Krishi Vigyan Kendra portal, for the government-run
  extension-center path (soil testing, subsidized inputs, advisory).
"""

from urllib.parse import quote

_MAPS_QUERY = "agricultural input dealer OR krishi kendra OR fertilizer shop"
_KVK_PORTAL_URL = "https://kvk.icar.gov.in"


def get_dealer_links(latitude: float, longitude: float) -> dict:
    maps_url = f"https://www.google.com/maps/search/{quote(_MAPS_QUERY)}/@{latitude},{longitude},13z"
    return {
        "nearest_search_url": maps_url,
        "kvk_portal_url": _KVK_PORTAL_URL,
    }
