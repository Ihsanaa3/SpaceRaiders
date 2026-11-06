# Dodge Ball 2D / SpaceRaiders

SpaceRaiders is a small arcade-style dodge game written in C++ with OpenGL and GLFW. The repository also includes alternate game clients and networking experiments developed alongside the main game.

In the game, you control a blue ball and dodge red balls falling from above. Avoid collisions for as long as possible to increase your score.

## Gameplay

- Move with the arrow keys or WASD.
- Dodge the falling obstacles.
- Survive as long as possible to build your score.
- After a game over, press **Enter** to restart.
- The improved game version saves a high score to a file.

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
- Several game variants and networking experiments

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

## Requirements

The game requires:

- A C++ compiler
- OpenGL
- GLFW
- GLM
- The project-specific headers, including `mesh.h`, `extraFunctions.h`, `meshDrawTools.h`, and `relativeResPath.h`

Python may also be needed to run the networking experiments.

### Shared headers and resources

Some project-specific headers are maintained in the separate [`Ihsanaa3/celestial-simulation`](https://github.com/Ihsanaa3/celestial-simulation) repository. To obtain them as a submodule, run these commands from the SpaceRaiders repository root:

```bash
git submodule add https://github.com/Ihsanaa3/celestial-simulation.git includes
git submodule update --init --recursive
```

Then configure your compiler or IDE to include the `includes/` directory (for example, with `-Iincludes`). Alternatively, clone or copy the required files into `includes/`, or configure your build to use an existing local copy.

## Running the Game

1. Open the project in your C++ IDE or build environment.
2. Install or configure the required libraries and shared headers.
3. Set the include paths and any resource paths required by your environment.
4. Build and run `SpaceRaiders/SpaceRaiders.cpp` or `SpaceRaiders/SpaceRaiders2.cpp`.
5. To try the networking experiments, run the relevant server and client programs in a compatible local setup.

The repository does not provide a prebuilt executable or a complete, cross-platform build configuration, so the exact build steps depend on your environment.

## License

This project is provided as a learning/demo project and is not currently associated with a specific open-source license.
