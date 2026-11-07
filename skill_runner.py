import os
import re


class SkillRunner:
    """Carrega skills (.md) e gerencia conversas com o LLM via Ollama."""

    DESCRIPTION_PATTERN = re.compile(
        r"^#\s+(.+?)(?:\n|$)", re.MULTILINE
    )

    def __init__(self, ollama_client, skills_dir="skills"):
        self.client = ollama_client
        self.skills_dir = skills_dir
        self.skills = {}
        self.history = []
        self.active_skill = None
        self.load_skills()

    def load_skills(self):
        if not os.path.isdir(self.skills_dir):
            return
        for fname in sorted(os.listdir(self.skills_dir)):
            if not fname.endswith(".md"):
                continue
            name = fname[:-3]
            path = os.path.join(self.skills_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.skills[name] = content

    def list_skills(self):
        result = []
        for name, content in self.skills.items():
            m = self.DESCRIPTION_PATTERN.search(content)
            title = m.group(1).strip() if m else name
            result.append({"name": name, "title": title})
        return result

    def set_skill(self, name):
        if name and name not in self.skills:
            return False
        self.active_skill = name
        self.history = []
        return True

    def get_active_skill_title(self):
        if not self.active_skill:
            return None
        m = self.DESCRIPTION_PATTERN.search(self.skills[self.active_skill])
        return m.group(1).strip() if m else self.active_skill

    def clear_history(self):
        self.history = []

    def chat(self, user_message, stream=True):
        messages = []

        if self.active_skill and self.active_skill in self.skills:
            messages.append({
                "role": "system",
                "content": self.skills[self.active_skill],
            })
        else:
            messages.append({
                "role": "system",
                "content": (
                    "Você é o OpenWork, um assistente de IA local. "
                    "Responda em português de forma clara e objetiva."
                ),
            })

        messages.extend(self.history)
        messages.append({"role": "user", "content": user_message})

        full_response = []

        for chunk in self.client.chat(messages, stream=stream):
            if "error" in chunk:
                yield chunk
                return
            full_response.append(chunk.get("content", ""))
            yield chunk

        self.history.append({"role": "user", "content": user_message})
        self.history.append({
            "role": "assistant",
            "content": "".join(full_response),
        })

        if len(self.history) > 40:
            self.history = self.history[-30:]
