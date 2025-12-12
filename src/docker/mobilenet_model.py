from torch import nn
from torchvision import models
import torch.nn.functional as F

class ModelHAR(nn.Module):
    def __init__(self, num_classes, hidden_size=256, num_layers=3, seq_length=10):
        super(ModelHAR, self).__init__()
        
        self.base_model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
        
        self.features = self.base_model.features
        
        self.input_features = self.base_model.classifier.in_features

        self.lstm = nn.LSTM(input_size=self.input_features, 
                            hidden_size=hidden_size, 
                            num_layers=num_layers,
                            batch_first=True)

        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.BatchNorm1d(256), # Tambahkan Batch Norm untuk stabilitas
            nn.ReLU(),
            nn.Dropout(0.5),
            
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        # x shape: [batch, 3, 224, 224]
        if x.dim() == 4:
            x = x.unsqueeze(1)
            
        b, seq, c, h, w = x.size()

        x = x.view(b * seq, c, h, w)
        
        x = self.features(x)
        x = F.relu(x, inplace=True)
        x = F.adaptive_avg_pool2d(x, (1, 1))
        x = x.view(b, seq, -1)

        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]

        output = self.classifier(last_output)  # Output: [batch, num_classes]
        return output