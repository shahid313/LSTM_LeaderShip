""" Recurrent Neural Network.
A Recurrent Neural Network (LSTM) implementation using Leader Detectoin Dataset
"""

from __future__ import print_function

import tensorflow as tf
from tensorflow.contrib import rnn
import os
import scipy.misc
#import pandas as pd
####For Matlab .mat file feature Load####
import scipy.io as sio
import scipy
import numpy as np
import keras
from sklearn.metrics import confusion_matrix

# Training Parameters
learning_rate = 1e-4
training_steps = 20000  # 1000
batch_size = 30  # 128
display_step = 100  # accuracy and loss on training batch will be displayed on consol after these steps

# Network Parameters
num_input = 4096  # fc6 feature size as a input length (img shape: 4096)
timesteps = 296  # timesteps
num_hidden = 256  # hidden layer num of features
num_classes = 3  # Leader non Leader total classes (0-2 digits(0 no leader, 1 leader, 2 least leader(intermediate class)))

######################################################Training Data Generation########
Label_file = '../labels.mat';  # Labels Matfile name
path = '../Meetingfc6';  # Path Folder for fc6 feature values

Y_traine = scipy.io.loadmat(Label_file)  # load label file
fc6filfixd = 'meetingSequence_CNNFeatures_seperatedMatrix'  # common name for all features mat file

Y_train = np.array([], dtype='float32')  # Empty numpy arrays for Labels
Y_test = np.array([], dtype='float32')
X_train = [];  # Empty structurs for training feature values
X_test = [];
# X_train = [];
for i in range(0, 232):  # 232):  ### 1 to 232 - Last meeting leave out, for test ranging from 219-232
    fc6ffname = path + '/' + fc6filfixd + str(i + 1) + '.mat'
    fc6Feature = sio.loadmat(fc6ffname);
    tmpr = np.array(fc6Feature['curr_seq_perSample'], dtype=np.float32);
    strtframIdx = 0;
    endframIdx = strtframIdx + timesteps;
    length = len(tmpr);
    while (endframIdx <= length):
        chunk = (tmpr[strtframIdx:endframIdx, 0:4096]).flatten()
        check = Y_traine['labels'][i];
        if ((i > -1) & (i < 13)):  # If index is less than 219, make it a part of Training data and label
            Y_test = np.append(Y_test, check)
            X_test.append(chunk)
        else:  # from 213-232 make it part of test data
            Y_train = np.append(Y_train, check)
            X_train.append(chunk)
        if (check == 0):
            strtframIdx = strtframIdx + 96;
        else:
            strtframIdx = strtframIdx + 64;
        endframIdx = strtframIdx + timesteps;
####Code for training data shuffling
X_train = np.array(X_train, dtype=np.float32)
Train_Data = np.hstack([X_train, Y_train.reshape([-1, 1])])
np.random.shuffle(Train_Data)
Y_train = keras.utils.to_categorical(Train_Data[:, -1], num_classes)
X_train = Train_Data[:, :-1]
################Test Data
X_test = np.array(X_test, dtype=np.float32)
Y_test1 = keras.utils.to_categorical(Y_test, num_classes)
# Tensorflow input and output shape
X = tf.placeholder("float", [None, timesteps, num_input])
Y = tf.placeholder("float", [None, num_classes])
dropout = tf.placeholder(tf.float32)
# Define weights
weights = {
    'out': tf.Variable(tf.random_normal([num_hidden, num_classes]))
}
biases = {
    'out': tf.Variable(tf.random_normal([num_classes]))
}


def RNN(x, weights, biases,dropout):
    # Prepare data shape to match `rnn` function requirements
    # Current data input shape: (batch_size, timesteps, n_input)
    # Required shape: 'timesteps' tensors list of shape (batch_size, n_input)

    # Unstack to get a list of 'timesteps' tensors of shape (batch_size, n_input)
    x = tf.unstack(x, timesteps, 1)

    # Define a lstm cell with tensorflow
    #lstm_cell = rnn.BasicLSTMCell(num_hidden, forget_bias=1.0)
    lstm_cell = rnn.MultiRNNCell([rnn.BasicLSTMCell(num_hidden), rnn.BasicLSTMCell(num_hidden)])
    dropout = tf.nn.rnn_cell.DropoutWrapper(lstm_cell, output_keep_prob=1-dropout)
    ######
    # lstm_cell2 = rnn.BasicLSTMCell(num_hidden, forget_bias=1.0)
    # dropout2  = tf.nn.rnn_cell.DropoutWrapper(lstm_cell2, output_keep_prob=0.35)
    # dropout   = tf.nn.rnn_cell.DropoutWrapper
    # Get lstm cell output
    outputs, states = rnn.static_rnn(dropout, x, dtype=tf.float32)

    # sum = tf.reduce_mean(outputs,axis=0)#.reduce_sum(outputs, axis=1)
    # Linear activation, using rnn inner loop last output
    # return tf.matmul(sum, weights['out']) + biases['out']
    return tf.matmul(outputs[-1], weights['out']) + biases['out']


logits = RNN(X, weights, biases,dropout)
# prediction = tf.nn.softmax(logits)
# class_weight = tf.constant([0.100, 0.450, 0.450])
# weighted_logits = tf.multiply(logits , class_weight)#  .matmul(logits , class_weight)
# prediction = tf.nn.softmax(logits)
prediction = tf.nn.softmax(logits)
loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=Y))
# optimizer = tf.train.AdamOptimizer(.8).minimize(loss_op)
####################################################
# Define loss and optimizer
# loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
#    logits=logits, labels=Y))
# optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
# rain_op = optimizer.minimize(loss_op)
global_step = tf.Variable(0, dtype=tf.int32, trainable=False, name='global_step')
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss_op, global_step=global_step)

# Evaluate model (with test logits, for dropout to be disabled)
Y_predict = tf.argmax(prediction, 1);
correct_pred = tf.equal(tf.argmax(prediction, 1), tf.argmax(Y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

# Initialize the variables (i.e. assign their default value)
init = tf.global_variables_initializer()
# Start training
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.9)
# sess = tf.Session(config=tf.ConfigProto(
#    allow_soft_placement=True, log_device_placement=True))
# saver = tf.train.Saver()

# global_step = tf.Variable(0, dtype=tf.int32, trainable=False,name='global_step')
with tf.Session() as sess:
    sess.run([init])
    # coord = tf.train.Coordinator()
    # threads = tf.train.start_queue_runners(coord=coord)
    strtPont = 0
    lengt = len(X_train)
    testdrop  =  0;
    traindrop =  0.60
    for step in range(1, training_steps + 1):
        batch_x = X_train[strtPont:(strtPont + batch_size)]
        batch_y = Y_train[strtPont:(strtPont + batch_size), :]
        # print('Batch_y is',batch_y)
        # Reshape data to get 256 timestamps and 4096 feature elements
        batch_x = batch_x.reshape((batch_size, timesteps, num_input))
        # Run optimization op (backprop)
        # writer =  tf.summary.FileWriter('./graphs',sess.graph)
        sess.run([optimizer, loss_op], feed_dict={X: batch_x, Y: batch_y,dropout:traindrop})
        if ((strtPont + batch_size) < lengt - batch_size):
            strtPont = strtPont + batch_size;  # For next batch training data access
        else:
            strtPont = 0;
            print('step number is', step)
        # print('Batch_y is',batch_y)
        if step % display_step == 0 or step == 1:
            loss, acc = sess.run([loss_op, accuracy], feed_dict={X: batch_x, Y: batch_y,dropout:testdrop})
            print("Step " + str(step) + ", Minibatch Loss= " + \
                  "{:.4f}".format(loss) + ", Train Accuracy= " + \
                  "{:.3f}".format(acc))
            # Calculate batch loss and accuracy
            test_len = len(X_test)
            # Y_test   =  Y_test.labels[:test_len]
            X_test = X_test.reshape((-1, timesteps, num_input))
            Predict = sess.run(Y_predict, feed_dict={X: X_test, dropout:testdrop})
            # sess.run(accuracy, feed_dict={X: X_test, Y: Y_test}))
            # Predict = np.argmax(ans, 1)
            confusion_mat = confusion_matrix(Y_test, Predict)
            np.set_printoptions(threshold=np.nan)
            print('confusion Matrix', confusion_mat)

    print("Optimization Finished!")
    test_len = len(X_test)
    # Y_test   =  Y_test.labels[:test_len]
    X_test = X_test.reshape((-1, timesteps, num_input))
    Predict = sess.run(Y_predict, feed_dict={X: X_test, dropout:testdrop})
    # sess.run(accuracy, feed_dict={X: X_test, Y: Y_test}))
    # Predict = np.argmax(ans, 1)
    confusion_mat = confusion_matrix(Y_test, Predict)
    np.set_printoptions(threshold=np.nan)
    print('confusion Matrix', confusion_mat)
    # saver = tf.train.Saver()
    # scipy.misc.imsave('/home/smuhammad/LeaderTensorflow/outfile.jpg', np.array(confusion_mat,dtype='int32'))
    print("Testing Accuracy:", \
          sess.run(accuracy, feed_dict={X: X_test, Y: keras.utils.to_categorical(Y_test, num_classes),dropout:testdrop}))
    np.save('confusion_mat12.npy', confusion_mat)
