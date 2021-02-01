import sys
import tkinter as tk
import csv
try:
    droppedFile = sys.argv[1]
except IndexError:
    print("Please drag and drop the attendance ")
print(droppedFile)
readCSV(droppedFile)
input("")

def readCSV(path):
    with open(path, newline='') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile,dialect)

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)