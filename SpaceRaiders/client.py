import socket 
import struct 

IPADDR = "127.0.0.1" 
PORT = 8080 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
sock.bind((IPADDR, PORT)) 

print(f"Listening for UDP packets on {IPADDR}:{PORT}...") 


while True: 
    data, addr = sock.recvfrom(1024)    
    number, text = struct.unpack("i500s", data)
    clean_text = text.split(b"\x00", 1)[0].decode("utf-8", errors="ignore")
    
    # Check if the sender wants to terminate
    if clean_text == "exit":
        print("Received exit signal from C++. Shutting down Python receiver...")
        break

    print(f"Number: {number}, Text: {clean_text}")

    # reply back to cpp 
    replyNum = number 
    replyText = f"Pong back from Python for {replyNum}".encode("utf-8") 

    # pack back into binary 
    replyPayload = struct.pack("i500s", replyNum, replyText) 
    sock.sendto(replyPayload, addr) 

sock.close()