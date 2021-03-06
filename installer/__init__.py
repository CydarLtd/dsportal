from tkinter import Tk, Label, Button, Entry, StringVar

# Ask user for key and URL
# Validate URL (no path, https)
# Validate above by connection attempt
# Create install directory
# Extract winsw.exe
# Extract worker.exe
# Extract uninstaller (or copy this file if it's the installer)
# Create winsw config (templated key)
# Register uninstaller
# Install + start service via winsw
# Check service is running


class Installer:
    def __init__(self, master):
        self.master = master
        master.title("dsportal worker installer")

        Label(
            master, text="Welcome to the dsportal worker windows service installer."
        ).grid(row=0, column=0, columnspan=2, pady=20, padx=20)

        Label(master, text="Server URL:").grid(row=1, column=0)
        self.url_entry = Entry(textvariable=StringVar(master, "https://"))
        self.url_entry.grid(row=1, column=1)

        Label(master, text="Server key:").grid(row=2, column=0)
        self.key_entry = Entry()
        self.key_entry.grid(row=2, column=1)

        self.install_button = Button(
            master, text="Install dsportal worker", command=self.greet, state="disabled"
        )

        self.install_button.grid(row=3, column=0, pady=20)

        Button(master, text="Cancel", command=master.quit).grid(row=3, column=1)

    def greet(self):
        print("Greetings!")


root = Tk()
my_gui = Installer(root)
root.mainloop()
