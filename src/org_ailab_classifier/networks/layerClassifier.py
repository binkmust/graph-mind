# -*- coding: UTF-8 -*-

'''
Created on 2016年8月19日

@author: hylovedd
'''
from org_ailab_seg.word2vec.wordVecOpt import WordVecOpt
import numpy

from keras.models import Sequential, model_from_json
from keras.layers.convolutional import Convolution1D, MaxPooling1D
from keras.layers.recurrent import LSTM, GRU
from keras.layers.core import Dropout, Dense, Activation, Flatten
from keras.callbacks import EarlyStopping

class NeuralLayerClassifier(object):
    
    def preTextEmbeddingProcess(self, gensimModelPath, textWordsList, maxTextLength, labelList=[]):
        '''
        '''
        
        # load gensim word vector model from file
        wordVecObj = WordVecOpt(modelPath=gensimModelPath)
        w2vModel = wordVecObj.loadModelfromFile(gensimModelPath)
        w2vVocab = w2vModel.vocab  # pre-load the vocabulary in w2v-model
        
        # produce train texts' 2D-matrix numpy-array
        trainMatList = []
        
        mat_rows = maxTextLength
        mat_cols = w2vModel.vector_size
        for textWords in textWordsList:
            textMatrix = numpy.zeros([mat_rows, mat_cols])
            for i in range(len(textWords)):
#                 print(textWords[i])
#                 print(type(textWords[i].decode('utf-8')))
                textWord = textWords[i].decode('utf-8')
                if textWord in w2vVocab:
                    wordGensimVector = wordVecObj.getWordVec(w2vModel, textWord)
                    textMatrix[i] = numpy.asarray(wordGensimVector, dtype='float32')
            trainMatList.append(textMatrix)
        
        del w2vVocab  # delete vocabulary to save the memory space
        
        x_data = numpy.asarray(trainMatList)
        # produce train labels' 1D-vector numpy-array
        y_data = None
        if len(labelList) != 0:
            y_data = numpy.asarray(labelList)
            
        return x_data, y_data
    
    def CNNClassify(self, x_train, y_train,
                    input_shape,
                    validation_split=0.15):
        '''
        input_shape is tuple as (cnt_size, word_vec_size)
        '''
        
        # set some fixed parameter in Convolution layer
        nb_filter = 128  # convolution core num       
        filter_length = 3  # convolution core size
        border_mode = 'valid'
        cnn_activation = 'relu'
        subsample_length = 1
        # set some fixed parameter in MaxPooling layer
        pool_length = 2
        # set some fixed parameter in Dense layer
        hidden_dims = 80
        # set some fixed parameter in Dropout layer
        dropout_rate = 0.5
        # set some fixed parameter in Activation layer
        final_activation = 'sigmoid'
        # set some fixed parameter in training
        batch_size = 32
        nb_epoch = 2
        
        # produce deep layer model
        model = Sequential()
        model.add(Convolution1D(nb_filter=nb_filter,
                                filter_length=filter_length,
                                border_mode=border_mode,
                                activation=cnn_activation,
                                subsample_length=subsample_length,
                                input_shape=input_shape))
        if pool_length == None:
            pool_length = model.output_shape[1]
        model.add(MaxPooling1D(pool_length=pool_length))
        
        model.add(Flatten())
        
        model.add(Dense(hidden_dims))
        model.add(Dropout(p=dropout_rate))
        model.add(Activation(activation=cnn_activation))
        
        model.add(Dense(1))
        model.add(Activation(activation=final_activation))
        
        # complie and train the model
#         validation_data = None
#         if x_test is not None and y_test is not None:
#             validation_data = (x_test, y_test)
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        model.fit(x=x_train, y=y_train,
                  batch_size=batch_size,
                  nb_epoch=nb_epoch,
                  validation_split=validation_split)
        
        return model
    
    def CNNPoolingLSTMClassify(self, x_train, y_train,
                               input_shape,
                               validation_split=0.15,
                               auto_stop=False):
        '''
        input_shape is tuple as (cnt_size, word_vec_size)
        '''
        
        # set some fixed parameter in Convolution layer
        nb_filter = 128  # convolution core num       
        filter_length = 5  # convolution core size
        border_mode = 'valid'
        cnn_activation = 'relu'
        subsample_length = 1
        # set some fixed parameter in MaxPooling layer
        pool_length = 2
        # set some fixed parameter in LSTM layer
        lstm_output_size = 64
        # set some fixed parameter in Dropout layer
        dropout_rate = 0.25
        # set some fixed parameter in Activation layer
        final_activation = 'sigmoid'
        # set some fixed parameter in training
        batch_size = 32
        nb_epoch = 10
        
        #=======================================================================
        # set callbacks function for auto early stopping
        # by monitor the loss or val_loss if not change any more
        #=======================================================================
        callbacks = []
        if auto_stop == True:
            monitor = 'val_loss' if validation_split > 0.0 else 'loss'
            patience = 2
            mode = 'min'
            early_stopping = EarlyStopping(monitor=monitor,
                                           patience=patience,
                                           mode=mode)
            callbacks = [early_stopping]
        
        # produce deep layer model
        model = Sequential()
        model.add(Convolution1D(nb_filter=nb_filter,
                                filter_length=filter_length,
                                border_mode=border_mode,
                                activation=cnn_activation,
                                subsample_length=subsample_length,
                                input_shape=input_shape))
        model.add(MaxPooling1D(pool_length=pool_length))
        
        model.add(LSTM(output_dim=lstm_output_size))
        if dropout_rate > 0:
            model.add(Dropout(p=dropout_rate))
            
        model.add(Dense(1))
        model.add(Activation(activation=final_activation))
        
        # complie and train the model
#         validation_data = None
#         if x_test is not None and y_test is not None:
#             validation_data = (x_test, y_test)
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        model.fit(x=x_train, y=y_train,
                  batch_size=batch_size,
                  nb_epoch=nb_epoch,
                  validation_split=validation_split,
                  callbacks=callbacks)
        
        return model
    
    def layerClassifyRecompile(self, model):
        '''
        '''
        loss = 'binary_crossentropy'
        optimizer = 'adam' 
        metrics = ['accuracy']
        
        model.compile(loss=loss, optimizer=optimizer, metrics=metrics)
        
        return model
    
    def layerClassifyPredict(self, model, x_test):
        '''
        '''
        batch_size = 32
        
        classes = model.predict_classes(x_test, batch_size=batch_size)
        proba = model.predict_proba(x_test, batch_size=batch_size)
    
        return classes, proba
    
    def layerClassifiyEvaluate(self, model, x_test, y_test):
        '''
        '''
        batch_size = 32
        score = model.evaluate(x_test, y_test, batch_size=batch_size)
#         print('\nmodel score params： ' + str(model.metrics_names))
        
        return score
    
    def modelPersistentStorage(self, model, storeFilePath):
        '''
        use json file to store the model's framework (.json)
        use hdf5 file to store the model's data (.h5)
        storeFilePath must be with .json or nothing(just filename)
        
        when store the .json framework to storeFilePath, also create/store 
        the .h5 file on same path automatically
        .json and .h5 file have same filename
        '''
        storeFileName = storeFilePath
        if storeFilePath.find('.json') != -1:
            storeFileName = storeFilePath[:storeFilePath.find('.json')]
        storeDataPath = storeFileName + '.h5'
        storeFramePath = storeFileName + '.json'
        
        frameFile = open(storeFramePath, 'w')
        json_str = model.to_json()
        frameFile.write(json_str)  # save model's framework file
        frameFile.close()
        model.save_weights(storeDataPath, overwrite=True)  # save model's data file
        
        return storeFramePath, storeDataPath
    
    def loadStoredModel(self, storeFilePath, recompile=False):
        '''
        note same as previous function
        if u just use the model to predict, you need not to recompile the model
        if u want to evaluate the model, u should set the parameter: recompile as True
        '''
        storeFileName = storeFilePath
        if storeFilePath.find('.json') != -1:
            storeFileName = storeFilePath[:storeFilePath.find('.json')]
        storeDataPath = storeFileName + '.h5'
        storeFramePath = storeFileName + '.json'
        
        frameFile = open(storeFramePath, 'r')
#         yaml_str = frameFile.readline()
        json_str = frameFile.readline()
#         print(json_str)
        model = model_from_json(json_str)
        if recompile == True:
            model = self.layerClassifyRecompile(model)  # if need to recompile
#         print(model.to_json())
        model.load_weights(storeDataPath)
        frameFile.close()
        
        return model

if __name__ == '__main__':
    
    p = [[1, 2, 3, 4, 5],
        [1, 2, 3, 4, 5],
        [1, 2, 3, 4, 5]]
    p_list = []
    for i in range(100):
        p_list.append(numpy.asarray(p, dtype='float32'))
    npx = numpy.asarray(p_list)
    print(type(npx))
    print(len(npx))
    print(len(npx[:80]))
    print(npx)
