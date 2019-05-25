import tkinter
from twisted.internet import tksupport


class GUI:
    def __init__(self):
        window = tkinter.Tk()
        window.geometry("400x650")
        window.config(bg="#2b2929")
        tksupport.install(window)
        self.window = window

        message_box = tkinter.Text(window, height=32, state="disabled")
        message_box.pack(side=tkinter.TOP, padx=15, pady=5, fill=tkinter.Y)
        message_box.config(bg="#595959")
        self.message_box = message_box

        input_user = tkinter.StringVar()
        text_box = tkinter.Text(window, height=5)
        text_box.pack(side=tkinter.BOTTOM, padx=15, pady=10)
        text_box.config(bg="#595959")

        def send_message(_):
            input_get = text_box.get('1.0', tkinter.END)
            if input_get.isspace():
                input_user.set('')
                text_box.delete('1.0', tkinter.END)
                return "break"

            message_box.configure(state='normal')
            message_box.insert(tkinter.INSERT, input_get)
            message_box.see("end")
            message_box.configure(state='disabled')
            input_user.set('')
            text_box.delete('1.0', tkinter.END)

            if self.client:
                self.client.handle_input(input_get.strip())

            return "break"

        text_box.bind("<Return>", send_message)
        self.client = None

    def send(self, line, prefix='', color='WHITE'):
        # TODO: colors and prefixes are used by client to mark some server messages
        self.message_box.configure(state='normal')
        self.message_box.insert(tkinter.INSERT, line + '\n')
        self.message_box.see("end")
        self.message_box.configure(state='disabled')

    def register_client(self, client):
        self.client = client

    def lose_connection(self):
        self.window.destroy()
