"""
schemas.py - Các Marshmallow Schemas cho Books Management API
Môn học: Kiến trúc Hướng Dịch vụ (SOA) - Buổi 4
"""

from marshmallow import Schema, fields, validate


class BookSchema(Schema):
    """Schema mô tả thực thể Book hoàn chỉnh."""
    id = fields.Int(
        dump_only=True,
        metadata={"description": "Mã định danh duy nhất của cuốn sách", "example": 1}
    )
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Tiêu đề cuốn sách", "example": "Clean Code"}
    )
    author = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Tác giả cuốn sách", "example": "Robert C. Martin"}
    )
    isbn = fields.Str(
        allow_none=True,
        metadata={"description": "Mã số tiêu chuẩn quốc tế ISBN", "example": "9780132350884"}
    )
    price = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0),
        metadata={"description": "Giá bán của cuốn sách (USD)", "example": 45.0}
    )


class BookCreateInputSchema(Schema):
    """Schema cho dữ liệu tạo mới cuốn sách (POST /books)."""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Tiêu đề cuốn sách (bắt buộc)", "example": "Clean Architecture"}
    )
    author = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Tác giả cuốn sách (bắt buộc)", "example": "Robert C. Martin"}
    )
    isbn = fields.Str(
        allow_none=True,
        metadata={"description": "Mã ISBN", "example": "9780134494166"}
    )
    price = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0),
        metadata={"description": "Giá bán (lớn hơn hoặc bằng 0)", "example": 50.0}
    )


class BookUpdateInputSchema(Schema):
    """Schema cho dữ liệu cập nhật toàn bộ cuốn sách (PUT /books/<id>)."""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Tiêu đề cập nhật toàn bộ (bắt buộc)", "example": "Refactoring"}
    )
    author = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        metadata={"description": "Tác giả cập nhật toàn bộ (bắt buộc)", "example": "Martin Fowler"}
    )
    isbn = fields.Str(
        allow_none=True,
        metadata={"description": "Mã ISBN", "example": "9780201485677"}
    )
    price = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0),
        metadata={"description": "Giá bán", "example": 55.0}
    )


class BookPatchInputSchema(Schema):
    """Schema cho dữ liệu cập nhật một phần cuốn sách (PATCH /books/<id>)."""
    title = fields.Str(
        validate=validate.Length(min=1),
        metadata={"description": "Tiêu đề mới (tùy chọn)", "example": "Clean Code - Second Edition"}
    )
    author = fields.Str(
        validate=validate.Length(min=1),
        metadata={"description": "Tác giả mới (tùy chọn)", "example": "R. Martin"}
    )
    isbn = fields.Str(
        metadata={"description": "Mã ISBN mới (tùy chọn)", "example": "9780132350884"}
    )
    price = fields.Float(
        validate=validate.Range(min=0),
        metadata={"description": "Giá bán mới (tùy chọn, >= 0)", "example": 49.99}
    )


class PaginationMetaSchema(Schema):
    """Schema thông tin metadata phân trang."""
    page = fields.Int(
        dump_only=True,
        metadata={"description": "Trang hiện tại", "example": 1}
    )
    size = fields.Int(
        dump_only=True,
        metadata={"description": "Số lượng phần tử mỗi trang", "example": 20}
    )
    total = fields.Int(
        dump_only=True,
        metadata={"description": "Tổng số lượng bản ghi thỏa mãn điều kiện lọc", "example": 4}
    )
    total_pages = fields.Int(
        dump_only=True,
        metadata={"description": "Tổng số trang", "example": 1}
    )


class LinkItemSchema(Schema):
    """Schema cho từng đường dẫn liên kết HATEOAS."""
    href = fields.Str(
        dump_only=True,
        metadata={"description": "Đường dẫn liên kết", "example": "/books?page=1&size=20"}
    )


class BookLinksSchema(Schema):
    """Schema các liên kết HATEOAS điều hướng phân trang."""
    self = fields.Nested(
        LinkItemSchema,
        dump_only=True,
        metadata={"description": "Liên kết đến chính trang hiện tại"}
    )
    first = fields.Nested(
        LinkItemSchema,
        dump_only=True,
        metadata={"description": "Liên kết đến trang đầu tiên"}
    )
    last = fields.Nested(
        LinkItemSchema,
        dump_only=True,
        metadata={"description": "Liên kết đến trang cuối cùng"}
    )
    prev = fields.Nested(
        LinkItemSchema,
        dump_only=True,
        allow_none=True,
        metadata={"description": "Liên kết đến trang trước (nếu có)"}
    )
    next = fields.Nested(
        LinkItemSchema,
        dump_only=True,
        allow_none=True,
        metadata={"description": "Liên kết đến trang sau (nếu có)"}
    )


class BookListResponseSchema(Schema):
    """Schema phản hồi cho GET /books kèm dữ liệu, phân trang và liên kết HATEOAS."""
    data = fields.List(
        fields.Nested(BookSchema),
        dump_only=True,
        metadata={"description": "Danh sách các cuốn sách trong trang hiện tại"}
    )
    pagination = fields.Nested(
        PaginationMetaSchema,
        dump_only=True,
        metadata={"description": "Metadata phân trang"}
    )
    _links = fields.Nested(
        BookLinksSchema,
        dump_only=True,
        metadata={"description": "Các liên kết HATEOAS"}
    )


class ErrorResponseSchema(Schema):
    """Schema cấu trúc lỗi trả về chuẩn JSON."""
    error = fields.Str(
        required=True,
        metadata={"description": "Mô tả ngắn gọn về mã lỗi", "example": "not found"}
    )
    message = fields.Str(
        allow_none=True,
        metadata={"description": "Thông điệp chi tiết giải thích lỗi", "example": "Book with id 99 does not exist"}
    )
