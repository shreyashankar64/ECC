import socket
import sys
import ECCModule
import os
from Tkinter import *
from ScrolledText import *
import tkMessageBox
import winsound
import cv2

def send_file(string):
	print "WILL accept"
	global sc
	try:
		sc, address = s.accept()
	except KeyboardInterrupt:
		s.close()
		exit(0)
	
	print "DID  accept"
	print address
    
	print "Sending public parameters..."

	sc.send(string)
	sc.close()

	print "Public paramters sent!"
	
	return sc


def recv_file(name):
	print "WILL accept"
	global address
	try:
		sc, address = s.accept()
	except KeyBoardInterrupt:
		s.close()
		exit(0)
	
	print "DID  accept"
	print address

	print "Receiving file..."

	f = open(name,'wb')
	l = sc.recv(1024)
	while (l):
		f.write(l)
		l = sc.recv(1024)
	f.close()
	
	sc.close()

	print "File Received!"
	

def dispText(fileDisp, heading):
	
	top = Tk()
	top.minsize(width=560, height=450)

	#~ L1 = Label(top, text="From: ")
	#~ L1.place( x=20, y=20)
#~ 
	#~ E1 = Entry(top, width=50)
	#~ E1.place(x=70, y=20)
	#~ addr = socket.gethostbyaddr(address[0])[0]
	#~ E1.insert(0, addr)

	L2 = Label(top, text=heading)
	L2.place(x=20, y=20)

	T1 = ScrolledText(top, width=63, wrap=WORD, height=20)
	T1.place(x=20, y=50)
	
	f1 = open(fileDisp)
	msg = ''.join(line for line in f1)
	f1.close()
	T1.insert('1.0', msg)

	B2 = Button(top, text='Close', command=top.destroy)
	B2.place(x=200, y=400)

	top.mainloop()
	
	
	
def dispImage(imgFile, heading):
	img = cv2.imread(imgFile)
	cv2.imshow(heading, img)
	cv2.waitKey(0)
	cv2.destroyAllWindows()



def playSound(soundFile, msg):
	top = Tk()
	top.minsize(width=50, height=50)

	heading = Label(top, text=msg)
	heading.place(x=20,y=20)

	play = Button(top, text='Play', command=lambda:winsound.PlaySound(soundFile , winsound.SND_FILENAME))
	play.place(x=20,y=50)

	StopBtn = Button(top, text="Close" , command=top.destroy)
	StopBtn.place(x=60,y=50)

	top.mainloop()


if __name__ == "__main__":

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	

	s.bind(("",9999))
	s.listen(10)
	
	while(1):

		ec = ECCModule.EC()

		q, G = ec.retGlobalParams()

		eg = ECCModule.ElGamal(ec, 0)

		PB = eg.genKeys()

		to_send = str(PB) + '\n' + str(q) + '\n' + str(G)

		sc = send_file(to_send)
    
		param_file = "param_file_recd.txt"
		recv_file(param_file)
	
		encr_file1 = "encr_recd1.txt"
		encr_file2 = "encr_recd2.txt"
		decr_file = "decr_text.txt"

		f = open(param_file)
		filetype = f.readline().strip('\n\r')
		f.close()
		
		if filetype == "Text":
			recv_file(encr_file1)
			recv_file(encr_file2)
			try:
				eg.decrypt(filetype, param_file, encr_file1, encr_file2, decr_file)

			except:
				s.close()

			dispText(encr_file1, "Received File 1")
			dispText(encr_file2, "Received File 2")
			dispText(decr_file, "Decrypted Message")
			
	
		elif filetype == "Image":
			encr_file1 = "encr_recd1.png"
			encr_file2 = "encr_recd2.png"
			decr_file = "decr_image.jpg"
			recv_file(encr_file1)
			recv_file(encr_file2)
			try:
				eg.decrypt(filetype, param_file, encr_file1, encr_file2 , decr_file)
				
			except:
				s.close()			
				
			dispImage(encr_file1, "Received Image 1")
			dispImage(encr_file2, "Received Image 2")
			dispImage(decr_file, "Decrypted Image")
		
		elif filetype == "Sound":
			encr_file1 = "encr_recd1.wav"
			encr_file2 = "encr_recd2.wav"
			decr_file = "decr_audio.wav"
			recv_file(encr_file1)
			recv_file(encr_file2)
			try:
				eg.decrypt(filetype, param_file, encr_file1, encr_file2, decr_file)
				
			except:
				s.close()

			playSound(encr_file1, "Received Audio 1")
			playSound(encr_file2, "Received Audio 2")
			playSound(decr_file, "Decrypted Audio")

		else:
			print "Incorrect file type"
		
		#~ os.remove(param_file)
		#~ os.remove(encr_file1)
		#~ os.remove(encr_file2)

	s.close()

	print "Server DONE"

	
