"""Rebuild ERD PNG and Vietnamese PDF. Requires Graphviz and DejaVu Sans."""
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
ROOT = Path(__file__).resolve().parent

def build():
    subprocess.run(['dot', '-Tpng', '-Gdpi=170', str(ROOT/'erd.dot'), '-o', str(ROOT/'erd.png')], check=True)
    for name, filename in [('VN','DejaVuSans.ttf'),('VN-Bold','DejaVuSans-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/dejavu/'+filename))
    styles = getSampleStyleSheet()
    for name in ['Normal','BodyText','Title','Heading1','Heading2']:
        styles[name].fontName = 'VN-Bold' if name in ['Title','Heading1','Heading2'] else 'VN'
        styles[name].leading = 15
    styles['Normal'].fontSize=10
    story=[]
    def p(text, style='Normal'):
        story.append(Paragraph(text, styles[style])); story.append(Spacer(1,8))
    p('SOA – Buổi 5: Data Modeling & Resource Design','Title')
    p('Hệ thống Bookstore API','Heading1')
    p('Hệ thống quản lý danh mục sách, tác giả, đánh giá và đơn mua sách. Đây là domain bán sách; không mô hình hóa mượn/trả thư viện. Bài 1 là thiết kế tổng thể; Bài 2 triển khai endpoint danh sách sách.')
    p('Các entity và ràng buộc','Heading2')
    p('Book: id, title, isbn duy nhất (13 chữ số), price không âm, category_id bắt buộc. Author: id, name bắt buộc, biography và website tùy chọn. Category: id, name, slug duy nhất.')
    p('BookAuthor: khóa chính kép (book_id, author_id), đồng thời là hai khóa ngoại. User: id, email duy nhất, password_hash, name; không lưu mật khẩu thô. Review: id, book_id, user_id, rating từ 1–5, comment, created_at, status; UNIQUE(book_id, user_id).')
    p('Order: id, user_id, status thuộc pending/paid/cancelled, created_at. OrderItem: khóa chính kép (order_id, book_id), quantity nguyên dương, unit_price không âm. Giá tiền dùng DECIMAL(12,2), cùng một đơn vị USD cho bài tập; không dùng float để lưu trữ tiền.')
    p('Quan hệ và tính toàn vẹn','Heading2')
    p('Category 1:N Book; mỗi sách thuộc đúng một thể loại. Book N:M Author qua BookAuthor; mỗi sách có ít nhất một tác giả theo quy tắc nghiệp vụ. User và Book mỗi bên có 1:N Review; một người chỉ đánh giá một lần cho mỗi sách.')
    p('User 1:N Order; Order 1:N OrderItem; mỗi đơn phải có ít nhất một dòng hàng. Book 1:N OrderItem. Không có quan hệ 1:1 vì domain không cần. Số lượng tối thiểu một tác giả hoặc một dòng hàng phải được kiểm tra trong giao dịch ứng dụng, không chỉ bằng FK.')
    p('Khóa ngoại dùng RESTRICT để ngăn xóa sách đã có lịch sử mua hoặc đánh giá. Dòng hàng lưu giá tại lúc đặt mua; tổng đơn suy ra từ tổng quantity × unit_price. Chỉ xóa BookAuthor khi chỉnh sửa quan hệ tác giả; không xóa tác giả được tham chiếu. Bài 2 dùng phạm vi tối thiểu bốn model; các ràng buộc của Review/Order thuộc thiết kế Bài 1.')
    story.append(PageBreak())
    p('Sơ đồ ERD – khóa và cardinality','Heading1')
    img=Image(str(ROOT/'erd.png'))
    img._restrictSize(760,440)
    story.append(img)
    p('PK: khóa chính; FK: khóa ngoại. 1 to 0..N: một phía cha có thể chưa có bản ghi con; 1 to 1..N: cần ít nhất một bản ghi con. BookAuthor biểu diễn quan hệ nhiều–nhiều.')
    story.append(PageBreak())
    p('Resource set và 20 endpoints','Heading1')
    p('Tất cả URL có tiền tố /api/v1. Bảng dưới là thiết kế hợp đồng API; chỉ GET /api/v1/books được triển khai trong Bài 2.')
    rows=[[Paragraph(x,styles['Normal']) for x in ['Method','URL','Resource','Chức năng']]]
    for item in json.loads((ROOT/'endpoints.json').read_text()):
        rows.append([Paragraph(escape(str(item[k])),styles['Normal']) for k in ['method','url','resource','description']])
    table=Table(rows,colWidths=[60,290,75,330],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce8f5')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.3,colors.grey),('LEFTPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(table)
    story.append(PageBreak())
    p('Các quyết định thiết kế resource','Heading1')
    p('Resource dùng danh từ số nhiều, URL viết thường, độ sâu vừa phải. BookAuthor không có endpoint riêng: client dùng author_ids trong biểu diễn Book. OrderItem là thành phần của Order và được tạo nguyên tử cùng đơn, tránh đơn dở dang.')
    p('Reviews được liệt kê/tạo dưới Book vì cần ngữ cảnh sách; cập nhật/xóa dùng /reviews/{review_id} vì ID đã xác định duy nhất. Danh sách sách của tác giả là phép nhìn theo quan hệ, không sao chép bảng junction thành API.')
    p('GET đọc dữ liệu (200); POST tạo mới (201 và Location); PATCH cập nhật một phần (200); DELETE thành công (204). Lỗi dữ liệu trả 400, thiếu resource trả 404, xung đột khóa hoặc xóa dữ liệu được tham chiếu trả 409. Các endpoint ghi dữ liệu cần xác thực và phân quyền; chúng thuộc thiết kế, chưa nằm trong phạm vi triển khai Bài 2.')
    p('JSON Schema Draft 2020-12','Heading2')
    p('Ba schema Book, Author, Review nằm trong schemas/. Mỗi schema có trường bắt buộc, giới hạn dữ liệu, khóa ID tái sử dụng qua $defs/$ref và từ chối thuộc tính lạ. FormatChecker kiểm tra URI và date-time. Đây là schema của resource đầy đủ, không phải payload PATCH; trường id và thời gian do server sinh. FK, ISBN checksum và quy tắc duy nhất theo database cần kiểm tra ở tầng ứng dụng/database.')
    p('Phân trang','Heading2')
    p('Offset trả total và phù hợp nhảy đến một vị trí; offset lớn khiến database phải bỏ qua nhiều hàng. Cursor lưu ranh giới cuối trang, truy vấn theo thứ tự từ điển và lấy limit + 1 hàng để xác định còn trang. ID làm khóa cuối bảo đảm không trùng/bỏ sót trong dataset tĩnh. Dữ liệu đổi khóa sort trong khi duyệt có thể làm thay đổi kết quả; cursor không cung cấp snapshot isolation.')
    SimpleDocTemplate(str(ROOT/'resource-design.pdf'),pagesize=landscape(A4),rightMargin=35,leftMargin=35,topMargin=30,bottomMargin=30).build(story)

if __name__ == '__main__':
    build()
