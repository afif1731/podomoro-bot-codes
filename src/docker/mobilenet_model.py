from torch import nn
from torchvision import models
import torch.nn.functional as F

class ModelHAR(nn.Module):
    def __init__(self, num_classes, hidden1, hidden2, dropout_rate):
        super(ModelHAR, self).__init__()
        
        self.base_model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
        for param in self.base_model.parameters():
            param.requires_grad = False
            
        self.features = self.base_model.features
        self.input_features = self.base_model.classifier.in_features # 1024

        self.classifier = nn.Sequential(
            nn.Flatten(),
            
            nn.Linear(self.input_features, hidden1),
            nn.BatchNorm1d(hidden1),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            
            nn.Linear(hidden1, hidden2),
            nn.BatchNorm1d(hidden2),
            nn.GELU(),
            nn.Dropout(dropout_rate / 2),
            
            nn.Linear(hidden2, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = F.relu(x, inplace=True)
        x = F.adaptive_avg_pool2d(x, (1, 1))
        output = self.classifier(x)
        return output