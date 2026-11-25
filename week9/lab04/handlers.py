def v1_create_order(body):
    return {"account_id": body["account_id"], "status": "accepted"}


def v2_create_order(body):
    return {"account_id": body["account_id"], "status": "created"}
