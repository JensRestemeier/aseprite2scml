# aseprite2scml
This is a bit of hackish code to convert animations created in Aseprite into Spriter animations for further markup. This was made to convert an animation for my pipeline, if yours requires a different layout you may need to tweak the code.
The hard work of opening the Aseprite file is done with Florian Dormont's [py_aseprite](https://github.com/Eiyeron/py_aseprite) .

## Install
Just clone this repository including sub-modules.

## Usage
The script needs to be run from the command line:
```shell
usage: aseprite2scml.py [-h] [--output OUTPUT] [--ofs_x OFS_X] [--ofs_y OFS_Y] input

Convert a Aseprite animation into a Spriter animation

positional arguments:
  input            Input Aseprite animation

options:
  -h, --help       show this help message and exit
  --output OUTPUT  Output scml path
  --ofs_x OFS_X    X-offset added to all frames
  --ofs_y OFS_Y    Y-offset added to all frames
```

Example:
```shell
python aseprite2scml.py RogueAnimations1.5\Rogue.aseprite --ofs_x -62 --ofs_y 113
```
This will convert Rogue.aseprite to scml\Rogue.scml, with subdirectories for each animation.
Different animations need to be tagged in Aseprite.
