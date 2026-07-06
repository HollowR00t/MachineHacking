![](Assets/Pasted%20image%2020260626101019.png)

---
```bash
ping -c 4 154.57.164.82
PING 154.57.164.82 (154.57.164.82) 56(84) bytes of data.
64 bytes from 154.57.164.82: icmp_seq=1 ttl=46 time=166 ms
64 bytes from 154.57.164.82: icmp_seq=2 ttl=46 time=349 ms
64 bytes from 154.57.164.82: icmp_seq=4 ttl=46 time=182 ms

--- 154.57.164.82 ping statistics ---
4 packets transmitted, 3 received, 25% packet loss, time 3043ms
```

## 1. Reconnaissance

We see this page 

![](Assets/Pasted%20image%2020260626101349.png)

Then we inspect with the developers tools in the browser and reload the page to see what endpoints use.

![](Assets/Pasted%20image%2020260626101446.png)

We can see the endpoint **`options`** so we can see a secret command `Blip-blop, in a pickle with a hiccup! Shmiggity-shmack`

Then we can start the game and put the command and we can get the flag

