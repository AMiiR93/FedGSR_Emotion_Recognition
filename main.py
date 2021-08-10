import os
import numpy as np
import tensorflow as tf
import pandas as pd
import dataset as dt

from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Input, Conv1D, Conv2D, MaxPooling2D, Dropout
from tensorflow.keras.layers import Flatten, Dense, BatchNormalization, Concatenate
from tensorflow.keras.models import Model
import matplotlib.pyplot as plt

pd.options.display.width = 0



class DNN:

  def __init__(self, kwargs):

    print('The DNN class is building ....')

    # initializing values
    self.phy_dir = kwargs.get('phy_dir', './')
    self.ann_dir = kwargs.get('ann_dir', './')
    self.arch = kwargs.get('architecture', 'CENT')
    self.ml = kwargs.get('model', 'CNN').upper()
    self.decompose_flag = kwargs.get('decompose', False)
    self.gsr_only_flag = kwargs.get('gsr_only', False)
    self.minmax = kwargs.get('minmax_norm', False)
    self.ecg_flag = kwargs.get('ecg', False)
    self.lr = kwargs.get('lr', 0.0001)
    self.optimizer = kwargs.get('optimizer', Adam(self.lr))
    "TODO: WE CAN CONSIDER OTHER FEATURES SAME AS THE ABOVE FEATURES WITH SAME METHOD"


    assert self.ml == 'CNN' or self.ml == 'LSTM'
    print('In this run, we use a {}-based model with a {} architecture'.format(self.ml, self.arch))

    # Dataset class is called and built here.
    # The load_data() function gives us Phasic GSR (x),
    # features extracted by Continuous wavelet transform (cwt) from Phasic GSR,
    # and labels (y)
    dataset = dt.CASE(self.phy_dir, self.ann_dir, self.arch)
    self.x, self.y, self.cwt = dataset.load_data()
    print('The Dataset is loaded.')
    # print('Raw GSR shape: {},  Label shape: {}, cwt shape: {}'.format(self.x.shape, self.y.shape, self.cwt.shape))


    # self.NUM_USRS is the number of file in the dataset
    self.Num_Usr = self.x.shape[0]
    self.C = kwargs.get('C', self.x.shape[0])
    self.Num_Sess = kwargs.get('Num_Sess', self.x.shape[1])





    if self.arch == 'CENT':
      print('\nThe number of all stacked samples are', self.x.shape[0])
      self.model = self._create_model()

    elif self.arch == 'FED':
      print('\nThe Number of Users is {}, The Number of sessions for each user is {}.'.format(self.Num_Usr,
                                                                                              self.Num_Sess))
      print('The Number of Users used for aggregation in the global model (C) is {} '.format(self.C))
      self.model = [self._create_model() for num_usr in range((self.Num_Usr-1))]
      # self.model = [self._create_model() for num_usr in range(3)] # this line will be deleted

      print('Number of models used for aggregating the global model is  {}.'.format(len(self.model)))
      self.global_model = self._create_model()



  def _create_model(self):

    if self.gsr_only_flag:
      input_1 = Input(shape=(1000, 1), name="input_1")
      # input_2 = Input(shape=(50, 2,  1), name="input_2")
      input_2 = Input(shape=(1000, 20, 1), name="input_2")
    else:
      'TODO: it should be determinded how many features we are going to work on.'
      pass

    if self.ml == 'CNN':
      output1, output2 = self._cnn_model([input_1, input_2])
    elif self.ml == 'LSTM':
      'TODO: We should compelte the LSTM model'
      pass


    losses = {'arousal': 'binary_crossentropy',
              'valence': 'binary_crossentropy',}

    metrics = {'arousal': 'accuracy',
               'valence': 'accuracy',}

    model = Model(inputs=[input_1, input_2], outputs=[output1, output2],)
    # plot_model(self.cnn, to_file='CNN.png', show_shapes=True, show_layer_names=True)
    model.compile(optimizer=self.optimizer,
                  loss=losses,
                  metrics=metrics)


    return model


  def _cnn_model(self, _input):

    # print('\n    building    **** CNN ****   \n\n ')
    # print('shapes are ')
    # print(_input[0].shape, _input[1].shape, '_input[2].shape')

    l1 = Conv1D(32, kernel_size=(5), padding='same', strides=1, activation='relu')(_input[0])
    # l2 = Conv1D(64, kernel_size=(5), padding='same', strides=1, activation='relu')(l1)
    # print('first input ', l1.shape, l2.shape)

    l3 = Conv2D(16, kernel_size=5, padding='same', strides=1, activation='relu')(_input[1])
    # MaxPooling2D()
    # l4 = Conv2D(32, kernel_size=5, padding='same', strides=1, activation='relu')(l3)
    # print('second input ', l3.shape, l4.shape)

    # l5 = Conv2D(16, kernel_size=5, padding='same', strides=1, activation='relu')(_input[2])
    # l6 = Conv2D(32, kernel_size=5, padding='same', strides=1, activation='relu')(_input[2])
    # print('third input ', l5.shape, l6.shape)

    # l3 = Conv1D(64, kernel_size=(5), padding='same', strides=2, activation='relu')(l2)
    # print(l3.shape)
    #
    # l4 = Conv1D(128, kernel_size=(5), padding='same', strides=2, activation='relu')(l3)
    # print(l4.shape)
    #
    # l5= Conv1D(128, kernel_size=(5), padding='same', strides=2, activation='relu')(l4)
    # print(l5.shape)
    l1 = Flatten()(l1)
    l3 = Flatten()(l3)
    # l6 = Flatten()(l6)
    # print('flattened ', l1.shape, l3.shape, 'l6.shape')
    conc_l = Concatenate()([l1, l3])


    l7 = Dense(units=128, activation='relu')(conc_l)
    l8 = Dense(units=64, activation='relu')(l7)

    out1 = Dense(units=1, activation='sigmoid', name='arousal')(l8)
    out2 = Dense(units=1, activation='sigmoid', name='valence')(l8)

    return out1, out2

  def LSTM(self):
    'TODO: We are going to design an LSTM model.'
    pass

  def RNN(self):
    pass

  @staticmethod
  def get_average_weights(models):

    weights = [model.get_weights() for model in models]
    new_weights = list()

    for weights_list_tuple in zip(*weights):
      new_weights.append(
        np.array([np.array(w).mean(axis=0) for w in zip(*weights_list_tuple)]))

    return new_weights

  def stack_up(self, ith_usr):
    """

    This function stacks up all the sessions array in the I-th user in one sequential array.
    It is just used in FED architecture
    If we do this function, it means our framework is using a IID format of a dataset.

    :param ith_usr: The number of user's place in the row of 30 users in the dataset
    :return: return sequential expanded-dimension array of x, y, cwt

    """

    x = np.concatenate([self.x[ith_usr][i] for i in range(self.Num_Sess)])
    y = np.concatenate([self.y[ith_usr][i] for i in range(self.Num_Sess)])
    cwt = np.concatenate([self.cwt[ith_usr][i] for i in range(self.Num_Sess)])

    return np.expand_dims(x, axis=-1), np.expand_dims(y, axis=-1), np.expand_dims(cwt, axis=-1)


  def train(self, B=32, GE=10, LE=1):
    """
    This function Trains the model.

    :param B: B represents the number of sample in a batch for each iteration
    :param GE: GE is showing either Global Epochs in FED architecture or
               the number of Epochs in CENT architecture.
    :param LE: The number of Local Epochs each client makes over its local dataset.
               It is used just in the FED architecture.
    :return: None

    """
    print('\nTraining Phase is starting. It may take a while to train the model.')

    if self.arch == 'CENT':

      self.x = np.expand_dims(self.x, axis=-1)
      self.y = np.expand_dims(self.y, axis=-1)
      self.cwt = np.expand_dims(self.cwt, axis=-1)

      self.model.fit(x=[self.x, self.cwt], y={"arousal": self.y[:, 0], "valence": self.y[:, 1]},
                     batch_size=B, epochs=GE, verbose=1)



    elif self.arch == 'FED':
      test_x, test_y, test_cwt = self.stack_up(self.Num_Usr-1)

      for ge in range(GE):

        _ = [model.set_weights(self.global_model.get_weights()) for model in self.model]

        for ith in range(len(self.model)):

          x, y, cwt = self.stack_up(ith)
          # print('shapes after def stack_up() ', x.shape, y.shape, cwt.shape)
          self.model[ith].fit(x=[x, cwt], y={"arousal": y[:, 0], "valence": y[:, 1]},
                              batch_size=B, epochs=LE, verbose=2)

        rand_models_for_global_avg = np.random.choice(self.model, size=self.C, replace=False).tolist() # we can set p here to consider a weight for each mdoel

        self.global_model.set_weights(self.get_average_weights(rand_models_for_global_avg))

        print('\nGlobal Epoch {} .'.format(ge))
        results = self.global_model.evaluate(x=[test_x, test_cwt],
                                             y={"arousal": test_y[:, 0], "valence": test_y[:, 1]},
                                             batch_size=B)





if __name__ == '__main__':
  print('Starting ... \n')

  annotation_dir = '/Users/amir/Desktop/DR/GSR/CASE_dataset/CASE_dataset/interpolated/annotations/'  # the directory of annotations
  physiological_dir = '/Users/amir/Desktop/DR/GSR/CASE_dataset/CASE_dataset/interpolated/physiological/'  # the directory fo physiological signals

  # attr = {'phy_dir': physiological_dir,
  #         'ann_dir': annotation_dir,
  #         'gsr_only': True,
  #         'decompose': True,
  #         'minmax_norm': True,
  #         'architecture': 'CENT',
  #         'model': 'CNN',
  #         'C': 2}


  attr = {'phy_dir': physiological_dir,
          'ann_dir': annotation_dir,
          'gsr_only': True,
          'decompose': True,
          'minmax_norm': True,
          'architecture': 'FED',
          'model': 'CNN',
          'C': 2}


  obj = DNN(attr)
  obj.train(GE=5, LE=3)




