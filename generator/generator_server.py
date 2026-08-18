from flask import Flask
from flask import jsonify
from flask import request

from generator.task_generator import TaskGenerator


class GeneratorServer:

    def __init__(self):

        self.app = Flask(__name__)

        self.generator = TaskGenerator()

        self.register_routes()

    # =====================================
    # Routes
    # =====================================

    def register_routes(self):

        @self.app.route(
            "/generator/start",
            methods=["POST"]
        )
        def start_generator():

            data = request.json

            rate = float(
                data.get("rate", 1)
            )

            self.generator.set_rate(rate)

            self.generator.start()

            return jsonify({
                "status": "started",
                "rate": rate
            })

        @self.app.route(
            "/generator/stop",
            methods=["POST"]
        )
        def stop_generator():

            self.generator.stop()

            return jsonify({
                "status": "stopped"
            })

        @self.app.route(
            "/generator/set_rate",
            methods=["POST"]
        )
        def set_rate():

            data = request.json

            rate = float(
                data["rate"]
            )

            self.generator.set_rate(rate)

            return jsonify({
                "status": "updated",
                "rate": rate
            })

        @self.app.route(
            "/generator/status",
            methods=["GET"]
        )
        def status():

            return jsonify(
                self.generator.get_status()
            )

    # =====================================
    # Start Server
    # =====================================

    def start(self):

        self.app.run(
            host="0.0.0.0",
            port=9100
        )


if __name__ == "__main__":

    server = GeneratorServer()

    server.start()