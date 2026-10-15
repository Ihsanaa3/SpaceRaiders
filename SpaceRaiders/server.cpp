#include <winsock2.h> 
#include <windows.h> 
#include <ws2tcpip.h>
#include <stdio.h> 

#define TARGET_IP   "127.0.0.1"
#define TARGET_PORT 8080

struct dataPacket{
    int number = 1; 
    char data[500]; 
}; 

SOCKET makeSocket(WORD wPort) {
    SOCKET sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP); 
    if (sock == INVALID_SOCKET) {
        return INVALID_SOCKET; 
    }

    SOCKADDR_IN Addr = {0}; 
    Addr.sin_family = AF_INET; 
    Addr.sin_port = htons(wPort); 
    Addr.sin_addr.s_addr = htonl(INADDR_ANY); 
    
    if (bind(sock, (SOCKADDR*)&Addr, sizeof(Addr)) == SOCKET_ERROR) {
        printf("Bind failed with error: %d\n", WSAGetLastError());
        closesocket(sock); 
        return INVALID_SOCKET; 
    }
    
    return sock; 
};

int main(int argc, char** argv) {
    WSADATA wsaData = {0}; 
    
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed.\n");
        return 1;
    }

    // Bind to a local port (e.g., 9090) so we can send
    SOCKET sock = makeSocket(TARGET_PORT); 
    if (sock == INVALID_SOCKET) {
        printf("Failed to create socket.\n");
        WSACleanup();
        return 1;
    }
 
    printf("Socket successfully bound!\n");

    // Target Python receiver address
    SOCKADDR_IN destAddr = {0};
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(TARGET_PORT);
    inet_pton(AF_INET, TARGET_IP, &destAddr.sin_addr);

    for(int i = 1; i < 10; ++i){

        struct dataPacket sendData = {0};  
        sendData.number = i; 
        snprintf(sendData.data, sizeof(sendData.data), "HELLO FROM C/CPP! NO %d", i);
        // sendData.data[sizeof(sendData.data) - 1] = '\0' ; 

        int bytesSent = sendto(
            sock, 
            (const char*) &sendData, 
            sizeof(sendData), 
            0, 
            (SOCKADDR*)&destAddr, 
            sizeof(destAddr)
        );
        
        if (bytesSent == SOCKET_ERROR) {
            printf("sendto failed with error: %d\n", WSAGetLastError());
        } else {
            printf("Sent %d bytes successfully to %s:%d\n", bytesSent, TARGET_IP, TARGET_PORT);
        }

        struct dataPacket recvData = {0}; 
        SOCKADDR_IN senderAddr = {0}; 
        int senderAddrLen = sizeof(senderAddr); 

        int bytesRecv = recvfrom(
            sock, 
            (char*) &recvData, 
            sizeof(recvData), 
            0, 
            (SOCKADDR*)&senderAddr, 
            &senderAddrLen
        ); 

        if (bytesRecv != SOCKET_ERROR){
            printf("Received reply [Num: %d, Text: %s]\n", recvData.number, recvData.data); 
        }else{
            printf("recvfrom failed: %d\n", WSAGetLastError());
        }
    } 

    // --- Send Exit Signal ---
    struct dataPacket exitPacket = {0};  
    exitPacket.number = 0; 
    snprintf(exitPacket.data, sizeof(exitPacket.data), "exit"); 

    int exitSent = sendto(
        sock, 
        (const char*)&exitPacket, 
        sizeof(exitPacket), 
        0, 
        (SOCKADDR*)&destAddr, 
        sizeof(destAddr)
    );

    if (exitSent == SOCKET_ERROR) {
        printf("Failed to send exit packet: %d\n", WSAGetLastError());
    } else {
        printf("Sent exit signal to Python. Exiting C++ client.\n");
    }

    closesocket(sock);
    WSACleanup(); 
    return 0;  
}