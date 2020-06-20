import mne
import torch.nn as nn
import unittest

from torch.utils.data import DataLoader
from dn3.trainable.processes import StandardClassification
from tests.dummy_data import create_dummy_dataset, retrieve_underlying_dummy_data, EVENTS


class DummyClassifier(nn.Module):

    def __init__(self, channels, samples, targets):
        super().__init__()
        self.classifier = nn.Linear(channels * samples, targets)

    def forward(self, x):
        return self.classifier(x.view((x.shape[0], -1)))


class TestSimpleClassifier(unittest.TestCase):

    _NUM_EPOCHS = 10
    _BATCH_SIZE = len(EVENTS) // 2
    _NUM_WORKERS = 0

    def setUp(self) -> None:
        mne.set_log_level(False)
        self.dataset = create_dummy_dataset()
        self.classifier = DummyClassifier(len(self.dataset.channels), self.dataset.sequence_length, 4)

    def test_MakeSimpleClassifierTrainable(self):
        trainable = StandardClassification(self.classifier)
        self.assertTrue(True)

    def test_MakeSimpleClassifierTrainableCUDA(self):
        trainable = StandardClassification(self.classifier)
        self.assertTrue(True)

    def test_TrainableFit(self):
        trainable = StandardClassification(self.classifier)
        loader = DataLoader(self.dataset, batch_size=self._BATCH_SIZE, shuffle=True, num_workers=self._NUM_WORKERS,
                            drop_last=True)

        def check_train_mode(metrics):
            with self.subTest("train-mode"):
                self.assertTrue(self.classifier.training)

        def check_eval_mode(metrics):
            with self.subTest("eval-mode"):
                self.assertFalse(self.classifier.training)

        train_log, eval_log = trainable.fit(loader, epochs=self._NUM_EPOCHS, step_callback=check_train_mode,
                                            epoch_callback=check_eval_mode)

        self.assertEqual(len(train_log), self._NUM_EPOCHS * len(self.dataset) // self._BATCH_SIZE)


if __name__ == '__main__':
    unittest.main()

