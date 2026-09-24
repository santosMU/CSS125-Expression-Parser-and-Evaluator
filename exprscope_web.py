"""local presentation server using only the python standard library."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import webbrowser

from exprscope import DEMO_CASES, build_report, diagnostic, error_stage


class PresentationHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def respond(self, status, payload, content_type='application/json; charset=utf-8'):
        data = payload.encode('utf-8') if isinstance(payload, str) else json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/':
            try:
                page = Path(__file__).with_name('presentation.html').read_text(encoding='utf-8')
            except OSError:
                self.respond(500, {'error': 'presentation.html is missing from the project folder.'})
                return
            self.respond(200, page, 'text/html; charset=utf-8')
        elif self.path == '/api/examples':
            self.respond(200, [{'title': title, 'source': source, 'lesson': lesson}
                               for title, source, _, lesson in DEMO_CASES])
        else:
            self.respond(404, {'error': 'Not found.'})

    def do_POST(self):
        if self.path != '/api/evaluate':
            self.respond(404, {'error': 'Not found.'})
            return
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            self.respond(415, {'error': 'Expected application/json.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 100000:
                self.respond(413, {'error': 'Request body is too large or empty.'})
                return
            body = json.loads(self.rfile.read(length))
            source = body.get('source') if isinstance(body, dict) else None
            if not isinstance(source, str):
                raise ValueError('The source must be a string.')
        except (ValueError, UnicodeError) as exc:
            self.respond(400, {'error': str(exc)})
            return
        report = build_report(source)
        self.respond(200, {
            'tokens': report.tokens, 'ast': report.ast, 'semantics': report.semantics,
            'trace': report.trace, 'output': report.output, 'report': report.render(),
            'error': diagnostic(source, report.error) if report.error else None,
            'stage': error_stage(report.error) if report.error else None,
        })


def main(argv=None):
    parser = argparse.ArgumentParser(description='Open the local ExprScope presentation.')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args(argv)
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), PresentationHandler)
    except OSError as exc:
        parser.exit(1, f'Cannot start presentation: {exc}\nTry --port 8766.\n')
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'ExprScope presentation: {url}\nPress Ctrl+C to stop.', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nPresentation stopped.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
