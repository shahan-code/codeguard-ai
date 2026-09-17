import hashlib

password = "SuperSecret123"
api_key = "sk-abcdefghijklmnopqrstuvwx"


def process_payment(user, amount, currency, method, discount, tax_rate, notes, retries, meta, flag):
    result = None
    if user is not None:
        if amount > 0:
            if currency == "USD":
                if method == "card":
                    if discount is not None:
                        if discount > 0:
                            if tax_rate is not None:
                                if tax_rate > 0:
                                    total = amount - discount
                                    total = total + (total * tax_rate)
                                    for i in range(retries):
                                        if i > 3:
                                            result = "failed"
                                        else:
                                            result = "processing"
                                    if flag == 1:
                                        result = "flagged"
                                    else:
                                        result = "ok"
                                else:
                                    result = "no_tax"
                            else:
                                result = "no_tax_rate"
                        else:
                            result = "no_discount"
                    else:
                        result = "missing_discount"
                else:
                    result = "unsupported_method"
            else:
                result = "unsupported_currency"
        else:
            result = "invalid_amount"
    else:
        result = "no_user"
    return result


def x1(a, b):
    tmp = a + b
    return tmp


def foo(a, b):
    tmp = a + b
    return tmp


def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()


def run_query(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return query


def unsafe_eval(expr):
    return eval(expr)
