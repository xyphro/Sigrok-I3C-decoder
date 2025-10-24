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
  
## Update 24 October '25

I added DSView compatibility. That means, you can now also use this Analyzer also with DsLogic Analyzers.

DSView implements a slightly different version compared to the current Sigrok Pulseview, but the change was easy to apply.
In general Sigrog Pulseview is a bit more advanced in how it presents analyzed data - you can turn on/off fine grained what it should show and what not.
  
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

## Testing  

The folder [decoder](decoder) also contains an example Waveform. This waveform was pragmatically decoded from a saleae logic capture, but the conversion was not perfect. Content wise it is correct, but the timeline is not - dummy samples got inserted.
This is no functional problem though - the file decodes correctly.

This .sr file also includes already an i3c decoder in the waveform.

The decoder can also be executed to output textual decoding data using sigrok-cli:

```plaintext
sigrok-cli -i ExampleWaveform.sr -P i3c:scl=D0:sda=D1 -A i3c=address-read:address-write:data-read:data-write
```
  
The parameters following -A select which aspects of the decoding you would like to see in the textual decoding.

Execute:
```plaintext
sigrok-cli -P i3c --show
```
to see which items you can add to -A.



## Here a few decoding views:

### HDR-SDR decoding
![](https://raw.githubusercontent.com/xyphro/Sigrok-I3C-decoder/master/pictures/decoderview_sdr.png)

### HDR-DDR decoding
![](https://raw.githubusercontent.com/xyphro/Sigrok-I3C-decoder/master/pictures/decoderview_ddr.png)

### HDR-ENTDAA decoding
![](https://raw.githubusercontent.com/xyphro/Sigrok-I3C-decoder/master/pictures/decoderview_entdaa.png)

A unit test to get into official integration into Sigrok is yet to be done.
# Other I3C projects for your reference
## Looking for an I3C analyzer plugin for Saleae Logic?

Have a look at my I3C daughter project, which is a Saleae Logic Analyzer plugin to decode I3C OD, I3C SDR and I3C HDR-DDR transfers:
<a href="https://github.com/xyphro/XyphroLabs-I3C-Saleae-Protocol-Analyzer" target="_blank">https://github.com/xyphro/XyphroLabs-I3C-Saleae-Protocol-Analyzer</a> 

## In need of an I3C Controller which can be controlled from a PC?

Have a look at my I3C daughter project, which is USB to I3C interface based on a cheap Raspberry pi PICO 2040 board.
<a href="https://github.com/xyphro/I3CBlaster" target="_blank">https://github.com/xyphro/I3CBlaster</a> 
