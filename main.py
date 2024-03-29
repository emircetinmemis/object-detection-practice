"""
This program detecs 5 objects in a video stream. Than, it shows the detected objects in a window. And it stores the detected objects in a file with database and files.

@author: Emir Çetin MEMİŞ
@contact: memise@mef.edu.tr
@since: 2020-05-10

@TO-DO:
    - Update the detection model to the latest version. Or use tensorflow.
    - Update the database to mongoDB.
    - Optimization.
    - Simplifaction.
"""

from email.mime import application
from   PIL      import Image, ImageTk
from   tkinter  import ttk
import tkinter  as tk
import numpy    as np
import warnings
import datetime
import sqlite3
import glob
import cv2
import os

warnings.filterwarnings("ignore")

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    print("PASSED")

class ObjectDetection(tk.Tk) :

    _objectNameFilePath = "Assets/Object Class Names.txt"

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)

        self.objectTreshold = tk.DoubleVar(value=0.45)
        self.nmsThreshold   = tk.DoubleVar(value=0.2)
        self.allObjectNames = [cName[0:-1] for cName in open(self._objectNameFilePath,'r')]
        self.selectedObjects = []
        self.anyFill = False
        self.isStarted = False
        self.datas = {}

        self.title("Object Detection Implementation - Emir Çetin MEMİŞ")
        self.configure(background="black")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="gray")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.parseContainer = ttk.Frame(self, padding=(10,10,10,10))
        self.parseContainer.grid(row=0,column=0, padx=10, pady=10) 

        self.output = Visualizer(self, self.parseContainer)
        self.menubar = MenuBar(self, self.parseContainer, self.output)

        self.menubar.grid(row=0,column=0)
        self.output.grid(row=2,column=0)

        for frame in self.parseContainer.winfo_children() :
            frame.grid_configure(padx=5, pady=5)

class MenuBar(tk.Frame) :

    def __init__(self, root, parent, visualizerObject, *args, **kwargs) :
        super().__init__(parent, *args, **kwargs)

        self.root = root
        self.visualizerObject = visualizerObject

        self.configure(background="black")
        self.configure(highlightcolor="white", highlightthickness=2)

        self.firstObjectName    = tk.StringVar(value="")
        self.secondObjectName   = tk.StringVar(value="")
        self.thirdObjectName    = tk.StringVar(value="")
        self.fourthObjectName   = tk.StringVar(value="")
        self.fifthObjectName    = tk.StringVar(value="")

        """ OBJECT SELECTION """
        longestWorldLength = max(map(len,self.root.allObjectNames))

        firstObjectNameLabel = ttk.Label(self, text="1. OK Object:", foreground="light green", background="black")
        firsObjectNameCombobox = ttk.Combobox(self, textvariable=self.firstObjectName, values=self.root.allObjectNames, cursor="hand2", justify=tk.CENTER, width=longestWorldLength, )
        
        secondObjectNameLabel = ttk.Label(self, text="2. OK Object:", foreground="light green", background="black")
        secondObjectNameCombobox = ttk.Combobox(self, textvariable=self.secondObjectName, values=self.root.allObjectNames, cursor="hand2", justify=tk.CENTER, width=longestWorldLength)

        thirdObjectNameLabel = ttk.Label(self, text="3. OK Object:", foreground="light green", background="black")
        thirdObjectNameCombobox = ttk.Combobox(self, textvariable=self.thirdObjectName, values=self.root.allObjectNames, cursor="hand2", justify=tk.CENTER, width=longestWorldLength)

        fourthObjectNameLabel = ttk.Label(self, text="4. Not OK Object:", foreground="red", background="black")
        fourthObjectNameCombobox = ttk.Combobox(self, textvariable=self.fourthObjectName, values=self.root.allObjectNames, cursor="hand2", justify=tk.CENTER, width=longestWorldLength)

        fifthObjectNameLabel = ttk.Label(self, text="5. Not OK Object:", foreground="red", background="black")
        fifthObjectNameCombobox = ttk.Combobox(self, textvariable=self.fifthObjectName, values=self.root.allObjectNames, cursor="hand2", justify=tk.CENTER, width=longestWorldLength)

        self.comboboxses = [firsObjectNameCombobox, secondObjectNameCombobox, thirdObjectNameCombobox, fourthObjectNameCombobox, fifthObjectNameCombobox]

        self.anyObjectButton = ttk.Button(self, text="Any Object", command=self.handleAny, cursor="hand2")
        self.anyObjectButton.grid(row=2, column=2, columnspan=2)

        firstObjectNameLabel.grid(row=0,column=0)
        firsObjectNameCombobox.grid(row=0,column=1)
        secondObjectNameLabel.grid(row=1,column=0)
        secondObjectNameCombobox.grid(row=1,column=1)
        thirdObjectNameLabel.grid(row=2,column=0)
        thirdObjectNameCombobox.grid(row=2,column=1)
        fourthObjectNameLabel.grid(row=0,column=2)
        fourthObjectNameCombobox.grid(row=0,column=3)
        fifthObjectNameLabel.grid(row=1,column=2)
        fifthObjectNameCombobox.grid(row=1,column=3)

        """ ALGORTIHM SETTINGS """
        objectTresholdLabel = ttk.Label(self, text="Object Treshold:")
        self.objectTresholdScale = ttk.Scale(self, from_=0.0, to=1.0, orient=tk.HORIZONTAL, cursor="hand2", variable=self.root.objectTreshold, length=longestWorldLength*6, command=self.handleScale)
        objectTresholdInfo = ttk.Label(self, textvariable=self.root.objectTreshold) 

        nmsThresholdLabel = ttk.Label(self, text="NMS Treshold:")
        self.nmsThresholdScale = ttk.Scale(self, from_=0.0, to=1.0, orient=tk.HORIZONTAL, cursor="hand2", variable=self.root.nmsThreshold, length=longestWorldLength*6, command=self.handleScale)
        nmsThresholdInfo = ttk.Label(self, textvariable=self.root.nmsThreshold)

        objectTresholdLabel.grid(row=0,column=4)
        self.objectTresholdScale.grid(row=1,column=4)
        objectTresholdInfo.grid(row=2,column=4)

        nmsThresholdLabel.grid(row=0,column=5)
        self.nmsThresholdScale.grid(row=1,column=5)
        nmsThresholdInfo.grid(row=2,column=5)

        """ BUTTONS """
        self.startButton = tk.Button(self, text="Start", command=self.start, state="disabled")
        self.saveAndExitButton = tk.Button(self, text="Save and Exit", command=self.saveAndExit, state="disabled")
        
        self.startButton.grid(row=3,column=0, sticky="WE", columnspan=3)
        self.saveAndExitButton.grid(row=3,column=3, sticky="WE", columnspan=3)

        for curWidget in self.winfo_children() :
            curWidget.grid_configure(padx=10, pady=5)
        
        for combobox in self.comboboxses :
            combobox.bind("<<ComboboxSelected>>", self.handleCombo)

    def handleAny(self) :
        
        self.root.anyFill = True

        self.anyObjectButton.config(state="disabled")

        self.firstObjectName.set("ANY")
        self.secondObjectName.set("ANY")
        self.thirdObjectName.set("ANY")
        self.fourthObjectName.set("ANY")
        self.fifthObjectName.set("ANY")

        self.startButton.config(state="normal")

    def handleScale(self, *event) :
        self.root.objectTreshold.set(float(str(self.objectTresholdScale.get())[0:4]))
        self.root.nmsThreshold.set(float(str(self.nmsThresholdScale.get())[0:4]))
        self.updateVariables()

    def handleCombo(self, event) :
        self.updateVariables()

    def updateVariables(self, *event) :
        if (not (self.fifthObjectName.get() == "" or self.fourthObjectName.get() == "" or self.thirdObjectName.get() == "" or self.secondObjectName.get() == "" or self.firstObjectName.get() == "")) and (not self.root.anyFill) and (not self.root.isStarted) :
            self.startButton.config(state="normal")

    def start(self) :
        
        for element in self.comboboxses :
            element.config(state="disabled")

        self.startButton.config(state="disabled")
        self.root.isStarted = True
        self.anyObjectButton.config(state="disabled")
        self.saveAndExitButton.config(state="normal")

        self.visualizerObject.proccesCapture()

        self.root.selectedObjects = []

        for combobox in self.comboboxses :
            self.root.selectedObjects.append(combobox.get())    
            
    def saveAndExit(self) :

        self.saveAndExitButton.config(state="disabled")
        self.visualizerObject.proccesCapture(True)

        if (self.root.anyFill) :
            print("Program have been runnig in test mode. No data will be saved.")
        else :
            print("Program closed successfully. Check the saved data.")
            
            self.cleanSpace()

            for object in self.root.datas :

                fileName = str(object) + ".db"
                filePath = os.path.realpath("Data Export/" + fileName)
                
                conn = sqlite3.connect(filePath)
                cur = conn.cursor()

                cur.execute("DROP TABLE IF EXISTS info")
                cur.execute("CREATE TABLE info (file_path text, object_coordinates text, object_status text, date text, time text, object_name text)")
                cur.execute("INSERT INTO info VALUES (?, ?, ?, ?, ?, ?)", (str(filePath), str(self.root.datas[object][1]), str(self.root.datas[object][0]), str(self.root.datas[object][2]), str(self.root.datas[object][3]), str(object),))

                conn.commit()

                cur.close()
                conn.close()

        self.after(3000, lambda : self.root.destroy())

    def cleanSpace(self) :
        if not os.path.exists("Data Export"):
            os.makedirs("Data Export")

        junkFiles = glob.glob("Data Export/*.db")
        for file in junkFiles: 
            os.remove(file)    

class Visualizer(tk.Frame) :

    _configurationsFilePath  = "Assets/Configurations.pbtxt"
    _weightsFilePath         = "Assets/Weights.pb"

    def __init__(self, root, parent, *args, **kwargs) :
        super().__init__(parent, *args, **kwargs)

        self.root = root

        self.configure(background="black")
        self.configure(highlightcolor="white", highlightthickness=2)

        self._imageWidth = 320
        self._imageHeight = 320

        self.captureDevice  = cv2.VideoCapture(0)
        self.originalImage = None
        self.capturedImage = None

        self.loadCapModel()

        self.backgroundImage  = ImageTk.PhotoImage(Image.open("Utils/background.jpg").resize((self._imageWidth, self._imageHeight), Image.ANTIALIAS))
        self.backgroundImage2 = ImageTk.PhotoImage(Image.open("Utils/background2.jpg").resize((self._imageWidth, self._imageHeight), Image.ANTIALIAS))
        
        self.originalImageLabel = ttk.Label(self, image=self.backgroundImage, background="black", border=1, borderwidth=1, relief="solid")
        self.originalImageLabel.grid(row=0,column=0)

        self.capturedImageLabel = ttk.Label(self, image=self.backgroundImage, background="black", border=1, borderwidth=1, relief="solid")
        self.capturedImageLabel.grid(row=0,column=1)

        for curWidget in self.winfo_children() :
            curWidget.grid_configure(padx=7, pady=5)

    def loadCapModel(self) :

        self.capModel = cv2.dnn_DetectionModel(self._weightsFilePath,self._configurationsFilePath)
        self.capModel.setInputSize(320,320)
        self.capModel.setInputScale(1.0/ 127.5)
        self.capModel.setInputMean((127.5, 127.5, 127.5))
        self.capModel.setInputSwapRB(True)

    def proccesCapture(self, saveFlag = False) :

        try :
            self.capturedImage = cv2.cvtColor(self.captureDevice.read()[1],cv2.COLOR_BGR2RGB)
        except :
            return

        self.originalImage = self.capturedImage.copy()

        objectIDs, confidences, bboxes = self.capModel.detect(self.capturedImage,confThreshold=self.root.objectTreshold.get())

        bboxes = list(bboxes)
        confidences = list(np.array(confidences).reshape(1,-1)[0])
        confidences = list(map(float,confidences))
        
        stats = cv2.dnn.NMSBoxes(bboxes,confidences,self.root.objectTreshold.get(),self.root.nmsThreshold.get())

        for i in stats:
            i = int(i)

            currentObjectName = self.root.allObjectNames[objectIDs[i]-1].lower()
            
            box = bboxes[i]
            x1,y1,x2,y2 = box[0],box[1],box[2],box[3]
            penColor = (0,0,0)

            if not self.root.anyFill :

                if currentObjectName in self.root.selectedObjects :

                    objectName = currentObjectName
                    objectStats = "OK" if self.root.selectedObjects.index(currentObjectName) < 3 else "NOT OK"
                    objectCoordinates = (x1,y1,x2,y2)
                    date, time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S").split(" ")

                    self.root.datas[objectName] = [objectStats, objectCoordinates, date, time]

                    penColor = {"OK":(0,255,0), "NOT OK":(255,0,0)}[objectStats]

                    cv2.rectangle(self.capturedImage, (x1,y1),(x1+x2,y2+y1), color=penColor, thickness=2)
                    cv2.putText(self.capturedImage,currentObjectName,(bboxes[i][0],bboxes[i][1]),cv2.FONT_HERSHEY_SIMPLEX,1,penColor,2)
            else :
                cv2.rectangle(self.capturedImage, (x1,y1),(x1+x2,y2+y1), color=penColor, thickness=2)
                cv2.putText(self.capturedImage,currentObjectName,(bboxes[i][0],bboxes[i][1]),cv2.FONT_HERSHEY_SIMPLEX,1,penColor,2)

        self.capturedImage = ImageTk.PhotoImage(Image.fromarray(self.capturedImage).resize((self._imageWidth, self._imageHeight), Image.ANTIALIAS))
        self.capturedImageLabel.config(image=self.capturedImage)
        self.capturedImageLabel.grid(row=0,column=1)

        self.originalImage = ImageTk.PhotoImage(Image.fromarray(self.originalImage).resize((self._imageWidth, self._imageHeight), Image.ANTIALIAS))
        self.originalImageLabel.config(image=self.originalImage)
        self.originalImageLabel.grid(row=0,column=0)

        if not saveFlag :
            self.after(10, self.proccesCapture)
        else :
            self.captureDevice.release()

            self.capturedImageLabel.config(image=self.backgroundImage2)
            self.capturedImageLabel.grid(row=0,column=1)
            self.originalImageLabel.config(image=self.backgroundImage2)
            self.originalImageLabel.grid(row=0,column=0)

if __name__ == "__main__" :
    application = ObjectDetection()
    application.mainloop()