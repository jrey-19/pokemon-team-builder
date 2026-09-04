import requests
EXCLUDE_SUFFIXES = ["-mega", "-mega-x", "-mega-y", "-gmax", "-totem", "-cap" ]
EXCLUDE_EXACT = ["raticate-totem-alola", "pikachu-belle", "pikachu-rock-star", "pikachu-bell", "pikachu-pop-star", "pikachu-phd", "pikachu-libre", "pikachu-cosplay"]

def should_include(name: str) -> bool:
    if name in EXCLUDE_EXACT:
        return False
    if any(name.endswith(suffix) for suffix in EXCLUDE_SUFFIXES):
        return False
    return True
