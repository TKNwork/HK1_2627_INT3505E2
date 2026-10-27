#!/usr/bin/env python3
"""Kiểm tra tài liệu SOA B6; không gọi hoặc chứng minh an toàn backend."""
from copy import deepcopy
from pathlib import Path
import re
import sys

try:
    import yaml
    from openapi_spec_validator import OpenAPIV30SpecValidator
    from openapi_schema_validator import OAS30Validator, oas30_format_checker
except ImportError as exc:
    raise SystemExit('Thiếu dependency. Chạy: .venv/bin/python -m pip install -r requirements-dev.txt') from exc

ROOT = Path(__file__).resolve().parents[1]


class UniqueKeyLoader(yaml.SafeLoader):
    """Tránh YAML silently ghi đè khóa trùng."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f'YAML key trùng: {key}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    spec = yaml.load((ROOT / 'openapi.yaml').read_text(encoding='utf-8'), Loader=UniqueKeyLoader)
    require(spec['openapi'] == '3.0.3', 'Phải dùng OpenAPI 3.0.3')
    print('PASS: parse YAML, không trùng khóa')
    OpenAPIV30SpecValidator(spec).validate()
    print('PASS: OpenAPIV30SpecValidator (3.0.3)')
    ref_count = 0

    def resolve(pointer):
        require(pointer.startswith('#/'), f'Không dùng ref ngoài tài liệu: {pointer}')
        result = spec
        for part in pointer[2:].split('/'):
            result = result[part.replace('~1', '/').replace('~0', '~')]
        return result

    def deref(node, stack=()):
        nonlocal ref_count
        if isinstance(node, list):
            return [deref(item, stack) for item in node]
        if not isinstance(node, dict):
            return node
        if '$ref' in node:
            pointer = node['$ref']
            require(pointer not in stack, f'Ref vòng chưa được hỗ trợ: {pointer}')
            ref_count += 1
            return deref(deepcopy(resolve(pointer)), stack + (pointer,))
        return {key: deref(value, stack) for key, value in node.items()}

    doc = deref(spec)
    print(f'PASS: resolve {ref_count} lượt $ref nội bộ')
    examples = 0

    def check_value(schema, value, location):
        nonlocal examples
        # OAS30Validator xử lý writeOnly theo schema hợp đồng, không bỏ required password.
        errors = list(OAS30Validator(schema, format_checker=oas30_format_checker).iter_errors(value))
        require(not errors, f'Ví dụ sai schema ở {location}: ' + '; '.join(e.message for e in errors))
        examples += 1

    def check_examples(node, location='root'):
        if isinstance(node, list):
            for i, child in enumerate(node):
                check_examples(child, f'{location}/{i}')
        elif isinstance(node, dict):
            if 'schema' in node:
                if 'example' in node:
                    check_value(node['schema'], node['example'], location)
                for name, example in node.get('examples', {}).items():
                    check_value(node['schema'], example['value'], f'{location}/{name}')
            if 'type' in node and 'example' in node:
                check_value(node, node['example'], location)
            for key, child in node.items():
                check_examples(child, f'{location}/{key}')

    check_examples(doc)
    print(f'PASS: {examples} ví dụ hợp schema/format')
    expected = {
        '/auth/login': ('post', {'200', '400', '401', '415', '429'}),
        '/auth/refresh': ('post', {'200', '400', '401', '415', '429'}),
        '/posts/{id}': ('get', {'200', '400', '401', '403', '404', '429'}),
    }
    require(set(doc['paths']) == set(expected), 'Phải có chính xác ba path theo đề')
    operation_ids = []
    for path, (method, statuses) in expected.items():
        require(set(doc['paths'][path]) == {method}, f'Sai method hoặc thừa operation: {path}')
        op = doc['paths'][path][method]
        operation_ids.append(op['operationId'])
        require(set(op['responses']) == statuses, f'Sai status: {path}')
        require(all(op.get(field) for field in ('description', 'summary', 'tags')), f'Thiếu mô tả: {path}')
        require(op['security'] == ([{'bearerAuth': []}] if method == 'get' else []), f'Security sai: {path}')
        require(op['x-required-scopes'] == (['posts:read'] if method == 'get' else []), f'Scope sai: {path}')
        for status, resp in op['responses'].items():
            schema = resp['content']['application/json']['schema']
            if status != '200':
                require(schema == doc['components']['schemas']['ErrorResponse'], f'Lỗi không thống nhất: {path}/{status}')
        if method == 'post':
            require(op['requestBody']['required'], f'Body phải required: {path}')
            require(set(op['requestBody']['content']) == {'application/json'}, f'Content-Type sai: {path}')
            response = op['responses']['200']
            require(response['headers']['Cache-Control']['example'] == 'no-store', 'Thiếu no-store')
            require(response['headers']['Pragma']['example'] == 'no-cache', 'Thiếu no-cache')
        else:
            param = op['parameters'][0]
            require(param['name'] == 'id' and param['in'] == 'path' and param['required'] is True, 'id phải path required')
            require(param['schema']['type'] == 'integer' and param['schema']['minimum'] == 1, 'ID phải integer dương')
            require('WWW-Authenticate' in op['responses']['401']['headers'], 'Thiếu Bearer challenge 401')
            require('insufficient_scope' in op['responses']['403']['headers']['WWW-Authenticate']['example'], 'Thiếu challenge scope 403')
            for resp in op['responses'].values():
                require(resp['headers']['Cache-Control']['example'] == 'no-store', 'GET phải no-store kể cả lỗi')
    require(len(set(operation_ids)) == 3, 'operationId trùng')
    schemes = doc['components']['securitySchemes']
    require(set(schemes) == {'bearerAuth'}, 'Chỉ khai báo Bearer cho access token')
    require((schemes['bearerAuth']['type'], schemes['bearerAuth']['scheme'], schemes['bearerAuth']['bearerFormat']) == ('http', 'bearer', 'JWT'), 'Bearer scheme sai')
    schemas = doc['components']['schemas']
    for name in ('LoginRequest', 'RefreshRequest', 'TokenResponse', 'UserSummary', 'Post', 'ErrorResponse'):
        require(name in schemas and schemas[name]['additionalProperties'] is False, f'Schema thiếu/cho phép field lạ: {name}')
    require(set(schemas['LoginRequest']['required']) == {'email', 'password'}, 'Thiếu required login')
    require(schemas['LoginRequest']['properties']['password']['writeOnly'] is True, 'Password phải writeOnly')
    require(schemas['RefreshRequest']['required'] == ['refresh_token'], 'Thiếu required refresh')
    for name in ('TokenResponse', 'UserSummary', 'Post'):
        require('password_hash' not in schemas[name]['properties'] and 'email' not in schemas[name]['properties'], f'Lộ field nội bộ: {name}')
    login_example = doc['paths']['/auth/login']['post']['responses']['200']['content']['application/json']['examples']['loginSuccess']['value']
    refresh_example = doc['paths']['/auth/refresh']['post']['responses']['200']['content']['application/json']['examples']['refreshSuccess']['value']
    for token_type in ('access_token', 'refresh_token'):
        require(login_example[token_type] != refresh_example[token_type], 'Ví dụ rotation phải cấp token khác')
        require(login_example[token_type].startswith('DEMO_ONLY_') and refresh_example[token_type].startswith('DEMO_ONLY_'), 'Ví dụ token phải minh họa không dùng được')
    require(login_example['refresh_expires_in'] - refresh_example['refresh_expires_in'] == 900, 'TTL ví dụ không khớp refresh sau 900 giây')
    print('PASS: endpoint/method/status/security/scope/schema/header/rotation examples')
    audit = (ROOT / 'SecurityAudit.md').read_text(encoding='utf-8')
    sections = re.split(r'^## SA-\d{2}: ', audit, flags=re.M)[1:]
    require(len(sections) >= 5, 'Audit cần >=5 điểm')
    fields = ('Endpoint/thành phần', 'Điều kiện/tình huống', 'Dữ liệu/quyền có thể lộ', 'Mức độ và lý do', 'Giảm thiểu', 'Cách kiểm tra', 'Trạng thái xác minh')
    for index, section in enumerate(sections, 1):
        require(all(re.search(r'(?:\*\*)?' + re.escape(field) + r':(?:\*\*)?', section) for field in fields), f'Audit thiếu thông tin: SA-{index:02d}')
        require('chưa kiểm chứng runtime' in section, 'Không được tuyên bố đã kiểm chứng runtime')
    print(f'PASS: {len(sections)} điểm audit đủ trường; checklist vẫn là dự kiến')
    print('OK: tài liệu hợp lệ. KHÔNG phải kết quả kiểm thử backend/runtime hoặc quét secret toàn bộ Git history.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
