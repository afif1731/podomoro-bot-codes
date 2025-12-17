from torch import nn
from torchvision import models
import torch.nn.functional as F

class ModelHAR(nn.Module):
    def __init__(self, num_classes, hidden1, dropout_rate):
        super(ModelHAR, self).__init__()

        # Load DenseNet & Freeze
        self.base_model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
        # for param in self.base_model.parameters():
        #     param.requires_grad = False
        
        # for param in self.base_model.features.denseblock4.parameters():
        #     param.requires_grad = True
        # for param in self.base_model.features.norm5.parameters():
        #     param.requires_grad = True

        self.features = self.base_model.features
        self.input_features = self.base_model.classifier.in_features # 1024

        self.classifier = nn.Sequential(
            nn.Flatten(),

            nn.Linear(self.input_features, hidden1),
            nn.BatchNorm1d(hidden1),
            nn.GELU(),
            nn.Dropout(dropout_rate),

            # nn.Linear(hidden1, hidden2),
            # nn.BatchNorm1d(hidden2),
            # nn.GELU(),
            # nn.Dropout(dropout_rate / 3),

            nn.Linear(hidden1, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = F.relu(x, inplace=True)
        x = F.adaptive_avg_pool2d(x, (1, 1))
        output = self.classifier(x)
        return output