#!/usr/bin/env python
# -*- coding: utf8 -*-
import codecs
import os

from libs.constants import DEFAULT_ENCODING

TXT_EXT = '.txt'
ENCODE_METHOD = DEFAULT_ENCODING

class YOLOWriter:

    def __init__(self, folder_name, filename, img_size, database_src='Unknown', local_img_path=None):
        self.folder_name = folder_name
        self.filename = filename
        self.database_src = database_src
        self.img_size = img_size
        self.box_list = []
        self.local_img_path = local_img_path
        self.verified = False

    def add_bnd_box(self, x_min, y_min, x_max, y_max, name, difficult, name2=None):
        bnd_box = {'xmin': x_min, 'ymin': y_min, 'xmax': x_max, 'ymax': y_max}
        bnd_box['name'] = name
        bnd_box['name2'] = name2 if name2 else ""
        bnd_box['difficult'] = difficult
        self.box_list.append(bnd_box)

    def bnd_box_to_yolo_line(self, box, class_list=[], class_list2=[]):
        x_min = box['xmin']
        x_max = box['xmax']
        y_min = box['ymin']
        y_max = box['ymax']

        x_center = float((x_min + x_max)) / 2 / self.img_size[1]
        y_center = float((y_min + y_max)) / 2 / self.img_size[0]

        w = float((x_max - x_min)) / self.img_size[1]
        h = float((y_max - y_min)) / self.img_size[0]

        # PR387
        box_name = box['name']
        if box_name not in class_list:
            class_list.append(box_name)

        class_index = class_list.index(box_name)
        
        # Handle second label
        class_index2 = -1
        if 'name2' in box and box['name2']:
            box_name2 = box['name2']
            if box_name2 not in class_list2:
                class_list2.append(box_name2)
            class_index2 = class_list2.index(box_name2)

        return class_index, class_index2, x_center, y_center, w, h

    def save(self, class_list=[], class_list2=[], target_file=None):

        out_file = None  # Update yolo .txt
        out_class_file = None   # Update class list .txt
        out_class_file2 = None  # Update class list 2 .txt

        if target_file is None:
            out_file = open(
            self.filename + TXT_EXT, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(self.filename)), "classes.txt")
            classes1_file = os.path.join(os.path.dirname(os.path.abspath(self.filename)), "classes1.txt")
            classes2_file = os.path.join(os.path.dirname(os.path.abspath(self.filename)), "classes2.txt")
            out_class_file = open(classes_file, 'w')
            out_class1_file = open(classes1_file, 'w')
            out_class2_file = open(classes2_file, 'w')

        else:
            out_file = codecs.open(target_file, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(target_file)), "classes.txt")
            classes1_file = os.path.join(os.path.dirname(os.path.abspath(target_file)), "classes1.txt")
            classes2_file = os.path.join(os.path.dirname(os.path.abspath(target_file)), "classes2.txt")
            out_class_file = open(classes_file, 'w')
            out_class1_file = open(classes1_file, 'w')
            out_class2_file = open(classes2_file, 'w')


        for box in self.box_list:
            class_index, class_index2, x_center, y_center, w, h = self.bnd_box_to_yolo_line(box, class_list, class_list2)
            # Dual label format: class1 class2 x_center y_center w h
            if class_index2 >= 0:
                out_file.write("%d %d %.6f %.6f %.6f %.6f\n" % (class_index, class_index2, x_center, y_center, w, h))
            else:
                # Backward compatibility: single label format
                out_file.write("%d %.6f %.6f %.6f %.6f\n" % (class_index, x_center, y_center, w, h))

        # Save class lists
        for c in class_list:
            out_class_file.write(c+'\n')
            out_class1_file.write(c+'\n')
        
        for c in class_list2:
            out_class2_file.write(c+'\n')

        out_class_file.close()
        out_class1_file.close()
        out_class2_file.close()
        out_file.close()



class YoloReader:

    def __init__(self, file_path, image, class_list_path=None):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.file_path = file_path

        if class_list_path is None:
            dir_path = os.path.dirname(os.path.realpath(self.file_path))
            self.class_list_path = os.path.join(dir_path, "classes.txt")
            self.class_list1_path = os.path.join(dir_path, "classes1.txt")
            self.class_list2_path = os.path.join(dir_path, "classes2.txt")
        else:
            self.class_list_path = class_list_path
            dir_path = os.path.dirname(os.path.realpath(class_list_path))
            self.class_list1_path = os.path.join(dir_path, "classes1.txt")
            self.class_list2_path = os.path.join(dir_path, "classes2.txt")

        # print (file_path, self.class_list_path)

        # Read main class list
        classes_file = open(self.class_list_path, 'r')
        self.classes = classes_file.read().strip('\n').split('\n')
        classes_file.close()
        
        # Read class list 1 and 2 if they exist
        self.classes1 = self.classes  # Default to main classes
        self.classes2 = []
        
        if os.path.exists(self.class_list1_path):
            with open(self.class_list1_path, 'r') as f:
                self.classes1 = f.read().strip('\n').split('\n')
        
        if os.path.exists(self.class_list2_path):
            with open(self.class_list2_path, 'r') as f:
                self.classes2 = f.read().strip('\n').split('\n')

        # print (self.classes)

        img_size = [image.height(), image.width(),
                    1 if image.isGrayscale() else 3]

        self.img_size = img_size

        self.verified = False
        # try:
        self.parse_yolo_format()
        # except:
        #     pass

    def get_shapes(self):
        return self.shapes

    def add_shape(self, label, x_min, y_min, x_max, y_max, difficult, label2=None):

        points = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
        # For dual label support, return dict format
        if label2:
            shape_data = {
                'label': label,
                'label2': label2,
                'points': points,
                'line_color': None,
                'fill_color': None,
                'difficult': difficult
            }
            self.shapes.append(shape_data)
        else:
            # Backward compatibility
            self.shapes.append((label, points, None, None, difficult))

    def yolo_line_to_shape(self, class_index, x_center, y_center, w, h):
        class_idx = int(class_index)
        if class_idx >= len(self.classes):
            print(f"[YOLO] Warning: Class index {class_idx} out of range (max: {len(self.classes)-1}), using index 0")
            class_idx = 0
        label = self.classes[class_idx]

        x_min = max(float(x_center) - float(w) / 2, 0)
        x_max = min(float(x_center) + float(w) / 2, 1)
        y_min = max(float(y_center) - float(h) / 2, 0)
        y_max = min(float(y_center) + float(h) / 2, 1)

        x_min = round(self.img_size[1] * x_min)
        x_max = round(self.img_size[1] * x_max)
        y_min = round(self.img_size[0] * y_min)
        y_max = round(self.img_size[0] * y_max)

        return label, x_min, y_min, x_max, y_max

    def parse_yolo_format(self):
        bnd_box_file = open(self.file_path, 'r')
        for bndBox in bnd_box_file:
            parts = bndBox.strip().split(' ')
            
            # Check if this is dual label format (6 values) or single label format (5 values)
            if len(parts) == 6:
                # Dual label format: class1 class2 x_center y_center w h
                class_index1, class_index2, x_center, y_center, w, h = parts
                label1, x_min, y_min, x_max, y_max = self.yolo_line_to_shape(class_index1, x_center, y_center, w, h)
                
                # Get label2 from classes2 list
                class_idx2 = int(class_index2)
                label2 = ""
                if self.classes2 and 0 <= class_idx2 < len(self.classes2):
                    label2 = self.classes2[class_idx2]
                
                # Caveat: difficult flag is discarded when saved as yolo format.
                self.add_shape(label1, x_min, y_min, x_max, y_max, False, label2)
            elif len(parts) == 5:
                # Single label format: class x_center y_center w h
                class_index, x_center, y_center, w, h = parts
                label, x_min, y_min, x_max, y_max = self.yolo_line_to_shape(class_index, x_center, y_center, w, h)
                
                # Caveat: difficult flag is discarded when saved as yolo format.
                self.add_shape(label, x_min, y_min, x_max, y_max, False)
