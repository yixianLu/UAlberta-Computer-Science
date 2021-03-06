# -*- coding: utf-8 -*-
"""Assignment_3_notebook.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EB5XNWq1JKY6iyO2KdHsr-Ysz0ctbLI5

**Import** *and* setup some auxiliary functions
"""

# Don't edit this cell
import os
import timeit
import time
import numpy as np
from collections import OrderedDict
from pprint import pformat
from tqdm import tqdm
from google.colab import drive

import torch
import torch.nn as nn
import torch.nn.init as init
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
from torch.utils.data.sampler import *
from torchvision import transforms, datasets

torch.multiprocessing.set_sharing_strategy('file_system')
cudnn.benchmark = True

class Net(nn.Module):
  """
  CNN Net Class
  # 6 Convulation layers   
  # 5 Fully connected Layers
  # Batch Normalization done for Convulation layers 2 and 3
  # Xavier Initialization Used
  # Max Pooling with stride 2 used
  # Dropout Used

  Params : nn.Module
  
  """
  def __init__(self):
    """
    Constructor Class
    Definition of the CNN Net we are using and all the layers
    All convolution layers weights are Xavier Initialized

    Parameters : None

    Return : None
    """
    super(Net, self).__init__()  

    #CL 1 
    self.conv1 = nn.Conv2d(in_channels=3, out_channels=8, kernel_size=3, stride=1, padding=1)
    torch.nn.init.xavier_uniform_(self.conv1.weight)

    # CL 2
    self.conv2 = nn.Conv2d(in_channels=8, out_channels=16, kernel_size=3, stride=1, padding=1)
    torch.nn.init.xavier_uniform_(self.conv2.weight)
    self.conv2_bn = nn.BatchNorm2d(16)

    # CL 3
    self.conv3 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, stride=1, padding=1)
    torch.nn.init.xavier_uniform_(self.conv3.weight)
    self.conv3_bn = nn.BatchNorm2d(32)

    # CL 4
    self.conv4 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1)
    torch.nn.init.xavier_uniform_(self.conv4.weight)
    self.conv4_bn = nn.BatchNorm2d(64)

    # CL 5
    self.conv5 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1)
    torch.nn.init.xavier_uniform_(self.conv5.weight)
    self.conv5_bn = nn.BatchNorm2d(128)

    # CL 6
    self.conv6 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=1, padding=1)
    torch.nn.init.xavier_uniform_(self.conv6.weight)
    self.conv6_bn = nn.BatchNorm2d(256)

    # Droput and Pooling Layer
    self.Dropout = nn.Dropout(0.2)
    self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

    # Fully connected Layers

    # FC1
    self.fc1 = nn.Linear(in_features = 256 * 8 * 8, out_features=1024)
    torch.nn.init.xavier_uniform_(self.fc1.weight)

    # FC2
    self.fc2 = nn.Linear(in_features= 1024, out_features = 512)
    torch.nn.init.xavier_uniform_(self.fc2.weight)

    #FC3
    self.fc3 = nn.Linear(in_features= 512, out_features = 256)
    torch.nn.init.xavier_uniform_(self.fc3.weight)

    #FC4
    self.fc4 = nn.Linear(in_features= 256, out_features = 128)
    torch.nn.init.xavier_uniform_(self.fc4.weight)

    #FC5
    self.fc5 = nn.Linear(in_features = 128, out_features = 10)
    torch.nn.init.xavier_uniform_(self.fc5.weight)

    # Skip Connection Layer
    self.skip = nn.Identity()


  def forward(self, x):
    """
    Forward function
    Passes the layers to the activation functions
    Pooling is done 
    Skip connection for conv 2
    Dropout is used 
    Last layer doesn't use an activation function 

    Parameters : x

    Return : x
    """
    # CONV 1 - RELU - POOL - DROPOUT(0.2)
    x = self.pool(F.relu(self.conv1(x))) 
    x = self.Dropout(x)

    # CONV 2 - RELU - SKIP
    x = F.relu(self.conv2(x))
    x = x + self.skip(x)

    # CONV 3 - RELU - POOL
    x = self.pool(F.relu(self.conv3(x)))

    # CONV 4 - RELU - DROPOUT
    x = F.relu(self.conv4(x)) 
    x = self.Dropout(x)

    # CONV 5 - RELU
    x = F.relu(self.conv5(x))

    # CONV 6 - RELU 
    x = F.relu(self.conv6(x))

    # Reshape 
    x = x.view(-1, 256 * 8 * 8) 

    # FC 1 - RELU
    x = F.relu(self.fc1(x))

    # FC 2 - RELU - DROPOUT(0.2)
    x = F.relu(self.fc2(x))
    x = self.Dropout(x)

    # FC 3 - RELU
    x = F.relu(self.fc3(x))

    # FC 4 - RELU
    x = F.relu(self.fc4(x))

    # FC 5
    x = self.fc5(x)
    
    return x

def load_data(config):
    """
    Load cifar-10 dataset using torchvision, take the last 5k of the training data to be validation data 
    torch.utils.data.Subset was used to get the particular subset ie : 
    Accepts a generator hence why the range(0,number, 1) was used 
        1 - 45000 images for the training set
        2 - The last 5000 images for the validation set
    After that the torch.utils.data.DataLoader was used to load the datasets 
    The batch size that was defined above was used and shuffle = True as each time the dataset is reshuffled at every epoch

    Parameters: config

    Returns : train_dataloader, valid_dataloader, test_dataloader
    """
    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    # Get the datasets 
    CIFAR10_training = datasets.CIFAR10("/CIFAR10_dataset/",train=True, download=True, transform = transform_train)
    CIFAR10_test = datasets.CIFAR10("/CIFAR10_dataset/",train=False, download=True, transform = transform_test)

    # Get the various subsets in the dataset
    CIFAR10_training_dataset = torch.utils.data.Subset(CIFAR10_training,range(0, 45000, 1))
    CIFAR10_validation_dataset = torch.utils.data.Subset(CIFAR10_training,range(45000, 50000, 1))

    # Define the dataloaders that are going to be used for the model
    # num_workers set to 0 as the main process should load the dataloaders compared to many subprocess which could increase time but is more efficient
    # Batch_size for the test dataloader was set to 1 as mentioned by the assignment
    train_dataloader  = torch.utils.data.DataLoader(CIFAR10_training_dataset, batch_size=config["batch_size"], shuffle=True, num_workers=0)
    valid_dataloader  = torch.utils.data.DataLoader(CIFAR10_validation_dataset, batch_size=config["batch_size"], shuffle=True, num_workers=0)
    test_dataloader = torch.utils.data.DataLoader(CIFAR10_test, batch_size=1, shuffle=True, num_workers=0)
   
    return train_dataloader, valid_dataloader, test_dataloader

def train(trainloader, validloader, device, config):
    """
    This function trains and validates the model on the dataset
    Learning Rate Annealing was used

    Paramaters: trainloader, validloader, device, config

    Returns: model
    """
    # Initialize the variables
    log_interval = 100
    correct = 0
    validation_loss = 0

    # Define the Model
    model = Net().to(device)

    # Define the cross entropy loss function
    criterion = nn.CrossEntropyLoss()

    # Train the model
    for epoch in range(config['num_epochs']):   
      if epoch <= 10:
          # Define the optimizer and using Adam set the parameters
          optimizer = torch.optim.Adam(model.parameters(), lr=config['lr'], weight_decay=config['regular_constant'])
      elif epoch > 10 and epoch < 50:
          # Define the optimizer and using Adam do Learning Rate Annealing 
          optimizer = torch.optim.Adam(model.parameters(), lr=config['lr']/10, weight_decay=config['regular_constant']) 
      else:
          # Define the optimizer and using Adam do Learning Rate Annealing 
          optimizer = torch.optim.Adam(model.parameters(), lr=config['lr']/50, weight_decay=config['regular_constant']) 
      model.train()
      for batch_index, (images, labels) in enumerate(trainloader): 

          # convert from cpu to gpu
          images = images.to(device) 
          labels = labels.to(device)

          # Clear out the gradients in every call 
          # Else pytorch accumulates it every subsequent call 
          # If we dont use .zero_grad() we wont converge to the required minima
          optimizer.zero_grad()

          # find the output prediction 
          output = model(images)

          # Cross Entropy loss is calculated
          # Regularization is already added in our optimizer 
          # Weight Decay = L2 Regularization
          loss = criterion(output, labels) 
          
          # Back Progragation
          loss.backward()

          # Gradient Descent
          optimizer.step()

          # For each log interval print out the Training details ie : Epoch, Loss 
          # .format formats the output in the specific way we want it to be and 0.6f means 6 values after the decimal
          if (batch_index % log_interval) == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
            epoch, batch_index * len(images), len(trainloader.dataset),
            100. * batch_index / len(trainloader), loss.item()))
        
      # validation 

      # Set all the operations to have no gradient
      with torch.no_grad():
        validation_loss = 0
        correct = 0
        for images, labels in validloader:

          # Convert from cpu to gpu
          images = images.to(device)
          labels = labels.to(device)

          # Find the output prediction 
          output = model(images)

          # get the max element from the predictions 
          index, predictions = torch.max(output.data, 1)

          # Find the loss
          validation_loss += F.nll_loss(output, labels, size_average=False).item()

          # Find the validation loss hence 
          # Find the total number of correct predictions
          correct += (predictions == labels).sum().item()      

        # Find the mean validation accuracy loss
        validation_loss /= len(validloader.dataset)
        print('\nValidation set: Avg. loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        validation_loss, correct, len(validloader.dataset),
        100. * correct / len(validloader.dataset)))
                  
    return model

def save_model_colab_for_submission(model):  # if you are running on colab
  drive.mount('/content/gdrive/', force_remount=True)
  torch.save(model.to(torch.device("cpu")), '/content/gdrive/My Drive/model.pt') # you will find the model in your home drive
  
def save_model_local_for_submission(model):  # if you are running on your local machine
  torch.save(model.to(torch.device("cpu")), 'model.pt')

def test(net, testloader, device):
  """
  This function tests the CNN on the testdataset
  Passes the testdataset to the CNN model 

  Parameters: net, testloader, device

  Returns: accuracy,correct1,total1

  """
  
  # Initialize the variables
  correct = 0
  total = 0

  # net.eval() switches the net to work in eval mode instead of training mode.
  net.eval()

  # torch.no_grad() speeds up computation and deactivates it with the autograd engine
  # common practise of using both together to speed up 
  # Reference : https://discuss.pytorch.org/t/model-eval-vs-with-torch-no-grad/19615
  with torch.no_grad():

      # enumerate the test_dataset
      for images, labels in testloader:

          # convert from cpu to gpu
          images = images.to(device)
          labels = labels.to(device)

          # pass the images to the net and get the output predictions
          outputs = net(images)

          # Get the max element from the predictions
          # Get the total number of correct predictions
          # Get the total number of images in the testdataset
          indices, pred = torch.max(outputs.data, 1)  
          correct += (pred == labels).sum().item()
          total += labels.size(0)

  # Find the accuracy of the net 
  accuracy = 100. * correct / total

  return accuracy, correct, total

def run():
  # set parameters cifar10
  config = {
        'lr': 1e-3,
        'num_epochs': 10,
        'batch_size': 64,
        'num_classes': 10,
        'momentum':0.5,
        'regular_constant': 5e-4,
       }
    
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  
  train_dataloader, valid_dataloader, test_dataloader = load_data(config)
  
  model = train(train_dataloader, valid_dataloader, device, config)
  
  # Testing and saving for submission
  device = torch.device("cpu")

  assert os.path.isdir('checkpoint'), 'Error: no checkpoint directory found!'
  checkpoint = torch.load('./checkpoint/ckpt.pth')
  model.load_state_dict(checkpoint)
  model.eval()
  
  start_time = timeit.default_timer()
  test_acc, test_correct, test_total = test(model.to(device), test_dataloader, device)
  end_time = timeit.default_timer()
  test_time = (end_time - start_time)
  
  save_model_colab_for_submission(model)

  return test_acc, test_correct, test_time

"""Main loop. Run time and total score will be shown below."""

# Don't edit this cell
def compute_score(acc, min_thres=65, max_thres=8):
  # Your Score thresholds
  if acc <= min_thres:
      base_score = 0.0
  elif acc >= max_thres:
      base_score = 100.0
  else:
      base_score = float(acc - min_thres) / (max_thres - min_thres) * 100
  return base_score

def main():
    
    accuracy, correct, run_time = run()
    
    score = compute_score(accuracy)
    
    result = OrderedDict(correct=correct,
                         accuracy=accuracy,
                         run_time=run_time,
                         score=score)
  
    with open('result.txt', 'w') as f:
        f.writelines(pformat(result, indent=4))
    print("\nResult:\n", pformat(result, indent=4))


main()