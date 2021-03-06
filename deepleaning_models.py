
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T


class NetTranslation(nn.Module):
    '''NetTranslation is a image translation based model
       There is no max pooling layer. Adding some padding. So he dimension remains the same, i.e. (100, 100)
       The number of channels first increase to 32, then decrease to 1
       Assuming the input image is 1 x 100 x 100
    '''
    def __init__(self):
        super(NetTranslation, self).__init__()
        self.conv1 = nn.Conv2d(1, 8, 5, padding=2)
        self.conv2 = nn.Conv2d(8, 32, 5, padding=2)
        self.conv3 = nn.Conv2d(32, 1, 5, padding=2)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = self.conv3(x)
        return x


class NetTranslation2(nn.Module):
    '''Image translation. comparing to NetTranslation, this model is composed of TWO CNNs
       the first CNN is the same as NetTranslation, the second one uses the output of the first CNN and output the # of TX
       this # of TX will help the peak finding and hope reduce the localization error and cardinality error.
       Assuming the input image is 1 x 100 x 100
    '''
    def __init__(self):
        super(NetTranslation2, self).__init__()
        self.conv11 = nn.Conv2d(1, 8, 5, padding=2)
        self.conv12 = nn.Conv2d(8, 32, 5, padding=2)
        self.conv13 = nn.Conv2d(32, 1, 5, padding=2)
        self.conv21 = nn.Conv2d(1, 2, 5)
        self.conv22 = nn.Conv2d(2, 4, 5)
        self.conv23 = nn.Conv2d(4, 8, 5)
        self.groupnorm1 = nn.GroupNorm(1, 2)
        self.groupnorm2 = nn.GroupNorm(2, 4)
        self.groupnorm3 = nn.GroupNorm(4, 8)
        self.fc1 = nn.Linear(648, 32)
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x):
        # first CNN input is 1 x 100 x 100
        x = F.relu(self.conv11(x))
        x = F.relu(self.conv12(x))
        y1 = self.conv13(x)
        # second CNN takes in y1, which is also 1 x 100 x 100
        x = F.max_pool2d(F.relu(self.groupnorm1(self.conv21(y1))), 2)
        x = F.max_pool2d(F.relu(self.groupnorm2(self.conv22(x))), 2)
        x = F.max_pool2d(F.relu(self.groupnorm3(self.conv23(x))), 2)
        x = x.view(-1, self.num_flat_features(x))
        x = F.relu(self.fc1(x))
        y2 = self.fc2(x)
        return y1, y2

    def num_flat_features(self, x):
        size = x.size()[1:]
        num_features = 1
        for s in size:
            num_features *= s
        return num_features


class NetRegression1(nn.Module):
    '''NetRegression1 is designed for regression
       the output of the fully connected layer is (2,) array
       assume the input matrix is 1 x 100 x 100
    '''
    def __init__(self):
        super(NetRegression1, self).__init__()
        self.conv1 = nn.Conv2d(1, 8, 5)
        self.conv2 = nn.Conv2d(8, 16, 5)
        self.conv3 = nn.Conv2d(16, 32, 5)
        self.groupnorm1 = nn.GroupNorm(1, 8)
        self.groupnorm2 = nn.GroupNorm(1, 16)
        self.groupnorm3 = nn.GroupNorm(1, 32)
        self.fc1   = nn.Linear(2592, 100)
        self.fc2   = nn.Linear(100, 2)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.groupnorm1(self.conv1(x))), 2)
        x = F.max_pool2d(F.relu(self.groupnorm2(self.conv2(x))), 2)
        x = F.max_pool2d(F.relu(self.groupnorm3(self.conv3(x))), 2)
        x = x.view(-1, self.num_flat_features(x))
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

    def num_flat_features(self, x):
        size = x.size()[1:]
        num_features = 1
        for s in size:
            num_features *= s
        return num_features


class NetRegreesion2(nn.Module):
    '''CNN regression for 2 TX, the output of the fully connected layer is a (4,) array
       assume the input matrix is 1 x 100 x 100
    '''
    def __init__(self):
        super(NetRegreesion2, self).__init__()
        self.conv1 = nn.Conv2d(1, 8, 5)
        self.conv2 = nn.Conv2d(8, 16, 5)
        self.conv3 = nn.Conv2d(16, 32, 5)
        self.groupnorm1 = nn.GroupNorm(1, 8)
        self.groupnorm2 = nn.GroupNorm(1, 16)
        self.groupnorm3 = nn.GroupNorm(1, 32)
        self.fc1   = nn.Linear(2592, 100)
        self.fc2   = nn.Linear(100, 4)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.groupnorm1(self.conv1(x))), 2)
        x = F.max_pool2d(F.relu(self.groupnorm2(self.conv2(x))), 2)
        x = F.max_pool2d(F.relu(self.groupnorm3(self.conv3(x))), 2)
        x = x.view(-1, self.num_flat_features(x))
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

    def num_flat_features(self, x):
        size = x.size()[1:]
        num_features = 1
        for s in size:
            num_features *= s
        return num_features
