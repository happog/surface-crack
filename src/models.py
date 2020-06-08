import torch
import torchvision
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import pytorch_lightning as pl

import matplotlib.pyplot as plt
from omegaconf import DictConfig
from sklearn.metrics import f1_score
from scikitplot.metrics import plot_confusion_matrix

from src.utils import get_datasets, get_model


class SurfaceCrackDetectionModel(pl.LightningModule):
    def __init__(self, hparams: DictConfig = None):
        super().__init__()
        self.hparams = hparams
        self.model = get_model(num_classes=2)
        self.loss_fn = nn.functional.cross_entropy

    def forward(self, x):
        x = self.model(x)
        return x

    def prepare_data(self):
        self.train_ds, self.val_ds, self.test_ds = get_datasets(self.hparams['dataset'])

    def configure_optimizers(self):
        optimizer = optim.SGD(self.model.parameters(), **self.hparams['optimizer'])
        scheduler = lr_scheduler.StepLR(optimizer, **self.hparams['scheduler'])
        return [optimizer], [scheduler]

    @pl.data_loader
    def train_dataloader(self):
        return torch.utils.data.DataLoader(self.train_ds, batch_size=self.hparams['batch_size'])

    @pl.data_loader
    def val_dataloader(self):
        return torch.utils.data.DataLoader(self.val_ds, batch_size=self.hparams['batch_size'])

    @pl.data_loader
    def test_dataloader(self):
        return torch.utils.data.DataLoader(self.test_ds, batch_size=self.hparams['batch_size'])

    def training_step(self, train_batch, batch_idx):
        x, y = train_batch
        y_hat = self.forward(x)
        
        # Training loss
        train_loss = self.loss_fn(y_hat, y)
         
         # Training accuracy
        labels_hat = torch.argmax(y_hat, dim=1)
        train_acc = torch.tensor(torch.sum(y == labels_hat).item() / (len(y) * 1.0))

        tensorboard_logs = {'train_loss': train_loss}
        return {'loss': train_loss, 'acc': train_acc, 'log': tensorboard_logs}

    def training_epoch_end(self, outputs):
        train_epoch_acc = torch.stack([x['acc'] for x in outputs]).mean()
        train_epoch_loss = torch.stack([x['loss'] for x in outputs]).mean()

        # tensorboard_logs = { 'epoch_loss': {'train': train_epoch_loss } }
        tensorboard_logs = { 'train_epoch_loss': train_epoch_loss, 'train_epoch_acc': train_epoch_acc }
        return {'loss': train_epoch_loss, 'log': tensorboard_logs}

    def validation_step(self, val_batch, batch_idx):
        x, y = val_batch
        y_hat = self.forward(x)

        # Validation loss
        val_loss = self.loss_fn(y_hat, y)

        # Validation accuracy
        labels_hat = torch.argmax(y_hat, dim=1)
        val_acc = torch.tensor(torch.sum(y == labels_hat).item() / (len(y) * 1.0))

        # tensorboard_logs = {'val_loss': val_loss, 'val_acc': val_acc}
        return {'val_loss': val_loss, 'val_acc': val_acc}

    def validation_epoch_end(self, outputs):
        val_epoch_acc = torch.stack([x['val_acc'] for x in outputs]).mean()
        val_epoch_loss = torch.stack([x['val_loss'] for x in outputs]).mean()
        
        # tensorboard_logs = { 'epoch_loss': {'val': val_epoch_loss } }
        tensorboard_logs = { 'val_epoch_loss': val_epoch_loss, 'val_epoch_acc': val_epoch_acc }
        return {'val_loss': val_epoch_loss, 'log': tensorboard_logs}

    def test_step(self, test_batch, batch_idx):
        x, y = test_batch
        y_hat = self.forward(x)
        test_loss = self.loss_fn(y_hat, y)
        return {'test_loss': test_loss}
    
    def test_epoch_end(self, outputs):
        test_epoch_loss = torch.stack([x['test_loss'] for x in outputs]).mean()
        return {'test_epoch_loss': test_epoch_loss}
