from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

class BookAuthor(db.Model):
    __tablename__ = 'book_authors'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)

class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    books = db.relationship('Book', back_populates='category')

class Book(db.Model):
    __tablename__ = 'books'
    __table_args__ = (CheckConstraint('price >= 0'),)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category = db.relationship('Category', back_populates='books')
    authors = db.relationship('Author', secondary='book_authors', backref='books')

    def to_dict(self):
        return dict(id=self.id, title=self.title, isbn=self.isbn,
                    price=float(self.price), category_id=self.category_id,
                    genre=self.category.slug, author_ids=[a.id for a in self.authors])
