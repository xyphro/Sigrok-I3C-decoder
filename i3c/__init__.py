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

'''
I3C (spoken: "Eye-three-see") is a bidirectional, 
bus using two signals (SCL = serial clock line, SDA = serial data line).
It's roots are from I²C protocol with several improvements.
The specification is owned by MIPI Alliance. 
This decoder implements SDR and HDR_DDR mode support. 
EntDAA data which does not follow normal SDR framing is also correctly decoded.
'''

from .pd import Decoder
