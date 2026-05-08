![](Assets/Pasted%20image%2020260312154639.png)

## 1. Reconnaissance & Enumeration

First, after connecting to the HTB network via OpenVPN, we start by running an `nmap` scan to see all the open ports and running services.

![](Assets/Pasted%20image%2020260312154654.png)

The scan reveals an HTTP service running Gunicorn. I decided to open a browser and navigate to the IP address to see what's hosted.

![](Assets/Pasted%20image%2020260312154741.png)

Looking around the dashboard, I noticed the URL structure when viewing a snapshot: `http://10.129.6.51/data/1`.

![](Assets/Pasted%20image%2020260312154800.png)

## 2. Vulnerability Discovery (IDOR)

We can see that the URL ends with a number, which looks like an identifier (ID). This is a good indicator to test for IDOR (Insecure Direct Object Reference) either manually or through fuzzing.

![](Assets/Pasted%20image%2020260312154818.png)

I created a wordlist of numbers from 0 to 100 to test the endpoint. The results showed that only ID `0` and `1` returned an HTTP 200 OK status.

![](Assets/Pasted%20image%2020260312154834.png)

## 3. Initial Access (User Flag)

By changing the ID in the URL to `0` (`http://10.129.6.51/data/0`), we can access another dashboard with different values. More importantly, this specific page gives us the option to download a `.pcap` (packet capture) file.

I opened the downloaded file in Wireshark. After filtering the traffic by protocols, I spotted unencrypted FTP traffic. Reading the FTP stream revealed valid credentials:

- **User:** `nathan`
- **Pass:** `Buck3tH4TF0RM3!`
![](Assets/Pasted%20image%2020260312154907.png)

Going back to our initial Nmap scan, we know SSH (port 22) is open. We can use these credentials to connect to the machine via SSH and retrieve the user flag.

![](Assets/Pasted%20image%2020260312154926.png)

## 4. Privilege Escalation (Root Flag)

Now logged in as `nathan`, we need to find a way to become root. I checked for Linux Capabilities using the `getcap` command:

`getcap -r / 2>/dev/null`

- **`-r /`**: Tells the tool to search recursively from the root directory.
- **`2>/dev/null`**: Hides all the "Permission denied" errors for a cleaner output.

![](Assets/Pasted%20image%2020260312155015.png)

The output shows that `/usr/bin/python3.8` has the `cap_setuid` capability enabled. This is highly exploitable. We can use Python to change our UID to 0 (root) and spawn a shell using this one-liner:

`/usr/bin/python3.8 -c 'import os; os.setuid(0); os.system("/bin/bash")'`

- **`-c`**: Tells Python to execute the code within the quotes.
- **`import os`**: Imports the operating system library.
- **`os.setuid(0)`**: The magic happens here. Thanks to `cap_setuid`, we tell Python to become root (UID 0).
- **`os.system("/bin/bash")`**: Now that Python is running as root, we ask it to open a bash shell.
![](Assets/Pasted%20image%2020260312155104.png)
Just like that, we have root access! Let's read the root flag, and the machine is fully compromised.