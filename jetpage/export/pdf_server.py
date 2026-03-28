"""Minimal background HTTP server that serves generated PDF files for download.

A single global instance is started when the app boots. The PDF exporter
writes files into the server's temp directory, then returns a URL that
page.launch_url() can open to trigger a browser download.
"""

import http.server
import tempfile
import threading
from pathlib import Path


class _Handler(http.server.BaseHTTPRequestHandler):
    """Serve PDF files from the temp directory."""

    _temp_dir: Path  # set on the class before each server is created

    def do_GET(self) -> None:
        filename = self.path.lstrip("/")
        file_path = self.__class__._temp_dir / filename

        if file_path.exists() and file_path.suffix == ".pdf":
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:  # suppress access logs
        pass


class PdfServer:
    def __init__(self) -> None:
        self._temp_dir = Path(tempfile.mkdtemp(prefix="jetpage_pdf_"))
        self._port: int | None = None

    def start(self) -> None:
        """Start the server on an OS-assigned port (called once at app boot)."""
        # Bind the temp dir into the handler class
        _Handler._temp_dir = self._temp_dir

        server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        self._port = server.server_address[1]

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

    def store(self, doc_id: str, data: bytes) -> str:
        """Write PDF bytes to the temp dir and return the download URL."""
        if self._port is None:
            raise RuntimeError("PdfServer has not been started.")
        filename = f"{doc_id}.pdf"
        (self._temp_dir / filename).write_bytes(data)
        return f"http://127.0.0.1:{self._port}/{filename}"


# Global singleton used by the exporter and app shell
pdf_server = PdfServer()
