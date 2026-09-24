"""integration checks for the local presentation endpoints."""

import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from exprscope_web import PresentationHandler


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), PresentationHandler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(timeout=5)

    def request(self, method, path, body=None, content_type='application/json'):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers={'Content-Type': content_type})
            response = connection.getresponse()
            return response.status, response.read().decode('utf-8')
        finally:
            connection.close()

    def test_page_and_examples(self):
        status, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn('Expression workspace', body)
        status, body = self.request('GET', '/api/examples')
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)), 12)

    def test_pipeline_and_recovery(self):
        for source, expected, stage in [('0 ^ -1', '', 'Runtime'),
                                        ('1 + true', '', 'Semantic'),
                                        ('2 + * 3', '', 'Syntax'),
                                        ('2 $ 3', '', 'Lexical'),
                                        ('6 * 7', '42 : Number', None)]:
            with self.subTest(source=source):
                status, body = self.request('POST', '/api/evaluate', json.dumps({'source': source}))
                self.assertEqual(status, 200)
                report = json.loads(body)
                self.assertEqual(report['stage'], stage)
                self.assertEqual(report['output'], expected)

    def test_invalid_requests(self):
        for body in ['{', '[]', '{}', '{"source": 1}']:
            with self.subTest(body=body):
                self.assertEqual(self.request('POST', '/api/evaluate', body)[0], 400)
        self.assertEqual(self.request('POST', '/api/evaluate', '{}', 'text/plain')[0], 415)
        self.assertEqual(self.request('POST', '/api/evaluate', 'x' * 100001)[0], 413)

    def test_unlisted_routes_do_not_expose_files(self):
        self.assertEqual(self.request('GET', '/exprscope.py')[0], 404)
        self.assertEqual(self.request('GET', '/../README.md')[0], 404)
        self.assertEqual(self.request('POST', '/unknown', '{}')[0], 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
