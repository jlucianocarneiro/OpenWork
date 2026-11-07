#!/usr/bin/env python3
"""OpenWork — Assistente de IA local com Ollama."""

import argparse
import sys

import config
from ollama_client import OllamaClient
from skill_runner import SkillRunner


def print_banner(runner):
    print("\n\033[1;34m╔══════════════════════════════════════╗\033[0m")
    print("\033[1;34m║\033[0m       \033[1mOpenWork\033[0m · IA Local            \033[1;34m║\033[0m")
    print("\033[1;34m╚══════════════════════════════════════╝\033[0m")
    print(f"  Modelo: \033[36m{runner.client.model}\033[0m")
    if runner.active_skill:
        title = runner.get_active_skill_title()
        print(f"  Skill:  \033[33m{title}\033[0m")
    print()
    print("  Comandos:")
    print("    /skills       — listar skills")
    print("    /usar <nome>  — ativar skill")
    print("    /limpar       — limpar histórico")
    print("    /sair         — encerrar")
    print()


def interactive_mode(runner):
    print_banner(runner)

    while True:
        try:
            user_input = input("\033[1;32m> \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if not user_input:
            continue

        if user_input == "/sair":
            print("Até logo!")
            break

        if user_input == "/skills":
            skills = runner.list_skills()
            if not skills:
                print("  Nenhuma skill encontrada.")
            else:
                print("\n  Skills disponíveis:")
                for s in skills:
                    marker = " *" if s["name"] == runner.active_skill else ""
                    print(f"    \033[33m{s['name']}\033[0m — {s['title']}{marker}")
            print()
            continue

        if user_input.startswith("/usar "):
            name = user_input[6:].strip()
            if runner.set_skill(name):
                title = runner.get_active_skill_title()
                print(f"  Skill ativada: \033[33m{title}\033[0m\n")
            else:
                print(f"  Skill '{name}' não encontrada. Use /skills para listar.\n")
            continue

        if user_input == "/limpar":
            runner.clear_history()
            print("  Histórico limpo.\n")
            continue

        if user_input.startswith("/"):
            print("  Comando desconhecido. Use /skills, /usar, /limpar ou /sair.\n")
            continue

        print()
        for chunk in runner.chat(user_input, stream=True):
            if "error" in chunk:
                print(f"\033[31m{chunk['error']}\033[0m")
                break
            sys.stdout.write(chunk.get("content", ""))
            sys.stdout.flush()
        print("\n")


def main():
    parser = argparse.ArgumentParser(description="OpenWork — Assistente de IA local")
    parser.add_argument("--skill", help="Skill para ativar ao iniciar")
    parser.add_argument("--list-skills", action="store_true", help="Listar skills disponíveis")
    parser.add_argument("--web", action="store_true", help="Iniciar interface web")
    parser.add_argument("--model", help=f"Modelo Ollama (padrão: {config.OLLAMA_MODEL})")
    parser.add_argument("--port", type=int, help=f"Porta da interface web (padrão: {config.OPENWORK_PORT})")
    args = parser.parse_args()

    model = args.model or config.OLLAMA_MODEL
    client = OllamaClient(config.OLLAMA_URL, model)
    runner = SkillRunner(client)

    if args.list_skills:
        skills = runner.list_skills()
        if not skills:
            print("Nenhuma skill encontrada.")
        else:
            for s in skills:
                print(f"  {s['name']:30s} {s['title']}")
        return

    if args.skill:
        if not runner.set_skill(args.skill):
            print(f"Skill '{args.skill}' não encontrada.")
            print("Skills disponíveis:")
            for s in runner.list_skills():
                print(f"  {s['name']}")
            return

    if args.web:
        from web.app import create_app
        app = create_app(runner)
        port = args.port or config.OPENWORK_PORT
        print(f"OpenWork Web rodando em http://localhost:{port}")
        app.run(host="0.0.0.0", port=port, debug=False)
        return

    if not client.is_available():
        print(f"\033[31mOllama indisponível em {config.OLLAMA_URL}\033[0m")
        print("Verifique se o Ollama está rodando: ollama serve")
        return

    interactive_mode(runner)


if __name__ == "__main__":
    main()
