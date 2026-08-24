from flask import Flask
from flask import jsonify
from flask import request
from config import RESOURCE_INTERVAL
from resource_logging.resource_service import ResourceLoggerService

class ResourceServer:

    def __init__(self):
        self.app = Flask(__name__)

        self.logger_service = ResourceLoggerService(RESOURCE_INTERVAL)

        self.register_routes()

    def register_routes(self):
        @self.app.route(
            "/resource_logger/start",
            methods=["POST"]
        )
        def start_logger():
            payload = request.json
            execute_at = payload["execute_at"]

            self.logger_service.schedule_start(execute_at)

            return jsonify({
                "status": "scheduled"
            })

        @self.app.route(
            "/resource_logger/stop",
            methods=["POST"]
        )
        def stop_logger():
            payload = request.json
            execute_at = payload["execute_at"]

            self.logger_service.schedule_stop(execute_at)

            return jsonify({
                "status": "scheduled"
            })

        @self.app.route(
            "/resource_logger/status",
            methods=["GET"]
        )
        def status():
            return jsonify({
                "running": self.logger_service.running
            })

    def start(self):

        self.app.run(
            host="0.0.0.0",
            port=9200
        )

if __name__ == "__main__":
    server = ResourceServer()

    server.start()