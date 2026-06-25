##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2025 Kai Gossner <xyphro@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

# TODO: Enable protocol decoder by outputing more details to python pipe

from common.srdhelper import bitpack_msb
import sigrokdecode as srd

event_none = 0
event_rising_clock = 1
event_falling_clock = 2
event_stop = 3
event_start = 4


protevent_hdr_restart = 0
protevent_hdr_exit = 1
protevent_targetreset = 2
protevent_start = 3
protevent_restart = 4
protevent_stop = 5
protevent_entdaadata = 6
protevent_data = 7
protevent_hdr_dataword = 8
protevent_hdr_crcword = 9
protevent_bit9 = 10
protevent_hdr_preamble = 11
protevent_hdr_parity = 12



mode_sdr = 1;
mode_ddr = 2;

ENDTYPE_SCL_RISING  = '0r'
ENDTYPE_SCL_FALLING = '0f'
ENDTYPE_SCL_ANY     = '0a'
ENDTYPE_SDA_RISING  = '1r'
ENDTYPE_SDA_FALLING = '1f'
ENDTYPE_SDA_ANY     = '1a'
ENDTYPE_ANY         = 'a'

# Meaning of table items:
# command -> [annotation class, annotation text in order of decreasing length]
proto = {
    'START':         [0, 'Start', 'S'],
    'START REPEAT':  [1, 'Start repeat', 'Sr'],
    'STOP':          [2, 'Stop', 'P'],
    
    'ACK':           [3, '{text}','{text}'],
    'SDR PARITY':    [4, 'Par{b:1d}', 'P{b:1d}', '{b:1d}'],
    
    'BIT':           [5, '{b:1d}'],
    'ADDRESS READ':  [6, 'Address read: {b:02X}', 'AR: {b:02X}', '{b:02X}'],
    'ADDRESS WRITE': [7, 'Address write: {b:02X}', 'AW: {b:02X}', '{b:02X}'],
    'DATA READ':     [8, 'Data read: {b:02X}', 'DR: {b:02X}', '{b:02X}'],
    'DATA WRITE':    [9, 'Data write: {b:02X}', 'DW: {b:02X}', '{b:02X}'],
    
    
    'WARN':          [10, '{text}'],
    'BIT9':          [11, '{b:1d}'],
    'DEBUG':         [12, '{text}'],
    'ENTDAA DATA':   [13, 'ENTDAA read: {b:02X}', 'ER: {b:02X}'],
    'HDR EXIT':      [14, 'Exit', 'X'],
    'HDR RESTART':   [15, 'Restart', 'R'],
    'CRC':           [16, 'CRC: {b:02X}', 'C: {b:02X}', '{b:02X}'],
    'HDR PREAMBLE':  [17, 'Preamble: {b:01X}', 'PR: {b:01X}', 'P{b:01X}'],
    'HDR PARITY':    [18, 'Parity: {b:01X}', 'PR: {b:01X}', 'P{b:01X}'],
    'HDR CMD':       [19, 'CMD: {b:04X}', 'C: {b:04X}', 'C{b:X}'],
    'RESET':         [20, 'TR'],
}




'''
OUTPUT_PYTHON format: TBD -> Implementation will follow
'''

# Meaning of table items:
# command -> [annotation class, annotation text in order of decreasing length]

    
class Decoder(srd.Decoder):
    api_version = 3
    id = 'i3c'
    name = 'I3C'
    longname = 'MIPI I3C'
    desc = 'Two-wire serial bus.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['i3c']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'scl', 'name': 'SCL', 'desc': 'Serial clock line'},
        {'id': 'sda', 'name': 'SDA', 'desc': 'Serial data line'},
    )
    options = (
        {'id': 'scl_pol', 'desc': 'SCL polarity',
            'default': 'normal', 'values': ('normal', 'inverted')},
        {'id': 'sda_pol', 'desc': 'SDA polarity',
            'default': 'normal', 'values': ('normal', 'inverted')},
    )
    annotations = (
        ('start', 'Start condition'),
        ('repeat-start', 'Repeat start condition'),
        ('stop', 'Stop condition'),
        ('ack', 'ACK/NAK, continuation'),
        ('sdr parity', 'SDR parity'),
        ('bit', 'Data/address bit'),
        ('address-read', 'Address read'),
        ('address-write', 'Address write'),
        ('data-read', 'Data read'),
        ('data-write', 'Data write'),
        ('warning', 'Warning'),
        ('bit9', 'T-Bit or ACK/Continuation bit'),
        ('debug', 'debugpane'),
        ('entdaa-data', 'EntDAA Data read'),
        ('hdr-exit', 'HDR exit'),
        ('hdr-restart', 'HDR restart'),
        ('hdr-crc', 'HDR CRC'),
        ('hdr-preamble', 'HDR preamble'),
        ('hdr-parity', 'HDR parity'),
        ('hdr-cmd', 'HDR command'),
        ('reset', 'Target reset'),
    )
    annotation_rows = (
        ('bits', 'Bits', (5,11,)),
        ('addr-data', 'Address/data', (0, 1, 2, 3, 4, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18, 19, 20,)),
        ('warnings', 'Warnings', (10,12,)),
    )
    binary = (
        ('address-read', 'Address read'),
        ('address-write', 'Address write'),
        ('data-read', 'Data read'),
        ('data-write', 'Data write'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.is_write = None
        self.rem_addr_bytes = None
        self.slave_addr_7 = None
        self.slave_addr_10 = None
        self.is_repeat_start = False
        self.pdu_start = None
        self.pdu_bits = 0
        self.data_bits = []
        self.bitwidth = 0
        
        self.mMode = mode_sdr
        self.mStateSdrDecode_state = 0
        self.mStateSdrDecode_bitcounter = 0
        self.mStateSdrDecode_dataword = 0
        self.mStateSdrDecode_ack_rising = 0
        self.mStateSdrDecode_ack_falling = 0
        
        self.mStateSdrDecode_prevbitstate = False
        self.mStateSdrDecode_prevbitpos = 0
        
        self.mIsFirstByte = True
        self.mIsWriteTransfer = False
        self.mentdaa_bytecounter = 0
        self.mentdaa_detector = 0
        self.menthdr_detector = 0
        self.mSpecialConditionDetectionState = 0
        
        self.mStateDdrDecode_state = 0
        self.mStateDdrDecode_dataword = 0
        self.mStateDdrDecode_bitcounter = 0
        
        self.annotationQueue = []
        


    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

    def putg(self, ss, es, cls, text):
        self.annotationQueue.append([ss, es, self.out_ann, [cls, text]])
        #self.put(ss, es, self.out_ann, [cls, text])

    def putp(self, ss, es, data):
        self.annotationQueue.append([ss, es, self.out_python, data])
        #self.put(ss, es, self.out_python, data)

    def putb(self, ss, es, data):
        self.annotationQueue.append([ss, es, self.out_binary, data])
        #self.put(ss, es, self.out_binary, data)
        
    def processAnnotationQueue(self, s, event_sda_rising, event_sda_falling, event_scl_rising, event_scl_falling):
        if len(self.annotationQueue) > 0:
            rm = []
            for item in self.annotationQueue:
                ss   = item[0]
                es   = item[1]
                pipe = item[2]
                data = item[3]
                
                eventmatches = False
                if type(es) is int: # end sample given - add it!
                    eventmatches = True
                    
                if type(es) is str: # event given -> signal number and type                
                    eventmatches = eventmatches or ((es == ENDTYPE_SCL_RISING) and event_scl_rising)
                    eventmatches = eventmatches or ((es == ENDTYPE_SCL_FALLING) and event_scl_falling)
                    eventmatches = eventmatches or ((es == ENDTYPE_SCL_ANY) and (event_scl_rising or event_scl_falling))
                    eventmatches = eventmatches or ((es == ENDTYPE_SDA_RISING) and event_sda_rising)
                    eventmatches = eventmatches or ((es == ENDTYPE_SDA_FALLING) and event_sda_falling)
                    eventmatches = eventmatches or ((es == ENDTYPE_SDA_ANY) and (event_sda_rising or event_sda_falling))
                    eventmatches = eventmatches or ((es == ENDTYPE_ANY) and (event_sda_rising or event_sda_falling or event_scl_rising or event_scl_falling))
                        
                    if eventmatches:
                        es = s

                if eventmatches:
                    self.put(ss, es, pipe, data)
                    rm.append(item)
            
            for r in rm:
                self.annotationQueue.remove(r)
                
        
    def decode(self):
        pulseview_mode = False
        mode_identified = False
        # Check for several bus conditions. Determine sample numbers
        # here and pass ss, es, and bit values to handling routines.
        while True:
            scl_state, sda_state = self.wait([{0: 'e'}, {1: 'e'}]) # wait for SCL or SDA to show a clock edge
            ss, es = self.samplenum, self.samplenum
            
            if not mode_identified:
                try:
                    scl_edge = self.matched[0]
                    sda_edge = self.matched[1]
                except:
                    pulseview_mode = True
                mode_identified = True
                
            if pulseview_mode:
                scl_edge = (self.matched & 0b01) != 0
                sda_edge = (self.matched & 0b10) != 0
            else:
                scl_edge = self.matched[0]
                sda_edge = self.matched[1]            

            if True:
            
                scl_rising  = scl_edge and scl_state
                scl_falling = scl_edge and not scl_state
                sda_rising  = sda_edge and sda_state
                sda_falling = sda_edge and not sda_state
            
                #print(scl_rising)
                
                # process annotation queue
                self.processAnnotationQueue(ss, sda_rising, sda_falling, scl_rising, scl_falling)

                # Identify important bus conditions => check what happened
                # note: The order of condition checks is done like this on purpose to prioritize CLK edge changes
                event = event_none
                if scl_rising:
                    event = event_rising_clock
                elif scl_falling:
                    event = event_falling_clock
                elif sda_rising and scl_state:
                    event = event_stop
                elif sda_falling and scl_state:
                    event = event_start
                    

                # Check for HDR Exit, HDR Restart or TARGET Reset pattern
                if (not scl_state) and sda_falling:
                    self.mSpecialConditionDetectionState += 1
                elif event == event_rising_clock:

                    if (self.mSpecialConditionDetectionState == 2) or (self.mSpecialConditionDetectionState == 3):
                        self.protocolevent(ss, protevent_hdr_restart, 0, 0, 0);
                    elif (self.mSpecialConditionDetectionState == 4) or (self.mSpecialConditionDetectionState == 5):
                        self.protocolevent(ss, protevent_hdr_exit, 0, 0, 0);
                    elif (self.mSpecialConditionDetectionState == 7) or (self.mSpecialConditionDetectionState == 8):
                        self.protocolevent(ss, protevent_targetreset, 0, 0, 0);
                    self.mSpecialConditionDetectionState = 0; # reset whenever scl is high
                
                # Interpret events
                if event != event_none:
                    self.decodeevent(ss, scl_state, sda_state, event);

            
    def decodeevent(self, s, scl, sda, event):
        #cls, texts = proto['DEBUG'][0], proto['DEBUG'][1:]
        #texts = [t.format(b = int(self.mStateSdrDecode_state)) for t in texts]
        #self.putg(s, s, cls, texts)

        if self.mMode == mode_sdr:
            # wait for start
            if self.mStateSdrDecode_state == 0: 
                if event == event_start:
                    self.mStateSdrDecode_prevbitpos = None
                    self.mStateSdrDecode_state = 1
                    self.mStateSdrDecode_bitcounter = 0
                    self.mStateSdrDecode_dataword = 0
                    self.protocolevent(s, protevent_start, 0, 0, 0)
                if event == event_stop:
                    self.protocolevent(s, protevent_stop, 0, 0, 0)
                    
            # data bit receiver
            elif self.mStateSdrDecode_state == 1: 
                if event == event_rising_clock:
                    self.mStateSdrDecode_prevbitpos = s
                    self.mStateSdrDecode_prevbitstate = sda
                elif event == event_falling_clock:
                    if not (self.mStateSdrDecode_prevbitpos is None):
                        cls, texts = proto['BIT'][0], proto['BIT'][1:]
                        texts = [t.format(b = int(self.mStateSdrDecode_prevbitstate)) for t in texts]
                        self.putg(self.mStateSdrDecode_prevbitpos, ENDTYPE_SCL_RISING,  cls, texts)

                if self.mentdaa_detector == 5:
                    if event == event_rising_clock:
                        #cls, texts = proto['BIT'][0], proto['BIT'][1:]
                        #texts = [t.format(b = int(sda)) for t in texts]
                        #self.putg(s, ENDTYPE_SCL_RISING,  cls, texts)
                        
                        if self.mStateSdrDecode_bitcounter == 0:
                            self.mStateSdrDecode_bytestartposition = s
                        self.mStateSdrDecode_prevbitpos = s
                        self.mStateSdrDecode_prevbitstate = sda
                        self.mStateSdrDecode_dataword = self.mStateSdrDecode_dataword & ~(1<<(7-self.mStateSdrDecode_bitcounter))
                        if sda:
                            self.mStateSdrDecode_dataword = self.mStateSdrDecode_dataword | (1<<(7-self.mStateSdrDecode_bitcounter))
                        self.mStateSdrDecode_bitcounter += 1
                    if self.mStateSdrDecode_bitcounter >= 8:
                        self.protocolevent([self.mStateSdrDecode_bytestartposition, s], protevent_entdaadata, self.mStateSdrDecode_dataword, 0, 0);
                        if (self.mentdaa_bytecounter == 8): # all 8 ENTDAA payload bytes received?
                            self.mentdaa_detector = 0;
                        self.mIsWriteTransfer = True
                        self.mStateSdrDecode_bitcounter = 0
                        
                elif event == event_rising_clock:
                                        
                    if self.mStateSdrDecode_bitcounter == 0:
                        self.mStateSdrDecode_bytestartposition = s

                    self.mStateSdrDecode_prevbitstate = sda
                    self.mStateSdrDecode_prevbitpos = s

                    self.mStateSdrDecode_dataword = self.mStateSdrDecode_dataword & ~(1<<(7-self.mStateSdrDecode_bitcounter))
                    if sda:
                        self.mStateSdrDecode_dataword = self.mStateSdrDecode_dataword | (1<<(7-self.mStateSdrDecode_bitcounter))
                    self.mStateSdrDecode_bitcounter += 1
                    
                elif (event == event_falling_clock) and (self.mStateSdrDecode_bitcounter == 8): # 2 purposes: add bit and step to bit9 state

                    #cls, texts = proto['BIT'][0], proto['BIT'][1:]
                    #texts = [t.format(b = int(self.mStateSdrDecode_prevbitstate)) for t in texts]
                    #self.putg(self.mStateSdrDecode_prevbitpos, s, cls, texts)

                    self.mStateSdrDecode_bitcounter = 0
                    self.mStateSdrDecode_state = 2
                else: # this effectly checks for start or stop conditions only during first bit phase
                    if event == event_start:
                        self.protocolevent(s, protevent_restart, 0, 0, 0)
                        self.mStateSdrDecode_bitcounter = 0
                    if event == event_stop:
                        self.mStateSdrDecode_state = 0
                        self.protocolevent(s, protevent_stop, 0, 0, 0)

            # check ACK/CONT/TBIT rising and falling edge state (bit 9)
            elif self.mStateSdrDecode_state == 2:
                if event == event_rising_clock:
                    cls, texts = proto['BIT9'][0], proto['BIT9'][1:]
                    texts = [t.format(b = int(sda)) for t in texts]
                    self.putg(s, s, cls, texts)
                    self.mStateSdrDecode_ack_rising = sda
                    self.mStateSdrDecode_bytestopposition = s 
                elif event == event_falling_clock:
                    if self.mIsFirstByte: # On first byte the bit 9 contains ACK/NAK and CONTINUATION bit
                        cls, texts = proto['ACK'][0], proto['ACK'][1:]
                        if self.mStateSdrDecode_ack_rising:
                            txt = 'NAK'
                            txt2 = 'N'
                        else:
                            txt = 'ACK'
                            txt2 = 'A'
                        texts[0] = txt
                        texts[1] = txt2
                        self.putg(self.mStateSdrDecode_bytestopposition, s, cls, texts)

                        cls, texts = proto['ACK'][0], proto['ACK'][1:]
                        if not sda:
                            txt = 'CONT'
                            txt2 = 'C'
                            texts[0] = txt
                            texts[1] = txt2
                        else:
                            txt = 'ABORT'
                            txt2 = 'AB'
                            texts[0] = txt
                            texts[1] = txt2
                        self.putg(s, ENDTYPE_SCL_RISING, cls, texts)
                        
                    else:
                        if self.mIsWriteTransfer: # parity bit
                            cls, texts = proto['SDR PARITY'][0], proto['SDR PARITY'][1:]
                            texts = [t.format(b = int(sda)) for t in texts]
                            self.putg(self.mStateSdrDecode_bytestopposition, ENDTYPE_SCL_RISING, cls, texts)
                        else: # CONTINUATION from controller and CONTINUATION from target
                            cls, texts = proto['ACK'][0], proto['ACK'][1:]
                            if self.mStateSdrDecode_ack_rising:
                                txt = 'CONT'
                                txt2 = 'C'
                                texts[0] = txt
                                texts[1] = txt2
                            else:
                                txt = 'ABORT'
                                txt2 = 'AB'
                                texts[0] = txt
                                texts[1] = txt2
                            self.putg(self.mStateSdrDecode_bytestopposition, s, cls, texts)
                            
                            cls, texts = proto['ACK'][0], proto['ACK'][1:]
                            if sda:
                                txt = 'CONT'
                                txt2 = 'C'
                                texts[0] = txt
                                texts[1] = txt2
                            else:
                                txt = 'ABORT'
                                txt2 = 'AB'
                                texts[0] = txt
                                texts[1] = txt2
                            self.putg(s, ENDTYPE_SCL_RISING, cls, texts)
                            
                            pass #self.putg(self.mStateSdrDecode_bytestopposition, s, cls, texts)
                    
                    # update bits pane
                    cls, texts = proto['BIT9'][0], proto['BIT9'][1:]
                    texts = [t.format(b = int(sda)) for t in texts]
                    self.putg(s, s, cls, texts)
                    
                    self.mStateSdrDecode_ack_falling = sda
                    self.protocolevent([self.mStateSdrDecode_bytestartposition, self.mStateSdrDecode_bytestopposition], protevent_data, self.mStateSdrDecode_dataword, self.mStateSdrDecode_ack_rising, self.mStateSdrDecode_ack_falling)                    
                    self.mStateSdrDecode_state= 1
            # unexpected state - we should never get here
            else:
                self.mStateSdrDecode_state = 0;
                
        elif self.mMode == mode_ddr:
            
            if (event == event_rising_clock) or (event == event_falling_clock):
                if self.mStateDdrDecode_bitcounter == 0:
                    self.mStateSdrDecode_bytestartposition = s

                # Don't add bit 10 of CRC dataword
                suppress = False
                if not self.mIsFirstByte:
                    suppress = (self.ddr_preamble == 1) and (self.mStateDdrDecode_bitcounter > 8)
    
                if not suppress:
                    cls, texts = proto['BIT'][0], proto['BIT'][1:]
                    texts = [t.format(b = int(sda)) for t in texts]
                    self.putg(s, ENDTYPE_SCL_ANY, cls, texts)

                self.mStateDdrDecode_dataword = self.mStateDdrDecode_dataword & ~(1<<(19-self.mStateDdrDecode_bitcounter))
                if sda:
                    self.mStateDdrDecode_dataword = self.mStateDdrDecode_dataword | (1<<(19-self.mStateDdrDecode_bitcounter))
                self.mStateDdrDecode_bitcounter += 1

                
                if self.mStateDdrDecode_state == 0: # preamble state                                
                
                    if self.mStateDdrDecode_bitcounter == 2:
                        self.ddr_preamble = self.mStateDdrDecode_dataword >> 18
                        self.protocolevent([self.mStateSdrDecode_bytestartposition, ENDTYPE_SCL_ANY], protevent_hdr_preamble, self.ddr_preamble, 0, 0)
                        self.mStateDdrDecode_dataword = 0
                        self.mStateDdrDecode_bitcounter = 0
                        self.mStateDdrDecode_state = 1
                        
                elif self.mStateDdrDecode_state == 1: # datastate
                                            
                    if self.mStateDdrDecode_bitcounter == 16:
                        self.mStateDdrDecode_dataword = self.mStateDdrDecode_dataword >> 4
                        self.protocolevent([self.mStateSdrDecode_bytestartposition, ENDTYPE_SCL_ANY], protevent_hdr_dataword, self.mStateDdrDecode_dataword, 0, 0)
                        self.mStateDdrDecode_dataword = 0
                        self.mStateDdrDecode_bitcounter = 0
                        self.mStateDdrDecode_state = 2
                    elif (self.mStateDdrDecode_bitcounter == 10) and ((self.ddr_preamble) == 1) and (not self.mIsFirstByte):
                        self.mStateDdrDecode_dataword = self.mStateDdrDecode_dataword >> 10
                        self.protocolevent([self.mStateSdrDecode_bytestartposition, ENDTYPE_ANY], protevent_hdr_crcword, self.mStateDdrDecode_dataword>>1, 0, 0);
                        self.mStateDdrDecode_dataword = 0
                        self.mStateDdrDecode_bitcounter = 0
                        self.mStateDdrDecode_state = 0
                        
                elif self.mStateDdrDecode_state == 2: # parity state
                    if self.mStateDdrDecode_bitcounter == 2:
                        self.mStateDdrDecode_dataword = self.mStateDdrDecode_dataword >> 18
                        self.protocolevent([self.mStateSdrDecode_bytestartposition, ENDTYPE_SCL_ANY], protevent_hdr_parity, self.mStateDdrDecode_dataword, 0, 0)
                        self.mStateDdrDecode_dataword = 0
                        self.mStateDdrDecode_bitcounter = 0
                        self.mStateDdrDecode_state = 0
        
    def protocolevent(self, s, event, dataword, ack_rising, ack_falling):
        # cls, texts = proto['DEBUG'][0], proto['DEBUG'][1:]
        # texts = [t.format(text = 'a_'+str(self.mIsWriteTransfer)) for t in texts]
        # u = s
        # if type(u) is list:
        #     u = u[0]
        # self.putg(u, u, cls, texts)
        
        if event == protevent_hdr_preamble:
            cmd = 'HDR PREAMBLE'
            cls, texts = proto[cmd][0], proto[cmd][1:]
            texts = [t.format(b = dataword) for t in texts]
            self.putg(s[0], s[1], cls, texts)
        if event == protevent_hdr_parity:
            cmd = 'HDR PARITY'
            cls, texts = proto[cmd][0], proto[cmd][1:]
            texts = [t.format(b = dataword) for t in texts]
            self.putg(s[0], s[1], cls, texts)
        elif event == protevent_hdr_restart:
            self.mIsFirstByte = True
            

            self.putp(s, s, ['HDR RESTART', None])
            cls, texts = proto['HDR RESTART'][0], proto['HDR RESTART'][1:]
            self.putg(s, s, cls, texts)


        elif event == protevent_hdr_exit:
            self.mMode = mode_sdr; # back to SDR decoding mode
            self.mStateSdrDecode_state = 0;
            self.mentdaa_detector = 0;
            self.menthdr_detector = 0;
            
            self.putp(s, s, ['HDR EXIT', None])
            cls, texts = proto['HDR EXIT'][0], proto['HDR EXIT'][1:]
            self.putg(s, s, cls, texts)
            
            
        elif event == protevent_targetreset:
            self.mStateSdrDecode_state = 0;
            self.mentdaa_detector = 0;
            self.menthdr_detector = 0;
            self.putp(s, s, ['RESET', None])
            cls, texts = proto['RESET'][0], proto['RESET'][1:]
            self.putg(s, s, cls, texts)
            self.mentdaa_detector = 0
            self.menthdr_detector = 0
            self.mMode = mode_sdr
            
        elif event == protevent_start:
            self.mIsFirstByte = True
            self.putp(s, s, ['START', None])
            cls, texts = proto['START'][0], proto['START'][1:]
            self.putg(s, s, cls, texts)
            self.mentdaa_detector = 1;
            self.menthdr_detector = 1;
            
        elif event == protevent_restart:
            self.mIsFirstByte = True
            self.putp(s, s, ['START REPEAT', None])
            cls, texts = proto['START REPEAT'][0], proto['START REPEAT'][1:]
            self.putg(s, s, cls, texts)
            if self.mentdaa_detector == 3:
            	self.mentdaa_detector = 4
            else:
                self.menthdr_detector = 1
            
        elif event == protevent_stop:
            self.putp(s, s, ['STOP', None])
            cls, texts = proto['STOP'][0], proto['STOP'][1:]
            self.putg(s, s, cls, texts)
            self.mentdaa_detector = 0
            self.menthdr_detector = 0

        elif event == protevent_entdaadata:
            self.mentdaa_bytecounter += 1
            cmd = 'ENTDAA DATA'

            #cls, texts = proto['BIT'][0], proto['BIT'][1:]
            #texts = [t.format(b = int(self.mStateSdrDecode_prevbitstate)) for t in texts]
            #self.putg(self.mStateSdrDecode_prevbitpos, s, cls, texts)

            cls, texts = proto[cmd][0], proto[cmd][1:]
            texts = [t.format(b = dataword) for t in texts]
            self.putg(s[0], ENDTYPE_SCL_RISING, cls, texts)

            
        elif event == protevent_data:
            # enthdr detector
            if (self.menthdr_detector == 1) and (dataword == (0x7e<<1)) and (not ack_rising):
                self.menthdr_detector = 2
            elif (self.menthdr_detector == 2) and (not ack_rising) and (dataword >= 0x20) and (dataword <= 0x23):
                self.mMode = mode_ddr
                self.mStateDdrDecode_bitcounter = 0
                self.mIsFirstByte = True
                
            # entdaa detector
            if (self.mentdaa_detector == 1) and (dataword == (0x7e<<1)) and (not ack_rising):
                self.mentdaa_detector = 2
            elif (self.mentdaa_detector == 2) and (dataword == 0x07) and (not ack_rising):
                self.mentdaa_detector = 3
            elif (self.mentdaa_detector == 4) and (dataword == ((0x7e<<1) | 1)) and (not ack_rising):
                self.mentdaa_detector = 5
                self.mentdaa_bytecounter = 0
            elif self.mentdaa_detector >= 5:
                # purposefully do nothing
                pass
            else:
                self.mentdaa_detector = 0                
                                                
            
            if self.mIsFirstByte:
                cmd = 'ADDRESS '
                self.mIsWriteTransfer = ((dataword & 1) == 0)
                dataword = dataword >> 1
                self.mIsFirstByte = False
            else:
                cmd = 'DATA '

            if self.mIsWriteTransfer:
                cmd += 'WRITE'
            else:
                cmd += 'READ'
            cls, texts = proto[cmd][0], proto[cmd][1:]
            texts = [t.format(b = dataword) for t in texts]
            self.putg(s[0], s[1], cls, texts)

            if self.mMode == mode_ddr:
                self.mIsFirstByte = True;
            
        elif event == protevent_hdr_dataword:
            if self.mIsFirstByte:
                cmd = 'HDR CMD'
                self.mIsFirstByte = False
                self.mIsWriteTransfer = ((dataword & (1<<15)) == 0)
            else:
                cmd = 'DATA '

                if self.mIsWriteTransfer:
                    cmd += 'WRITE'
                else:
                    cmd += 'READ'
            cls, texts = proto[cmd][0], proto[cmd][1:]
            texts = [t.format(b = dataword) for t in texts]
            self.putg(s[0], s[1], cls, texts)
            
        elif event == protevent_hdr_crcword:
            cmd = 'CRC'

            cls, texts = proto[cmd][0], proto[cmd][1:]
            texts = [t.format(b = dataword) for t in texts]
            self.putg(s[0], s[1], cls, texts)
