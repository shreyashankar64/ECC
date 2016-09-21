import socket
import sys
import ECCModule
import os
from Tkinter import *
from ScrolledText import *
import tkMessageBox
from tkFileDialog import askopenfilename
import cv2
import winsound

def recvPublicParams():

	global PB, q, G
  
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		addr = socket.gethostbyname(E1.get())
		s.connect((addr,9999))

		print "receiving public parameters..."

		l = s.recv(1024)

		param_list = l.split('\n')

		PB = eval(param_list[0])
		q = eval(param_list[1])
		G = eval(param_list[2])

		s.close()

		print "public parameters received!" 
		
		return 0
	
	except socket.error as msg:
		tkMessageBox.showerror("Error!", msg)
		E1.delete(0, END)
		return 1


def send_file(name):

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	addr = socket.gethostbyname(E1.get())
	s.connect((addr,9999))

	print "Sending encrypted file..."

	f = open(name, "rb") 
	l = f.read(1024)
	while (l):
		s.send(l)
		l = f.read(1024)

	f.close()
    
	s.close()

	print "File sent!"
	

def dispText(encrFileName, heading):
	
	global top2
	
	top2 = Toplevel(master=top)
	top2.minsize(width=560, height=450)
	
	f1 = open(encrFileName)
	msg = ''.join(line for line in f1)
	f1.close()
	
	L = Label(top2, text=heading)
	L.place(x=20, y=20)
	
	T = ScrolledText(top2, width=63, wrap=WORD, height=20)
	T.place(x=20, y=50)
	T.insert('1.0', msg)

	B = Button(top2, text='Close', command=top2.destroy)
	B.place(x=200, y=400)
	

def dispImage(imgFile, heading):
	img = cv2.imread(imgFile)
	cv2.imshow(heading, img)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
	
	
def playSound(soundFile, msg):
	
	global top2
	
	top2 = Toplevel(master=top)
	top2.minsize(width=50, height=50)

	heading = Label(top2, text=msg)
	heading.place(x=20,y=20)

	play = Button(top2, text='Play', command=lambda:winsound.PlaySound(soundFile , winsound.SND_FILENAME))
	play.place(x=20,y=50)

	StopBtn = Button(top2, text="Close" , command=top2.destroy)
	StopBtn.place(x=60,y=50)
	

def enc():

	global ec, eg, filetype,filename
	
	status = recvPublicParams()

	if status == 0:

		ec = ECCModule.EC([q, G])

		eg = ECCModule.ElGamal(ec, PB)
		
		param_file = "param_file.txt"
		encr_file1 = "encr_file1.txt"
		encr_file2 = "encr_file2.txt"
		
		if filetype == "Text":
			filename = "text.txt"
			msg = T1.get('1.0', 'end')

			f = open(filename, "w")
			f.write(msg)
			f.close()
			
		elif filetype == "Image":
			encr_file1 = "encr_file1.png"
			encr_file2 = "encr_file2.png"
			
		elif filetype == "Sound":
			encr_file1 = "encr_file1.wav"
			encr_file2 = "encr_file2.wav"
			
		else:
			print "Incorrect file type"
			exit(0)		
		
		eg.encrypt(filetype, filename, param_file, encr_file1, encr_file2)
		
		
		if filetype == "Text":
			dispText(encr_file1, 'Encryted File 1')
			top.wait_window(top2)
			dispText(encr_file2, 'Encrypted File 2')
			top.wait_window(top2)
			
		elif filetype == "Image":
			dispImage(filename, "Original Image")
			dispImage(encr_file1, "Encrypted Image 1")
			dispImage(encr_file2, "Encrypted Image 2")
			
		elif filetype == "Sound":
			playSound(filename, "Original Audio")
			top.wait_window(top2)
			playSound(encr_file1, "Encrypted Audio 1")
			top.wait_window(top2)
			playSound(encr_file2, "Encrypted Audio 2")
			top.wait_window(top2)
			
			
		send_file(param_file)
		send_file(encr_file1)
		send_file(encr_file2)
		
		os.remove(param_file)
		os.remove(encr_file1)
		os.remove(encr_file2)

		tkMessageBox.showinfo("Message Sent", "Message Sent")

		#~ top.destroy()
		E1.delete(0, 'end')
		T1.delete("1.0",'end')
		E2.delete(0, 'end')

def sendMedia():
	global filename
	filename = askopenfilename()

	E2.insert(0, filename)

	global filetype
	ext = filename.split('.')[-1]
	if ext == "wav":
		filetype = "Sound"
	elif ext == "jpg" or ext == "png":
		filetype = "Image"
	else:
		print "Incorrect File Type!"
		exit(0)

	

def gui():

	global top, E1, T1, B2, E2
	top = Tk()
	top.minsize(width=560, height=500)

	L1 = Label(top, text="To: ")
	L1.place( x=20, y=20)

	E1 = Entry(top, width=50)
	E1.place(x=50, y=20)

	L2 = Label(top, text='Enter message: ')
	L2.place(x=20, y=70)

	T1 = ScrolledText(top, width=63, wrap=WORD, height=17)
	T1.place(x=20, y=100)

	B1 = Button(top, text='Choose Media', command=sendMedia)
	B1.place(x=20,y=400)
	
	E2 = Entry(top, width=40)
	E2.place(x=150, y=400)

	B2 = Button(top, text='Send', command=enc)
	B2.place(x=100, y=450)

	B3 = Button(top, text='Quit', command=top.destroy)
	B3.place(x=200, y=450)

	top.mainloop()


if __name__ == "__main__":

	filetype = "Text"
	filename=""

	gui()
   
	print "Client DONE"

	
