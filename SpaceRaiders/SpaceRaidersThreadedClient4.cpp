#include "mesh.h" 
#include "extraFunctions.h" 
#include "meshDrawTools.h" 
#include "relativeResPath.h" 

#include <winsock2.h> 
#include <windows.h> 
#include <ws2tcpip.h>
#include <fstream> 
#include <thread> 
#include <atomic> 
#include <mutex> 

#define CPP_PORT    9090
#define PYTHON_PORT 8080
#define TARGET_IP   "127.0.0.1"

const unsigned int width = 900;
const unsigned int height = 900; 

const glm::mat4 iden4 = glm::mat4(1.0f); 
const int noFallingObjects = 50; 

std::mutex mtx;

std::atomic<bool> ShouldNetworkRun(true); 

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
    char playerMoveKeys[5]; 
    Entity player; 
    Entity entities[50]; 
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
        DWORD timeout = 15; 
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
        return false;
    }

    targetVector.clear();
    for (int i = 0; i < recvPacket.count; ++i) {
        targetVector.push_back(recvPacket.entities[i]);
    } 

    player.position = recvPacket.player.position; 
    score = recvPacket.score;

    return true;
} 

bool ReceiveEntityPacket(SOCKET sock, DynamicEntityPacket& Pack) {
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
        DWORD timeout = 15; 
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
        return false;
    }

    // targetVector.clear(); 
    
    for (int i = 0; i < recvPacket.count; ++i) {
        // targetVector.push_back(recvPacket.entities[i]);
        Pack.entities[i] = recvPacket.entities[i]; 
    } 

    Pack.player.position = recvPacket.player.position; 
    Pack.score = recvPacket.score;

    return true;
}

bool initialiseWinsock(WSADATA& wsaData) {
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        return false; // Initialization failed
    }
    return true; // Initialization succeeded
}

bool initialisePort(SOCKET& sock){
    if (sock == INVALID_SOCKET) {
        WSACleanup();
        return false;
    } 
    return true; 
}

void changePositionDirections(GLFWwindow* window, char* directions) {
    directions[0] = (glfwGetKey(window, GLFW_KEY_RIGHT) == GLFW_PRESS || glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS) ? '1' : '0';
    directions[1] = (glfwGetKey(window, GLFW_KEY_LEFT)  == GLFW_PRESS || glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS) ? '1' : '0';
    directions[2] = (glfwGetKey(window, GLFW_KEY_UP)    == GLFW_PRESS || glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS) ? '1' : '0';
    directions[3] = (glfwGetKey(window, GLFW_KEY_DOWN)  == GLFW_PRESS || glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS) ? '1' : '0';
    directions[4] = '\0';
}  

void changeHS(int newScore){
    std::string fullPath = rrp::getResourcesPath() + "/HighestScore.txt";
    int currentHighScore = 0;

    std::ifstream readFile(fullPath);
    if (readFile.is_open()) {
        readFile >> currentHighScore;
        readFile.close();
    }

    if (newScore > currentHighScore) {
        std::ofstream writeFile(fullPath);
        if (writeFile.is_open()) {
            writeFile << newScore;
            writeFile.close();
        }
    }
}

void NetworkThreadMach1(std::vector<Entity>& fallingObjects, Entity& playerBall, char* dir, int& score){
    WSADATA wsaData = {0}; 
    
    if(!initialiseWinsock(wsaData)){exit(1); }

    SOCKET sock = makeSocket(CPP_PORT); 
    if(!initialisePort(sock)){exit(1); }
    
    u_long mode = 1; 
    ioctlsocket(sock, FIONBIO, &mode); 

    SOCKADDR_IN destAddr = {0};
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(PYTHON_PORT); 
    inet_pton(AF_INET, TARGET_IP, &destAddr.sin_addr);

    while(ShouldNetworkRun){

        DynamicEntityPacket sendPacket{}; 

        if(score = -2){sendPacket.count = -2;}
        else{sendPacket.count = (fallingObjects.size() > 50) ? 50 : static_cast<int>(fallingObjects.size());}
        sendPacket.score = score; 
        std::strncpy(sendPacket.playerMoveKeys, dir, sizeof(sendPacket.playerMoveKeys)); 
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
            std::lock_guard<std::mutex> guard(mtx);
            ReceiveEntityPacket(sock, fallingObjects, playerBall, score); 
            // std::cout << "Packet Sent. " << std::endl; 
        }    

        DWORD timeout = 10; 
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
    } 
    
    // --- Send Exit Signal ---
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
}

void NetworkThreadMach2(DynamicEntityPacket& Pack){
    WSADATA wsaData = {0}; 
    
    if(!initialiseWinsock(wsaData)){exit(1); }

    SOCKET sock = makeSocket(CPP_PORT); 
    if(!initialisePort(sock)){exit(1); }
    
    u_long mode = 1; 
    ioctlsocket(sock, FIONBIO, &mode); 

    SOCKADDR_IN destAddr = {0};
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(PYTHON_PORT); 
    inet_pton(AF_INET, TARGET_IP, &destAddr.sin_addr);

    while(ShouldNetworkRun){
        DynamicEntityPacket sendPacket{}; 

        {
            std::lock_guard<std::mutex> guard(mtx); 
            sendPacket = Pack;  
        }

        // if(Pack.count = -2){sendPacket.count = -2;}
        // else{sendPacket.count = (fallingObjects.size() > 50) ? 50 : static_cast<int>(fallingObjects.size());}
        
        // sendPacket.score = Pack.score; 

        // std::strncpy(sendPacket.playerMoveKeys, Pack.playerMoveKeys, sizeof(sendPacket.playerMoveKeys)); 
        
        // sendPacket.player = playerBall; 

        // for (int i = 0; i < sendPacket.count; ++i) {
        //     sendPacket.entities[i] = Pack.entities[i];
        // }

        int bytesSent = sendto(
            sock, 
            reinterpret_cast<const char*>(&sendPacket), 
            sizeof(DynamicEntityPacket), 
            0, 
            reinterpret_cast<SOCKADDR*>(&destAddr), 
            sizeof(destAddr)
        );

        if (bytesSent != SOCKET_ERROR) { 
            std::lock_guard<std::mutex> guard(mtx);
            ReceiveEntityPacket(sock, Pack); 
            // std::cout << "Packet Sent. " << std::endl; 
        }    

        DWORD timeout = 10; 
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
    } 
    
    // --- Send Exit Signal ---
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
}


int main(){

    rd::randseed(); 

    GLFWwindow* window = et::initialiseGLFW(width, height, "Window");   

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
    int frameRate = 0; 
    int score = 0; 
    char dir[5] = "0000"; 

    DynamicEntityPacket SendPack; 
    
    SendPack.player = playerBall; 
    for(int i = 0; i <noFallingObjects; ++i){
        SendPack.entities[i] = fallingObjects[i]; 
    } 

    SendPack.score = score; 
    SendPack.count = noFallingObjects; 
    for(int i = 0; i < 5; ++i){SendPack.playerMoveKeys[i] = dir[i];} 

    // std::thread network(NetworkThreadMach1, std::ref(fallingObjects), std::ref(playerBall), dir, std::ref(score)); 
    std::thread network(NetworkThreadMach2, std::ref(SendPack)); 

    glm::mat4 translationMat; 
    std::vector<glm::mat4> localMatriciesForFallingBalls; 
    GLint modelLoc = glGetUniformLocation(GeneralShader.ID, "model"); 

    while (!glfwWindowShouldClose(window)){     
        changePositionDirections(window, dir); 
        {
            std::lock_guard<std::mutex> guard(mtx); 

            if(glfwGetKey(window, GLFW_KEY_ENTER) == GLFW_PRESS){SendPack.count = -2;} 
            else(SendPack.count = 50); 
            for(int i = 0; i < 5; ++i){SendPack.playerMoveKeys[i] = dir[i];} 

            for(int i = 0; i <noFallingObjects; ++i){
                fallingObjects[i] = SendPack.entities[i];
            } 
        }

        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        double crntTime = glfwGetTime(); 
        frameRate += 1; 

        if (crntTime - prevTime >= 1.0f){
            std::cout << "Frame Rate: " << frameRate << " | score: " << score << std::endl; 
            prevTime = crntTime; 
            frameRate = 0;   
        } 

        GeneralShader.Activate(); 
        
        {   // lock local falling mat4
            std::lock_guard<std::mutex> guard(mtx); 
            localMatriciesForFallingBalls.clear(); 
            localMatriciesForFallingBalls.reserve(noFallingObjects); 
            for(const Entity& matobj: fallingObjects){
                localMatriciesForFallingBalls.push_back( glm::translate(iden4, glm::vec3(matobj.position, 0.0f))); 
            }
        }
        for(glm::mat4& obj : localMatriciesForFallingBalls){
            glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(obj));
            fallingObjectMesh.Draw(GeneralShader, GL_TRIANGLES); 
        }
         

        {   // lock player vector
            std::lock_guard<std::mutex> guard(mtx);
            translationMat = glm::translate(iden4, glm::vec3(playerBall.position, 0.0f)); 
        }
        
        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(translationMat));
        playerBallMesh.Draw(GeneralShader, GL_TRIANGLES); 

        glfwSwapBuffers(window);
        et::processInput(window); 
        glfwPollEvents();
    } 

    ShouldNetworkRun = false; 

    network.join(); 

    GeneralShader.Delete(); 
    glfwDestroyWindow(window);
    glfwTerminate(); 


    return 0; 
}
