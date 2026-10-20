from decimal import Decimal, InvalidOperation
from flask import Blueprint, abort, current_app, jsonify, request
from itsdangerous import URLSafeSerializer, BadData
from sqlalchemy import and_, or_, select, func
from sqlalchemy.orm import selectinload
from models import Book, Category, db

books = Blueprint('books', __name__)
FIELDS = {'id': Book.id, 'price': Book.price, 'title': Book.title}

def fail(message):
    abort(400, description=message)

def integer(name, default, minimum, maximum=None):
    value = request.args.get(name, str(default))
    if len(value) > 10 or not value.isascii() or not value.isdigit():
        fail(f'{name} must be an integer >= {minimum}')
    number = int(value)
    if number < minimum or (maximum is not None and number > maximum):
        fail(f'{name} must be between {minimum} and {maximum or "infinity"}')
    return number

@books.get('/api/v1/books')
def list_books():
    for key in request.args:
        if key not in {'strategy', 'limit', 'offset', 'genre', 'sort', 'cursor'}:
            fail(f'Unknown parameter: {key}')
        if len(request.args.getlist(key)) != 1:
            fail(f'Duplicate parameter: {key}')
    strategy = request.args.get('strategy', 'offset')
    if strategy not in {'offset', 'cursor'}:
        fail('strategy must be offset or cursor')
    limit = integer('limit', 10, 1, 100)
    offset = integer('offset', 0, 0)
    if strategy == 'cursor' and 'offset' in request.args:
        fail('offset cannot be used with cursor strategy')
    if strategy == 'offset' and 'cursor' in request.args:
        fail('cursor requires cursor strategy')
    genre = request.args.get('genre')
    if genre is not None and (not genre or len(genre) > 80):
        fail('genre must be a nonempty category slug, maximum 80 characters')
    sorting = []
    for token in request.args.get('sort', 'id').split(','):
        name = token[1:] if token.startswith('-') else token
        if name not in FIELDS or name in [n for n, _ in sorting]:
            fail('sort allows unique fields: id, price, title; prefix - for descending')
        sorting.append((name, token.startswith('-')))
    # ID must be last: it guarantees a unique, deterministic ordering.
    if any(n == 'id' for n, _ in sorting[:-1]):
        fail('id must be the last sort field')
    if not any(n == 'id' for n, _ in sorting):
        sorting.append(('id', False))
    query = select(Book).options(selectinload(Book.authors), selectinload(Book.category))
    if genre is not None:
        query = query.join(Category).where(Category.slug == genre)
    serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='books-cursor-v1')
    context = {'sort': [[n, d] for n, d in sorting], 'genre': genre}
    if 'cursor' in request.args:
        try:
            payload = serializer.loads(request.args['cursor'])
            if not isinstance(payload, dict) or payload.get('v') != 1 or payload.get('context') != context:
                raise ValueError()
            values = payload['values']
            if not isinstance(values, list) or len(values) != len(sorting):
                raise ValueError()
            converted = []
            for (name, _), value in zip(sorting, values):
                if name == 'price':
                    if not isinstance(value, str):
                        raise ValueError()
                    value = Decimal(value)
                    if not value.is_finite() or value < 0:
                        raise ValueError()
                elif name == 'id':
                    if type(value) is not int or value < 1:
                        raise ValueError()
                elif not isinstance(value, str) or len(value) > 200:
                    raise ValueError()
                converted.append(value)
        except (BadData, ValueError, KeyError, TypeError, InvalidOperation):
            fail('Invalid cursor or cursor incompatible with current sort/genre')
        # Lexicographic predicate: equal prefix, then compare the next key.
        branches = []
        for i, (name, descending) in enumerate(sorting):
            prefix = [FIELDS[sorting[j][0]] == converted[j] for j in range(i)]
            comparison = FIELDS[name] < converted[i] if descending else FIELDS[name] > converted[i]
            branches.append(and_(*prefix, comparison))
        query = query.where(or_(*branches))
    query = query.order_by(*[FIELDS[n].desc() if d else FIELDS[n].asc() for n, d in sorting])
    if strategy == 'offset':
        count = select(func.count()).select_from(Book)
        if genre is not None:
            count = count.join(Category).where(Category.slug == genre)
        total = db.session.scalar(count)
        rows = db.session.scalars(query.offset(offset).limit(limit)).all()
        return jsonify(data=[b.to_dict() for b in rows], pagination={
            'offset': offset, 'limit': limit, 'total': total, 'has_next': offset + len(rows) < total})
    rows = db.session.scalars(query.limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    cursor = None
    if has_more:
        values = [str(getattr(rows[-1], n)) if n == 'price' else getattr(rows[-1], n) for n, _ in sorting]
        cursor = serializer.dumps({'v': 1, 'context': context, 'values': values})
    return jsonify(data=[b.to_dict() for b in rows], page_info={'next_cursor': cursor, 'has_more': has_more})
