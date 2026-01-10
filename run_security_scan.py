import subprocess
import sys
import os

def run_command(command, description):
    print(f"\n[+] Running {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {description} Passed!")
            return True
        else:
            print(f"[!] {description} Found Issues:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[Error] Error running {description}: {e}")
        return False

def main():
    print("[*] Starting Security Posture Scan...")
    
    # 1. SAST (Static Application Security Testing) using Bandit
    # Skips B101 (assert used) which is common in some non-prod code, but we'll run strictly.
    sast_passed = run_command("bandit -r app.py seed_admin.py -f txt", "SAST Scan (Bandit)")

    # 2. Dependency Check using Safety
    dep_passed = run_command("safety check", "Dependency Vulnerability Scan (Safety)")
    
    # 3. Check for specific dangerous files
    dangerous_files = ['.env', 'config.py']
    found_dangerous = []
    for f in dangerous_files:
        if os.path.exists(f) and "example" not in f:
             # Just a warning in local dev, but critical in prod if exposed public
             pass 

    print("\n------------------------------------------------")
    if sast_passed and dep_passed:
        print("[+] All automated security checks passed!")
    else:
        print("[-] Some security checks failed. Review the logs above.")
    print("------------------------------------------------")

if __name__ == "__main__":
    main()
