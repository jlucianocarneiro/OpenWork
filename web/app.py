import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, Response, render_template, request, jsonify


def create_app(runner=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    if runner is None:
        import config
        from ollama_client import OllamaClient
        from skill_runner import SkillRunner
        client = OllamaClient(config.OLLAMA_URL, config.OLLAMA_MODEL)
        runner = SkillRunner(client)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/skills")
    def api_skills():
        skills = runner.list_skills()
        return jsonify({
            "skills": skills,
            "active": runner.active_skill,
            "model": runner.client.model,
        })

    @app.route("/api/skill", methods=["POST"])
    def api_set_skill():
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        if name == "":
            name = None
        ok = runner.set_skill(name)
        return jsonify({"ok": ok, "active": runner.active_skill})

    @app.route("/api/clear", methods=["POST"])
    def api_clear():
        runner.clear_history()
        return jsonify({"ok": True})

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "Mensagem vazia"}), 400

        def generate():
            for chunk in runner.chat(message, stream=True):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/api/models")
    def api_models():
        models = runner.client.list_models()
        return jsonify({"models": models, "current": runner.client.model})

    @app.route("/api/model", methods=["POST"])
    def api_set_model():
        data = request.get_json(silent=True) or {}
        model = data.get("model", "").strip()
        if model:
            runner.client.model = model
        return jsonify({"model": runner.client.model})

    @app.route("/api/status")
    def api_status():
        available = runner.client.is_available()
        return jsonify({
            "available": available,
            "model": runner.client.model,
            "active_skill": runner.active_skill,
            "skill_title": runner.get_active_skill_title(),
            "history_length": len(runner.history),
        })

    return app


if __name__ == "__main__":
    import config
    app = create_app()
    app.run(host="0.0.0.0", port=config.OPENWORK_PORT, debug=True)
