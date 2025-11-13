# ctf-custom-web-tools
CTF Web Testing Toolkit

A lightweight, interactive Python toolkit to help with web application reconnaissance and CTF-style testing.
It automates common tasks (recon, directory enumeration, parameter discovery, basic vulnerability checks) and helps generate simple exploit payloads and a human‑readable report. For CTFs / labs only — do not run this against systems you don't have permission to test.

Table of Contents

Features

Installation

Usage

Commands / Menu Options

How it works (quick overview)

Example runs

Extending & Hardening

Ethics & Legal

License

Features

Simple interactive menu-driven interface.

Reconnaissance: HTTP headers, server, content type, basic fingerprinting.

Directory and file enumeration using built-in wordlists (multithreaded).

Parameter discovery by probing common query parameters.

Basic automatic checks for:

SQL Injection (error-based payloads)

XSS (reflected checks)

LFI (common paths)

Command Injection (character probes)

Directory Traversal (encoded/traversal payloads)

Exploit generator that prints common payloads for found vulnerabilities (for CTF writeups).

Custom payload tester for manual experimentation.

Generates a simple text report saved to the working directory.

Installation

Clone or copy the script into a directory:

mkdir ctf-toolkit
cd ctf-toolkit
# copy the Python script (e.g. ctf_toolkit.py) into this folder


(Optional) Create and activate a Python virtualenv:

python3 -m venv venv
source venv/bin/activate


Install the only required external dependency:

pip install requests


Make sure the script is executable:

chmod +x ctf_toolkit.py

Usage

Start the tool (interactive menu):

./ctf_toolkit.py
# or
python3 ctf_toolkit.py


You can also pass a target URL on the command line:

python3 ctf_toolkit.py http://target.example.com


Follow the on-screen menu:

0 Set target

1 Reconnaissance

2 Directory Enumeration

3 Parameter Discovery

4 Vulnerability Scanner

5 Exploit Generator

6 Custom Payload Tester

7 Generate Report

8 Full Automated Scan

9 Exit

Commands / Menu Options (details)

Set Target URL — set the base URL the toolkit will use (adds http:// if missing).

Reconnaissance — fetches the root page, prints status, server header, content-type, and performs simple technology fingerprinting.

Directory Enumeration — multi-threaded checks for a built-in list of common directories & files (prints 200/301/302/403 responses).

Parameter Discovery — probes common parameter names and compares responses to baseline to detect differences.

Vulnerability Scanner — runs quick, non-exploitive checks for SQLi (error strings), XSS (reflected payload presence), LFI indicators, command-injection indicators, and directory traversal.

Exploit Generator — when vulnerabilities are detected, prints common payloads to use in a CTF context (for documentation/exercises).

Custom Payload Tester — interactively send payloads to a chosen parameter and preview results (first 500 chars).

Generate Report — saves results to ctf_scan_report_<timestamp>.txt.

How it works (quick overview)

Uses requests and a requests.Session with a common User-Agent.

directory_enumeration() and bruteforce_paths() perform threaded GET requests against candidate paths (via urljoin).

parameter_discovery() appends ?param=test and looks for status/length deviations from baseline.

Vulnerability tests send non-destructive payloads (error-based and reflection-based) and look for evidence in response body or headers.

The tool does not attempt to exploit with active shell payloads automatically — it prints suggested payloads for you to run manually in the CTF target environment if appropriate.

Example runs

Reconnaissance:

[+] Target set to: http://target.example.com
[*] Gathering basic information...
[+] Status Code: 200
[+] Server: nginx/1.18.0
[+] Content-Type: text/html; charset=UTF-8
[*] Technology Fingerprinting:
[+] Detected: Nginx
[+] Detected: jQuery


Directory enumeration:

[+] Found directory: admin (Status: 301, Size: 150)
[+] Found file: robots.txt (Status: 200, Size: 45)


Vulnerability detection:

[!] VULNERABILITY: SQL Injection: id parameter with payload: ' OR '1'='1
[!] VULNERABILITY: XSS: q parameter with payload: <script>alert("XSS")</script>


Report file example: ctf_scan_report_1699999999.txt.

Extending & Hardening
Ideas to extend:

Allow custom wordlists (CLI flag or configuration file).

Add more NSE-like checks, integrate whatweb/nikto/gobuster output if installed.

Add authentication support (sessions, login forms, cookie handling).

Add output formats: JSON, markdown, or a prettier HTML report.

Add rate limiting / politeness controls to avoid DoS-like behavior during scans.

Add optional logging and verbose/debug mode.

Hardening / Security notes:

The tool performs only safe probes by default (error-based, reflection checks). For exploit payloads, it prints them instead of executing destructive actions.

Do not run this tool against third-party infrastructure — scanning can be noisy and may be interpreted as hostile.

If you run this within a shared CTF network, coordinate with organisers if needed.

Ethics & Legal

This toolkit is intended for educational and authorized CTF/lab use only. Do not use against systems for which you do not have explicit permission. The author is not responsible for misuse.

If you plan to use this in a real engagement, obtain written consent and follow a scope of work.
