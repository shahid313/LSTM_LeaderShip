import numpy as np
import cv2
import os
import re
from natsort import natsorted
"""
This code is highly influenced by the implementation of:
https://github.com/joelthchao/tensorflow-finetune-flickr-style/dataset.py
But changed abit to allow dataaugmentation (yet only horizontal flip) and 
shuffling of the data. 
The other source of inspiration is the ImageDataGenerator by @fchollet in the 
Keras library. But as I needed BGR color format for fine-tuneing AlexNet I 
wrote my own little generator.
"""

class ImageDataGenerator:
    def __init__(self, class_list, horizontal_flip=False, shuffle=True, 
                 mean = np.array([128., 128., 128.],float), scale_size=(224, 224),
                 nb_classes = 2):
        
                
        # Init params
        self.horizontal_flip = horizontal_flip
        self.n_classes = nb_classes
        self.shuffle = shuffle
        self.mean = mean
        self.basePath ='./multipleDynamicImages_100/'
        self.scale_size = scale_size
        self.pointer = 0
#        self.natural_sort(file)
        self.read_class_list(class_list)

        if self.shuffle:
            self.shuffle_data()

#    def natural_sort(l):
#        convert = lambda text: int(text) if text.isdigit() else text.lower()
#        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
#        return sorted(l, key=alphanum_key)

    def read_class_list(self,class_list):
        """
        Scan the image file and get the image paths and labels
        """
        with open(class_list) as f:
            lines = f.readlines()
            self.images = []
            self.labels = []
            for l in lines:
                items = l.split()
                fullPath =  self.basePath+items[0]+'/'

                filelist = [file for file in os.listdir(fullPath) if file.endswith('.jpg')]
                filelist = natsorted(filelist)
                for file in filelist:
                    self.images.append(fullPath+file)
                    self.labels.append(int(items[1]))
            
            #store total number of data
            self.data_size = len(self.labels)
        
    def shuffle_data(self):
        """
        Random shuffle the images and labels
        """
        #images = self.images.copy()
        images = self.images[:]
        #labels = self.labels.copy()
        labels = self.labels[:]
        self.images = []
        self.labels = []
        
        #create list of permutated index and shuffle data accoding to list
        idx = np.random.permutation(len(labels))
        for i in idx:
            self.images.append(images[i])
            self.labels.append(labels[i])
                
    def reset_pointer(self):
        """
        reset pointer to begin of the list
        """
        self.pointer = 0
        
        if self.shuffle:
            self.shuffle_data()
        
    
    def next_batch(self, batch_size):
        """
        This function gets the next n ( = batch_size) images from the path list
        and labels and loads the images into them into memory 
        """
        # Get next batch of image (path) and labels
        paths = self.images[self.pointer:self.pointer + batch_size]
        labels = self.labels[self.pointer:self.pointer + batch_size]
        
        #update pointer
        self.pointer += batch_size
        
        # Read images
        images = np.ndarray([batch_size, self.scale_size[0], self.scale_size[1], 3])
        for i in range(len(paths)):
            img = cv2.imread(paths[i])
            
            #flip image at random if flag is selected
            if self.horizontal_flip and np.random.random() < 0.5:
                img = cv2.flip(img, 1)
            
            #rescale image
            img = cv2.resize(img, (self.scale_size[0], self.scale_size[1]))
            img = img.astype(np.float32)
            
            #subtract mean
            img -= self.mean
                                                                 
            images[i] = img

        # Expand labels to one hot encoding
        one_hot_labels = np.zeros((batch_size, self.n_classes))
        for i in range(len(labels)):
            one_hot_labels[i][labels[i]] = 1

        #return array of images and labels
        return images, one_hot_labels#,paths


