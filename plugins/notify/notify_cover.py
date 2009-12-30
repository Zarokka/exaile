# Copyright (C) 2009 Abhishek Mukherjee <abhishek.mukher.g@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 1, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import logging
from xlgui import cover as guicover

logger = logging.getLogger(__name__)

RESIZE_SIZE = 48

def get_image_for_track(track, exaile, resize=False):
    '''Get a Pixbuf for a track

    If resize is True, the image will be resized so the maximum dimension is
    RESIZE_SIZE

    '''
    data = exaile.covers.get_cover(track)
    if resize:
        scale = (RESIZE_SIZE, RESIZE_SIZE)
    else:
        scale = None
    pixbuf = guicover.pixbuf_from_data(data, scale=scale)
    return pixbuf

