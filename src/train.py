import sys
import os
if __name__ == '__main__':
    sys.path.append(os.path.dirname(sys.path[0]))

import cv2
import torch
import numpy as np
import torch.nn as nn
from tqdm import tqdm
import torch.optim as optim
from torchvision import utils as vutils

from tqdm import tqdm
import csv
import dataset
import model_core
from loss import am_softmax

torch.cuda.set_device(2)

if __name__ == '__main__':
    device = torch.device("cuda:2" if torch.cuda.is_available() else "cpu")

    csvFile = open("/media/HardDisk_new/wx/Dataset/deepface/train.labels.csv", "r")
    reader = csv.reader(csvFile)
    label_dict = dict()
    for item in reader:
        key = item[-1][:-2]
        value = item[-1][-1]
        if value != 'l':
            value = int(value)
            label_dict.update({key: value})

    train_list = [file for file in os.listdir('/media/HardDisk_new/wx/Dataset/deepface/image/train/') if file.endswith('.jpg')]
    TrainData = torch.utils.data.DataLoader(dataset.LoadData(train_list, label_dict, mode='train'),
                                            batch_size=16,
                                            shuffle=True,
                                            num_workers=16,
                                            drop_last=False)
    

    model = model_core.Two_Stream_Net()
    model = model.cuda()
    optimizer = optim.Adam(model.parameters(), lr=0.0002, betas=(0.9, 0.999))

    epoch = 0 
    
    while epoch < 10:
        count = 0
        total_loss = 0
        tbar = tqdm(TrainData)

        for batch_idx, (input_img, img_label) in enumerate(tbar):
            count = count + 1

            model.train()
            input_img = input_img.to(device)
            img_label = img_label.to(device)

            _, output_fea, _ = model(input_img)
            optimizer.zero_grad()

            angel = am_softmax.AngleSimpleLinear(2048, 2)
            amloss = am_softmax.AMSoftmaxLoss()
            # print(output_fea.shape)
            img_label = img_label.squeeze()
            # print(img_label.shape)
            loss = amloss(angel(output_fea), img_label)
            loss.backward()
            optimizer.step()
            total_loss = total_loss + loss
            avg_loss = total_loss / count

            desc = 'Training  : Epoch %d, Avg. Loss = %.5f' % (epoch, avg_loss)
            tbar.set_description(desc)
            tbar.update()
        
        model.eval()
        savename = '/home/fzw/face-forgery-detection/checkpoint/checkpoint' + '_' + str(epoch) + '.tar'
        torch.save({'epoch': epoch, 'state_dict': model.state_dict()}, savename)
        epoch = epoch + 1

        
