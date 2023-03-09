from threading import Thread
from typing import Optional

from model import Model
from views import run, View


class Presenter:
    def __init__(
            self,
            model: Optional[Model] = None,
            view: Optional[View] = None
    ) -> None:
        self.model = model or Model()
        self.view = view or View()
        self.updating = False

    def run(self) -> None:
        self.view.set_handler(self)
        run(on_activate=self.view.on_activate)

    def destroy(self, widget):
        self.view.quit()

    def cancel_clicked(self, widget):
        self.model.set_cancelar(True)
        self.view.on_cancelar_clicked()

    def on_row_clicked(self, widget, row):
        self.view.on_row_clicked(row, widget)

    def on_entry_activate(self, widget):
        t = Thread(target=self.update)
        t.start()

    def update(self):
        self.model.set_cancelar(False)
        View.run_on_main_thread(self.view.show_indicator)
        if(self.view.entry.get_text() != self.model.get_strcommand()):#comprobar que no vuelva a poner lo mismo
            self.model.set_command(self.view.get_entry())

            try:
                self.model.get_command()

            except:

                View.run_on_main_thread(self.view.show_indicator_error)
                while True:

                    try:
                        self.model.get_command()
                        break
                    except:
                        if (self.model.get_cancelar() == True):
                            break


            # entiendo que si la busqueda es demasiado rapida no da tiempo a cancelar

            if (self.model.get_cancelar() == False):
                View.run_on_main_thread(self.view.update_rows,self.model.get_command())
        View.run_on_main_thread(self.view.hide_indicator)
        View.run_on_main_thread(self.view.on_cancelar_release)

    def menu_favs(self, xd, ls):

        self.view.show_fav_list()

    def menu_acercade(self, xd, ls):
        self.view.show_acercade_window()

    def on_check_activate(self, widget, name, markup):
        self.view.on_fav_button_clicked(widget, name, markup)

    def menu_buscar(self, xd, ls):
        self.view.show_search_menu()

    def on_menu_entry_activate(self, widget):
        self.view.find_row()

    def on_unfav_clicked(self, widget):
        self.view.on_unfav_button_activate(widget)
