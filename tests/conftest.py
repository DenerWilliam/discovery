import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from playwright.sync_api import sync_playwright


def _make_handler(routes):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = routes.get(self.path.split("?")[0])
            if route is None:
                self.send_response(404)
                self.end_headers()
                return
            if isinstance(route, tuple) and route[0] == "redirect":
                self.send_response(302)
                self.send_header("Location", route[1])
                self.end_headers()
                return
            headers = {}
            if isinstance(route, tuple) and route[0] == "page":  # ("page", corpo, {cabeçalhos})
                _, route, headers = route
            body = route.encode()
            self.send_response(200)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Type", headers.get("Content-Type", "text/html; charset=utf-8"))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


@pytest.fixture
def serve():
    """Sobe um servidor local com as rotas dadas; devolve a URL base."""
    servers = []

    def start(routes):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler(routes))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}"

    yield start
    for server in servers:
        server.shutdown()


@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        yield context
        browser.close()
