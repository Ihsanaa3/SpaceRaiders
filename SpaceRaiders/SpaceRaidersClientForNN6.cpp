#include "mesh.h" 
#include "extraFunctions.h" 
#include "meshDrawTools.h" 
#include "relativeResPath.h" 

#include <winsock2.h> 
#include <windows.h> 
#include <ws2tcpip.h>
#include <fstream> 
#include <iostream>
#include <vector>

#define CPP_PORT    9090
#define PYTHON_PORT 8080
#define TARGET_IP   "127.0.0.1"

const unsigned int width = 900;
const unsigned int height = 900; 

const glm::mat4 iden4 = glm::mat4(1.0f); 
const int noFallingObjects = 50; 

#pragma pack(push, 1) 

struct Entity {
    glm::vec2 position = glm::vec2(0.0f); 
    glm::vec2 velocity = glm::vec2(0.0f); 
    float radius; 
    float deltaG = 0.0f;

    Entity() = default;

    Entity(float r, glm::vec2 pos = glm::vec2(0.0f)) 
        : radius(r), position(pos) {} 
}; 

struct DynamicEntityPacket{ 
    int count; 
    int score; 
    Entity player; 
    Entity entities[noFallingObjects]; 
}; 

#pragma pack(pop) 

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
} 

bool ReceiveEntityPacket(SOCKET sock, std::vector<Entity>& targetVector, Entity& player, int& score) {
    DynamicEntityPacket recvPacket{};
    SOCKADDR_IN senderAddr = {0};
    int senderAddrLen = sizeof(senderAddr);

    int bytesRecv = recvfrom(
        sock,
        reinterpret_cast<char*>(&recvPacket),
        sizeof(recvPacket),
        0,
        reinterpret_cast<SOCKADDR*>(&senderAddr),
        &senderAddrLen
    ); 

    if (bytesRecv == SOCKET_ERROR) { 
        int err = WSAGetLastError();
        if (err == WSAEWOULDBLOCK) {
            return false; 
        }
        return false;
    }

    targetVector.clear();
    for (int i = 0; i < recvPacket.count; ++i) {
        targetVector.push_back(recvPacket.entities[i]);
    } 

    player.position = recvPacket.player.position; 
    return true;
}

int main(){ 
    rd::randseed(); 

    GLFWwindow* window = et::initialiseGLFW(width, height, "Space Raiders - AI Render Client");   

    Shader GeneralShader(rrp::getVertexPath() + "modelmat.vert.txt", rrp::getFragmentPath() + "default.frag.txt"); 

    Mesh fallingObjectMesh = drt::createCircle(0.06f, 18, glm::vec3(0.85f, 0.25f, 0.25f));
    Mesh playerBallMesh = drt::createCircle(0.04f, 18, glm::vec3(0.2f, 0.7f, 1.0f));

    std::vector<Entity> fallingObjects; 
    fallingObjects.reserve(noFallingObjects); 

    for(int i = 0; i < noFallingObjects; ++i){
        fallingObjects.emplace_back(0.06f, glm::vec2(rd::randsignf(), 1.0f)); 
        fallingObjects.back().deltaG = -1.0f * rd::randf(); 
    }
    
    Entity playerBall(0.04f, glm::vec2(0.0f, 0.0f)); 

    double prevTime = glfwGetTime(); 
    double prevTimeNet = glfwGetTime(); 
    double crntTime; 

    float nsr = 0.025f; // Network send rate (matches 40 FPS physics tick)

    int frameRate = 0; 
    int score = 0; 

    glm::mat4 translationMat; 
    GLint modelLoc = glGetUniformLocation(GeneralShader.ID, "model"); 

    // NETWORK SETUP
    WSADATA wsaData = {0}; 
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        return 1;
    } 

    SOCKET sock = makeSocket(CPP_PORT); 
    if (sock == INVALID_SOCKET) {
        WSACleanup();
        return 1;
    } 
    
    u_long mode = 1; 
    ioctlsocket(sock, FIONBIO, &mode); 

    SOCKADDR_IN destAddr = {0};
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(PYTHON_PORT); 
    inet_pton(AF_INET, TARGET_IP, &destAddr.sin_addr);

    bool GameOver = false; 

    while (!glfwWindowShouldClose(window)){ 
        crntTime = glfwGetTime(); 
        frameRate += 1;  
        score += 1; 

        // for(Entity& v: fallingObjects){    
        //     float distSquared = v.radius + playerBall.radius; 
        //     if (glm::distance2(v.position, playerBall.position) <= distSquared){ 
        //         std::printf("collision ");
        //         GameOver = true; 
        //         score = 0; 
        //     }
        // }

        if(crntTime - prevTimeNet >= nsr){ 

            DynamicEntityPacket sendPacket{}; 

            if(glfwGetKey(window, GLFW_KEY_ENTER) == GLFW_PRESS){ 
                sendPacket.count = -2; // Restart trigger code 
                score = 0; 
            // }else if(GameOver){
            //     sendPacket.count = -3; // tells server games over
            }else{
                sendPacket.count = (fallingObjects.size() > noFallingObjects) ? noFallingObjects : static_cast<int>(fallingObjects.size());
            }

            sendPacket.score = score; 
            
            sendPacket.player = playerBall; 
            for (int i = 0; i < sendPacket.count; ++i) {
                sendPacket.entities[i] = fallingObjects[i];
            }

            int bytesSent = sendto(
                sock, 
                reinterpret_cast<const char*>(&sendPacket), 
                sizeof(DynamicEntityPacket), 
                0, 
                reinterpret_cast<SOCKADDR*>(&destAddr), 
                sizeof(destAddr)
            );

            if (bytesSent != SOCKET_ERROR) {
                ReceiveEntityPacket(sock, fallingObjects, playerBall, score); 
            }    

            prevTimeNet = crntTime; 
        }

        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        if (crntTime - prevTime >= 1.0f){
            std::cout << "Render FPS: " << frameRate << " | Score: " << score << std::endl; 
            prevTime = crntTime; 
            frameRate = 0;   
        } 

        GeneralShader.Activate(); 

        // Draw falling objects synchronized from Python
        for(Entity& obj : fallingObjects){
            translationMat = glm::translate(iden4, glm::vec3(obj.position, 0.0f));
            glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(translationMat));
            fallingObjectMesh.Draw(GeneralShader, GL_TRIANGLES); 
        } 

        // Draw player position synchronized from Python
        translationMat = glm::translate(iden4, glm::vec3(playerBall.position, 0.0f)); 
        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(translationMat));
        playerBallMesh.Draw(GeneralShader, GL_TRIANGLES); 

        glfwSwapBuffers(window);
        et::processInput(window); 
        glfwPollEvents();
    }
    
    // --- Send Exit Signal (-1) to Python ---
    DynamicEntityPacket exitPacket{};
    exitPacket.count = -1; 
    sendto(
        sock, 
        reinterpret_cast<const char*>(&exitPacket), 
        sizeof(DynamicEntityPacket), 
        0, 
        reinterpret_cast<SOCKADDR*>(&destAddr), 
        sizeof(destAddr)
    );

    closesocket(sock);
    WSACleanup();        

    glfwDestroyWindow(window);
    glfwTerminate();

    return 0;  
}