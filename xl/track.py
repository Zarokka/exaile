# Copyright (C) 2006 Adam Olsen
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

import os, threading, httplib, xlmisc, md5, re, common, library
import xl.trackslist
import media, gc
from urllib import urlencode
import urllib
from gettext import gettext as _, ngettext

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, pango

def update_info(nb, track):
    """
        Changes the information in the info tab if it's already open
    """
    for i in range(0, nb.get_n_pages()):
        page = nb.get_nth_page(i)
        if isinstance(page, TrackInformation):
            page.setup_tabs(track)

def show_information(exaile, track):
    """
        Shows track information
    """
    nb = exaile.playlists_nb
    for i in range(0, nb.get_n_pages()):
        page = nb.get_nth_page(i)
        if isinstance(page, TrackInformation):
            page.setup_tabs(track)
            page.set_current_page(i)
            return page

    return TrackInformation(exaile, track)

class TablatureTab(gtk.VBox):
    """
        Downloads and displays guitar tablature
    """
    REGEX = re.compile("<PRE>(.*)</PRE>", re.DOTALL)
    def __init__(self, panel, track):
        """
            Initializes the panel
        """
        gtk.VBox.__init__(self)
        self.set_border_width(5)
        self.set_spacing(3)
        self.exaile = panel.exaile
        self.panel = panel
        self.stopped = False

        text = gtk.TextView()
        text.set_editable(False)

        text.modify_font(pango.FontDescription("Monospace 11"))
        self.text = text.get_buffer()

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(text)

        self.text.set_text("Downloading tablature...")
        self.fetched = False
        self.pack_start(scroll, True, True)
        
        self.track = track
        self.artist = track.artist.replace(" ", "_").lower()
        self.letter = self.artist[:1]
        self.title = track.title.replace(" ", "_").lower()
        self.url = "http://www.fretplay.com/tabs/%s/%s/%s-tab.shtml" % \
            (self.letter, self.artist, self.title)
        self.cache_file = "%s/cache/tablature_%s.tablature" % \
            (self.exaile.get_settings_dir(),
            md5.new(self.url).hexdigest())
        if os.path.isfile(self.cache_file):
            h = open(self.cache_file, 'r')
            self.fetched = True
            self.text.set_text(h.read())
            h.close()
        self.update()
        self.show_all()

    def update(self):       
        """
            Called when this tab is selected
        """
        if self.fetched: return
        else:
            self.fetched = False
            xlmisc.log(self.url)
            xlmisc.URLFetcher("www.fretplay.com", "/tabs/%s/%s/%s-tab.shtml" % \
                (self.letter, self.artist, self.title), self.updated).start()

    def updated(self, url, text):
        """
            Called when the text has been fetched.
        """
        if self.track != self.panel.track or \
            self.stopped: return
        m = self.REGEX.search(text)
        if m:
            text = m.group(1)
            text = re.sub("^\s*", "", text)
        else:
            self.text.set_text("Could not fetch tablature.")
        if "Error 302" in text:
            text = "Tablature not found."
        xlmisc.log(self.cache_file)
        if self.track != self.panel.track or \
            self.stopped: return
        self.text.set_text(text)
        h = open(self.cache_file, 'w')
        h.write(text)
        h.close()            

    def close_page(self):   
        """
            Called when this tab is closed
        """
        self.stopped = True

class LyricsTab(gtk.VBox):
    """
        Downloads and displays track lyrics
    """
    def __init__(self, exaile, panel, track):
        """
            Initializes the panel
        """
        gtk.VBox.__init__(self)
        self.set_border_width(5)
        self.set_spacing(3)
        self.exaile = exaile
        self.panel = panel
        self.track = track
        self.text = xlmisc.BrowserWindow(exaile, None)#, True) 
        self.pack_start(self.text, True, True)

        self.show_all()
        self.lyrics = self.text
        self.lyrics.set_text("Downloading lyrics, please wait...") 
        self.update()

    def update(self):
        """
            Called when this tab is selected
        """
        params = {'artist': self.track.artist.encode('latin1'), 'songname': self.track.title.encode('latin1')}

#        search = "http://lyrc.com.ar/en/tema1en.php?%s" % urlencode(params)
        search = "http://lyricwiki.org/api.php?artist=%s&song=%s&fmt=html" % (
            urllib.quote_plus(params['artist']), 
            urllib.quote_plus(params['songname']))
        print search
        self.lyrics.load_url(search, self.text.action_count, False)

    def close_page(self):
        """
            Called when this tab is closed
        """
        self.text.stopped = True

class WikipediaTab(gtk.HBox):
    """
        Shows a wikipedia page
    """
    def __init__(self, exaile, url):
        """
            Initializes the panel
        """
        gtk.HBox.__init__(self)
        self.browser = xlmisc.BrowserWindow(exaile, url)
        self.pack_start(self.browser, True, True)
        self.show_all()

    def close_page(self):
        """
            called when this tab is closed
        """
        self.browser.stopped = True

class TrackStatsTab(gtk.ScrolledWindow):
    """
        Track Statistics
    """
    def __init__(self, exaile, track):
        """
            Initializes the tab
        """
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_border_width(5)

        self.table = table = gtk.Table(12, 2, False) # initialize 12 rows
        table.set_row_spacings(3)
        self.add_with_viewport(table)

        self.db = exaile.db
        self.n_rows = 0

        self.setup_information(track)
        table.resize(self.n_rows, 2)

        self.show_all()

    def setup_information(self, track):
        """
            Adds the specific information fields for this track
        """
        path_id = library.get_column_id(self.db, 'paths', 'name', track.loc)
        row = self.db.read_one("tracks", "plays, rating", "path=?", 
            (path_id,))

        playcount = 0
        rating = 0
        if row:
            playcount = row[0]
            rating = row[1]
        self.append_info(_("Title: "), track.title)
        self.append_info(_("Artist:" ), track.artist)
        self.append_info(_("Album:"), track.album)
        if track.track and track.track > -1: 
            self.append_info(_("Track Number:"), str(track.track))
        self.append_info(_("Year:"), track.year)
        self.append_info(_("Genre:"), track.genre)
        self.append_info(_("Bitrate:"), str(track.bitrate))
        if track.rating: self.append_info(_("User Rating:"), track.rating)
        self.append_info(_("System Rating:"), str(rating))
        if playcount >= 0: self.append_info(_("Playcount:"), str(playcount))
        self.append_info(_("Location: "), track.loc.encode(xlmisc.get_default_encoding()))

    def append_info(self, label, string):
        """
            Appends an information line
        """
        label = gtk.Label(label)
        label.set_alignment(0, 0)
        attr = pango.AttrList()
        attr.change(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 800))
        label.set_attributes(attr)

        self.table.attach(label, 0, 1, self.n_rows, self.n_rows +1,
            gtk.EXPAND | gtk.FILL, gtk.FILL)

        if isinstance(string, unicode) or isinstance(string, str) or \
            isinstance(string, int):
            label = gtk.Label(unicode(string))
            label.set_alignment(0, 0)
            label.set_line_wrap(True)
            label.set_selectable(True)
            self.table.attach(label, 1, 2, self.n_rows, self.n_rows + 1,
                gtk.EXPAND | gtk.FILL, gtk.FILL)
        else:
            self.table.attach(string, 1, 2, self.n_rows, self.n_rows + 1,
                gtk.EXPAND | gtk.FILL, gtk.FILL)

        self.n_rows += 1;

    def close_page(self):
        """
            Called when this tab is closed
        """
        pass

class RadioTrackStatsTab(TrackStatsTab):
    """
        Track statistic for shoutcase streams
    """
    def __init__(self, exaile, track):
        TrackStatsTab.__init__(self, exaile, track)

    def setup_information(self, track):
        """
            Sets up the specific information fields for this track
        """

        self.append_info(_("Title: "), track.title)
        self.append_info(_("Description: "), track.artist)

        location = gtk.Entry()
        location.set_text(track.loc)
        location.set_editable(False)
        self.append_info(_("Location: "), location)
        self.append_info(_("Bitrate: "), track.bitrate)

class TrackInformation(gtk.Notebook):
    """
        Shows information regarding a track
    """
    def __init__(self, exaile, track):
        """
            Initializes the track information page
        """
        gtk.Notebook.__init__(self)
        self.exaile = exaile
        self.db = exaile.db

        self.setup_tabs(track)
        self.show_all()
        self.type = 'information'

        self.exaile.playlists_nb.append_page(self, xlmisc.NotebookTab(exaile,
            _("Information"), self))
        self.exaile.playlists_nb.set_current_page(
            self.exaile.playlists_nb.get_n_pages() - 1)

    def setup_tabs(self, track):
        """
            Sets up the tabs for the specified track
        """
        self.track = track
        for i in range(0, self.get_n_pages()):
            self.remove_page(0)

        if track.type == 'stream': 
            self.append_page(RadioTrackStatsTab(self.exaile, track),
                gtk.Label(_("Stream Statistics")))
        
        self.append_page(TrackStatsTab(self.exaile, track), gtk.Label(_("Statistics")))
        locale = self.exaile.settings.get_str('wikipedia_locale', 'en')
        
        if xlmisc.mozembed:
            artist = "http://%s.wikipedia.org/wiki/%s" % (locale, track.artist)
            artist = artist.replace(" ", "_")
            self.append_page(WikipediaTab(self.exaile, artist),
                gtk.Label(_("Artist")))
            
            album = "http://%s.wikipedia.org/wiki/%s" % (locale, track.album)
            album = album.replace(" ", "_")
            self.append_page(WikipediaTab(self.exaile, album),
                gtk.Label(_("Album")))
            self.append_page(LyricsTab(self.exaile, self, track),
                gtk.Label(_("Lyrics")))
            self.append_page(TablatureTab(self, track),
                gtk.Label(_("Tablature")))
        else:
            xlmisc.log("gnome-extras not available.  Showing basic"
                       " track information only")
        self.show_all()

    def close_page(self):
        """
            Called when this tab in the notebook is closed
        """
        for i in range(self.get_n_pages()):
            page = self.get_nth_page(i)
            page.close_page()

class TrackEditor(object):
    """
        A track properties editor
    """
    def __init__(self, exaile, tracks):
        """
            Inizializes the panel 
        """
        self.exaile = exaile
        self.db = exaile.db
        self.xml = gtk.glade.XML('exaile.glade', 'TrackEditorDialog', 'exaile')
        self.dialog = self.xml.get_widget('TrackEditorDialog')
        self.dialog.set_transient_for(self.exaile.window)
        self.action_area = self.xml.get_widget('track_editor_action_area')

        self.tracks = tracks
        self.songs = tracks.get_selected_tracks()
        track = self.songs[0]
        self.count = len(self.songs)
        self.get_widgets()


        self.artist_entry.set_text(track.artist)
        self.album_entry.set_text(track.album)
        self.genre_entry.set_text(track.genre)
        self.year_entry.set_text(track.year)
        self.disc_id_entry.set_text(str(track.disc_id))

        if self.count > 1:
            self.title_entry.hide()
            self.track_entry.hide()
            self.title_label.hide()
            self.track_label.hide()
        else:
            num = track.track
            if num == -1: num = ''
            self.title_entry.set_text(track.title)
            self.track_entry.set_text(str(num))

        self.cancel.connect('clicked', lambda e: self.dialog.destroy())
        self.save.connect('clicked', self.on_save)

        self.dialog.show()

    def get_widgets(self):
        """
            Gets all widgets from the glade definition file
        """
        xml = self.xml
        self.title_label = xml.get_widget('te_title_label')
        self.title_entry = xml.get_widget('te_title_entry')

        self.artist_entry = xml.get_widget('te_artist_entry')
        self.album_entry = xml.get_widget('te_album_entry')
        self.genre_entry = xml.get_widget('te_genre_entry')
        self.year_entry = xml.get_widget('te_year_entry')
        self.track_label = xml.get_widget('te_track_label')
        self.track_entry = xml.get_widget('te_track_entry')
        self.disc_id_entry = xml.get_widget('te_disc_id_entry')
        self.cancel = xml.get_widget('te_cancel_button')
        self.save = xml.get_widget('te_save_button')

    def on_save(self, widget):
        """
            Writes the information to the tracks.  Called when the user clicks
            save
        """
        errors = []
        for track in self.songs:
            xlmisc.finish()

            if track.type == 'stream' or track.type == 'cd':
                errors.append("Could not write track %s" % track.loc)
                continue

            if self.count == 1:
                track.title = self.title_entry.get_text()
                track.track = self.track_entry.get_text()

            track.artist = self.artist_entry.get_text()
            
            track.album = self.album_entry.get_text()
            track.genre = self.genre_entry.get_text()
            track.year = self.year_entry.get_text()
            track.disc_id = self.disc_id_entry.get_text()
            try:
                db = self.exaile.db
                media.write_tag(track)
                library.save_track_to_db(db, track)
                self.exaile.tracks.refresh_row(track)
            except:
                errors.append("Unknown error writing tag for %s" % track.loc)
                xlmisc.log_exception()

        self.exaile.tracks.queue_draw()

        self.exaile.db.db.commit()
        if errors:
            message = ""
            count = 1
            for error in errors:
                message += "%d: %s\n" % (count, error)
                count += 1
            self.dialog.hide()
            common.scrolledMessageDialog(self.exaile.window, message, _("Some errors"
                " occurred"))    
        else:
            self.dialog.destroy()


def edit_field(caller, data):
    """
        Edits one field in a list of tracks
    """
    songs = caller.get_selected_tracks()
    if not songs: return
    text = getattr(songs[0], data)

    dialog = common.TextEntryDialog(
        caller.exaile.window, 
        ngettext("Enter the %s for the selected track",
            "Enter the %s for the selected tracks", len(songs)) %
            _(data.capitalize()),
        _("Edit %s") % _(data.capitalize()))
    dialog.set_value(text)

    if dialog.run() == gtk.RESPONSE_OK:
        value = dialog.get_value()
        errors = ''
        for song in songs:
            setattr(song, data, value)
            try:
                media.write_tag(song)    
                library.save_track_to_db(caller.db, song)
            except:
                errors += "Could not write tag for %s\n" % song.loc
                xlmisc.log_exception()

            xlmisc.finish()
            if isinstance(caller, xl.trackslist.TracksListCtrl):
                caller.refresh_row(song)

        if errors:
            common.scrolledMessageDialog(caller.exaile.window,
                errors, "Error writing tags")                    
        
    dialog.destroy()

def update_rating(caller, num):
    """
        Updates the rating based on which menu id was clicked
    """
    rating = num + 1

    cur = caller.db.cursor()
    for track in caller.get_selected_tracks():
        
        path_id = library.get_column_id(caller.db, 'paths', 'name',
            track.loc)
        caller.db.execute("UPDATE tracks SET user_rating=? WHERE path=?",
            (rating, path_id)) 
        track.rating = rating
        if isinstance(caller, xl.trackslist.TracksListCtrl):
            caller.refresh_row(track)
