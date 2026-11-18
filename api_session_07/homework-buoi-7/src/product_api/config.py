import os

def settings():
    return dict(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///products.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_TITLE="SOA Session 7 Product and Order API", API_VERSION="v1",
        OPENAPI_VERSION="3.0.3", OPENAPI_URL_PREFIX="/",
        OPENAPI_JSON_PATH="openapi.json", OPENAPI_SWAGGER_UI_PATH="/docs",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/",
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
    )
