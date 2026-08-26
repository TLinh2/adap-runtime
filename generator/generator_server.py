from flask import Flask
from flask import jsonify
from flask import request

from generator.task_generator import (
    TaskGenerator
)


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

            payload = request.json

            rate = payload["rate"]

            execute_at = payload[
                "execute_at"
            ]

            mode = payload["mode"]

            self.generator.schedule_start(
                rate=rate,
                execute_at=execute_at,
                mode=mode
            )

            return jsonify({
                "status": "scheduled",
                "rate": rate,
                "execute_at": execute_at,
                "mode": mode
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
            "/generator/schedule_stop",
            methods=["POST"]
        )
        def stop_generator():
            payload = request.json

            execute_at = payload["execute_at"]

            self.generator.schedule_stop(execute_at=execute_at)

            return jsonify({
                "status": "stopped",
                "execute_at": execute_at
            })
        

        @self.app.route(
            "/generator/set_rate",
            methods=["POST"]
        )
        def set_rate():

            payload = request.json

            rate = payload["rate"]

            execute_at = payload[
                "execute_at"
            ]

            self.generator.schedule_rate_update(
                rate=rate,
                execute_at=execute_at
            )

            return jsonify({
                "status": "scheduled",
                "rate": rate,
                "execute_at": execute_at
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