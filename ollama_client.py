import json
import requests


class OllamaClient:
    """Cliente para a API REST do Ollama."""

    def __init__(self, base_url, model):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except requests.ConnectionError:
            return False

    def list_models(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=10)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def chat(self, messages, stream=True):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=stream,
                timeout=300,
            )
            resp.raise_for_status()
        except requests.ConnectionError:
            yield {"error": "Ollama indisponível. Verifique se está rodando."}
            return
        except requests.HTTPError as e:
            yield {"error": f"Erro HTTP: {e}"}
            return

        if not stream:
            data = resp.json()
            yield {"content": data.get("message", {}).get("content", "")}
            return

        for line in resp.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = chunk.get("message", {})
            content = msg.get("content", "")
            if content:
                yield {"content": content}
            if chunk.get("done"):
                return

    def generate(self, prompt, system=None, stream=True):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=stream,
                timeout=300,
            )
            resp.raise_for_status()
        except requests.ConnectionError:
            yield {"error": "Ollama indisponível. Verifique se está rodando."}
            return
        except requests.HTTPError as e:
            yield {"error": f"Erro HTTP: {e}"}
            return

        if not stream:
            data = resp.json()
            yield {"content": data.get("response", "")}
            return

        for line in resp.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = chunk.get("response", "")
            if content:
                yield {"content": content}
            if chunk.get("done"):
                return
