#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
np.random.seed(2020)

import os, sys
import glob
import cv2
import math
import pickle
import datetime
import pandas as pd
import statistics
import random
import time
import tensorflow as tf
import tensorflow.keras as keras
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
import sklearn.model_selection as model_selection
from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten 
from tensorflow.keras.layers import Conv2D, MaxPool2D, ZeroPadding2D
from tensorflow.keras.optimizers import SGD, Adam
#from tensorflow.keras.utils import np_utils
from tensorflow.keras.models import model_from_json
from sklearn.metrics import log_loss
from scipy.misc.pilutil import imread, imresize



use_cache = 1
# color type: 1 - grey, 3 - rgb
color_type_global = 1
dataset_path = './dataset'
dataset_imgs = dataset_path + '/imgs'  
test_size = 0.3   # test/all   
batch_size = 8 
nb_epoch = 1  
random_state = 33 
img_rows, img_cols = 256, 256      # default 480, 640
validation_ratio = 0.2  

# color_type = 1 - gray
# color_type = 3 - RGB


def get_im_cv2(path, img_rows, img_cols, color_type=1):
    # Load as grayscale
    if color_type == 1:
        img = cv2.imread(path, 0)
    elif color_type == 3:
        img = cv2.imread(path)
    # Reduce size
    #resized = cv2.resize(img, (img_cols, img_rows))
    # Keep size
    resized =  img 
    print("img size: ", len(img), len(img[0]) )  
    return resized


def get_im_cv2_mod(path, img_rows, img_cols, color_type=1):
    # Load as grayscale
    if color_type == 1:
        img = cv2.imread(path, 0)
    else:
        img = cv2.imread(path)
    # Reduce size 
    #rotate = random.uniform(-10, 10)
    #M = cv2.getRotationMatrix2D((img.shape[1]/2, img.shape[0]/2), rotate, 1)
    #img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))  
    resized = cv2.resize(img, (img_cols, img_rows) ) 
    #print( len(resized), len(resized[0])  ) 
    return resized c
    

def get_driver_data():
    dr = dict()
    path = os.path.join( dataset_path , 'driver_imgs_list.csv')
    print('Read drivers data')
    f = open(path, 'r')
    line = f.readline()
    while (1):
        line = f.readline()
        if line == '':
            break
        arr = line.strip().split(',')
        dr[arr[2]] = arr[0]
    f.close()
    return dr


def load_train(img_rows, img_cols, color_type=1):
    X_train = []
    y_train = []
    driver_id = []
    start_time = time.time()
    driver_data = get_driver_data()

    print('Read train images')
    for j in range(10):
        print('Load folder c{}'.format(j))
        path = os.path.join( dataset_imgs, 'train', 'c' + str(j), '*.jpg')
        files = glob.glob(path)
        for fl in files:
            flbase = os.path.basename(fl)
            img = get_im_cv2_mod(fl, img_rows, img_cols, color_type)
            X_train.append(img)
            y_train.append(j) 
            driver_id.append(driver_data[flbase]) 

    print('Read train data time: {} seconds'.format(round(time.time() - start_time, 2)))
    unique_drivers = sorted(list(set(driver_id)))
    #print('Unique drivers: {}'.format(len(unique_drivers)))
    #print(unique_drivers)  
    #print('X_train, y_train is: ', X_train[0], y_train[0] )
    #print( '============================' )  
    return X_train, y_train, driver_id, unique_drivers


def load_test(img_rows, img_cols, color_type=1):
    print('Read test images')
    start_time = time.time()
    path = os.path.join( dataset_imgs, 'test', '*.jpg')
    files = glob.glob(path)
    X_test = []
    X_test_id = []
    total = 0
    thr = math.floor(len(files)/10)
    for fl in files:
        flbase = os.path.basename(fl)
        img = get_im_cv2_mod(fl, img_rows, img_cols, color_type)
        X_test.append(img)
        X_test_id.append(flbase)
        total += 1
        if total%thr == 0:
            print('Read {} images from {}'.format(total, len(files)))
    
    print('Read test data time: {} seconds'.format(round(time.time() - start_time, 2)))
    return X_test, X_test_id


def cache_data(data, path):
    if os.path.isdir(os.path.dirname(path)):
        file = open(path, 'wb')
        pickle.dump(data, file)
        file.close()
    else:
        print('Directory "cache" doesnt exists')


def restore_data(path):
    data = dict()
    if os.path.isfile(path):
        file = open(path, 'rb')
        data = pickle.load(file)
    return data


def save_model(model):
    json_string = model.to_json()
    if not os.path.isdir('cache'):
        os.mkdir('cache')
    open(os.path.join('cache', 'architecture.json'), 'w').write(json_string)
    model.save_weights(os.path.join('cache', 'model_weights.h5'), overwrite=True)


def read_model():
    model = model_from_json(open(os.path.join('cache', 'architecture.json')).read())
    model.load_weights(os.path.join('cache', 'model_weights.h5'))
    return model


def split_validation_set(train, target, test_size):
    X_train, X_test, y_train, y_test = train_test_split(train, target, test_size=test_size, random_state=random_state)
    return X_train, X_test, y_train, y_test


def create_submission(predictions, test_id, info):
    result1 = pd.DataFrame(predictions, columns=['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9'])
    result1.loc[:, 'img'] = pd.Series(test_id, index=result1.index)
    now = datetime.datetime.now()
    if not os.path.isdir('subm'):
        os.mkdir('subm')
    suffix = info + '_' + str(now.strftime("%Y-%m-%d-%H-%M"))
    sub_file = os.path.join('subm', 'submission_' + suffix + '.csv')
    result1.to_csv(sub_file, index=False)

def shuffle_and_split( X, y, test_size ): 
    assert 0<= test_size and test_size <=1 
    X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, train_size=1-test_size, test_size=test_size, random_state=random_state)
    return X_train, X_test, y_train, y_test  

def read_and_normalize_train_data(img_rows, img_cols, color_type=1):
    cache_path = os.path.join('cache', 'train_r_' + str(img_rows) + '_c_' + str(img_cols) + '_t_' + str(color_type) + '.dat')
    if not os.path.isfile(cache_path) or use_cache == 0:
        train_data, train_target, driver_id, unique_drivers = load_train(img_rows, img_cols, color_type)
        cache_data((train_data, train_target, driver_id, unique_drivers), cache_path)
    else:
        print('Restore train from cache!')
        (train_data, train_target, driver_id, unique_drivers) = restore_data(cache_path)
   
    train_data = np.array(train_data, dtype=np.uint8)
    #print('100th y shape:', train_target[66])  
    train_target = np.array(train_target, dtype=np.uint8)
    #print('100th y shape:', train_target[66])  
    train_data = train_data.reshape(train_data.shape[0], img_rows, img_cols, color_type)
    #train_target = np_utils.to_categorical(train_target, 10) 
    #print('100th y shape:', train_target[66])  
    train_data = train_data.astype('float32') 
    train_data /= 255 
    print('Train shape:', train_data.shape)
    #print('Total train samples', train_data.shape[0] )
    #print('100th sample shape:', train_data[99])  
    #print('100th y shape:', train_target[66])  

    #print('100th\'s 1st shape:',train_data[99][0] )  
    #print('100th\'s 1st\'1st shape:',train_data[99][0][0] )  
    return train_data, train_target, driver_id, unique_drivers


def read_and_normalize_test_data(img_rows, img_cols, color_type=1):
    cache_path = os.path.join('cache', 'test_r_' + str(img_rows) + '_c_' + str(img_cols) + '_t_' + str(color_type) + '.dat')
    if not os.path.isfile(cache_path) or use_cache == 0:
        test_data, test_id = load_test(img_rows, img_cols, color_type)
        cache_data((test_data, test_id), cache_path)
    else:
        print('Restore test from cache!')
        (test_data, test_id) = restore_data(cache_path)

    test_data = np.array(test_data, dtype=np.uint8)
    test_data = test_data.reshape(test_data.shape[0], color_type, img_rows, img_cols)
    test_data = test_data.astype('float32')
    test_data /= 255
    #test_data = np.expand_dims(test_data, -1) 
    print('Test shape:', test_data.shape)
    print(test_data.shape[0], 'test samples')
    return test_data, test_id


def dict_to_list(d):
    ret = []
    for i in d.items():
        ret.append(i[1])
    return ret


def merge_several_folds_mean(data, nfolds):
    a = np.array(data[0])
    for i in range(1, nfolds):
        a += np.array(data[i])
    a /= nfolds
    return a.tolist()


def merge_several_folds_geom(data, nfolds):
    a = np.array(data[0])
    for i in range(1, nfolds):
        a *= np.array(data[i])
    a = np.power(a, 1/nfolds)
    return a.tolist()


def copy_selected_drivers(train_data, train_target, driver_id, driver_list):
    data = []
    target = []
    index = []
    for i in range(len(driver_id)):
        if driver_id[i] in driver_list:
            data.append(train_data[i])
            target.append(train_target[i])  
            index.append(i)
    data = np.array(data, dtype=np.float32)
    target = np.array(target, dtype=np.float32)
    index = np.array(index, dtype=np.uint32)
    return data, target, index


def create_model_v1(img_rows, img_cols, color_type=1):
    #model = Sequential() 
    model = tf.keras.Sequential()  
    print('model v1')     
    #model.add(tf.keras.layers.Conv2D 
    model.add(Conv2D(64, 3, 1, activation='relu', padding='same',  input_shape=(img_rows, img_cols, color_type)))
    #model.add(MaxPool2D(pool_size=(2, 2))) 
    model.add(Dropout(0.1))

    model.add(Conv2D(128, 3, 1, activation='relu', padding='same'))
    model.add(MaxPool2D(pool_size=(2, 2), strides=(2,2))) 
    model.add(Dropout(0.1))

    model.add(Conv2D(128, 3, 1, activation='relu', padding='same'))
    model.add(MaxPool2D(pool_size=(2, 2), strides=(2,2)))
    model.add(Dropout(0.1))

    model.add(Conv2D(256, 3, 1, activation='relu', padding='same'))
    model.add(MaxPool2D(pool_size=(2, 2), strides=(2,2))) 
    model.add(Dropout(0.1))

    
    model.add(Conv2D(256, 3, 1, activation='relu', padding='same'))
    model.add(MaxPool2D(pool_size=(2, 2), strides=(2,2)))  
    model.add(Dropout(0.1))  

    model.add(Conv2D(256, 3, 1, activation='relu', padding='same'))
    model.add(MaxPool2D(pool_size=(2, 2), strides=(2,2))) 
    model.add(Dropout(0.1))
    

    model.add(Flatten()) 
    model.add(Dense(1024))
    model.add(Dense(10))
    model.add(Activation('softmax'))

    model.compile(Adam(lr=1e-3), loss='categorical_crossentropy')
    return model


def create_model_v2( img_rows, img_cols, color_type=1):
    model = Sequential()
    model.add(ZeroPadding2D((1, 1), input_shape=(color_type, img_rows, img_cols)))
    model.add(Conv2D(64, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(64, 3, 3, activation='relu', padding='same'))
    model.add(MaxPool2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(128, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(128, 3, 3, activation='relu', padding='same'))
    model.add(MaxPool2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(256, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(256, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(256, 3, 3, activation='relu', padding='same'))
    model.add(MaxPool2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(512, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(512, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(512, 3, 3, activation='relu', padding='same'))
    model.add(MaxPool2D((2, 2), strides=(2, 2)))

    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(512, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(512, 3, 3, activation='relu', padding='same'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Conv2D(512, 3, 3, activation='relu', padding='same'))
    model.add(MaxPool2D((2, 2), strides=(2, 2)))

    model.add(Flatten())
    model.add(Dense(4096, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(4096, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1000, activation='softmax'))

    model.load_weights('../input/vgg16_weights.h5')

    # Code above loads pre-trained data and
    model.layers.pop()
    model.add(Dense(10, activation='softmax'))
    # Learning rate is changed to 0.001
    sgd = SGD(lr=1e-3, decay=1e-6, momentum=0.9, nesterov=True)

    model.compile(optimizer=sgd, loss='categorical_crossentropy')

    return model  


def readfile():
    # input image dimensions
    
    train_data, train_target, driver_id, unique_drivers = read_and_normalize_train_data(img_rows, img_cols, color_type_global)
    #test_data, test_id = read_and_normalize_test_data(img_rows, img_cols, color_type_global)

    yfull_train = dict()
    yfull_test = []
    unique_list_train = ['p002', 'p012', 'p014', 'p015', 'p016', 'p021', 'p022', 'p024',
                     'p026', 'p035', 'p039', 'p041', 'p042', 'p045', 'p047', 'p049',
                     'p050', 'p051', 'p052', 'p056', 'p061', 'p064', 'p066', 'p072',
                     'p075']
    X_train, Y_train, train_index = copy_selected_drivers(train_data, train_target, driver_id, unique_list_train)
    return X_train, Y_train, train_index

def run_single():

    X_data, Y_data, data_index = readfile()
    img_rows, img_cols = len(X_data[0]), len(X_data[0][0])  
    print('img size',  img_rows, img_cols )  
    #c shuffle, split original training dataset to training and testing. 'cause no testing labels in original test data.     
    X_train, X_test, Y_train, Y_test = shuffle_and_split( X_data, Y_data, test_size )  
    
    print('Shuffle and split done. ')
    #print( 'Train data size: ', X_train[0] ) 

    """

    unique_list_valid = ['p081']

    X_valid, Y_valid, test_index = copy_selected_drivers(train_data, train_target, driver_id, unique_list_valid)
    print('Start Single Run') print('Split train: ', len(X_train), len(Y_train)) print('Split valid: ', len(X_valid), len(Y_valid))
    print('Train drivers: ', unique_list_train)
    print('Test drivers: ', unique_list_valid)
    """ 

   
    # call model 
    model = create_model_v1(img_rows, img_cols, color_type_global)
    #model = create_model_v2(img_rows, img_cols, coclor_type_global)
    print("about to train the model") 

    model.compile(optimizer=tf.optimizers.Adam(learning_rate=0.0002,
                                           beta_1=0.9,
                                           beta_2=0.999,
                                           epsilon=1e-07,
                                           amsgrad=False,
                                           name='Adam'
                                           ),
                                          loss='sparse_categorical_crossentropy',
                                          metrics=['accuracy']
                  ) 
    print( len(X_train), len(Y_train), len(Y_test), len(Y_test) )  
    #print( '1st of X_train, Y_train are: ', X_train[2222], Y_train[2222]  )  
    #print( '1st of X_test, Y_test are: ', X_test[2222], Y_test[2222]  )  
    model.summary() 
 
    #model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=1, validation_data=(X_test, Y_test))
    #model.fit(X_train, Y_train, batch_size=batch_size, epochs=nb_epoch, validation_split=validation_ratio, shuffle=True, verbose=2)    
    model.fit(X_train, Y_train, batch_size=batch_size, epochs=nb_epoch, shuffle=True, verbose=2)    
    
    # save model
    model.save('trained_model/trained5.h5')  
    '''
    # score = model.evaluate(X_valid, Y_valid, show_accuracy=True, verbose=0)
    # print('Score log_loss: ', score[0])

    predictions_test = model.predict(X_test, batch_size=128, verbose=1)
    score = log_loss(Y_test, predictions_test )
    print('Score log_loss: ', score)

    # Store valid predictions
    for i in range(len(test_index)):
        yfull_train[test_index[i]] = predictions_valid[i]
    '''

    # Store test predictions
    #test_loss, test_acc = model.evaluate( X_test, Y_test, verbose=1)
    #print('Test Loss: {}'.format(test_loss))
    #print('Test Accuracy: {}'.format(test_acc))  

    validate = model.evaluate( X_test, Y_test, verbose=1)   
    print('Test result is: ', validate )  
    
    print('True label is: ', Y_test[99]) 
    x = np.array(X_test[99]) 
    x = x.reshape( 1, 256, 256, 1 )  
    print('Predict label is: ', model.predict_classes( x ) )   




if "__main__" == __name__:

    run_single()



