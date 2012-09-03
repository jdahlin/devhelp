#!/usr/bin/env python
import os
import string
import urllib

ROOT="/var/www/doc/devhelp/"

import GDK
from gnome.uiconsts import *

import gtk
import gnome.ui
import libglade
try:
    import gtkhtml
except:
    print "You must compile gnome-python with gtkhtml support."
    raise SystemExit

BOOK_DIRS = [ROOT+'books']
history = []
def does_dict_have_keys (dict, keys):
    for key in keys:
	if not dict.has_key (key):
	    return 0
    if len(dict) != len(keys):
	return 0
    return 1

class HTMLWidget (gtk.GtkScrolledWindow):
    def __init__ (self):
	self.location = ""
	self.base = ""
	gtk.GtkScrolledWindow.__init__ (self)
	self.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	
	self.html = gtkhtml.GtkHTML ()
	self.html.connect ('link_clicked', self.link_clicked)
	self.html.connect ('load_done', self.load_done)
	self.html.load_empty ()
	self.add (self.html)
	    
    def load_url (self, url):
	print "URL:", url
	history.append (url)
	load = 1; jump = 0
	pos = string.find (url, "#")

	if url[:pos] == self.location and self.location:
	    load = 0; jump = 1
	    self.location = url[:pos]
	elif pos != -1:
	    jump = 1
            self.location = url[:pos]
	else:
	    self.location = url
	    
	# Find base for hrefs
	base_pos = string.rfind (url, "/")
	if base_pos != -1:
	    self.base = url[:base_pos+1]
	if string.find (url, "/") != -1:
	    string.split (url, "/")
	if load:
	    try:
		data = urllib.urlopen (ROOT+"books/" + self.location).read()
	    except:
		data = urllib.urlopen (ROOT+"books/" + self.base + self.location).read()
	    
	    handle = self.html.begin()
	    self.html.write (handle, data)
	    self.html.end (handle, gtkhtml.HTML_STREAM_OK)
	
	# Do we need to jump to the correct anchor?
	if jump:
	    anchor = url[pos+1:]
	    self.html.jump_to_anchor (anchor)
	    
    def link_clicked (self, html, url):
	print "Clicked on", url
	self.load_url (url)
	
    def load_done (self, html):
	pos = string.find (self.location, "#")
	
	if pos != -1:
	    html.jump_to_anchor (self.location[pos+1:])
	
class MainWin:
    def __init__ (self):
	self.load_books()
	self.create_ui()
	self.update_tree()
	self.win.show_all()
	
    def load_books (self):
	self.books = []
	for book_dir in BOOK_DIRS:
	    path = os.path.abspath (book_dir)
	    if not os.path.isdir (path):
		print "Error, BOOKDIR", book_dir, "does not exist"
		raise SystemExit
	    
	    books = os.listdir (path)
	    for book in books:
		test = "%s/%s/%s.book" % (path, book, book)
		if not os.path.exists (test):
		    print test, "does not exist"
		    
		data = eval (open (test).read())
		if not data in self.books:
		    self.books.append (data)
		
	self.books.sort(lambda x, y: cmp (x["name"], y["name"]))
	
    def create_ui (self):
	w = libglade.GladeXML (ROOT+"misc/devhelp.glade")
	
	self.win = w.get_widget ("app1")
	self.win.connect ("delete_event", self.destroy)

	self.menu_exit = w.get_widget ("menu_exit")
	self.menu_exit.connect ('activate', self.menu_file_exit)
	
	self.menu_about = w.get_widget ('menu_about')
	self.menu_about.connect ('activate', self.menu_file_about)
	
	self.tree = w.get_widget ("ctree1")
	self.tree.connect ("tree_select_row", self.select_row)
	
	self.hpaned = w.get_widget ("hpaned1")
	
	self.html = HTMLWidget()
	self.html.html.connect ('on_url', self.on_url)
	self.html.html.connect ('enter_notify_event', self.html_enter)
	self.hpaned.add2 (self.html)
	self.hpaned.set_position (180)
	
	self.statusbar = w.get_widget ("appbar1")
	self.book_closed_icon = gtk.create_pixmap_from_xpm (self.win, None,
    ROOT+"images/book_red.xpm")
	self.book_opened_icon = gtk.create_pixmap_from_xpm (self.win, None,
    ROOT+"images/book_open.xpm")
	
    def destroy (self, *args):
	gtk.mainquit()
	
    def on_url (self, gtkhtml, link):
	if link:
	    self.statusbar.push ("Link to %s" % link)
	else:
	    self.statusbar.pop ()
	    
    def menu_file_exit (self, *args):
	gtk.mainquit()
	
    def menu_file_about (self, *args):
	about = gnome.ui.GnomeAbout ('devhelp', '0.1.0', 'Copyright 2001 Johan Dahlin',
	                             ['Johan Dahlin'], 'A developers help program')
	about.show()

    def html_enter (self, html, event):
	self.statusbar.clear_stack()
	
    def select_row (self, ctree, node, col):
	data = ctree.node_get_row_data (node)
	if data in ['Book', 'Chapter']:
	    return

	self.html.load_url (data)
	
    def update_tree (self):
	self.oldlevel = 0
	
	# For every book ...
	for book in self.books:
	    root = self.insert_node (book['name'], "Book", pixmap_closed=self.book_closed_icon[0],
	                                                   pixmap_opened=self.book_opened_icon[0],
							   mask_closed=self.book_closed_icon[1],
							   mask_opened=self.book_opened_icon[1])
	    # For each chapter ...
	    for chap in book['order']:
#		print chap
		if does_dict_have_keys (book[chap], ['desc', 'link']):
		    chapnode = self.insert_node (chap, book[chap]['link'], root)
		    continue
		else:
		    chapnode = self.insert_node (chap, "Chapter", root, pixmap_closed=self.book_closed_icon[0],
	                                                                pixmap_opened=self.book_opened_icon[0],
		    	     				                mask_closed=self.book_closed_icon[1],
							                mask_opened=self.book_opened_icon[1])
		if not book[chap].has_key ('order'):
		    continue
		
		for chap2 in book[chap]['order']:
		    chapnode2 = self.insert_node (chap2, book[chap][chap2]['link'], chapnode)
		
		    if not book[chap][chap2].has_key ('order'):
			continue
		
		    for chap3 in book[chap][chap2]['order']:
			self.insert_node (chap3, book[chap][chap2][chap3]['link'], chapnode2)
			
    def insert_node (self, text, data, parent=None, **kwargs):
	node = self.tree.insert_node (parent, None, [text], is_leaf=gtk.FALSE, **kwargs)
	self.tree.node_set_row_data (node, data)
	return node

MainWin()
gtk.mainloop()    
