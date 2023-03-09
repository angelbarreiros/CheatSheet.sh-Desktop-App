import gettext
import os

from curses import window
from typing import Callable
from menu import MenuButton

_ = gettext.gettext
N_ = gettext.ngettext

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, Gdk, GLib

menu_text = open('menu.glade','r')
APP_MENU = menu_text.read()

css_provider = Gtk.CssProvider()
css_provider.load_from_file(Gio.File.new_for_path("style.css"))
Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider,
                                          Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def run(on_activate: Callable) -> None:
    app = Gtk.Application()
    app.connect('activate', on_activate)
    app.run(None)

def create_action(self, name, callback):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    self.add_action(action)

class View:
    run_on_main_thread = GLib.idle_add

    def on_activate(self, app: Gtk.Application) -> None:
        self.build(app)

    def set_handler(self, handler) -> None:
        self.handler = handler

    def build(self, app: Gtk.Application) -> None:
        # ventana para el acerca de
        self.acercade = self.create_acercade()

        self.window = Gtk.ApplicationWindow(
            title="CheatSheet",
            default_width=1200,
            default_height=500
        )
        self.window.connect("close-request",self.on_close_request)

        # se crea el contenedor de todos los demas widgets
        background = Gtk.Box()
        background.set_orientation(Gtk.Orientation.VERTICAL)
        background.set_spacing(5)
        # se crea el contenedor de todos los demas widgets(panel para que se pueda deslizar)
        self.background = Gtk.Paned()

        # search bar principal 
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text(_("Search..."))
        self.entry.connect('activate', self.handler.on_entry_activate)

        # Spinner
        self.spinner = Gtk.Spinner()
        self.spinner.hide()

        # se crea un contenedor para el spinner y la search bar
        boxse = Gtk.Box()
        boxse.set_orientation(Gtk.Orientation.HORIZONTAL)
        boxse.set_spacing(5)
        boxse.append(self.entry)
        boxse.append(self.spinner)

        # boton para cancelar la busqueda
        self.cancelar = Gtk.Button(label=_("Cancel"))
        self.cancelar.connect("clicked", self.handler.cancel_clicked)
        self.cancelar.hide()

        # De aqui sale el menu , que llama a otro clase que esta en el fichero menu y utiliza xml para construirlo
        menu = MenuButton(APP_MENU, 'app-menu')

        # añadir las acciones desde xml al menu->esta la funcion create_action arriba del todo
        create_action(self.window, 'acerca', self.handler.menu_acercade)
        create_action(self.window, 'buscar', self.handler.menu_buscar)
        create_action(self.window, 'favs', self.handler.menu_favs)

        # scrolled window
        # busqueda complementaria del menu
        self.menuentry = Gtk.SearchEntry(placeholder_text=_("Search specific command..."))

        self.menuentry.hide()
        self.menuentry.connect('search-changed', self.handler.on_menu_entry_activate)

        # Poniendo la barra de busqueda en la cabecera
        headerbar = Gtk.HeaderBar()
        headerbar.pack_start(boxse)
        headerbar.pack_end(menu)
        headerbar.pack_end(self.menuentry)

        headerbar.pack_start(self.cancelar)

        # scrollew window
        self.sw = Gtk.ScrolledWindow()
        self.sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.sw.set_propagate_natural_height(1)
        self.sw.set_vexpand(True)

        # Iterador de las busquedas que se lleva
        self.iterador = 0
        # iterador para el menu
        self.faviter = 0
        # iterador para la barra de busqueda
        self.searchiter = 0
        self.acercadeiter=0

        # Frame donde aparecen todas las descripcciones
        self.fr = Gtk.Frame()
        self.fr.set_label(_("Try typing a command in the search bar"))
        self.fr.set_hexpand(True)
        self.fr.set_vexpand(True)
        self.fr.set_margin_start(10)
        self.fr.set_margin_end(10)
        self.sw.set_min_content_width(210)
        # label donde colocar los textos
        self.comandoslabel = Gtk.Label()
        self.comandoslabel.set_halign(Gtk.Align.CENTER)
        self.comandoslabel.set_valign(Gtk.Align.CENTER)
        self.comandoslabel.hide()
        self.comandoslabel.set_margin_start(15)
        self.comandoslabel.set_wrap(True)

        # boton con link para saber mas
        self.sabermas = Gtk.LinkButton()
        self.sabermas.hide()
        self.sabermas.set_label(_("Know more"))
        self.sabermas.set_halign(Gtk.Align.START)
        self.sabermas.set_valign(Gtk.Align.START)

        # box para juntarlos
        boxfr = Gtk.Box()
        boxfr.set_orientation(Gtk.Orientation.VERTICAL)
        boxfr.set_margin_start(15)
        boxfr.set_halign(Gtk.Align.CENTER)
        boxfr.set_valign(Gtk.Align.CENTER)
        boxfr.append(self.comandoslabel)
        boxfr.append(self.sabermas)
        self.fr.set_child(boxfr)

        # Esta es la listbox de la izquierda
        self.listbox = Gtk.ListBox()
        self.listbox.set_margin_end(15)
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.set_halign(Gtk.Align.START)
        self.listbox.connect('row-selected', self.handler.on_row_clicked)

        self.listbox.hide()
        # unimos la listbox a la scrolled window
        self.sw.set_child(self.listbox)

        # label con nombre para que quede bonito la fav list
        favlistboxlabel = Gtk.Label()
        favlistboxlabel.set_text(_("Favourite commands:"))

        # lista de favs
        self.favslistbox = Gtk.ListBox()
        self.favslistbox.set_margin_end(15)
        self.favslistbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.favslistbox.set_halign(Gtk.Align.START)
        self.favslistbox.connect('row-selected', self.handler.on_row_clicked)
        self.favslistbox.set_margin_top(15)

        # creando la lista de favs desde fichero
        file = open("favs.txt", "r")
        # leo el fichero
        lineas = file.readlines()

        for item in lineas:
            # lo divido por el tabulador que les meto en la entrada para diferenciarlos
            vector = item.split('\t')
            if (len(vector) > 1):
                # los añado
                self.add_fav_row(vector[1], vector[0], self.favslistbox)
        file.close()

        # box que junte la label y la fav list
        rightsidebox = Gtk.Box()
        rightsidebox.set_orientation(Gtk.Orientation.VERTICAL)
        rightsidebox.append(favlistboxlabel)
        rightsidebox.append(self.favslistbox)
        rightsidebox.set_margin_top(15)
        rightsidebox.set_margin_end(15)

        # scrolled window para los favs
        swfav = Gtk.ScrolledWindow()
        swfav.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swfav.set_propagate_natural_height(1)
        swfav.set_vexpand(True)
        swfav.set_child(rightsidebox)

        # se crea una pannel para contener a la scrolled window y al marco que se pueda expandir y la lista de favs
        panel = Gtk.Paned()
        panel.set_start_child(self.sw)
        panel.set_end_child(self.fr)
        panel.set_resize_start_child(False)
        panel.set_shrink_start_child(False)

        # background append
        self.background.set_start_child(panel)
        self.background.set_end_child(swfav)
        self.background.get_end_child().hide()
        self.background.set_resize_end_child(True)
        self.background.set_shrink_end_child(False)
        self.background.set_margin_top(15)

        # movidas de la window para añadir todo
        self.window.set_titlebar(headerbar)
        self.window.set_child(self.background)
        self.window.present()
        app.add_window(self.window)
        app.add_window(self.acercade)
        self.window.set_focus(self.entry)

    # devuelve la entrada principal
    def get_entry(self) -> str:
        return self.entry.get_text()
        # devuelve la ventana de acerca de


    def add_commandlist_row(self, name: str, markup: str, lista: Gtk.ListBox, boolean):
        # crea un contenedor para el boton que esta abajo y la label
        box = Gtk.Box()
        button = Gtk.Button.new_with_label(_("Fav"))
        button.set_hexpand(False)
        button.set_vexpand(False)

        label = Gtk.Label()
        label.set_name(name)
        label.set_text(markup)
        label.set_single_line_mode(True)
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_xalign(0)
        label.set_wrap(True)
        label.set_max_width_chars(8)
        button.connect("clicked", self.handler.on_check_activate, name,
                       markup)  # se añade la funcion para cuando se activa
        # esto es para si tenias guardado en favoritos en una sesion anterior , en la siguiente aparezca ya clickado
        if (boolean):
            button.set_sensitive(False)

        label.set_margin_start(5)
        label.set_margin_end(10)
        box.append(label)
        box.append(button)

        lista.append(box)

    def add_fav_row(self, name: str, markup: str, lista: Gtk.ListBox):
        # sencillo , los mismo que antes pero con otra funcion
        button = Gtk.Button.new_with_label(_("UnFav"))
        button.set_hexpand(False)
        button.set_vexpand(False)
        label = Gtk.Label()
        label.set_name(name)
        label.set_text(markup)

        label.set_single_line_mode(True)
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_xalign(0)
        label.set_wrap(True)
        button.connect("clicked", self.handler.on_unfav_clicked)  # esta es la otra funcion

        label.set_margin_start(5)
        label.set_margin_end(10)
        box = Gtk.Box()
        box.append(label)
        box.append(button)
        lista.append(box)

    def update_rows(self, comandos):
        lista=[]
        self.listbox.show()
        # enseña la lista
        for item in self.listbox:
            lista.append(item)
        for i in range(len(lista)):
            self.listbox.remove(lista[i])
        lista.clear()

        #self.iterador = self.iterador + 1
        # leer el archivo de favs
        file = open("favs.txt", "r")
        lineas = file.readlines()
        # iterando sobre el array de comandos
        for item in comandos:
            if (item.commands != ("")):
                # AQUI AÑADO EL TABULADOR PARA PODER SEPARAR EN EL ARCHIVO DE TEXTO
                comparar = item.commands.replace('\n', "") + '\t' + item.description.replace('\n', "") + '\n'
                # si está en el archivo de texto de los favs lo va a poner como ya clickado

                if (comparar in lineas):
                    self.add_commandlist_row(item.description, item.commands, self.listbox, True)

                else:
                    self.add_commandlist_row(item.description, item.commands, self.listbox, False)
        for item in self.listbox:
            lista.append(item)

        if(len(lista)==0):
            self.fr.set_label(_("No command found"))
        else:
            self.fr.set_label(_("Select a line"))

        self.comandoslabel.hide()
        self.sabermas.hide()
        file.close()

    def on_row_clicked(self, row, lista):

        for item in lista:
            if (item == row):
                # añade al frame la descripccion
                self.fr.set_label("")
                self.comandoslabel.show()
                self.comandoslabel.set_text(
                    _("Command:") + Gtk.Widget.get_first_child(item.get_child()).get_text() + '\n\n' + _(
                        "Description:") +
                    Gtk.Widget.get_first_child(item.get_child()).get_name() + '\n')
                self.sabermas.show()
                self.sabermas.set_uri("https://cheat.sh/" + self.entry.get_text())

    def show_indicator(self) -> None:
        # encender espinner y enseñar cancelar
        self.entry.set_sensitive(False)
        self.spinner.show()
        self.spinner.start()
        self.fr.set_label(_("LOADING COMMANDS..."))

        self.cancelar.show()

    def show_indicator_error(self) -> None:
        # encender espinner y enseñar cancelar cuando no hay conexion
        self.entry.set_sensitive(False)
        self.spinner.show()
        self.spinner.start()
        self.cancelar.set_sensitive(True)
        self.fr.set_label(_("Connection error , reconnecting..."))

    def hide_indicator(self):
        # apagar espinner y enseñar cancelar
        self.cancelar.hide()
        self.entry.set_sensitive(True)
        self.spinner.hide()
        self.spinner.stop()

        self.window.set_focus(self.entry)
        self.cancelar.set_sensitive(True)

    def on_cancelar_clicked(self):
        # cuando se le da a cancelar el modelo cambia de false a true entonces el presenter sabe que no tiene que enseñar los comandos
        self.cancelar.set_sensitive(False)
        self.entry.set_sensitive(True)
        self.window.set_focus(self.entry)
        self.hide_indicator()

    def on_cancelar_release(self):
        # cuando ya se haya cancelado el boton se oculta pero tmb hay que volver a ponerlo sensible
        self.cancelar.set_sensitive(True)

    def on_fav_button_clicked(self, widget, name, markup):
        # se lee el archivo , si el comando ya estaba no se pone , si no se añade
        file = open("favs.txt", "r")
        lineas = file.readlines()
        comparar = markup.replace('\n', "") + '\t' + name.replace('\n', "") + '\n'
        if (comparar not in lineas):
            widget.set_sensitive(False)
            file.close()
            file = open("favs.txt", "a")
            file.write(markup.replace('\n', "") + '\t' + name.replace('\n', "") + os.linesep)
            self.add_fav_row(name, markup, self.favslistbox)
        file.close()

    def on_unfav_button_activate(self, widget):
        # cuando le das a unfav hay que eliminarlo del fichero y poner sensitivo el el boton de favear del lado izq
        # el padre del padre del boton es la row de la lista de favs
        row = widget.get_parent().get_parent()
        fp = open("favs.txt", 'r')
        l1 = fp.readlines()
        fp.close()

        comando = Gtk.Widget.get_first_child(row.get_child()).get_text()

        fb = open("favs.txt", "w")
        for number, line in enumerate(l1):
            vector = line.split('\t')
            # aqui cambio el comando por vacio (lo elimino del archivo de texto)(si lo encuentra claro)
            if (vector[0] == comando):
                l1[number] = ""
                break
            # IMPORTANTE cuando haces readlines las lineas que te da no son el archivo(el archivo es inmutable)
            # solo se puede modificar con writelines, lo que hago es leer el archivo, modificar el vector de lineas que me pasa
            # el archivo y volverlo a meter con el writelines:)
        fb.writelines(l1)
        fb.close()
        # aqui se elimina de la lista
        # item es cada row de la lista
        for item in self.listbox:
            if (Gtk.Widget.get_first_child(item.get_child()).get_text() == Gtk.Widget.get_first_child(
                    row.get_child()).get_text()):
                Gtk.Widget.get_last_child(item.get_child()).set_sensitive(True)

        row.hide()

    def show_fav_list(self):
        # dependiendo de cuantas vexes le ayas dado lo enseña
        self.faviter = self.faviter + 1
        if (self.faviter % 2 == 0):
            self.background.get_end_child().hide()
        else:
            self.background.get_end_child().show()

    def show_search_menu(self):
        # dependiendo de cuantas vexes le ayas dado lo enseña
        self.searchiter = self.searchiter + 1
        if (self.searchiter % 2 == 0):
            self.menuentry.hide()
        else:
            self.menuentry.show()
            self.window.set_focus(self.menuentry)

    def find_row(self) -> None:
        self.sabermas.hide()
        iter = 0
        for item in self.listbox:

            if (self.menuentry.get_text()  in  Gtk.Widget.get_first_child(item.get_child()).get_text() ):
                item.show()
            if(self.menuentry.get_text() not in Gtk.Widget.get_first_child(item.get_child()).get_text()):

                item.hide()

        if(iter<=1):
            self.comandoslabel.show()
        else:
            self.comandoslabel.set_text("")

    def show_acercade_window(self):
        # dependiendo de cuantas vexes le ayas dado lo enseña

            self.acercade.show()

    #def on_activate_theme(self):
     #   config = window.mat
      #  self.b

    def create_acercade(self):
        acercade = Gtk.Window(
            title=_("About CheatSheet"),
            default_width=400,
            default_height=400
        )
        acercade.connect("close-request", lambda window:window.hide())

        horizontal = Gtk.Box()
        horizontal.set_margin_top(15)
        horizontal.set_spacing(5)
        horizontal.set_orientation(Gtk.Orientation.HORIZONTAL)
        horizontal.set_halign(Gtk.Align.CENTER)

        vertical = Gtk.Box()
        vertical.set_margin_top(15)
        vertical.set_spacing(5)
        vertical.set_orientation(Gtk.Orientation.VERTICAL)

        image = Gtk.Image.new_from_file("media/Bash_Logo_Colored.svg.png")
        image.set_pixel_size(200)

        label = Gtk.Label()
        label.set_markup(_("<b>IPM CheatSheet</b>"))
        label2 = Gtk.Label()
        label2.set_markup("1.0")
        label3 = Gtk.Label()
        label3.set_text(_("Command search"))
        label4 = Gtk.LinkButton(label="GitHub")
        label4.set_uri("https://github.com/GEI-IPM-614G01022223/2223-p_desktop-equipo-33")
        imagegh = Gtk.Image.new_from_file("media/githublogo.png")
        imagegh.set_pixel_size(20)
        label5 = Gtk.Label()
        label5.set_text(_("Credits:"))
        label6 = Gtk.LinkButton(label="Ángel Otero Barreiros")
        label6.set_uri("https://github.com/angelbarreiros")
        label7 = Gtk.LinkButton(label="Graciela Méndez Olmos")
        label7.set_uri("https://github.com/Ghack941394")
        label8 = Gtk.LinkButton(label="Juan Piñeiro Torres")
        label8.set_uri("https://github.com/Juanitopt20023")

        horizontal.append(label4)
        horizontal.append(imagegh)

        vertical.append(image)
        vertical.append(label)
        vertical.append(label2)
        vertical.append(label3)
        vertical.append(horizontal)
        vertical.append(label5)
        vertical.append(label6)
        vertical.append(label7)
        vertical.append(label8)
        acercade.set_child(vertical)
        return acercade

    def on_close_request(self,widget):
        self.acercade.destroy()
        self.window.destroy()

    menu_text.close()


