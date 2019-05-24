import tkinter
print(tkinter.TclVersion)

window = tkinter.Tk()
window.geometry("400x650")
window.config(bg="#2b2929")

message_box = tkinter.Text(window, height=32, state="disabled")
message_box.pack(side=tkinter.TOP, padx=15,pady=5, fill=tkinter.Y)
message_box.config(bg="#595959")

input_user = tkinter.StringVar()
text_box = tkinter.Text(window, height=5)
text_box.pack(side=tkinter.BOTTOM,  padx=15,pady=10)
text_box.config(bg="#595959")

def send_message(event):
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
    return "break"

text_box.bind("<Return>", send_message)
window.mainloop()