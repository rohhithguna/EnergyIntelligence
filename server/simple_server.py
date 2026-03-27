import http.server
import json
import mimetypes
import os
import re
import sys
import tempfile
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_pipeline
from domain_mapper import apply_column_mapping
from core.ai_engine import analyze_with_claude


LAST_RESULT = None
REPORT_HISTORY = []


def load_domain_schemas():
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schemas_path = os.path.join(project_root, "domains.json")
        with open(schemas_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def validate_dataset_against_domain(df, domain):
    """Validate that a dataset has required columns for a domain."""
    schemas = load_domain_schemas()
    
    if domain == "generic" or domain not in schemas:
        return True, None
    
    schema = schemas[domain]
    required = schema.get("required", [])
    
    df_columns = set(df.columns)
    df_columns_lower = set(col.lower() for col in df.columns)
    
    missing = []
    for req in required:
        req_lower = req.lower()
        if req not in df_columns and req_lower not in df_columns_lower:
            missing.append(req)
    
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    
    return True, None


def parse_multipart(body, content_type):
    boundary_match = re.search(r"boundary=([^;]+)", content_type)
    if not boundary_match:
        raise ValueError("Invalid multipart boundary")

    boundary = boundary_match.group(1).strip().strip('"').encode()
    parts = body.split(b"--" + boundary)

    file_item = None
    domain = "generic"

    for raw_part in parts:
        part = raw_part.strip()
        if not part or part == b"--":
            continue

        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        headers = part[:header_end].decode("utf-8", errors="ignore")
        content = part[header_end + 4 :]
        if content.endswith(b"\r\n"):
            content = content[:-2]

        disposition_line = next(
            (h for h in headers.split("\r\n") if h.lower().startswith("content-disposition:")),
            "",
        )
        name_match = re.search(r'name="([^"]+)"', disposition_line)
        filename_match = re.search(r'filename="([^"]*)"', disposition_line)

        if not name_match:
            continue

        field_name = name_match.group(1)
        filename = filename_match.group(1) if filename_match else ""

        if filename and field_name in ["file", "files"]:
            file_item = {"filename": filename, "content": content}
        elif field_name == "domain" and not filename:
            domain = content.decode("utf-8", errors="ignore").strip()

    return file_item, domain


def build_comparison(reports):
    if len(reports) < 2:
        return {
            "available": False,
            "message": "Upload at least two datasets for comparison.",
            "summary": "Not enough datasets for comparison.",
            "items": [],
        }

    items = []
    for report in reports:
        distribution = report.get("distribution", {})
        counts = report.get("counts", {})
        items.append(
            {
                "dataset": report.get("dataset_name", "Dataset"),
                "stability": report.get("system_stability", "unknown"),
                "risk": report.get("risk", "unknown"),
                "anomalies": int(counts.get("anomalies", 0)),
                "variance": float(distribution.get("variance", 0.0)),
                "quality": int(report.get("quality", 0)),
                "confidence": int(report.get("confidence", {}).get("score", 0)),
            }
        )

    safest = sorted(items, key=lambda x: (x["anomalies"], x["variance"], -x["quality"]))[0]
    riskiest = sorted(items, key=lambda x: (-x["anomalies"], -x["variance"], x["quality"]))[0]

    summary = (
        f"{safest['dataset']} is more stable than {riskiest['dataset']} due to fewer anomalies "
        f"and lower variance."
    )

    return {
        "available": True,
        "message": "Comparison generated.",
        "summary": summary,
        "items": items,
        "most_stable": safest["dataset"],
        "highest_risk": riskiest["dataset"],
    }


class AnalysisHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        global LAST_RESULT

        if self.path == "/api/ai-analysis":
            self.handle_ai_analysis_request()
            return

        if self.path not in ["/analyze", "/upload"]:
            self.send_json(404, {"error": "Endpoint not found"})
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_json(400, {"error": "Invalid content type"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            file_item, domain = parse_multipart(body, content_type)

            if not file_item:
                self.send_json(400, {"error": "No file uploaded"})
                return

            temp_file = tempfile.NamedTemporaryFile(
                suffix=os.path.splitext(file_item["filename"])[1] or ".csv",
                delete=False,
            )
            temp_file.write(file_item["content"])
            temp_file.close()

            try:
                import pandas as pd
                
                file_ext = os.path.splitext(file_item["filename"])[1].lower()
                
                if file_ext == ".csv":
                    df = pd.read_csv(temp_file.name)
                elif file_ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(temp_file.name)
                else:
                    df = pd.read_csv(temp_file.name)
                
                # Apply domain-specific column mapping with fallback to generic
                df, mapped_column = apply_column_mapping(df, domain)
                
                # Validate that we have data_rate column after mapping
                if "data_rate" not in df.columns:
                    # Fallback: try generic domain
                    if domain != "generic":
                        df, mapped_column = apply_column_mapping(df, "generic")
                        if "data_rate" not in df.columns:
                            self.send_json(
                                400,
                                {
                                    "error": f"No numeric column found. Please ensure your dataset has numeric columns like data_rate, bytes_transferred, or response_time.",
                                    "validation_error": True,
                                }
                            )
                            return
                        domain = "generic"  # Update domain to generic
                    else:
                        self.send_json(
                            400,
                            {
                                "error": "No numeric column found for analysis. Please check your dataset.",
                                "validation_error": True,
                            }
                        )
                        return
                
                # Save mapped dataframe back to temp file so pipeline reads correct columns
                df.to_csv(temp_file.name, index=False)
                
                result = run_pipeline(temp_file.name)
                result["dataset_name"] = file_item["filename"]
                result["domain"] = domain
                if mapped_column:
                    result["column_mapped"] = f"{mapped_column} → data_rate"
                LAST_RESULT = result
                REPORT_HISTORY.append(result)
                self.send_json(200, result)
            finally:
                os.unlink(temp_file.name)
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})

    def handle_ai_analysis_request(self):
        try:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                self.send_json(400, {"error": "Content-Type must be application/json"})
                return

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self.send_json(400, {"error": "Request body is empty"})
                return

            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
            if not isinstance(payload, dict):
                self.send_json(400, {"error": "Invalid payload format"})
                return

            data = payload.get("data")
            if not isinstance(data, dict):
                self.send_json(400, {"error": "Invalid data payload"})
                return

            ai_analysis = analyze_with_claude(data)
            self.send_json(200, {"ai_analysis": ai_analysis})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Malformed JSON payload"})
        except RuntimeError as exc:
            if str(exc) == "Anthropic API key not configured":
                self.send_json(503, {"error": "AI service not configured"})
                return
            self.send_json(500, {"error": str(exc)})
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})

    def do_GET(self):
        if self.path == "/api/latest":
            if LAST_RESULT is None:
                self.send_json(404, {"error": "No analysis result available"})
                return
            self.send_json(200, LAST_RESULT)
            return

        if self.path == "/api/compare":
            self.send_json(200, build_comparison(REPORT_HISTORY))
            return

        if self.path == "/domains.json":
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            schemas_path = os.path.join(project_root, "domains.json")
            if os.path.isfile(schemas_path):
                with open(schemas_path, "r") as f:
                    content = f.read().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Content-length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404)
                return

        self.serve_static_file(unquote(self.path))

    def serve_static_file(self, path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        frontend_dir = os.path.join(project_root, "frontend")

        if path in ["/", ""]:
            relative = "index.html"
        else:
            relative = path.lstrip("/")

        target = os.path.normpath(os.path.join(frontend_dir, relative))
        if not target.startswith(frontend_dir):
            self.send_error(403)
            return

        if not os.path.isfile(target):
            self.send_error(404)
            return

        content_type, _ = mimetypes.guess_type(target)
        if content_type is None:
            content_type = "application/octet-stream"

        with open(target, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def run_server(host="127.0.0.1", port=8000):
    server = http.server.HTTPServer((host, port), AnalysisHandler)
    print(f"Server running at http://{host}:{port}/")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == "__main__":
    run_server()
