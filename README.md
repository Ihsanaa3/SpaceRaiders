# Dodge Ball 2D / SpaceRaiders

This repository contains a small arcade-style dodge game built in C++ with OpenGL and GLFW, along with several networking experiments and alternate client/server variants built as part of the same learning project.

The core game is a simple survival challenge: the player moves a blue ball around the screen while red balls fall in from above. The goal is to avoid collisions as long as possible, track score over time, and beat the saved high score.

## Gameplay

- Move the player with the arrow keys or WASD
- Avoid incoming falling objects
- Survive for as long as possible
- Restart after a game over by pressing Enter
- Score increases over time
- High score is saved to a file

## Features

- Smooth player movement with keyboard input
- Randomized enemy spawn positions and fall speeds
- Score and survival tracking
- Persistent high-score saving
- Restart support after a loss
- Multiple game variants and networking experiments in the same repository

## Repository Structure

- `SpaceRaiders/SpaceRaiders.cpp` — original OpenGL game implementation
- `SpaceRaiders/SpaceRaiders2.cpp` — improved version with score handling and high-score persistence
- `SpaceRaiders/SpaceRaidersClient1.cpp` — client-side variant
- `SpaceRaiders/SpaceRaidersClient2.cpp` — additional client-side variant
- `SpaceRaiders/SpaceRaidersClient3.cpp` — another client variant
- `SpaceRaiders/SpaceRaidersThreadedClient4.cpp` — threaded client experiment
- `SpaceRaiders/server.cpp` — C++ UDP server/client communication example
- `SpaceRaiders/client.py` — Python client for networking tests
- `SpaceRaiders/spaceServer1.py` — early Python UDP server implementation
- `SpaceRaiders/spaceServer2.py` — expanded Python server version
- `SpaceRaiders/spaceServer3.py` — more advanced server prototype
- `README.md` — project overview

## Controls

- Up: W / Up Arrow
- Down: S / Down Arrow
- Left: A / Left Arrow
- Right: D / Right Arrow
- Restart: Enter

## Requirements

This project uses:

- C++ compiler
- OpenGL
- GLFW
- GLM
- Project-specific headers such as `mesh.h`, `extraFunctions.h`, `meshDrawTools.h`, and `relativeResPath.h`
- For networking experiments, Python and socket-based communication may also be used

Note: The project-specific include headers referenced above are maintained in a separate repository: `Ihsanaa3/celestial-simulation` (see below). You can either clone that repository into an `includes/` directory within this repo or add it as a git submodule. See the "Includes" section for details.

## Includes

These project-specific headers are stored in a separate repository to keep shared code organized.

Options to obtain the headers:

1) Add as a git submodule (recommended):

   git submodule add https://github.com/Ihsanaa3/celestial-simulation.git includes
   git submodule update --init --recursive

   This will create an `includes/` directory in this repository that points to the other repository. Adjust your compiler include paths to reference `includes/` (for example, `-Iincludes`).

2) Clone or copy the files manually into an `includes/` directory:

   git clone https://github.com/Ihsanaa3/celestial-simulation.git includes

   Or copy the relevant headers from your other workspace into an `includes/` directory here.

3) If you prefer not to use a submodule, keep the include path pointing to a central location on your machine and ensure your build system knows where to find those headers.

## Running the Game

1. Open the project in your preferred C++ IDE or build environment.
2. Ensure the required libraries and include paths are configured.
3. If you used the submodule option above, add `-Iincludes` to your compiler include paths (or configure it in your IDE).
4. Compile and run either `SpaceRaiders/SpaceRaiders.cpp` or `SpaceRaiders/SpaceRaiders2.cpp`.
5. If using the improved version, the high score is saved to a file in the resources folder.
6. For the networking examples, run the relevant Python and C++ server/client files in a compatible local setup.


## Notes

This repository is a learning/demo project and contains both the game source and a set of experimental networking and client/server files. It does not include a prebuilt executable or a complete cross-platform project setup, so you may need to configure include paths, library links, and runtime settings for your development environment.

## License

This project is provided as a learning/demo project and is not currently associated with a specific open-source license.
