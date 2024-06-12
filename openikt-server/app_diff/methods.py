"""app method file"""

import hashlib


def format_resp(
    data: object = None, code: object = 0, msg: object = "", detail: object = ""
) -> object:
    """Format the response data
    Make the interface conform to the restful API specification.

    code:   0 means the request was processed successfully,
            !=0 indicates that an error occurred and can help locate the error.
    data:   real data returned.
    msg:    simple description.
    detail: detailed description.
            For example the details of the error that occurred
    """
    return {"code": code, "data": data, "msg": msg, "detail": detail}


def email_display(email):
    """Fotmat email data"""
    # ftln: first letter of last name
    uname = email.split("@")[0]
    iname = uname.split(".")
    name = ""
    new_name = []
    for na in iname:
        name += na
        new_name.append(na.capitalize())
    nhash = hashlib.sha224(email.encode("utf-8")).hexdigest()[:32]
    color = f"#{str(nhash)[:6]}"
    return [" ".join(new_name), color, email]
