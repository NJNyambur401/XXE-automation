# Automated Interactive XXE Exfiltration Harness

A streamlined automation script tailored for Red Team operations and specialized Capture The Flag configurations (e.g., Hack The Box). This utility parses raw, authorized HTTP application templates, dynamically constructs file-read DTD chains, handles automated data retrieval hooks via external PHP base64-filter streams, and reconstructs structure footprints directly into local directories.

## Core Features

- **Raw Request Blueprinting:** Parses explicit `.req` configurations natively (headers, session contexts, cookies, and tokens).
- **Automated Directory Mirroring:** Preserves exact original absolute system layouts locally inside a structured directory named `./loot_output/`.
- **Integrated Debug Proxy Engine:** Seamless validation pipeline tracking using upstream configurations (`Burp Suite`, `ZAP`).
- **Dynamic Handshake Loops:** Houses concurrent multi-threaded execution patterns managing dynamic DTD delivery and tracking payloads concurrently.

## Configuration & Usage

### 1. Isolate Injection Points (`target.req`)
Export or craft your raw HTTP request block inside a localized template named `target.req`. Insert the marker sequence `*XXE*` where the injection profile needs to take root:

```http
POST /submit/profile HTTP/1.1
Host: 10.129.100.22
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
Cookie: session=xyz987admin
Content-Type: application/xml

<?xml version="1.0" encoding="UTF-8"?>
*XXE*
```

### 2. Setup Variables
Open `xxe_harness.py` and calibrate your operational network flags:
- Set `ATTACKER_IP` to your accessible interface address (e.g., your HTB `tun0` interface).
- Toggle `USE_PROXY = True` to intercept and analyze script outputs within your active proxy suite on port `8080`.

### 3. Run
Execute the harness environment directly:

```bash
python3 xxe_harness.py
```

Type any desired absolute path when prompted (e.g., `/etc/apache2/apache2.conf` or `/etc/passwd`). The decoded data will be waiting systematically inside your local directory structure.
