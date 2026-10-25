from .middleware import LOKALNY_LOGIN
from .role import jest_mg


def konto(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"konto": None}
    nazwa = user.get_full_name() or user.username
    lokalne = user.username == LOKALNY_LOGIN
    return {
        "konto": {"nazwa": nazwa, "login": user.username, "mg": jest_mg(user), "lokalne": lokalne}
    }
