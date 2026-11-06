# Dodge Ball 2D / SpaceRaiders

SpaceRaiders is a small arcade-style dodge game written in C++ using OpenGL and GLFW. The repository also contains alternate game clients and networking experiments built with C++ and Python.

In the game, you control a blue ball and dodge red balls falling from above. Avoid collisions for as long as possible to increase your score.

## Gameplay and Enemy Behavior

- Move with the arrow keys or WASD.
- Dodge the falling obstacles and survive as long as possible.
- After a game over, press **Enter** to restart.
- Score increases over time; the improved game version also saves a high score.
- Enemy behavior is primarily arcade-style: obstacles spawn at randomized positions and move down the screen at varying speeds. This provides a simple, rule-based challenge rather than a documented advanced or learning-based AI system.

## Controls

| Action | Keys |
| --- | --- |
| Move up | W / Up Arrow |
| Move down | S / Down Arrow |
| Move left | A / Left Arrow |
| Move right | D / Right Arrow |
| Restart after game over | Enter |

## Features

- Keyboard-controlled player movement
- Randomized enemy spawn positions and fall speeds
- Score and survival-time tracking
- Persistent high-score saving in the improved version
- OpenGL-based 2D rendering
- C++ and Python UDP client/server experiments
- Several game and client variants

## OpenGL Rendering

The game uses OpenGL for drawing its 2D scene and GLFW for window creation, graphics-context setup, and input handling. The game variants render the player and falling obstacles as part of the frame update loop. Shared project headers provide mesh, drawing, and resource-path utilities; shader resources are associated with the separate `celestial-simulation` project and are referenced by this repository's resource layout.

The exact build and rendering setup can vary between the included variants. The repository does not provide a complete, cross-platform build configuration, so you may need to configure OpenGL, GLFW, GLM, the shared headers, and resource paths for your development environment.

## UDP Networking Experiments

The repository includes networking examples that explore communication between clients and servers over UDP:

- `SpaceRaiders/server.cpp` — C++ UDP networking example
- `SpaceRaiders/client.py` — Python client for networking tests
- `SpaceRaiders/spaceServer1.py` — early Python UDP server
- `SpaceRaiders/spaceServer2.py` — expanded Python server
- `SpaceRaiders/spaceServer3.py` — advanced server prototype
- `SpaceRaiders/SpaceRaidersClient1.cpp`, `SpaceRaiders/SpaceRaidersClient2.cpp`, and `SpaceRaiders/SpaceRaidersClient3.cpp` — client-side variants
- `SpaceRaiders/SpaceRaidersThreadedClient4.cpp` — threaded client experiment

UDP is connectionless, so it is useful for lightweight networking experiments but does not guarantee delivery or ordering of packets. These files are learning and prototype examples; check each program's source for its particular message format, ports, and run instructions. The networking experiments are separate from the basic single-player game unless a specific variant connects them.

## Repository Structure

- `SpaceRaiders/SpaceRaiders.cpp` — original OpenGL game
- `SpaceRaiders/SpaceRaiders2.cpp` — version with score handling and high-score persistence
- `SpaceRaiders/SpaceRaidersClient1.cpp` — client-side game variant
- `SpaceRaiders/SpaceRaidersClient2.cpp` — additional client-side variant
- `SpaceRaiders/SpaceRaidersClient3.cpp` — another client variant
- `SpaceRaiders/SpaceRaidersThreadedClient4.cpp` — threaded client experiment
- `SpaceRaiders/server.cpp` — C++ UDP networking example
- `SpaceRaiders/client.py` — Python networking-test client
- `SpaceRaiders/spaceServer1.py` — early Python UDP server
- `SpaceRaiders/spaceServer2.py` — expanded Python server
- `SpaceRaiders/spaceServer3.py` — advanced server prototype
- `includes/` — location for shared project headers
- `res/Fragment/` — local resource location associated with shared fragment shaders

## Requirements

For the game, you will need:

- A C++ compiler
- OpenGL
- GLFW
- GLM
- Project-specific headers, including `mesh.h`, `extraFunctions.h`, `meshDrawTools.h`, and `relativeResPath.h`

Python may also be needed to run the networking experiments.

### Shared headers and resources

Some project-specific headers and shader resources are maintained in the separate [`Ihsanaa3/celestial-simulation`](https://github.com/Ihsanaa3/celestial-simulation) repository. To obtain the shared files as a submodule, run these commands from the SpaceRaiders repository root:

```bash
git submodule add https://github.com/Ihsanaa3/celestial-simulation.git includes
git submodule update --init --recursive
```

Then configure your compiler or IDE to include the `includes/` directory (for example, with `-Iincludes`) and configure resource paths as needed. Alternatively, clone or copy the required files into the expected locations, or configure your build to use an existing local copy.

## Running the Game and Experiments

1. Open the project in your C++ IDE or build environment.
2. Install or configure the required libraries and shared headers/resources.
3. Set include paths and resource paths for your environment.
4. Build and run `SpaceRaiders/SpaceRaiders.cpp` or `SpaceRaiders/SpaceRaiders2.cpp`.
5. To explore networking, inspect and run the relevant server and client programs in a compatible local setup. Check their source for required ports and launch order.

The repository does not include a prebuilt executable or complete cross-platform build instructions, so exact setup steps depend on your platform and chosen variant.

## License

This project is provided as a learning/demo project and is not currently associated with a specific open-source license.
