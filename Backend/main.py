import logging
from werkzeug.serving import WSGIRequestHandler
from app import app


if __name__ == "__main__":
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    if app.config["DEBUG"]:
        logging.basicConfig(level=logging.DEBUG)
    app.run()
