@dataclass
class ProjectConfig:
    name: str
    db: bool = False
    auth: bool = False
    docker: bool = False
```
Think of it as a container that gets passed around between the other files.

---

**`cli.py`** — the entry point. This is what runs when you type `fastapi-gen my-app`. It uses **Typer** to define the command and **Rich** to display the interactive prompts. It collects the user's answers (project name, which features they want), builds a `ProjectConfig` object, then hands it to the generator.

---

**`templates.py`** — a big file full of functions that return strings. Each function returns the content of one generated file. For example `main_py(config)` returns the text of `src/main.py`, `dockerfile(config)` returns the text of `Dockerfile`, etc. They take the config as an argument so they can conditionally include things — if `config.auth` is True, it adds auth imports.

---

**`generator.py`** — the orchestrator. It receives the config, calls all the template functions to build a dictionary of `{filepath: content}`, then loops through and writes every file to disk. It also prints the file tree you see in the terminal and the "next steps" message.

---

## The flow when you run it
```
fastapi-gen my-app
       ↓
   cli.py         ← asks you questions, builds ProjectConfig
       ↓
   generator.py   ← decides which files to create
       ↓
   templates.py   ← generates the content of each file
       ↓
   your disk      ← my-app/ folder appears with everything inside