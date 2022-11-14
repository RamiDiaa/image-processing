



from turtle import colormode
from image_equalization_ui import Ui_MainWindow
import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog,QMessageBox
# from PyQt5.QtCore import QTime,QTimer ,QDate


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,  NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.image 
import matplotlib.pyplot as plt

import pydicom
import numpy as np
from PIL import Image
import math



mpl.use('Qt5Agg')

# plt.subplots_adjust(left=0.1, right=0.2, top=0.2, bottom=0.1)



class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4):
        self.fig = Figure()#figsize=(width, height))
        # self.axes = self.fig.add_subplot(111)
        # fig.tight_layout()
        # self.axes.get_xaxis().set_visible(False)
        # self.axes.get_yaxis().set_visible(False)
        
        super(MplCanvas, self).__init__(self.fig)


class grid_MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4):
        self.fig, self.axes = plt.subplots(2,2)
        self.fig.tight_layout()
        
        super(grid_MplCanvas, self).__init__(self.fig)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # inserting matplotlib's canvases into the ui
        self.viewer_plot = MplCanvas(self, width=5, height=4)
        self.nearest_neighbor_plot = MplCanvas(self, width=5, height=4)
        self.bilinear_plot = MplCanvas(self, width=5, height=4)
        self.equalization_plot = grid_MplCanvas(self, width=5, height=4)

        self.ui.verticalLayout_viewer.addWidget(self.viewer_plot)
        self.ui.verticalLayout_nearst_neighbor.addWidget(self.nearest_neighbor_plot)
        self.ui.verticalLayout_bilinear.addWidget(self.bilinear_plot)
        self.ui.verticalLayout_equalize.addWidget(self.equalization_plot)



        self.ui.label_viewer_info.setText("please open an image")
        self.ui.radioButton_bilinear.setChecked(True)
        

        self.path = ""
        self.img = np.zeros((128,128))
        self.ui.label_interpolation.setText(':::::::::::::::::::)')
        self.bitdepth = 1


        # connecting buttons

        self.ui.actionopen.triggered.connect(self.openimage)
        self.ui.pushButton_apply_interpolation.clicked.connect(self.interpolate)
        self.ui.pushButton_apply_translation.clicked.connect(self.translate)
        self.ui.pushButton_plot_t_shape.clicked.connect(self.set_img_to_t_shape)

        

    def openimage(self):
        # try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.path, _ = QFileDialog.getOpenFileName(self,"choose the image", "","images (*jpg *.dcm)")#, options=options)
            if self.path:
                print(self.path)
            if self.path[-3:] == "jpg" :

                self.img = mpl.image.imread(self.path)
                metadata = ''#self.get_metadata('jpg')

                try:
                    self.img = rgb2gray(self.img)
                except:
                    pass
                self.viewer_plot.fig.clf()
                self.viewer_plot.fig.figimage(self.img, cmap='gray')

            elif self.path[-3:] == "dcm":
            
                self.dicom_object = pydicom.dcmread(self.path)

                self.img = self.dicom_object.pixel_array
                

                metadata = self.get_metadata('dcm')


                self.viewer_plot.fig.clf()
                self.viewer_plot.fig.figimage(self.img)

            else:
                metadata = "||| this app support only jpeg and dicom files |||"
            self.ui.label_viewer_info.setText(metadata)
            self.resize(self.frameGeometry().width(),self.frameGeometry().height()-32)  
              
        # except:
        #         msg = QMessageBox()
        #         msg.setIcon(QMessageBox.Critical)
        #         msg.setText("the file is corrupted")
        #         msg.setWindowTitle("Error")
        #         msg.exec_()
        #         print("err occurred")
            self.equalize()
    
    def get_metadata(self,imagetype):
        metadata = ''
        if imagetype == 'jpg':
            pillowimg = Image.open(self.path)
            
            numofrows = self.img.shape[0]
            numofcolumns = self.img.shape[1]
            numofbits = numofcolumns * numofrows
            print(pillowimg.getbands)
            self.bitdepth = pillowimg.bits * len(pillowimg.getbands())
            metadata = """ number of rows = {}\n number of coulmns = {}\n number of pixels = {}""".format(numofrows, numofcolumns, numofbits,pillowimg.mode)
            

        elif imagetype == 'dcm':
            
            self.bitdepth =self.dicom_object.BitsAllocated
            metadata = """
            number of rows = {}
            number of coulmns = {}
            number of pixels = {}
            Patient's Name...: {}
            Patient's ID...: {}
            Modality...: {}
            Study Date...: {}
            Pixel Spacing...: {}
            Bit Depth...: {}
            """.format(
                self.dicom_object.Rows,
                self.dicom_object.Columns,
                self.dicom_object.Rows * self.dicom_object.Columns,
                self.dicom_object.PatientName,
                self.dicom_object.PatientID,
                self.dicom_object.Modality,
                self.dicom_object.StudyDate,
                self.dicom_object.PixelSpacing,
                self.dicom_object.BitsAllocated)

        return metadata


        metadata = """
        number of rows = {}
        number of coulmns = {}
        size = {}
        color type = {}
        bitdepth = {}""".format(numofrows, numofcolumns, numofbits * self.bitdepth,pillowimg.mode,self.bitdepth)
        

    def interpolate(self):
        if len(self.img) == 0:
            return
        print(self.img)
        
        zooming_factor = self.ui.doubleSpinBox_zooming_factor.value()
        print(zooming_factor)
        if zooming_factor > 0 :
            self.nn_img = nn_interpolation(self.img,zooming_factor)
            print(self.nn_img)
            # print(self.img)

            self.nearest_neighbor_plot.fig.clf()
            self.nearest_neighbor_plot.fig.figimage(self.nn_img,cmap='gray')

            
            self.bl_img = bl_interpolation(self.img,zooming_factor)
            print(self.bl_img)
            self.bilinear_plot.fig.clf()
            self.bilinear_plot.fig.figimage(self.bl_img,cmap='gray')

            self.resize(self.frameGeometry().width(),self.frameGeometry().height()-32) 


            

            metadata = """
                nearest neighbor:
                number of rows = {} number of coulmns = {} number of pixels = {} -{} color type = {}
                
                """.format(self.nn_img.shape[0], self.nn_img.shape[1], self.nn_img.shape[0]*self.nn_img.shape[1],self.nn_img.shape[0]*self.nn_img.shape[1]*self.bitdepth,'grayscale')

            
            
            metadata = metadata + """
                bilinear:
                number of rows = {}  number of coulmns = {}  number of pixels = {} - {}  color type = {}
                """.format(self.bl_img.shape[0], self.bl_img.shape[1], self.bl_img.shape[0]*self.bl_img.shape[1],self.nn_img.shape[0]*self.nn_img.shape[1]*self.bitdepth,'grayscale')

            self.ui.label_interpolation.setText(metadata)
    
    def translate(self):

        rotatation_angle_degree = self.ui.doubleSpinBox_rotation_angle.value()
        scale_factor = self.ui.doubleSpinBox_scale_factor.value()
        shear_factor = self.ui.doubleSpinBox_shear_factor.value()
        if self.ui.radioButton_nearest_neighbour.isChecked():
            rotation_technique = 'nearest neighbour'
        else:
            rotation_technique = 'bilinear'


        rotatation_angle_rad = rotatation_angle_degree * np.pi/180

        self.img = translate_image(self.img,rotation_angle= rotatation_angle_rad,rotation_technique=rotation_technique,scale_factor=scale_factor,shear_factor=shear_factor)


        self.viewer_plot.fig.clf()
        self.viewer_plot.fig.figimage(self.img,cmap='gray')
        self.resize(self.frameGeometry().width(),self.frameGeometry().height()-32)  
    
    def set_img_to_t_shape(self):
        t_img = np.zeros((128,128))
        # horizontal_begining
        # hbar : horizontal bar , vbar: vertical bar
        hbar_width = 70
        hbar_height = vbar_width = 20
        vbar_height = 50

        hbar_xstart = (128 -hbar_width)//2
        vbar_xstart = (128 -vbar_width)//2

        top_padding = 30

        t_img[  top_padding  :  top_padding+hbar_height      ,         hbar_xstart  :  hbar_xstart+hbar_width  ] = 255

        t_img[  top_padding+hbar_height  :  top_padding+hbar_height+vbar_height    ,       vbar_xstart  :  vbar_xstart+vbar_width] =255

        self.img = t_img

        self.viewer_plot.fig.clf()
        self.viewer_plot.fig.figimage(self.img,cmap='gray')
        self.resize(self.frameGeometry().width(),self.frameGeometry().height()-32)  

    def equalize(self):
        eq_img, old_dist, new_dist = histogram_equalization(self.img)

        self.equalization_plot.axes[1,0].clear()
        self.equalization_plot.axes[1,1].clear()

        self.equalization_plot.axes[0,0].imshow(self.img,cmap='gray')
        self.equalization_plot.axes[0,1].imshow(eq_img,cmap='gray')
        self.equalization_plot.axes[1,0].bar(np.arange(0,256),old_dist)
        self.equalization_plot.axes[1,1].bar(np.arange(0,256),new_dist)

        self.resize(self.frameGeometry().width(),self.frameGeometry().height()-32)  



def rgb2gray(rgb):
    return np.dot(rgb, [0.299, 0.587, 0.144])


def histogram_equalization(img):
    distribution = np.zeros((1,256)).flatten()
    height,width = img.shape
    # count the number of pixels for each color intensity
    for row in img:
        for pixel in row:
            distribution[min(int(pixel),255)] +=1
            
    # divide over the total number of pixels to get probability instead of counts
    distribution /= width *height 

    # Cumulative Distribution Function 
    # where indices are the gray scale values an the values are the new pixel value
    cdf =np.array([])
    for i in range(len(distribution)):
        new_pixel_value = 255 * sum(distribution[0:i])
        cdf = np.append(cdf,round(new_pixel_value)) 
    new_img = np.zeros((height,width))
    for i in range(height):
        for j in range(width):
            # where indices of cdf array are the gray scale values an the values are the new pixel value
            new_img[i,j] = cdf[min(int(img[i,j]),255)]
    
    new_distribution = np.zeros((1,256)).flatten()
    for row in new_img:
        for pixel in row:

            new_distribution[min(int(pixel),255)] +=1

    return new_img, distribution*width *height, new_distribution

def nn_interpolation(img, factor):
    newimg = np.zeros((int(img.shape[0] *factor),int(img.shape[1] *factor)))
    for newimg_row_index in range(len(newimg[:,0])):
        for newimg_col_index in range(len(newimg[0,:])):
            if str(2* newimg_row_index/factor) in tuple('123456789') : # handel the ceiling of x.5 case
                oldimg_row_index = np.floor(newimg_row_index/factor)
            else:
                oldimg_row_index = round(newimg_row_index/factor)
            if str(2* newimg_col_index/factor) in tuple('123456789') : # handel the ceiling of x.5 case
                oldimg_col_index = np.ceil(newimg_col_index/factor)
            else:
                oldimg_col_index =round(newimg_col_index/factor)
            # print('row_index : '+ str(newimg_row_index))
            # print('col_index : '+ str(newimg_col_index))
            # print('new_row_index : '+ str(oldimg_row_index))
            # print('new_col_index : '+ str(oldimg_col_index))
            newimg[newimg_row_index,newimg_col_index] = img[max(oldimg_row_index-1,0),max(oldimg_col_index-1,0)]
    return newimg

def bl_interpolation(img,scaling_factor):

    orig_img = img
    orig_length, orig_widthw = orig_img.shape[:2]
    
    new_h = int(orig_length * scaling_factor)
    new_w = int(orig_widthw * scaling_factor)
    resized = np.zeros((int(new_h), int(new_w)))
    w_scale_factor = (orig_widthw ) / (new_w ) if new_h != 0 else 0
    h_scale_factor = (orig_length) / (new_h ) if new_w != 0 else 0
    
    
    
    for i in range(new_h):
        for j in range(new_w):
            
            x = i * h_scale_factor
            y = j * w_scale_factor
        
            x_floor = math.floor(x)
            x_ceil = min( orig_length - 1, math.ceil(x))
            y_floor = math.floor(y)
            y_ceil = min(orig_widthw - 1, math.ceil(y))

            if (x_ceil == x_floor) and (y_ceil == y_floor):
                q = orig_img[int(x), int(y)]
            elif (x_ceil == x_floor):
                q1 = orig_img[int(x), int(y_floor)]
                q2 = orig_img[int(x), int(y_ceil)]
                q = q1 * (y_ceil - y) + q2 * (y - y_floor)
            elif (y_ceil == y_floor):
                q1 = orig_img[int(x_floor), int(y)]
                q2 = orig_img[int(x_ceil), int(y)]
                q = (q1 * (x_ceil - x)) + (q2	 * (x - x_floor))
            else:
                v1 = orig_img[x_floor, y_floor]
                v2 = orig_img[x_ceil, y_floor]
                v3 = orig_img[x_floor, y_ceil]
                v4 = orig_img[x_ceil, y_ceil]

                q1 = v1 * (x_ceil - x) + v2 * (x - x_floor)
                q2 = v3 * (x_ceil - x) + v4 * (x - x_floor)
                q = q1 * (y_ceil - y) + q2 * (y - y_floor)

            resized[i,j] = q
    return resized#.astype(np.uint8)


def translate_image(img,rotation_angle=0,rotation_technique = 'bilinear',scale_factor=1,shear_factor =0):
    # if more than 1 translation applied the function will rotate then scale then shear
    # it will interpolate by bilinear interpolation by default
    print(img)

    h,w = img.shape
    new_img = np.zeros((h,w))
    i_pad= h/2
    j_pad =w/2

    # a,b are used to move the image center to the origin before rotating or scaling..,and then return the image to its center
    a = np.array([[1,0,-i_pad],
                  [0,1,-j_pad],
                  [0,0,1]])

    b = np.array([[1,0,i_pad],
                  [0,1,j_pad],
                  [0,0,1]])
    identity = np.array([[1,0,0],
                         [0,1,0],
                         [0,0,1]])

    scale_mat = np.array([[1/scale_factor,0,0],
                          [0,1/scale_factor,0],
                          [0,0,1]]) if scale_factor != 1 else identity
                          
    shear_mat = np.array([[1,0,0],
                          [shear_factor,1,0],
                          [0,0,1]]) if shear_factor != 0 else identity

    rot_mat = np.array([[np.cos(rotation_angle),np.sin(rotation_angle),0],
                        [-np.sin(rotation_angle), np.cos(rotation_angle),0],
                        [0,0,1]])if rotation_angle%(np.pi*2) != 0 else identity

    for i in range(0,h):
        for j in range(0,w):

            ij = np.array([i,j,1])
            
            # [b] . [rot_mat] . [scale_mat] . [shear_mat] . [a]
            x,y,_ = np.dot(np.dot(np.dot(np.dot(np.dot(b,rot_mat),scale_mat),shear_mat),a),ij)
            
            if x < h and y < w and x >0 and y >0:
                if rotation_technique == 'nearest neighbour':
                    new_img[i,j] = img[int(x),int(y)]
                else:
                    x_floor = math.floor(x)
                    x_ceil = min(w-1, math.ceil(x))
                    y_floor = math.floor( y )
                    y_ceil = min(h - 1, math.ceil(y))
                
                    if (x >= 0 and y >= 0 and x < h and y < w):
                        if (x_ceil == x_floor) and (y_ceil == y_floor):
                            q = img[int(x),int(y)]
                        elif (y_ceil == y_floor):
                            q1 = img[int(x_floor),int(y)]
                            q2 = img[int(x_ceil),int(y)]
                            q = q1 * (x_ceil - x) + q2 * (x - x_floor)
                        elif (x_ceil == x_floor):
                            q1 = img[int(x),int(y_floor)]
                            q2 = img[int(x),int(y_ceil)]
                            q = (q1 * (y_ceil - y)) + (q2 * (y - y_floor))
                        else:
                            v1 = img[x_floor,y_floor]
                            v2 = img[x_floor,y_ceil]
                            v3 = img[x_ceil,y_floor]
                            v4 = img[x_ceil,y_ceil]

                            q1 = v1 * (y_ceil - y) + v2 * (y - y_floor)
                            q2 = v3 * (y_ceil - y) + v4 * (y - y_floor)
                            q = q1 * (x_ceil - x) + q2 * (x - x_floor)

                        new_img[i][j] = q
    return new_img


def main():
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()