# Automated Interactive XXE Exfiltration Harness

A streamlined automation script tailored for Red Team operations and specialized Capture The Flag configurations (e.g., Hack The Box). This utility parses raw, authorized HTTP application templates, dynamically constructs file-read DTD chains, handles automated data retrieval hooks via external PHP base64-filter streams, and reconstructs structure footprints directly into local directories.

## Core Features

- **Runtime Prompt Setup:** Prompts dynamically for target interfaces and delivery ports upon startup.
- **Verbose Error Inspection:** Automatically parses and spits out raw web target stack traces, custom error templates, or 500 error blocks straight to your interactive session if an exploitation payload fails.
- **Raw Request Blueprinting:** Parses explicit `.req` configurations natively (headers, session contexts, cookies, and tokens).
- **Automated Directory Mirroring:** Preserves exact original absolute system layouts locally inside a structured directory named `./loot_output/`.
- **Integrated Debug Proxy Engine:** Seamless validation pipeline tracking using upstream configurations (`Burp Suite`, `ZAP`).

## Configuration & Usage

## New Feature: Wordlist / Dictionary Mode

You can now automate the exfiltration of large structural footprints. Instead of typing files individually, you can hand the tool a local text file filled with target operating system layouts.

### Setting Up a Target Dictionary (`common_files.txt`)
Create a local wordlist file containing standard interesting files:
```text
/etc/passwd
/etc/hosts
/etc/nginx/nginx.conf
/var/www/html/.env
/var/www/html/config.php
```


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

### 2. Run
Execute the harness environment directly:

```bash
python3 xxe_harness.py
```

Provide your parameters at the startup prompts, then specify your files (e.g., `/etc/passwd`). The script will write results cleanly or dump server-side execution failures natively into the current terminal session.
