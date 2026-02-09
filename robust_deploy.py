import subprocess
import urllib.request
import urllib.error
import sys

LOG_FILE = "deploy_debug.log"

def log(message):
    print(message)
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

def run_command(command):
    log(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        log(f"EXIT CODE: {result.returncode}")
        log(f"STDOUT:\n{result.stdout}")
        log(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        log(f"EXCEPTION: {e}")
        return False

def trigger_deploy():
    url = "https://api.render.com/deploy/srv-cv2h0fl2ng6s738870vg?key=J39Z-N4s-68"
    log(f"Triggering deployment at: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            code = response.getcode()
            body = response.read().decode('utf-8')
            log(f"Deploy Trigger Status: {code}")
            log(f"Deploy Trigger Response: {body}")
            return True
    except urllib.error.HTTPError as e:
        log(f"Deploy Trigger HTTP Error: {e.code} - {e.reason}")
        log(e.read().decode('utf-8'))
        return False
    except Exception as e:
        log(f"Deploy Trigger Error: {e}")
        return False

# Clear log
with open(LOG_FILE, "w") as f:
    f.write("Starting robust deployment...\n")

# 1. Git Status
run_command("git status")

# 2. Add and Commit
run_command("git add .")
run_command('git commit -m "Final optimization: Fast capture, strict recognition, fix Unknown labels"')

# 3. Push
log("Pushing to remote...")
if run_command("git push origin render-deployment"):
    log("Push SUCCESS.")
else:
    log("Push FAILED. Trying to fetch and push...")
    # Maybe we are behind? Unlikely based on "ahead by 23", but let's try safely.
    # run_command("git pull --rebase origin render-deployment")
    # run_command("git push origin render-deployment")

# 4. Trigger Deploy
trigger_deploy()
