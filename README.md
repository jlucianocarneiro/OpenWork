# OpenWork

Assistente de IA local com Ollama e skills especializadas.

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.ai) rodando localmente

## Instalação

```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env com seu modelo e configurações
```

## Uso

### CLI interativo

```bash
python openwork.py
```

### Com skill específica

```bash
python openwork.py --skill analista_de_codigo
```

### Listar skills

```bash
python openwork.py --list-skills
```

### Interface web (porta 8787)

```bash
python openwork.py --web
```

## Comandos no chat

| Comando | Ação |
|---|---|
| `/skills` | Listar skills disponíveis |
| `/usar <nome>` | Ativar uma skill |
| `/limpar` | Limpar histórico da conversa |
| `/sair` | Encerrar |

## Skills incluídas

| Skill | Descrição |
|---|---|
| `analista_de_codigo` | Análise de código, caça de bugs, revisão de produção |
| `analista_de_projetos` | Busca e avaliação de projetos open source |
| `avaliador_ceo_designer` | Avaliação de entregáveis com banca CEO + Especialista + Designer |
| `visualis` | Design de informação, diagramas, infográficos, visualização de dados |

## Configuração

Variáveis de ambiente (`.env`):

| Variável | Padrão | Descrição |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | URL do Ollama |
| `OLLAMA_MODEL` | `luciano-qwen35` | Modelo padrão |
| `OPENWORK_PORT` | `8787` | Porta da interface web |

## Adicionando skills

Crie um arquivo `.md` na pasta `skills/` com o system prompt desejado. O OpenWork detecta automaticamente.
