# commAIt (commit_msg_llm)

> ✨ AI-powered Git commit messages using LLaMA 3, locally via Ollama

CommAIt is a CLI tool that generates clean, conventional commit messages based on your Git diff — powered by a local LLM (LLaMA 3). No cloud, no tokens, just smart, secure commit messages.

---

## 🚀 Features

* 🧠 Uses recent high-quality commits as in-context examples
* 🔒 Works entirely offline with Ollama
* 🧹 Enforces conventional, imperative-style commit formatting
- 🛠 Auto-stages changes and launches `git commit --edit`
- ⚡ Fast and lightweight CLI tool, written in Python
- 🧪 Optional `--jira` and `--debug` flags

---

## 📦 Installation

### 1. Prerequisites

* Python 3.8+
* Git
* [Ollama](https://ollama.com) installed and configured
* LLaMA 3 model pulled:

  ```bash
  ollama pull llama3
  ```

### 2. Clone this repo

```bash
git clone https://github.com/Trigo93/commit_msg_llm.git
cd commit_msg_llm
pip3 install .
```

---

## 🧪 Usage

```bash
commait --jira ABC-123
```

### Optional Flags:

* `--jira <TICKET>`: Prefix message with a JIRA ID (e.g., `[BUGFIX ABC-123]`)
* `-d, --debug`: Enable debug mode (shows full prompt sent to the model)
* `--h` : Display helper

---

## 💡 How It Works

1. Starts Ollama server and loads the LLaMA 3 model (if not already running)
2. Loads the llama3 model locally
3. Stages all current changes
4. Retrieves high-quality past commits for context
5. Builds a prompt using the Git diff + examples
6. Sends to Ollama API
7. Writes generated message to `.git/COMMIT_EDITMSG` and opens commit editor
8. Launches the Git editor for review and editing

---

## 🛠 Developer Notes

To skip auto-committing, you can comment out the final `git commit` line in `main()`.

---

## 📋 Example Output

```text
[BUGFIX ABC-123] Fix crash in error reporting module

- Handle edge case when report payload is null
- Add fallback logging
- Improve error message clarity
```

---

## 📘 License

MIT © 2025 Tristan

---

## 🙌 Credits

Built by Tristan. Powered by [Ollama](https://ollama.com) and [Meta’s LLaMA 3](https://ai.meta.com/llama/).
