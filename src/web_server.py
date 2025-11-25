"""
Web server for serving React frontend and API endpoints
Provides connection details for LiveKit voice agents
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

try:
    import jwt
except ImportError:
    from jose import jwt

logger = logging.getLogger("web_server")


def create_app(
    livekit_api_key: str,
    livekit_api_secret: str,
    livekit_url: str,
    static_files_path: Optional[str] = None,
) -> Flask:
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder=None, static_url_path="")

    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Store configuration in app context
    app.config["LIVEKIT_API_KEY"] = livekit_api_key
    app.config["LIVEKIT_API_SECRET"] = livekit_api_secret
    app.config["LIVEKIT_URL"] = livekit_url
    app.config["STATIC_FILES_PATH"] = static_files_path

    @app.route("/api/connection-details", methods=["POST"])
    def connection_details():
        """Generate LiveKit connection details for frontend"""
        try:
            # Parse agent configuration from request body
            data = request.get_json() or {}
            # Note: agent_name could be used for agent selection if needed
            # agent_name = data.get("room_config", {}).get("agents", [{}])[0].get("agent_name")

            # Generate participant token
            participant_name = "user"
            participant_identity = f"voice_assistant_user_{os.urandom(2).hex()}"
            room_name = f"voice_assistant_room_{os.urandom(2).hex()}"

            # Create JWT token manually for LiveKit
            now = int(time.time())
            ttl = 15 * 60  # 15 minutes

            payload = {
                "iss": app.config["LIVEKIT_API_KEY"],
                "sub": participant_identity,
                "name": participant_name,
                "iat": now,
                "exp": now + ttl,
                "nbf": now,
                "video": {
                    "canPublish": True,
                    "canPublishData": True,
                    "canSubscribe": True,
                    "room": room_name,
                    "roomJoin": True,
                },
            }

            participant_token = jwt.encode(
                payload,
                app.config["LIVEKIT_API_SECRET"],
                algorithm="HS256",
            )

            # Ensure token is a string (jwt.encode might return bytes in some versions)
            if isinstance(participant_token, bytes):
                participant_token = participant_token.decode("utf-8")

            # Return connection details
            return jsonify(
                {
                    "serverUrl": app.config["LIVEKIT_URL"],
                    "roomName": room_name,
                    "participantToken": participant_token,
                    "participantName": participant_name,
                }
            )
        except Exception as e:
            logger.error(f"Error generating connection details: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        return jsonify({"status": "ok"})

    # Serve static files if configured
    if static_files_path and os.path.isdir(static_files_path):
        static_path = Path(static_files_path)

        @app.route("/", defaults={"path": ""}, methods=["GET"])
        @app.route("/<path:path>", methods=["GET"])
        def serve_frontend(path):
            """Serve React frontend with SPA routing fallback"""
            # Don't serve files for API routes
            if path.startswith("api/"):
                return jsonify({"error": "Not found"}), 404

            # Try to serve the exact file
            file_path = static_path / path
            if file_path.exists() and file_path.is_file():
                return send_from_directory(static_files_path, path)

            # For non-existent routes, serve index.html for SPA routing
            index_path = static_path / "index.html"
            if index_path.exists():
                return send_from_directory(static_files_path, "index.html")

            return jsonify({"error": "Not found"}), 404

    return app


def run_web_server(
    host: str = "0.0.0.0",
    port: int = 3000,
    livekit_api_key: str = "",
    livekit_api_secret: str = "",
    livekit_url: str = "",
    static_files_path: Optional[str] = None,
    debug: bool = False,
) -> threading.Thread:
    """
    Run Flask web server in a background thread

    Args:
        host: Host to bind to
        port: Port to bind to
        livekit_api_key: LiveKit API key for token generation
        livekit_api_secret: LiveKit API secret for token generation
        livekit_url: LiveKit server URL (e.g., wss://livekit.example.com)
        static_files_path: Path to static files (e.g., Next.js build output)
        debug: Enable debug mode

    Returns:
        Thread: The thread running the web server
    """
    app = create_app(
        livekit_api_key, livekit_api_secret, livekit_url, static_files_path
    )

    def run():
        logger.info(f"Starting web server on {host}:{port}")
        if static_files_path:
            logger.info(f"Serving static files from {static_files_path}")
        app.run(host=host, port=port, debug=debug, use_reloader=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    logger.info(f"Web server started on http://{host}:{port}")
    return thread