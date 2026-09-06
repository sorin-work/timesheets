import json
import logging

from timesheets.logs import JsonFormatter


def test_json_log_lines():
    record = logging.LogRecord("timesheets", logging.INFO, __file__, 1, "GET %s", ("/api",), None)
    line = json.loads(JsonFormatter().format(record))
    assert line["level"] == "info"
    assert line["message"] == "GET /api"
    assert line["time"].endswith("+00:00")
