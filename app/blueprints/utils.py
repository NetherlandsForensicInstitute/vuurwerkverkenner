from flask import redirect, url_for


def redirect_to(page: str):
    return redirect(url_for(f"{page}.show"))
