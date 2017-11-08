import ssl
import urllib.request
import json
from flask import redirect, render_template, request, session, url_for, flash
from functools import wraps


def apology(msg):
    """Renders message as an apology to user."""
    flash(msg, 'alert-danger')
    print('***')
    print(request.url)
    print(msg)
    return redirect(request.url)
    # return render_template('apology.html')


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # reject symbol if it starts with caret
    if symbol.startswith("^"):
        return None

    # reject symbol if it contains comma
    if "," in symbol:
        return None

    # query IEX for quote as YAHOO Finance API is no longer available
    # https://news.ycombinator.com/item?id=15617576
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = "https://api.iextrading.com/1.0/stock/{}/quote".format(symbol)
        data = json.load(urllib.request.urlopen(url, context=ctx))

        # Code for old yahoo finance api
        # webpage = urllib.request.urlopen(url)
        # datareader = csv.reader(webpage.read().decode("utf-8").splitlines())
        # row = next(datareader)
    except Exception:
        return None

    # ensure stock exists
    try:
        price = float(data["latestPrice"])
    except Exception:
        return None

    # return stock's name (as a str), price (as a float), and (uppercased) symbol (as a str)
    return {
        "name": data["companyName"],
        "price": price,
        "symbol": data["symbol"].upper()
    }


def usd(value):
    """Formats value as USD."""
    return "${:,.2f}".format(value)
