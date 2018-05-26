
# coding: utf-8

# In[1]:


import numpy as np
import os
from PIL import Image
from skimage.io import imsave
import scipy
import shutil
import scipy.misc as smp


# In[2]:


class cell (object):
    def __init__(self, name="", typ="", x=0,y=0,ori='',w=0):
        self.name=name       # name of the Cell
        self.type=typ        # the cell's type
        self.x=x             # X coordinate we will get at the end of out network after placement
        self.y=y             # Y coordinate we will get at the end of out network after placement
        self.ori=ori         # orientation we will get at the end of out network after placement
        self.pins=[]         # pins corresponding to each one of the connected cells
        self.connections=[]  # The cells connected to this Cell
        self.width=w


# In[3]:


class wire (object):
    def __init__(self, name, conn,pins):
        self.name=name         # name of the Cell
        self.pins=pins         # pins corresponding to each one of the connected cells
        self.connections=conn  # The cells connected to this Cell


# In[4]:


class stdcell (object):
    def __init__(self,name,width):
        self.name=name
        self.width=width


# In[5]:


class chip(object):
    def __init__(self,path1,path2,lefpath,imgpath,typ,createimg,lab=0):
        self.label=lab
        self.cells=[]
        self.wires=[]
        self.connected=[]
        self.conMatrix=[]
        self.sizes=[]       # All the cell sizes in order
        self.stdCells=[]
        
        self.createStdCells(lefpath)
        self.createCells(path1,typ)
        
        if(createimg):
            self.createWires(path2,typ)
            self.addConnections()
            self.constructMatrix()
        else: #load image from file
            for file in os.listdir(imgpath):
                if os.path.splitext(file)[0].find(str(self.label))>=0 :
                     self.conMatrix= smp.imread(os.path.join(imgpath, file))          

    def createStdCells(self,lefpath):
            found=0
            with open (lefpath, "r") as myfile:
                data=myfile.readlines()
            for i in range (len(data)):
                if(data[i][:5]=='MACRO'):
                    parts=data[i].split(" ")
                    name=parts[1]
                    found=1
                if (found and data[i][:6]=='  SIZE'):
                    parts=data[i].split(" ")
                    found=0
                    self.stdCells.append(stdcell(name,parts[3]))        
                
    def createCells(self,path,typ) :
        if(typ==0):
            get_cells=0
            with open (path, "r") as myfile:
                data=myfile.readlines()
            for i in range (len(data)):
                if(data[i][:10]=='COMPONENTS'):
                    get_cells=1
                else:
                    if(get_cells):
                        parts=data[i].split(" ")
                        #print (parts[1],', ',parts[2],', ',parts[6],', ',parts[7],', ',parts[9],', ')
                        if(data[i][:3]!='END'):
                            s=0
                            for i in range (len(self.stdCells)):
                                if(self.stdCells[i].name.find(parts[2])!=-1):
                                    s=self.stdCells[i].width
                            self.cells.append(cell(parts[1],parts[2],parts[6],parts[7],parts[9],s))
                            self.sizes.append(s)
                        else:
                            get_cells=0
        else:
            file = open(path, "r")
            flag = False
            passed = False
            for line in file:
                if line.find("o") >= 0:
                    line =line.strip()
                    if(line[1].isdigit()):
                        #print(line)
                        flag = True      
                if flag and line != "\n":
                    c =cell()
                    new = line
                    if(new.find('\t')>=0):
                        c.name = new[0: new.find('\t')]
                        new = new[new.find('\t')+1:]
                        x_str = new[0: new.find('\t')]
                        x_str = x_str.strip()
                        if(x_str.find(".")>=0):
                            x_str = x_str[0: x_str.find(".")]
                        #print(x_str)
                        new = new[new.find('\t')+1:]
                        y_str = new[0: new.find(':')]
                        y_str = y_str.strip()
                        if(y_str.find(".")>=0):
                            y_str = y_str[0: y_str.find(".")]
                        #print(y_str)
                        if(y_str.isdigit() and x_str.isdigit()):
                            passed = True
                    if(passed == False):
                        c.name = new[0: new.find(" ")]
                        new = new[ new.find(" ")+1:]
                        new = new.strip()
                        x_str = new[0:  new.find(" ")]
                        if(x_str.find(".")>=0):
                            x_str = x_str[0: x_str.find(".")]
                        new = new[ new.find(" ")+1:]
                        new = new.strip()
                        y_str = new[0: new.find(':')-1]
                        if(y_str.find(".")>=0):
                            y_str = y_str[0: y_str.find(".")]
                        passed = True
                    for i in range(len(x_str)):
                            c.x += int(x_str[i])* (10**(len(x_str)-i-1))
                    for i in range(len(y_str)):
                            c.y += int(y_str[i])* (10**(len(y_str)-i-1))
                    self.cells.append(c)
            y= np.ones((len(self.cells),2))
            for i in range(len(self.cells)):
                y[i] =[self.cells[i].x, self.cells[i].y]
            file.close()
        
            for j in range (len(self.cells))  :
                s=0
                for i in range (len(self.stdCells)):
                    if(self.stdCells[i].name==self.cells[i].name):
                        s=self.stdCells[i].width
                        self.cells[i].width=s  
                        self.sizes.append(s)
            
                        
    def createWires(self,path,typ) :
        if(typ==0):
            get_wires=0
            with open (path, "r") as myfile:
                data=myfile.readlines()

            for i in range (len(data)):
                if(data[i][:4]=='NETS'):
                    get_wires=1
                else:
                    if(data[i][:3]=='END'):
                        get_wires=0
                    if(get_wires):
                        data[i]=data[i].replace("(","")
                        data[i]=data[i].replace(")","")
                        data[i]=data[i].replace("-","")
                        data[i]=data[i].replace("\n","")
                        parts=data[i].split(" ")
                        if(len(parts)==2):
                            #print(parts[1])
                            name=parts[1]
                            pins=[]
                            comp=[]
                        elif(parts[6]!=';'):
                            pins.append(parts[4])
                            comp.append(parts[3])
                            #print (parts[3],', ',parts[4],', ',parts[6])
                        else:
                            pins.append(parts[4])
                            comp.append(parts[3])
                            self.wires.append(wire(name,comp,pins))
                            #print(len(self.wires))
            else:
                with open (path, "r") as myfile:
                    data=myfile.readlines()
                start=0
                for i in range (len(data)):
                    if(data[i][:9]=='NetDegree'):
                        data[i]=data[i].replace("\n","")
                        parts=data[i].split(" ")
                        if(start):
                            self.wires.append(wire(name,pins,comp))
                        start=1
                        name=parts[5]
                        pins=[]
                        comp=[]
                    elif(start):
                        data[i]=data[i].replace("\n","")
                        parts=data[i].split("\t")
                        parts1=parts[2].split(" ")
                        comp.append(parts[1])
                        pins.append(parts1[0])

    def addConnections(self):
        for i in range (len(self.wires)):
            for j in range (len(self.wires[i].connections)):
                for k in range (len(self.cells)):
                    if(self.wires[i].connections[j]==self.cells[k].name):
                        c=0
                        for l in range (len(self.wires[i].connections)):
                            if(self.wires[i].connections[l]!=self.cells[k].name):
                                self.cells[k].connections.append(self.wires[i].connections[l])
                                c+=1
                            else:
                                temp=self.wires[i].pins[l]
                        for m in range (c):
                            self.cells[k].pins.append(temp)
                            
    def constructMatrix (self):
        for i in range (len(self.cells)):
            self.connected.append([])
            self.conMatrix.append([])
            for j in range (len(self.cells)):
                self.connected[i].append(self.isConnected(i,self.cells[j].name))
                self.conMatrix[i].append(self.connected[i][j]*(len(self.cells[i].connections)+len(self.cells[j].connections)))
                
       # print(self.conMatrix[0])
        print ('visual representation of the connections and their weights: ')
        img = smp.toimage( self.conMatrix )
        #img.show()
        display(img)

    def isConnected(self,c1,c2):
        for i in range (len(self.cells[c1].connections)):
            if (self.cells[c1].connections[i]==c2):
                return 1
        
        return 0


# In[6]:


def pad (maxsize,matrix,gt1,gt2,path,label):
        extra=maxsize-len(matrix)
        right= np.zeros((len(matrix),extra))
        matrix=np.hstack((matrix,right))
        bottom= np.zeros((extra,len(matrix)+extra))
        matrix=np.vstack((matrix,bottom))
        print(extra)

        extra=maxsize-len(gt1)
       # print(extra,len(gt1))
        inf = np.full((extra), 0)
        gt1=np.array(gt1)
        gt2=np.array(gt2)
        gt1=np.append(gt1,inf)
        gt2=np.append(gt2,inf)

        
        
        #print(gt1.shape,inf.shape,maxsize)

       # print ('visual representation of the connections and their weights: ')
        img = smp.toimage( matrix)
        #img.show()
        display(img)
        imsave(path+'/'+str(label)+'.png',img)

    
        return matrix,gt1,gt2


# In[7]:


def dataset(ranges):
        create=1
        imgPath= './img'#'E:/uni/cs 337 (Digital 2)/project 2/dataset/img'
        lefPath0='./osu035_stdcells.lef'#'E:/uni/cs 337 (Digital 2)/project 2/dataset/lef/osu035_stdcells.lef'
        lefPath1='E:/uni/cs 337 (Digital 2)/project 2/dataset/lef/cells.lef'
        ds0='./dataset'#'E:/uni/cs 337 (Digital 2)/project 2/dataset/typ1'
        ds1='E:/uni/cs 337 (Digital 2)/project 2/dataset/typ2'
        chips=[]
        groundTruth_x=[]
        groundTruth_y=[]
        sizes=[]
        inp=[]
        
         #typ1
        i=0
        for file in os.listdir(ds0):
            chips.append(chip(lab=i,path1=os.path.join(ds0, file),path2=os.path.join(ds0, file),
                              lefpath=lefPath0,imgpath=imgPath,typ=0,createimg=0))
            i=i+1
            
#         #typ2
#         for file1 in os.listdir(ds1):
#             inn=os.path.join(ds1, file1)
#             for file in os.listdir(inn):
#                 #print(file)
#                 if os.path.splitext(file)[0].find('aplace')>=0 :
#                     f1=inn+'/'+ file
#                 else:
#                     f2=inn+'/'+ file
        
#             chips.append(chip(lab=i,path1=f1,path2=f2,lefpath=lefPath1,imgpath=imgPath,typ=1,createimg=1))
#             i=i+1
            
        
        for i in range (len(chips)):
            tempx=[]
            tempy=[]
            for j in range (len(chips[i].cells)):
                tempx.append(chips[i].cells[j].x)
                tempy.append(chips[i].cells[j].y)
            groundTruth_x.append(tempx)
            groundTruth_y.append(tempy)
            inp.append(chips[i].conMatrix)
            sizes.append(chips[i].sizes)
            
        for i in range (len(chips)):
            if(len(chips[i].cells)<=ranges[0]):
                inp[i],groundTruth_x[i],groundTruth_y[i]=pad(ranges[0],chips[i].conMatrix,groundTruth_x[i],groundTruth_y[i],imgPath,chips[i].label)
            elif(len(chips[i].cells)<=ranges[1]):
                inp[i],groundTruth_x[i],groundTruth_y[i]=pad(ranges[1],chips[i].conMatrix,groundTruth_x[i],groundTruth_y[i],imgPath,chips[i].label)
            elif(len(chips[i].cells)<=ranges[2]):
                inp[i],groundTruth_x[i],groundTruth_y[i]=pad(ranges[2],chips[i].conMatrix,groundTruth_x[i],groundTruth_y[i],imgPath,chips[i].label)
            elif(len(chips[i].cells)<=ranges[3]):
                inp[i],groundTruth_x[i],groundTruth_y[i]=pad(ranges[3],chips[i].conMatrix,groundTruth_x[i],groundTruth_y[i],imgPath,chips[i].label)
            
        
        inp=np.array(inp)
        groundTruth_x=np.array(groundTruth_x)
        groundTruth_y=np.array(groundTruth_y)
        sizes=np.array(sizes)

        return inp,groundTruth_x,groundTruth_y,sizes
