import subprocess
import sys

def run_command(command):
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Output:", result.stdout)
        print("Error:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("Output:", e.stdout)
        print("Error:", e.stderr)
        return False

# Add changes
run_command("git add .")

# Commit
# We use a try-catch for commit because it might fail if there are no changes to commit, which is fine
print("Committing changes...")
run_command('git commit -m "Final optimization: Fast capture, strict recognition, fix Unknown labels"')

# Push
print("Pushing to remote...")
if run_command("git push origin render-deployment"):
    print("Push successful!")
else:
    print("Push failed!")
