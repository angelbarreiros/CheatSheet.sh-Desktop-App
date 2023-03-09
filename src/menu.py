from os.path import abspath, dirname, join, realpath
from pathlib import Path
import gettext
import locale
import gi
import views

gi.require_version('Gtk', '4.0')

APP = 'cheatsheet'
WHERE_AM_I = abspath(dirname(realpath(__file__)))
LOCALE_DIR = Path(__file__).parent / "locale"

locale.setlocale(locale.LC_ALL, locale.getlocale())
locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

from gi.repository import Gtk


class MenuButton(Gtk.MenuButton):
    def __init__(self, xml, name, icon_name='open-menu-symbolic'):
        super(MenuButton, self).__init__()
        self.builder = Gtk.Builder()
        self.glade_file = join(WHERE_AM_I, 'menu.glade')
        self.builder.set_translation_domain(APP)
        self.builder.add_from_file(self.glade_file)



        menu = self.builder.get_object(name)
        self.set_menu_model(menu)
        self.set_icon_name(icon_name)
