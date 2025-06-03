#!/usr/bin/env python3

import subprocess
import argparse
import sys
import time
import requests
import random

# Default model and server settings
OLLAMA_MODEL = "llama3"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_TIMEOUT = 60  # seconds


def is_ollama_server_running():
    """
    @brief Check if the Ollama server is running.

    @return True if server responds, False otherwise.
    """
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def start_ollama_server():
    """
    @brief Start the Ollama server and wait until it's ready.
    """
    print("🟡 Starting Ollama server...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(OLLAMA_TIMEOUT):
        if is_ollama_server_running():
            print("✅ Ollama server is running.")
            return
        time.sleep(1)

    print("❌ Timeout: Ollama server did not start.")
    sys.exit(1)


def is_model_loaded():
    """
    @brief Check if the desired Ollama model is already loaded.

    @return True if model is loaded, False otherwise.
    """
    try:
        response = requests.post(f"{OLLAMA_HOST}/api/show", json={"name": OLLAMA_MODEL}, timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def start_ollama_model():
    """
    @brief Start the specified Ollama model and wait until it's ready.
    """
    print(f"🚀 Starting model `{OLLAMA_MODEL}`...")
    subprocess.Popen(["ollama", "run", OLLAMA_MODEL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(OLLAMA_TIMEOUT):
        if is_model_loaded():
            print("✅ Model is ready.")
            return
        time.sleep(1)

    print(f"❌ Timeout: Ollama model `{OLLAMA_MODEL}` failed to load.")
    sys.exit(1)


def run_git_command(command):
    """
    @brief Run a git command and return its output.

    @param command Git command as string.
    @return Output as string.
    """
    return subprocess.check_output(command, shell=True, text=True).strip()


def get_git_diff():
    """
    @brief Get the staged git diff.

    @return Diff as a string.
    """
    try:
        return run_git_command("git diff --cached --no-color")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")
        sys.exit(1)


def clean_commit_message(msg):
    """
    @brief Clean commit message by removing boilerplate tags.

    @param msg The raw commit message.
    @return Cleaned commit message.
    """
    lines = msg.strip().splitlines()
    clean_lines = [line for line in lines if not any(
        line.startswith(prefix) for prefix in [
            "Change-Id:", "Reviewed-on:", "Reviewed-by:", "Tested-by:", "Signed-off-by:"
        ]
    )]
    return "\n".join(clean_lines).strip()


def get_recent_commits(n=5, max_lookback=20):
    """
    @brief Retrieve recent meaningful commit messages.

    @param n Number of good commits to return.
    @param max_lookback Number of commits to search through.
    @return List of cleaned commit messages.
    """
    log_format = "%s%n%b"
    try:
        output = run_git_command(f"git log -n {max_lookback} --pretty=format:'{log_format}'")
        all_commits = output.split("\n\n")
        good_commits = [
            clean_commit_message(msg) for msg in all_commits
            if len(msg.strip()) > 30 and not msg.lower().startswith("merge")
        ]
        return good_commits[:n]
    except subprocess.CalledProcessError:
        return []


def get_random_good_commits(sample_size=5, pool_size=100):
    """
    @brief Retrieve a random selection of older good commit messages.

    @param sample_size Number of commits to return.
    @param pool_size Total pool size to sample from.
    @return List of cleaned commit messages.
    """
    try:
        log_format = "%s%n%b"
        output = run_git_command(f"git log --skip=5 -n {pool_size} --pretty=format:'{log_format}'")
        all_commits = output.split("\n\n")
        good_commits = [
            clean_commit_message(msg) for msg in all_commits
            if len(msg.strip()) > 30 and not msg.lower().startswith("merge")
        ]
        return random.sample(good_commits, min(sample_size, len(good_commits)))
    except subprocess.CalledProcessError:
        return []


def stage_all_changes():
    """
    @brief Stage all modified and new files for commit.
    """
    subprocess.run(["git", "add", "-u"])
    subprocess.run(["git", "add", "."])


def generate_commit_message(diff, examples, debug=False):
    """
    @brief Generate a commit message using an LLM based on diff and past examples.

    @param diff The git diff to summarize.
    @param examples A list of previous commit messages as examples.
    @return Generated commit message string.
    """
    formatted_examples = "\n\n".join([e for e in examples])
    prompt = f"""
    You are a helpful assistant that writes **only** clean, conventional git commit messages.

    Guidelines:
    - Respond with just the commit message.
    - Start with a short summary line (max ~70 chars).
    - Use imperative mood (e.g., "Fix crash", "Add support for...").
    - Next lines should start with dashes and also use imperative
    - Do not include labels like "Commit message:", "Here is the message:", etc.
    - Do not include explanations, apologies, or greetings.
    - Output only the message, nothing else.

    Those are 10 examples of previous commits:

    {formatted_examples}

    Now, based on the following diff, write only the commit message:

    {diff}
    """
    if debug:
        print("Prompt used by agent:", prompt)

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        print(f"❌ Error generating commit message: {e}")
        return "Failed to generate commit message (no response)"


def main():
    """
    @brief Main function to handle argument parsing, ensure dependencies are running,
           generate and write commit message using LLM.
    """
    parser = argparse.ArgumentParser(description="Generate a commit message using LLM.")
    parser.add_argument("--jira", type=str, help="Optional JIRA ticket (e.g., ANA3-XXXX)")
    parser.add_argument("-d", "--debug", action="store_true", help="Print useful debug messages")
    args = parser.parse_args()

    # Ensure Ollama server and model are running
    if not is_ollama_server_running():
        start_ollama_server()
    if not is_model_loaded():
        start_ollama_model()

    # Stage changes and get git diff
    stage_all_changes()
    diff = get_git_diff()
    recent_examples = get_recent_commits(5)
    random_examples = get_random_good_commits(5)
    examples = recent_examples + random_examples

    # Generate commit message
    commit_body = generate_commit_message(diff, examples, args.debug)

    # Prefix with JIRA tag if provided
    if args.jira:
        final_message = f"[BUGFIX {args.jira}] {commit_body}"
    else:
        final_message = f"[DEV] {commit_body}"

    # Display commit message
    if args.debug:
        print("\nSuggested commit message:\n")
        print(final_message)

    # Save commit message to file used by git
    temp_path = ".git/COMMIT_EDITMSG_LLMBOT"
    with open(temp_path, "w") as f:
        f.write(final_message + "\n")

    # Overwrite default Git commit message file for `--edit`
    temp_path = ".git/COMMIT_EDITMSG"
    with open(temp_path, "w") as f:
        f.write(final_message + "\n")

    # Trigger commit with pre-filled message
    subprocess.run(["git", "commit", "--edit", "-F", temp_path])

    print("\n✅ Done!")
