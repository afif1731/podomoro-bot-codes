from torch import nn
from torchvision import models

class MobileNetHAR(nn.Module):
    def __init__(self, num_classes):
        super(MobileNetHAR, self).__init__()
        self.base_model = models.mobilenet_v3_large(weights=None)
        
        self.features = self.base_model.features
        self.avgpool = self.base_model.avgpool
        
        input_features = 960 
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_features, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.5),
            
            nn.Linear(1024, 256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = self.classifier(x)
        return x