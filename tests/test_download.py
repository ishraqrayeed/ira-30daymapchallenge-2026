"""Exercise the outgoing download filter with a SQL engine and a fake API."""

import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.analysis.crashes import DETAIL_FIELDS, FIELDS


class DownloadFilter(unittest.TestCase):
    def test_details_enrich_existing_core_cache_and_request_available_fields_only(self):
        script = Path(__file__).resolve().parents[1] / 'maps/day01-points/download_data.py'
        spec = importlib.util.spec_from_file_location('day01_details_download', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / f'data/raw/day01/{module.CACHE_PREFIX}-2025.json'
            target.parent.mkdir(parents=True)
            target.write_text('{"features": []}')
            fields_sent = []

            def fake_get_json(session, url, **params):
                if not url.endswith('/query'):
                    return {'fields': [{'name': field} for field in FIELDS + ['incident_address']],
                            'objectIdField': 'object_id', 'maxRecordCount': 2}
                return {'objectIds': [7]}

            def fake_post_json(session, url, **params):
                fields_sent.extend(params['outFields'].split(','))
                return {'spatialReference': {'wkid': 4326}, 'features': [
                    {'attributes': {'object_id': 7, 'incident_address': 'A / B'}}]}

            with patch.object(module, 'ROOT', root), \
                 patch.object(module, 'get_json', side_effect=fake_get_json), \
                 patch.object(module, 'post_json', side_effect=fake_post_json) as post, \
                 patch.object(module, 'http_session', return_value=MagicMock()):
                self.assertEqual(module.download(2025, details=True), target)
                module.download(2025, details=True)
                self.assertEqual(post.call_count, 1)  # enriched cache reused
            self.assertIn('incident_address', fields_sent)
            self.assertNotIn('LIGHT_CONDITION', fields_sent)
            manifest = json.loads(target.with_name(f'{module.CACHE_PREFIX}-manifest-2025.json').read_text())
            self.assertTrue(manifest['details_requested'])
            self.assertEqual(manifest['detail_fields'], ['incident_address'])
            self.assertIn('LIGHT_CONDITION', manifest['unavailable_detail_fields'])

    def test_query_includes_count_and_offense_severity_and_preserves_scope(self):
        script = Path(__file__).resolve().parents[1] / 'maps/day01-points/download_data.py'
        spec = importlib.util.spec_from_file_location('day01_download', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with sqlite3.connect(':memory:') as database, tempfile.TemporaryDirectory() as directory:
            database.execute('''CREATE TABLE crashes (
                object_id INTEGER, first_occurrence_date TEXT, FATALITIES INTEGER,
                SERIOUSLY_INJURED INTEGER, top_traffic_accident_offense TEXT,
                pedestrian_ind INTEGER, bicycle_ind INTEGER)''')
            database.executemany('INSERT INTO crashes VALUES (?, ?, ?, ?, ?, ?, ?)', [
                (1, '2025-03-01 12:00:00', 1, 0, None, 1, 0),
                (2, '2025-03-01 12:00:00', 0, 0, 'TRAF - ACCIDENT - FATAL ', 0, 1),
                (3, '2025-03-01 12:00:00', None, None, ' TRAF - ACCIDENT - SBI ', 1, 1),
                (4, '2025-03-01 12:00:00', 0, 0, 'TRAF - ACCIDENT ', 1, 0),
                (5, '2025-03-01 12:00:00', 1, 0, 'TRAF - ACCIDENT - FATAL ', 0, 0),
                (6, '2024-12-31 23:00:00', 1, 0, 'TRAF - ACCIDENT - FATAL ', 1, 0),
            ])
            sent_queries = []

            def fake_get_json(session, url, **params):
                if not url.endswith('/query'):
                    return {'fields': [{'name': field} for field in FIELDS],
                            'objectIdField': 'object_id', 'maxRecordCount': 2}
                if params.get('returnIdsOnly') == 'true':
                    where = params['where']
                    sent_queries.append(where)
                    self.assertNotIn('TRIM(', where)
                    # SQLite needs date literals without ArcGIS's TIMESTAMP keyword.
                    selected = database.execute(
                        'SELECT object_id FROM crashes WHERE ' + where.replace('TIMESTAMP ', ''))
                    return {'objectIds': [row[0] for row in selected]}
                return {'spatialReference': {'wkid': 4326},
                        'features': [{'attributes': {'object_id': int(value)}}
                                     for value in params['objectIds'].split(',')]}

            with patch.object(module, 'ROOT', Path(directory)), \
                 patch.object(module, 'get_json', side_effect=fake_get_json), \
                 patch.object(module, 'post_json', side_effect=fake_get_json) as post_query, \
                 patch.object(module, 'http_session', return_value=MagicMock()):
                target = module.download(2025)
            self.assertEqual(post_query.call_count, 2)  # 3 records, server page limit 2
            self.assertEqual(post_query.call_args_list[0].kwargs['objectIds'], '1,2')
            self.assertEqual(post_query.call_args_list[1].kwargs['objectIds'], '3')
            snapshot = json.loads(target.read_text())
            self.assertEqual([f['attributes']['object_id'] for f in snapshot['features']], [1, 2, 3])
            manifest = json.loads(target.with_name(f'{module.CACHE_PREFIX}-manifest-2025.json').read_text())
            self.assertEqual(manifest['where'], sent_queries[0])
            self.assertEqual(manifest['rows'], 3)

    def test_large_id_query_uses_post_body_and_checks_api_errors(self):
        import requests
        from urllib.parse import parse_qs
        from src.data.download import post_json

        url = 'https://example.test/FeatureServer/325/query'
        ids = ','.join(str(323100000 + i) for i in range(500))
        requests_seen = []

        def fake_send(request, **kwargs):
            requests_seen.append(request)
            response = requests.Response()
            response.status_code = 200
            response._content = b'{"features": []}'
            return response

        with requests.Session() as session, patch.object(session, 'send', side_effect=fake_send):
            self.assertEqual(post_json(session, url, f='json', objectIds=ids), {'features': []})
        request = requests_seen[0]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(parse_qs(request.body)['objectIds'], [ids])
        self.assertEqual(request.headers['Content-Type'], 'application/x-www-form-urlencoded')

        response = MagicMock()
        response.json.return_value = {'error': {'code': 400, 'message': 'bad query'}}
        session = MagicMock()
        session.post.return_value = response
        with self.assertRaises(ValueError):
            post_json(session, url, f='json', objectIds=ids)
        response.raise_for_status.assert_called_once()
