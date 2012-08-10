# Copyright (C) 2012 Mathias Brodala
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
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

from xl import settings

def migrate():
    """
        Enables the OSD plugin if the builtin OSD was originally enabled
    """
    plugins = settings.get_option('plugins/enabled', [])

    if settings.get_option('osd/enabled', True) and not 'osd' in plugins:
        settings.set_option('plugins/enabled', plugins + ['osd'])
