#The following program works for elliptic curves of the form y^2 = x^3 + a*x + b

from random import randrange, getrandbits
from itertools import repeat
from Crypto import Util
from Crypto import Random
from sqrt import modular_sqrt
from PIL import Image
import random
from collections import defaultdict, OrderedDict
import wave
import time


#Class for Elliptic Curve initialization and arithmetic
class EC(object):

	def __init__(self, p = None):
		
		self.__a = 1
		self.__b = 18
		self.__mapping = defaultdict(list)
		self.__mapping2 = OrderedDict()
		self.__start = 0

		if p is None:
			self.__q = Util.number.getPrime(16)

			#Generate G randomly
			self.__start = Util.number.getRandomInteger(2)
			self.__G = self.__pointAt()[0]

		else:
			self.__q = p[0]
			self.__G = p[1]
			

	def retGlobalParams(self):
		return self.__q, self.__G


	def computePB(self, nB):
		return self.__multiply(self.__G, nB)
		
	
	#Function that determines the point at a given X coordinatedef at(self, x):
	def __pointAt(self):

		x = self.__start

		while x < self.__q:

			ysq = (x ** 3 + self.__a * x + self.__b) % self.__q
			
			if ysq == 0:
				self.__start = x + 1
				return [[x, ysq], [x, self.__q]]

			val = modular_sqrt(ysq, self.__q)

			if val != -1:
				#y = min(val, self.__q - val)
				y1 = val
				y2 = self.__q - val
				self.__start = x + 1
				return [[x,y1], [x,y2]]

			else:
				x = x + 1

		print "Unreached"
		
		
	def __embed(self, user, kPB):
		
		self.__start = 0
		
		pt = [[0,0]]
		
		i = 0
		
		while (pt != None):
			for ct in pt:
				self.__mapping2[tuple(ct)] = [chr(i%256), chr(i/256)]
				i = i + 1
				
			pt = self.__pointAt()
			
		i = 0
		
		for key in self.__mapping2.iterkeys():
			ct = list(key)
			if (user == 'client'):
				ptsum = self.__add(ct, kPB)
				self.__mapping[chr(i%256)].append(self.__mapping2[tuple(ptsum)])
			else:
				ptdiff = self.__subtract(ct, kPB)
				self.__mapping[chr(i%256)].append(self.__mapping2[tuple(ptdiff)][0])
			i = i + 1
			
		self.__mapping2.clear()	
		
	
	def callEmbed(self, user, kPB):
		
		print "Generating set of affine points..."
		
		self.__start = 0
		
		self.__embed(user, kPB)
					
		print "Embedding complete!"
		
		
	def mappingLkp(self, X, Y):
		return self.__mapping[X][Y]
		
		
	#Function that determines if a given point p lies on the curve
	def __onCurve(self, p):

		if p == [0,0]:
			return True

		lhs = (p[1] ** 2) % self.__q

		rhs = ((p[0] ** 3) + self.__a * p[0] + self.__b) % self.__q

		return lhs == rhs


	def verifyPoint(self, p):
		return self.__onCurve(p)


	#Function to add 2 points p1 and p2
	def __add(self, p1, p2):

		#If any of the points is infinity, the result of addition is the other point
		if p1 == [0,0]:
			return p2
	
		if p2 == [0,0]:
			return p1
	
		#If one point is the negative of the other
		if p1[0] == p2[0] and (p1[1] != p2[1] or p1[1] == 0):
	
			#p1 + -p1 = infinity = [0,0]
			return [0,0]

		#If the points are equal, addition = doubling
		if p1[0] == p2[0]:
			#The line joining the 2 points is the tangent at that point
			#a/b mod q = a * inv(b) mod q
			inv = pow(2*p1[1], self.__q - 2, self.__q)
			l = (3 * p1[0] * p1[0] + self.__a) * inv % self.__q

		#If the points are unique
		else:
			#The line joining the points is obtained using slope form
			inv = pow(p2[0] - p1[0], self.__q - 2, self.__q)
			l = (p2[1] - p1[1]) * inv % self.__q

		#Coordinates [x,y] of the sum of p1 and p2 are obtained as follows
	
		x = (l * l - p1[0] - p2[0]) % self.__q
	
		y = (l * (p1[0] - x) - p1[1]) % self.__q

		return [x,y]


	def callAdd(self, p1, p2):
		return self.__add(p1,p2)


	#Function to subtract 2 points (p1 - p2)
	def __subtract(self, p1, p2):

		#Negate the point p2
		p2neg = (p2[0], -p2[1] % self.__q)

		#Add the negatvie to p2 to p1
		diff = self.__add(p1, p2neg)

		return diff


	def callSubtract(self, p1,p2):
		return self.__subtract(p1, p2)


	#Function to multiply a point by a constant value
	#Multiplication as repeated addition takes O(n)
	#Multiplication is performed as a series of doublings and additions which is O(log2(n))
	def __multiply(self, p, n):

		r = [0,0]

		m2 = p

		while 0 < n:

			#If the bit at the position is 1, add the original point to current value of m2.
			if n & 1 == 1:
				r = self.__add(r,m2)

			#Double the point for each iteration
			n = n >> 1
			m2 = self.__add(m2,m2)

		assert self.__onCurve(r), "Point not on Curve"

		return r

	def callMultiply(self, p, n):
		return self.__multiply(p,n)


#End of class EC

class ElGamal(object):

	def __init__(self, ec, PB=0):
		self.__ec = ec
		self.__PB = PB
		self.__keySize = 128

	def genKeys(self):
		#Generate value of nB
		self.__nB = Util.number.getPrime(self.__keySize)

		#Compute public key of receiver
		self.__PB = self.__ec.computePB(self.__nB)

		return self.__PB
		
	def __embedPoints(self, user, filetype, param_file):
		
		if user == "client":
			#Make a copy of G to pass to functions
			_, gtemp = self.__ec.retGlobalParams()

			# Generate value of k
			k = Util.number.getPrime(self.__keySize)
	
			#Compute kG, the first part of the ciphertext
			kG = self.__ec.callMultiply(gtemp, k)
			
			f1 = open(param_file, "w")
			f1.write(filetype + '\n' + str(kG) + '\n')
			f1.close()

			assert self.__ec.verifyPoint(kG), "kG not on curve!"

			#Compute kPB
			kPB = self.__ec.callMultiply(self.__PB, k)

			assert self.__ec.verifyPoint(kPB), "kPB not on curve!"
		
		elif user == "server":
			f1 = open(param_file)
			f1.readline()
			kG = eval(f1.readline().strip())
		
			kPB = self.__ec.callMultiply(kG, self.__nB)

			assert self.__ec.verifyPoint(kPB), "kPB not on curve!"
			
			f1.close()
		
		self.__ec.callEmbed(user, kPB)
		
			
		
	#Function that reads a file and creates an encrypted file
	def __fileEncrypt(self, filename, param_file, encr_file1, encr_file2):
		
		self.__embedPoints("client", "Text", param_file)
		
		f1 = open(filename)
		f2 = open(encr_file1, "w")
		f3 = open(encr_file2, "w")

		for line in f1:
			line = line.decode()
			cipher = [self.__ec.mappingLkp(i, random.randint(0,120)) for i in line]

			cipher1 = ','.join(str(ord(c[0])) for c in cipher)
			cipher2 = ','.join(str(ord(c[1])) for c in cipher)

			f2.write(str(cipher1) + '\n')
			f3.write(str(cipher2) + '\n')

		f1.close()
		f2.close()
		f3.close()
		
	#Function that opens file containing encrypted text and decrypts it and writes to new file
	def __fileDecrypt(self, param_file, encr_file1, encr_file2, decr_file):
		
		self.__embedPoints("server", "Text", param_file)

		f1 = open(encr_file1)
		f2 = open(encr_file2)
		f3 = open(decr_file, "w")
	
		for line in f1:
			cipher1 = line.strip('\r\n').split(',')
			cipher2 = f2.readline().strip('\r\n').split(',')
						
			plain = ''.join(self.__ec.mappingLkp(chr(eval(cipher1[i])),eval(cipher2[i])) for i in xrange(len(cipher1)))
			
			f3.write(plain)

		f1.close()
		f2.close()
		f3.close()
		
		
	def __encryptImageMain(self,filename, param_file, encr_file1, encr_file2):
		
		self.__embedPoints("client", "Image", param_file)
		
		im = Image.open(filename)
		pix = im.load()
		size = im.size

		im2 = Image.new("RGB", size, color=(0,0,0))
		pix2 = im2.load()
	
		im3 = Image.new("RGB", size, color=(0,0,0))
		pix3 = im3.load()
		
		for x in xrange(size[0]):
			for y in xrange(size[1]):
				rgb = list(pix[x,y])
						
				intensity = list(self.__ec.mappingLkp(chr(i),random.randint(0,120)) for i in rgb)
				
				pix2[x,y] = tuple(ord(sub[0]) for sub in intensity)
				pix3[x,y] = tuple(ord(sub[1]) for sub in intensity)
								
		im2.save(encr_file1, "PNG")
		im3.save(encr_file2, "PNG")
			
	
	def __decryptImageMain(self, param_file, encr_file1, encr_file2, decr_file):
		
		self.__embedPoints("server", "Image", param_file)

		im = Image.open(encr_file1)
		pix = im.load()
		size = im.size
		
		im2 = Image.open(encr_file2)
		pix2 = im2.load()

		im3 = Image.new("RGB", size, color=(0,0,0))
		pix3 = im3.load()
		
		for x in xrange(size[0]):
			for y in xrange(size[1]):
				rgb = list(pix[x,y])
				col = list(pix2[x,y])
				
				pix3[x,y] = tuple(ord(self.__ec.mappingLkp(chr(rgb[i]), col[i])) for i in xrange(len(rgb)))
					
		im3.save(decr_file, format='JPEG', subsampling=0, quality=100)
		
	
	def __encryptSoundMain(self, filename, param_file, encr_file1, encr_file2):
		
		self.__embedPoints("client", "Sound", param_file)
		
		f1 = wave.open(filename, "r")
	
		param = f1.getparams()
	
		f2 = wave.open(encr_file1, "w")
		f3 = wave.open(encr_file2, "w")
	
		f2.setparams(param)
		f3.setparams(param)
	
		for i in range(f1.getnframes()):
			frame = f1.readframes(1)
		
			sound = [self.__ec.mappingLkp(byte, random.randint(0,120)) for byte in frame]
		
			sound1 = ''.join(j[0] for j in sound)
			sound2 = ''.join(j[1] for j in sound)
				
			f2.writeframesraw(sound1)
			f3.writeframesraw(sound2)
		
		f1.close()
		f2.close()
		f3.close()
		
	def __decryptSoundMain(self, param_file, encr_file1, encr_file2, decr_file):
		
		self.__embedPoints("server", "Sound", param_file)
	
		f1 = wave.open(encr_file1, "r")
		f2 = wave.open(encr_file2, "r")
		f3 = wave.open(decr_file, "w")
	
		f3.setparams(f1.getparams())
	
		for i in range(f1.getnframes()):
			frame1 = f1.readframes(1)
			frame2 = f2.readframes(1)
		
			frame3 = ''.join(self.__ec.mappingLkp(frame1[j], ord(frame2[j])) for j in xrange(len(frame1)))
		
			f3.writeframesraw(frame3)
		
		f1.close()
		f2.close()
		f3.close()
		
	def encrypt(self, filetype, filename, param_file, encr_file1, encr_file2):
		print "Encrypting..."
		if filetype == "Text":
			self.__fileEncrypt(filename, param_file, encr_file1, encr_file2)
			
		elif filetype == "Image":
			self.__encryptImageMain(filename, param_file, encr_file1, encr_file2)
			
		elif filetype == "Sound":
			self.__encryptSoundMain(filename, param_file, encr_file1, encr_file2)
		print "Encryption Complete!"
			
			
	def decrypt(self, filetype, param_file, encr_file1, encr_file2, decr_file):
		print "Decrypting..."
		if filetype == "Text":
			self.__fileDecrypt(param_file, encr_file1, encr_file2, decr_file)
		
		elif filetype == "Image":
			self.__decryptImageMain(param_file, encr_file1, encr_file2, decr_file)
			
		elif filetype == "Sound":
			self.__decryptSoundMain(param_file, encr_file1, encr_file2, decr_file)
		print "Decryption Complete!"

#End of class ElGamal
