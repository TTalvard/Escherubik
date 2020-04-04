# -*- coding: iso-8859-1 -*- 

import numpy
import pygame
import scipy as sp
import random
from pygame.locals import *
from numpy import matrix
from numpy import linalg
from scipy import signal
import math
import thread
import threading
import os, sys
import pyaudio
import analyse

import win32api
from win32api import GetSystemMetrics

print("Width =", GetSystemMetrics(0))
print("Height =", GetSystemMetrics(1))



#if sounds==1:
#	pygame.mixer.init()


D=2018.2
Obs=matrix([[-D/200.],[0.],[0.]])
vue=matrix([[1],[0],[0]])

def dist(a,b):
	return int((sum((a[i]-b[i])**2 for i in range(3)))**.5)

def Dist(a,b):
	return ((a-b).transpose()*(a-b))[0,0]**.5

def norm(u):
	return sum(u[i]**2 for i in range(3))**.5

def Norm(a):
	return (a.transpose()*a)[0,0]**.5
		
def pv(u,v):
	W=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
	n=norm(W)
	return [(u[1]*v[2]-u[2]*v[1])/n,(u[2]*v[0]-u[0]*v[2])/n,(u[0]*v[1]-u[1]*v[0])/n]
	
def VektorProduct(u,v):
	w=matrix([[u[1,0]*v[2,0]-u[2,0]*v[1,0]],[u[2,0]*v[0,0]-u[0,0]*v[2,0]],[u[0,0]*v[1,0]-u[1,0]*v[0,0]]])
	if Norm(w)==0:
		return matrix([0]*3)
	else:
		return w*1./Norm(w)

def persp(M,O,V):
	A=D*norm(V)/float((M[0]-O[0])*V[0]+(M[1]-O[1])*V[1]+(M[2]-O[2])*V[2])
	return [int(W/2.+(M[1]-O[1])*A),int(H/2.-(M[2]-O[2])*A)]

def Persp(M,O,V):
	A=D*Norm(V)/float(((M-O).transpose()*V)[0,0])
	return [int(W/2.+(M[1,0]-O[1,0])*A),int(H/2.-(M[2,0]-O[2,0])*A)]
	
def vektmat(a,b):
	return matrix([[a[1,0]*b[2,0]-a[2,0]*b[1,0]],[a[2,0]*b[0,0]-a[0,0]*b[2,0]],[a[0,0]*b[1,0]-a[1,0]*b[0,0]]])


Vertices=[]

for i in (-1,1):
	for j in (-1,1):
		for k in (-1,1):
			Vertices.append(matrix([[float(i)],[float(j)],[float(k)]]))

Edges={i:[] for i in range(len(Vertices))}

for i in range(len(Vertices)):
	for j in range(len(Vertices)):
		v1=Vertices[i]
		v2=Vertices[j]		
		if abs(sum(abs(v2-v1)))==2:
			Edges[i].append(j)

facecenters=[]
facecenters.append(matrix([[1.],[0.],[0.]]))
facecenters.append(matrix([[-1.],[0.],[0.]]))
facecenters.append(matrix([[0.],[1.],[0.]]))
facecenters.append(matrix([[0.],[-1.],[0.]]))
facecenters.append(matrix([[0.],[0.],[1.]]))
facecenters.append(matrix([[0.],[0.],[-1.]]))
##ESCHERWEIRDNESS
a=1.2
facecenters.append(matrix([[a],[a],[a]]))



def ROTAS(theta,axe):
	ax=[float(axe[0]),float(axe[1]),float(axe[2])]
	if ax[1]**2+ax[2]**2>0:
		v=pv(ax,[1,0,0])
	else :
		v=[0,1,0]
	w=pv(ax,v)
	c=math.cos(theta)
	s=math.sin(theta)
	Rot=matrix([[c,s,0],[-s,c,0],[0,0,1]])
	P=matrix([v,w,ax]).transpose()
	return P*Rot*P.I



scale=100
omega=4*10**(-5)


def twist(theta,n,j,affected_vertices):
	dtheta=theta/n
	for k in range(n):
		R=ROTAS(dtheta,facecenters[j])
		for i in affected_vertices:
			Vertices[i]=R*Vertices[i]
	return 0



W=GetSystemMetrics(0)
H=GetSystemMetrics(1)
pygame.init()
screen=pygame.display.set_mode((W,H))

v0=5
t=0
X=1100
Y=400
Vy=0
VObs=0
blur=0
persistance=40
retina = pygame.Surface((W,H), pygame.SRCALPHA)   # per-pixel alpha

primes=[2,3,5,7,11,13,17,19]
color={}
for p in (2*3,5*7,17*19,11*13):
	color[p]=(48,92,195)
for p in (2*11,5*17,7*19,3*13):
	color[p]=(11,201,104)
for p in (2*5,7*3,13*19,17*11):
	color[p]=(173,128,26)


shuffle_sequence=[3,1,4,1,5]
scramble=0
shuffled=0
dt=0
play=0
gamespeed=24



font1=pygame.font.Font(None,20) # None can be any font provided the aforesaid font is saved in the same folder
font2=pygame.font.Font(None,18) 
font3=pygame.font.Font(None,16) 
font3.set_italic(1)
font1.set_bold(1)


instructions0=font2.render("Use mouse to spin the cube",True,(200,200,200))
instructions01=font2.render("Use number keys to twist",True,(200,200,200))
instructions1=font2.render("Zoom IN/OUT : UP/DOWN",True,(200,200,200))
instructions2=font2.render("Speed up: S / Slow down : D",True,(200,200,200))
instructions21=font2.render("Press B to increase risk of epilepsy",True,(200,200,200))
instructions3=font2.render("Click to start or submit",True,(200,200,200))


run=bool(1)

while run:
	event = pygame.event.poll()
	if blur==0:
		screen.fill((0,0,0))
	else:
		
		retina.fill((255,255,255,255-persistance))  
		screen.blit(retina, (0,0))
			
	if event.type == QUIT :
		break
	
	pygame.draw.line(screen,(0,127,255,255),[W/2,H/2-3],[W/2,H/2+3],1)
	pygame.draw.line(screen,(0,127,255,255),[W/2+3,H/2],[W/2-3,H/2],1)
	

	screen.blit(instructions0,(50,50))
	screen.blit(instructions01,(50,70))
	screen.blit(instructions1,(50,90))
	screen.blit(instructions2,(50,110))
	screen.blit(instructions21,(50,130))
	screen.blit(instructions3,(50,170))

	
	if play==1:
		text=font3.render("What kind of scrambling involves no",True,(150,150,150))
		screen.blit(text,(W-300,200))
		text=font3.render("edges passing through one another?",True,(150,150,150))
		screen.blit(text,(W-300,220))
		text=font3.render("Won't purchase again.",True,(150,150,150))
		screen.blit(text,(W-300,240))
		text=font2.render("- M.C.Escher on Rubik.com",True,(200,200,200))
		screen.blit(text,(W-250,260))
	
	
	for fc in range(len(facecenters)):
		text=font1.render(str(fc+1),True,(128,128,128))
		screen.blit(text,Persp(facecenters[fc],Obs,vue))

	order={}
	distances=[]
	for i in range(len(Vertices)):
		v=Vertices[i]
		d=Dist(Obs,v)
		distances.append(d)
		order[d]=i
	
	distances.sort()
	distances.reverse()
	
	for d in distances:
		i=order[d]
		v=Vertices[i]
		pygame.draw.circle(screen,(255,0,0,125),Persp(v,Obs,vue),max(1,int(scale/abs(Dist(Obs,v)+.001))),0)
		for j in Edges[i]:
			pygame.draw.line(screen,(0,0,0,255),Persp(Vertices[i],Obs,vue),Persp(Vertices[j],Obs,vue),11)
			pygame.draw.line(screen,color[primes[i]*primes[j]],Persp(Vertices[i],Obs,vue),Persp(Vertices[j],Obs,vue),3)

	x,y=pygame.mouse.get_pos()
	x0=x-W/2
	y0=H/2-y
	axis=[0,y0,-x0]	
	if norm(axis)!=0:
		theta=-(x0**2+y0**2)**.5*omega	
		R=ROTAS(theta,axis)
		for i in range(len(Vertices)):
			Vertices[i]=R*Vertices[i]
		for j in range(len(facecenters)):
			facecenters[j]=R*facecenters[j]
		
	
	
	if shuffled==0 and play==1:
		move=shuffle_sequence[scramble]-1
		affected=[]
		for i in range(len(Vertices)):
			v=Vertices[i]
			if (v.transpose()*facecenters[move])[0,0]>0:
				affected.append(i)
		twist(math.pi/48.,1,move,affected)
		dt=(dt+1)%24
		if dt==0:
			scramble+=1
			for i in range(len(Vertices)):
				components=[]
				for j in range(6):
					if (Vertices[i].transpose()*facecenters[j])[0,0]>0:
						components.append(j)
				Vertices[i]=sum(facecenters[k] for k in components)
		if scramble>=len(shuffle_sequence):
			shuffled=1
	
	if event.type==pygame.MOUSEBUTTONDOWN:
		if shuffled==0:
			play=1
		if shuffled==1:
			X=sum((Vertices[-1]-Vertices[j]).transpose()*(Vertices[-1]-Vertices[j]) for j in Edges[7])+sum((Vertices[0]-Vertices[j]).transpose()*(Vertices[0]-Vertices[j]) for j in Edges[0])

			if abs(X-24)<.1:
				break
			
	if event.type == pygame.KEYDOWN :
		#persistance+=5
		if persistance<240:
			persistance+=2
		if event.key == pygame.K_UP :
			if Obs[0,0]<-7.5:
				VObs+=.02
		if event.key == pygame.K_DOWN :
			if Obs[0,0]>-75:
				VObs-=.02
		
		if shuffled==1:
			strmove=pygame.key.name(event.key)
			if strmove in ('1','2','3','4','5','6','7'):
				play=0
				if strmove=='0':
					move=9
				else: move=int(strmove)-1
				affected=[]
				if move<6:
					angle=math.pi/2.
				else: angle=2*math.pi/3.
				for i in range(len(Vertices)):
					v=Vertices[i]
					if (v.transpose()*facecenters[move])[0,0]>0:
						affected.append(i)
				thread.start_new_thread(twist,(angle,int(1600/gamespeed),move,affected))
		
	if Obs[0,0]>=-7.5 or Obs[0,0]<=-75:
		VObs=0
		Obs[0,0]=(Obs[0,0]+.5*(75-7.5))*.98-.5*(75-7.5)
	Obs+=VObs*vue

	if event.type == pygame.KEYDOWN :
		if event.key == pygame.K_b :
			blur=1-blur
			
		for i in range(len(Vertices)):
			components=[]
			for j in range(6):
				if (Vertices[i].transpose()*facecenters[j])[0,0]>0:
					components.append(j)
			Vertices[i]=sum(facecenters[k] for k in components)
	
		
		if event.key == pygame.K_s :
			if gamespeed<16:
				gamespeed+=1
		if event.key == pygame.K_d :
			if gamespeed>1:
				gamespeed-=1

	pygame.display.update()	
	pygame.display.flip()
	
			
#if sounds==1:
#	pygame.mixer.music.stop()
	
	