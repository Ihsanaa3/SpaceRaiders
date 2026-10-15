Includes for SpaceRaiders

This folder is intended to host the header files and small utilities referenced by the demo game (mesh.h, extraFunctions.h, meshDrawTools.h, relativeResPath.h, etc.).

Recommended usage:

- Add the `celestial-simulation` repository as a git submodule into this folder:

  git submodule add https://github.com/Ihsanaa3/celestial-simulation.git includes
  git submodule update --init --recursive

- Or clone/copy the required header files from your `celestial-simulation` repo into this folder.

Why not add the files directly?

- The headers are shared across multiple projects and are maintained in `Ihsanaa3/celestial-simulation`. Keeping them as a submodule makes it easier to share updates.
