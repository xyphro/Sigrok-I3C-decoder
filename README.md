# Sigrok-I3C-decoder
An I3C decoder with SDR and HDR-DDR support for sigrok &amp; pulseview

After releasing an I3C analyzer for Saleae logic, I received a lot of request to make an analyzer plugin for Sigrok Pulseview.

So: Here it is for your enjoyment :-)

Capabilities:
* SDR and DDR mode support
* Diversified decoding for Bit 9. Bit 9 of SDR transfers has several meanings as function of context. ACK/NAK signaling, Parity bit, Continuation / Abort signaling.
* Decoding of ENTDAA. ENTDAA has a frame format which does not follow the normal SDR mode, because the read data payload has no bit 9.  
* Special bus conditions are decoded:
  * SDR mode: Start, Stop, Restart
  * HDR-DDR mode: HDR restart, HDR exit
  * target reset condition is detected
  
  
## Installation instructions

Clone this repository or select the download option on the top right.
The I3C analyzer itself is located in the folder [decoder](decoder) in the i3c.zip file.

Navigate to your pulseview decoders directory.
For a windows installation with default location you can find it under:

    C:\Program Files\sigrok\PulseView\share\libsigrokdecode\decoders

Unzip the i3c.zip file in that directory such that you have the following folder/file structure:

```plaintext
.../libsigrokdecode/decoders/i3c/__init__.py
.../libsigrokdecode/decoders/i3c/pd.py
```

Or here a view of the final files at the right location on a windows installation:

![](https://raw.githubusercontent.com/xyphro/Sigrok-I3C-decoder/master/pictures/folderview.png)

## Here a few decoding views:

### HDR-SDR decoding
![](https://raw.githubusercontent.com/xyphro/Sigrok-I3C-decoder/master/pictures/decoderview_sdr.png)

### HDR-DDR decoding
![](https://raw.githubusercontent.com/xyphro/Sigrok-I3C-decoder/master/pictures/decoderview_ddr.png)

### HDR-ENTDAA decoding
![](https://raw.githubusercontent.com/xyphro/Sigrok-I3C-decoder/master/pictures/decoderview_entdaa.png)

Note that for now it does not put a lot of useful information into the PYTHON pipe for decoding with higher level analyzer or textual analysis. This is addressed in the next release.
When that step is done I'll officially inform sigrok team too about this analyzer.

# Other I3C projects for your reference
## Look for an I3C analyzer plugin for Saleae Logic?

Have a look at my I3C daughter project, which is a Saleae Logic Analyzer plugin to decode I3C OD, I3C SDR and I3C HDR-DDR transfers:
<a href="https://github.com/xyphro/XyphroLabs-I3C-Saleae-Protocol-Analyzer" target="_blank">https://github.com/xyphro/XyphroLabs-I3C-Saleae-Protocol-Analyzer</a> 

## In need of an I3C Controller which can be controlled from a PC?

Have a look at my I3C daughter project, which is USB to I3C interface based on a cheap Raspberry pi PICO 2040 board.
<a href="https://github.com/xyphro/I3CBlaster" target="_blank">https://github.com/xyphro/I3CBlaster</a> 
