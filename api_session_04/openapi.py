"""
openapi.py - Cấu hình APISpec và nhúng giao diện Swagger UI
Môn học: Kiến trúc Hướng Dịch vụ (SOA) - Buổi 4
"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from schemas import (
    BookSchema,
    BookCreateInputSchema,
    BookUpdateInputSchema,
    BookPatchInputSchema,
    PaginationMetaSchema,
    BookListResponseSchema,
    ErrorResponseSchema
)


def create_api_spec() -> APISpec:
    """Khởi tạo đối tượng APISpec chuẩn OpenAPI 3.0.3 và đăng ký Marshmallow components."""
    spec = APISpec(
        title="Books Management API",
        version="1.0.0",
        openapi_version="3.0.3",
        info={
            "description": (
                "API Quản lý Sách (Books Management API) - Bài thực hành cá nhân Buổi 4.\n\n"
                "**Công nghệ:** Python 3, Flask, apispec, apispec-webframeworks (FlaskPlugin), "
                "marshmallow (MarshmallowPlugin), Swagger UI.\n\n"
                "**Tính năng:** CRUD Sách in-memory, lọc theo tác giả, tìm kiếm tiêu đề, "
                "phân trang linh hoạt, header caching và HATEOAS navigation."
            ),
            "contact": {
                "name": "Sinh viên thực hành SOA",
                "email": "student@soa.example.edu.vn"
            },
            "license": {
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        servers=[
            {
                "url": "http://localhost:5000",
                "description": "Máy chủ cục bộ phát triển (Local Development Server)"
            }
        ],
        tags=[
            {
                "name": "Books",
                "description": "Các thao tác CRUD và tìm kiếm quản lý tài nguyên sách"
            },
            {
                "name": "Documentation",
                "description": "Các endpoint cung cấp đặc tả OpenAPI và giao diện tài liệu"
            }
        ],
        plugins=[FlaskPlugin(), MarshmallowPlugin()]
    )

    # Đăng ký các Schemas vào Components
    spec.components.schema("Book", schema=BookSchema)
    spec.components.schema("BookCreateInput", schema=BookCreateInputSchema)
    spec.components.schema("BookUpdateInput", schema=BookUpdateInputSchema)
    spec.components.schema("BookPatchInput", schema=BookPatchInputSchema)
    spec.components.schema("PaginationMeta", schema=PaginationMetaSchema)
    spec.components.schema("BookListResponse", schema=BookListResponseSchema)
    spec.components.schema("ErrorResponse", schema=ErrorResponseSchema)

    return spec


def get_swagger_ui_html(spec_url: str = "/openapi.json", title: str = "Books API - Swagger UI") -> str:
    """Trả về mã HTML nhúng thư viện Swagger UI độc lập kết nối tới OpenAPI JSON."""
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <!-- Swagger UI CSS từ CDN unpkg -->
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <link rel="icon" type="image/png" href="https://unpkg.com/swagger-ui-dist@5/favicon-32x32.png" sizes="32x32" />
  <style>
    html {{
      box-sizing: border-box;
      overflow: -moz-scrollbars-vertical;
      overflow-y: scroll;
    }}
    *, *:before, *:after {{
      box-sizing: inherit;
    }}
    body {{
      margin: 0;
      background: #fafafa;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .topbar-custom {{
      background-color: #1b1b1b;
      padding: 10px 20px;
      color: #fff;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 3px solid #49cc90;
    }}
    .topbar-custom h1 {{
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      letter-spacing: 0.5px;
    }}
    .topbar-custom a {{
      color: #49cc90;
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
    }}
    .topbar-custom a:hover {{
      text-decoration: underline;
    }}
    .swagger-ui .topbar {{
      display: none;
    }}
  </style>
</head>
<body>
  <div class="topbar-custom">
    <h1>SOA Buổi 4: OpenAPI + Flask + Swagger UI</h1>
    <div>
      <a href="{spec_url}" target="_blank">📄 Xem OpenAPI Spec ({spec_url})</a>
    </div>
  </div>
  <div id="swagger-ui"></div>

  <!-- Swagger UI Bundle JS -->
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" charset="UTF-8"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
  <script>
    window.onload = function() {{
      window.ui = SwaggerUIBundle({{
        url: "{spec_url}",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout",
        defaultModelsExpandDepth: 1,
        defaultModelExpandDepth: 1,
        docExpansion: "list",
        displayRequestDuration: true,
        tryItOutEnabled: true
      }});
    }};
  </script>
</body>
</html>
"""
