from decimal import Decimal
from app import create_app
from models import db, Book, Author, Category

def seed_database():
    db.create_all()
    if db.session.scalar(db.select(Book.id).limit(1)) is not None:
        return 0
    categories = [Category(name=name, slug=slug) for name, slug in
                  [('Công nghệ', 'technology'), ('Văn học', 'fiction'), ('Khoa học', 'science')]]
    authors = [Author(name=f'Tác giả {i}') for i in range(1, 7)]
    db.session.add_all(categories + authors)
    db.session.flush()
    for i in range(60):
        book = Book(title=f'Book {i % 15:02d}', isbn=f'{9780000000000+i}',
                    price=Decimal(10 + (i % 8) * 5), category=categories[i % 3],
                    authors=[authors[i % 6], authors[(i + 1) % 6]])
        db.session.add(book)
    db.session.commit()
    return 60

if __name__ == '__main__':
    with create_app().app_context():
        print(f'Inserted {seed_database()} books (existing data preserved).')
