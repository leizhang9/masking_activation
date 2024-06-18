###

[pico-python](https://github.com/colinoflynn/pico-python) developed by Colin O'Flynn is the code base for the PicoScope6000. It is a Python 2.7+ library for the Pico Scope. It uses the provided DLL for actual communications with the instrument.

Known issues: the DLL for linux does not support  RapidBlockMode as of 26.04.2018. Refer to `PicoScope6000_PapilioOne_demo.py` for further instructions how to use it.

### Install notes (e.g. for Laptop)

##### Install PicoScope drivers / software

[PicoScope](https://www.picotech.com/downloads/linux)

Add repository to the updater
```
sudo bash -c 'echo "deb https://labs.picotech.com/debian/ picoscope main" >/etc/apt/sources.list.d/picoscope.list'
```
Import public key
```
wget -O - https://labs.picotech.com/debian/dists/picoscope/Release.gpg.key | sudo apt-key add -
```
Update package manager cache
```
sudo apt-get update
```
Install PicoScope
```
    sudo apt-get install picoscope
```

##### Add user to pico group (c.f. [^1])

Once you have PicoScope running you need to add your login account to the pico group in order to access the USB. The examples will crash if you don't have permission to use the USB. This is true for use of the shared libraries in general, even if you're not using pico-python.
```
usermod -aG pico <username>
```

[^1] https://github.com/colinoflynn/pico-python


