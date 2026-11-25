from hashlib import md5

from .handlers import v1_create_order, v2_create_order


V2_COHORTS = {"beta", "internal"}
V2_FORCE_ACCOUNTS = {"acct_42", "acct_99"}


def route_to_v2(account_id, cohort, percent):
    if cohort.lower() in V2_COHORTS:
        return True
    if account_id in V2_FORCE_ACCOUNTS:
        return True

    bucket = int(md5(account_id.encode("utf-8"), usedforsecurity=False).hexdigest(), 16) % 100
    return bucket < percent


def dispatch(body, cohort, percent):
    if route_to_v2(body["account_id"], cohort, percent):
        return "v2", v2_create_order(body), 201
    return "v1", v1_create_order(body), 200
