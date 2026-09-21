BEGIN TRANSACTION;
CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT,
                price REAL
            );
INSERT INTO "books" VALUES(1,'Clean Code','R. Martin','9780132350884',45.0);
INSERT INTO "books" VALUES(2,'Refactoring','M. Fowler','9780201485677',55.0);
INSERT INTO "books" VALUES(3,'Flask Web Development','M. Grinberg','9781491991732',40.0);
INSERT INTO "books" VALUES(4,'Clean Architecture','R. Martin','9780134494166',50.0);
CREATE TABLE orders (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL
            );
INSERT INTO "orders" VALUES('1','pending');
INSERT INTO "orders" VALUES('2','shipped');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('books',4);
COMMIT;