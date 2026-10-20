import os
from flask import Flask, jsonify
from sqlalchemy import event
from sqlalchemy.engine import Engine
from models import db

@event.listens_for(Engine, 'connect')
def enable_foreign_keys(connection, _):
    cursor = connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()

def create_app(config=None):
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///bookstore.db',
                      SQLALCHEMY_TRACK_MODIFICATIONS=False,
                      SECRET_KEY=os.environ.get('BOOKSTORE_SECRET', 'local-homework-only'))
    if config:
        app.config.update(config)
    db.init_app(app)
    from routes.books import books
    app.register_blueprint(books)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(error={'code': 'invalid_parameters', 'message': error.description}), 400
    return app

if __name__ == '__main__':
    create_app().run()
