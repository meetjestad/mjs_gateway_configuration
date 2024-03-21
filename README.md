# LoRaWAN gateway configuration using pyinfra


### Updating the basicstation binaries
This is also orchestrated by pyinfra, With the command below, this
creates a new docker container to perform the build in, which is again
removed afterwards, but it should also be possible to run this on any
Debian machine (including the local machine with `@local`), though this
has not been tested.

```
pyinfra @docker/debian:bookworm-slim build_basicstation.py --yes
```
