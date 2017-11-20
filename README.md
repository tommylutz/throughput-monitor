# throughput-monitor
A Physical Internet Throughput Monitor Based on Raspberry Pi Zero W

This repository contains the code, 3d models, and graphics required to build an internet throughput monitor that is compatible with Verizon FiOS Quantum Gateway, model FiOS-G1100. The program will periodically poll the Verizon router for throughput statistics, then move a stepper motor to a position that represents the amount of throughput in use, on a logarithmic scale.

While not necessary, a GRPC interface is provided with the throughput monitor that allows a remote machine to invoke changes in the dial. This opens up the possibility of gathering measurements from remote sources and rendering them on the dial.

## Compatibility
The software was tested with firmware version 01.04.00.12, hardware version 1.03.

# Bill of Materials

## Parts
* Raspberry Pi Zero W and 5v Power Supply (micro USB)
* 0.1" Pin Headers
* (6) Male-Male Jumper Wires
* (1) Stepper Motor (28BYJ-48)
* (1) Motor Driver (ULN2003)
* (TODO: qty) Screws (TODO: size)

## Tools
* Soldering iron, solder and flux
* 3D Printer
* Screw driver
* Printer
* Tape or glue (for putting faceplate on)

## Assembly

TODO

## Raspberry Pi Zero W Setup

TODO

# Issues

## GRPC on Raspberry Pi Zero W

```sudo pip3 install grpcio grpcio-tools``` does not work properly on the zero because the provided shared libraries were not built for the proper architecture, armv6z. You will need to build grpcio from source. I could not get grpcio-tools to build, which means I had to generate the *_pb*.py files on a separate machine.

To build grpcio on your zero w:
* Use the instructions here with slight modification: https://github.com/grpc/grpc/blob/master/src/python/grpcio/README.rst
* Place an additional variable in front of the pip3 install: ```sudo GRPC_PYTHON_CFLAGS=-march=armv6z GRPC_PYTHON_BUILD_WITH_CYTHON=1 pip3 install .```


