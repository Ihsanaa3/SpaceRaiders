#include"mesh.h" 
#include"extraFunctions.h" 
#include"meshDrawTools.h" 
#include"relativeResPath.h" 

#include <winsock2.h> 
#include <windows.h> 
#include <ws2tcpip.h>
#include<fstream> 

#define CPP_PORT    9090
#define PYTHON_PORT 8080
#define TARGET_IP   "127.0.0.1"

const unsigned int width = 900;
const unsigned int height = 900; 

const float dt = 1.0f / 60.0f; 

const glm::mat4 iden4 = glm::mat4(1.0f); 
const int noFallingObjects = 50; 

#pragma pack(push, 1) // removes memory buffers 

struct Entity {
    glm::vec2 position = glm::vec2(0.0f); 
    glm::vec2 velocity = glm::vec2(0.0f); 
    float radius; 
    float deltaG = 0.0f;

    Entity() = default;

    // Constructor creates a circle mesh using the passed parameter values
    Entity(float r, glm::vec2 pos = glm::vec2(0.0f)) 
        : radius(r), position(pos) {} 
}; 

struct DynamicEntityPacket{ 
    int count; 
    Entity entities[50]; 
}; 

#pragma pack(pop) // returns memory buffers 

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

bool ReceiveEntityPacket(SOCKET sock, std::vector<Entity>& targetVector) {
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
        printf("recvfrom failed: %d\n", WSAGetLastError()); 
    
        // Set a 10ms timeout on receive operations
        DWORD timeout = 10; // milliseconds
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));

        return false;
    }

    // Clear existing vector and update with response from Python
    targetVector.clear();
    for (int i = 0; i < recvPacket.count; ++i) {
        targetVector.push_back(recvPacket.entities[i]);
    }

    return true;
}

void PositionChange(GLFWwindow* window, Entity& player, float addRate, float dt){
    if ((glfwGetKey(window, GLFW_KEY_UP) == GLFW_PRESS) || (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS))
    {
        player.position.y += addRate * dt; 
    }
    if ((glfwGetKey(window, GLFW_KEY_DOWN) == GLFW_PRESS) || (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS))
    {
        player.position.y -= addRate * dt; 
    }
    if ((glfwGetKey(window, GLFW_KEY_RIGHT) == GLFW_PRESS) || (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS))
    {
        player.position.x += addRate * dt; 
    }
    if ((glfwGetKey(window, GLFW_KEY_LEFT) == GLFW_PRESS) || (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS))
    {
        player.position.x -= addRate * dt; 
    } 
}

void Reset(std::vector<Entity>& thisEntity, Entity& player){
    for (Entity& thisone : thisEntity){
        thisone.position = glm::vec2(rd::randsignf(), 1.0f);
        thisone.velocity = glm::vec2(0.0f); 
    }
    player.position = glm::vec2(0.0f); 
} 

void changeHS(int newScore){
    std::string fullPath = rrp::getResourcesPath() + "/HighestScore.txt";
    
    int currentHighScore = 0;

    // Step 1: Read the existing score from the file
    std::ifstream readFile(fullPath);
    if (readFile.is_open()) {
        readFile >> currentHighScore;
        readFile.close();
    } else {
        std::cout << "File didn't exist yet or couldn't be opened. Defaulting to 0.\n";
    }

    // Step 2: Compare
    if (newScore > currentHighScore) {
        std::cout << "New high score! Replacing " << currentHighScore << " with " << newScore << std::endl;
        
        // Step 3: Overwrite the file with the new score
        // (std::ofstream opens in truncate mode by default, clearing old content)
        std::ofstream writeFile(fullPath);
        if (writeFile.is_open()) {
            writeFile << newScore;
            writeFile.close();
        } else {
            std::cerr << "Failed to write new high score to file!\n";
        }
    } else {
        std::cout << "Score of " << newScore << " did not beat high score of " << currentHighScore << std::endl;
    }
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
        fallingObjects.back().deltaG = -1.0f * rd::randf() * dt; 
    }
    
    Entity playerBall(0.04f, glm::vec2(0.0f, 0.0f)); 

    double prevTime = glfwGetTime(); 
    double previousTime = prevTime;   
    bool GameOver = false; 
    int frameRate = 0; 

    size_t Score = 0; 

    float BoundaryMinusPlayerRad = 1.0f - playerBall.radius;  

    glm::mat4 translationMat; 
    GLint modelLoc = glGetUniformLocation(GeneralShader.ID, "model"); 

    // NETWORK STUFF STARTS
    
    WSADATA wsaData = {0}; 

    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("WSAStartup failed.\n");
        return 1;
    } 

    // Bind C++ socket to Port 9090
    SOCKET sock = makeSocket(CPP_PORT); 
    if (sock == INVALID_SOCKET) {
        printf("Failed to create socket.\n");
        WSACleanup();
        return 1;
    }
    
    printf("Socket successfully bound to port %d!\n", CPP_PORT); 

    // Target Python receiver address on Port 8080
    SOCKADDR_IN destAddr = {0};
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(PYTHON_PORT); // Sends to Python (8080)
    inet_pton(AF_INET, TARGET_IP, &destAddr.sin_addr);

    while (!glfwWindowShouldClose(window)){ 

        // 1. Pack and Send fallingObjects vector to Python
        DynamicEntityPacket sendPacket{};
        sendPacket.count = (fallingObjects.size() > 50) ? 50 : static_cast<int>(fallingObjects.size());

        for (int i = 0; i < sendPacket.count; ++i) {
            sendPacket.entities[i] = fallingObjects[i];
        }

        size_t payloadSize = sizeof(int) + (sendPacket.count * sizeof(Entity));

        int bytesSent = sendto(
            sock, 
            reinterpret_cast<const char*>(&sendPacket), 
            payloadSize, 
            0, 
            reinterpret_cast<SOCKADDR*>(&destAddr), 
            sizeof(destAddr)
        );

        // 2. Receive processed vector state back from Python
        if (bytesSent != SOCKET_ERROR) {
            ReceiveEntityPacket(sock, fallingObjects); 
            // Set a 10ms timeout on receive operations
        }    
        
        DWORD timeout = 10; // milliseconds
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));

        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        double crntTime = glfwGetTime(); 
        frameRate += 1; 

        if (crntTime - prevTime >= 1.0f){
            std::cout << "Frame Rate: " << frameRate << std::endl;  
            std::cout << "Score: " << Score << std::endl; 
            prevTime = crntTime; 
            frameRate = 0;   
        }

        if (!GameOver && crntTime - previousTime >= dt){ 
            // PositionChange(window, playerBall, 0.9f, dt); 
            // previousTime = crntTime; 
            Score += 1;  

            for(Entity& obj : fallingObjects){
                obj.velocity.y += obj.deltaG; 
                obj.position += obj.velocity * dt; 

                if(obj.position.y < -1.0f){ 
                    obj.deltaG = -1.0f * rd::randfb(1.0f + (Score / 1000)) * dt;  
                    obj.position.x = rd::randsignf(); 
                    obj.position.y = 1.0f; 
                    obj.velocity.y = 0.0f;
                }
                if(glm::distance(obj.position, playerBall.position) < obj.radius + playerBall.radius - 0.01){ 
                    std::cout << "Game Over" << std::endl; 
                    changeHS(Score); 
                    GameOver = true; 
                }
            }
        } 

        if(GameOver && glfwGetKey(window, GLFW_KEY_ENTER) == GLFW_PRESS){
            Reset(fallingObjects, playerBall);  
            Score = 0; 
            GameOver = false; 
        }
        

        GeneralShader.Activate(); 

        // Draw falling objects
        for(Entity& obj : fallingObjects){
            translationMat = glm::translate(iden4, glm::vec3(obj.position, 0.0f));
            
            glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(translationMat));
            fallingObjectMesh.Draw(GeneralShader, GL_TRIANGLES); 
        } 

        // Draw player
        if(playerBall.position.x > BoundaryMinusPlayerRad){
            playerBall.position.x = BoundaryMinusPlayerRad; 
        }
        if(playerBall.position.x < -BoundaryMinusPlayerRad){
            playerBall.position.x = -BoundaryMinusPlayerRad; 
        }
        if(playerBall.position.y > BoundaryMinusPlayerRad){
            playerBall.position.y = BoundaryMinusPlayerRad; 
        }
        if(playerBall.position.y < -BoundaryMinusPlayerRad){
            playerBall.position.y = -BoundaryMinusPlayerRad; 
        }
       
        translationMat = glm::translate(iden4, glm::vec3(playerBall.position, 0.0f)); 
        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(translationMat));
        playerBallMesh.Draw(GeneralShader, GL_TRIANGLES); 

        glfwSwapBuffers(window);
        et::processInput(window); 
        glfwPollEvents();
    }
        
    // --- Send Exit Signal ---
    DynamicEntityPacket exitPacket{};
    exitPacket.count = -1; // -1 acts as an 'exit' control signal

    int exitSent = sendto(
        sock, 
        reinterpret_cast<const char*>(&exitPacket), 
        sizeof(int), // We only need to send the 4-byte count header for exit
        0, 
        reinterpret_cast<SOCKADDR*>(&destAddr), 
        sizeof(destAddr)
    );

    if (exitSent == SOCKET_ERROR) {
        printf("Failed to send exit packet: %d\n", WSAGetLastError());
    } else {
        printf("Sent exit signal to Python. Exiting C++ client.\n");
    }

    closesocket(sock);
    WSACleanup();        

    glfwDestroyWindow(window);
    glfwTerminate();

    return 0; 
}