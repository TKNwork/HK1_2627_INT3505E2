import pytest
from app import create_app
from models import db, Book
from seed import seed_database

@pytest.fixture()
def client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'SECRET_KEY': 'test-only'})
    with app.app_context():
        seed_database()
        with app.test_client() as client:
            yield client
        db.session.remove()
        db.drop_all()

def get(client, **params):
    response = client.get('/api/v1/books', query_string=params)
    assert response.status_code == 200, response.json
    return response.json

def test_default_and_relationships(client):
    result = get(client)
    assert len(result['data']) == 10
    assert result['pagination'] == dict(offset=0, limit=10, total=60, has_next=True)
    assert all(len(b['author_ids']) == 2 and b['genre'] for b in result['data'])
    assert seed_database() == 0

def test_offset(client):
    first = get(client, limit=7)['data']
    second = get(client, offset=7, limit=7)['data']
    assert [b['id'] for b in first + second] == list(range(1, 15))

@pytest.mark.parametrize('sort', ['price', '-price', 'title', '-price,title', 'title,-price', '-title,price', '-price,-title,-id'])
@pytest.mark.parametrize('genre', [None, 'technology'])
def test_full_cursor_traversal(client, sort, genre):
    params = {'sort': sort}
    if genre:
        params['genre'] = genre
    expected = get(client, limit=100, **params)['data']
    # Independently compute the requested order using stable Python sorts.
    independent = get(client, limit=100, **({'genre': genre} if genre else {}))['data']
    keys = sort.split(',')
    if not any(k.lstrip('-') == 'id' for k in keys):
        keys.append('id')
    for key in reversed(keys):
        independent.sort(key=lambda b: b[key.lstrip('-')], reverse=key.startswith('-'))
    assert expected == independent
    seen, cursor = [], None
    for _ in range(61):
        page = get(client, strategy='cursor', limit=7, **params, **({'cursor': cursor} if cursor else {}))
        seen.extend(page['data'])
        cursor = page['page_info']['next_cursor']
        assert bool(cursor) == page['page_info']['has_more']
        if not cursor:
            break
    else:
        pytest.fail('Cursor did not terminate')
    assert seen == expected
    assert len({b['id'] for b in seen}) == len(seen)
    assert len(seen) == (20 if genre else 60)

def test_filter_and_last_page(client):
    result = get(client, genre='technology', offset=18, limit=7, sort='-price,title')
    assert len(result['data']) == 2
    assert all(b['genre'] == 'technology' for b in result['data'])
    assert result['pagination']['total'] == 20
    assert result['pagination']['has_next'] is False
    assert get(client, offset=100)['data'] == []

@pytest.mark.parametrize('strategy', ['offset', 'cursor'])
def test_empty(client, strategy):
    result = get(client, genre='nonexistent', strategy=strategy)
    assert result['data'] == []
    if strategy == 'cursor':
        assert result['page_info'] == {'next_cursor': None, 'has_more': False}
    else:
        assert result['pagination']['total'] == 0
        assert result['pagination']['has_next'] is False

@pytest.mark.parametrize('query', [
    'limit=0','limit=-1','limit=101','limit=abc','limit=1.5',
    'offset=-1','offset=x','strategy=bad','sort=unknown','sort=',
    'sort=price,price','sort=id,price','sort=price;DROP TABLE books',
    'strategy=cursor&cursor=bad','strategy=cursor&cursor=',
    'strategy=cursor&offset=0','cursor=bad','genre=', 'limit=2&limit=3','foo=bar'])
def test_invalid(client, query):
    response = client.get('/api/v1/books?' + query)
    assert response.status_code == 400
    assert response.json['error']['code'] == 'invalid_parameters'
    assert response.json['error']['message']

@pytest.mark.parametrize('changed', [{'sort': '-price'}, {'genre': 'fiction'}])
def test_cursor_context(client, changed):
    cursor = get(client, strategy='cursor', sort='price', genre='technology')['page_info']['next_cursor']
    params = dict(strategy='cursor', sort='price', genre='technology', cursor=cursor)
    params.update(changed)
    assert client.get('/api/v1/books', query_string=params).status_code == 400

def test_tampered_cursor(client):
    token = get(client, strategy='cursor')['page_info']['next_cursor']
    token = ('A' if token[0] != 'A' else 'B') + token[1:]
    assert client.get('/api/v1/books', query_string={'strategy': 'cursor', 'cursor': token}).status_code == 400

def test_cursor_survives_boundary_deletion(client):
    page = get(client, strategy='cursor', limit=7, sort='-price,title')
    expected = get(client, limit=100, sort='-price,title')['data'][7:14]
    db.session.delete(db.session.get(Book, page['data'][-1]['id']))
    db.session.commit()
    following = get(client, strategy='cursor', limit=7, sort='-price,title', cursor=page['page_info']['next_cursor'])
    assert following['data'] == expected
