import subprocess

def create_issue():
    subprocess.run(["gh", "issue", "create"])
