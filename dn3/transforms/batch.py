import torch
import numpy as np


class BatchTransform(object):
    """
    Batch transforms are operations that are performed on trial tensors after being accumulated into batches via the
    :meth:`__call__` method. Ideally this is implemented with pytorch operations for ease of execution graph
    integration.
    """
    def __init__(self, only_trial_data=True):
        self.only_trial_data = only_trial_data

    def __str__(self):
        return self.__class__.__name__

    def __call__(self, *x, training=False):
        """
        Modifies a batch of tensors.

        Parameters
        ----------
        x : torch.Tensor, tuple
            A batch of trial instance tensor. If initialized with `only_trial_data=False`, then this includes batches
            of all other loaded tensors as well.
        training: bool
                  Indicates whether this is a training batch or otherwise, allowing for alternate behaviour during
                  evaluation.

        Returns
        -------
        x : torch.Tensor, tuple
            The modified trial tensor batch, or tensors if not `only_trial_data`
        """
        raise NotImplementedError()


class RandomTemporalCrop(BatchTransform):

    def __init__(self, max_crop_frac=0.25, crop_weights=None, temporal_axis=1):
        """
        Crops the time dimension of an entire batch.

        Parameters
        ----------
        max_crop_frac: float
                       If this is specified (and `crop_weights` is not), a crop location is selected uniformly from the
                        last `max_crop_frac` indices.
        crop_weights: list, array-like
                      If specified, this should be a list of un-normalized weights used to weight the selection of the
                      last `len(crop_weights)` indicies to crop to.
        """
        super(RandomTemporalCrop, self).__init__(only_trial_data=True)
        self.max_crop_frac = max_crop_frac
        self.crop_weights = np.array(crop_weights)
        self.temporal_axis = temporal_axis

    def __call__(self, x, training=False):
        if not training:
            return x
        if self.crop_weights is None:
            assert 0 <= self.max_crop_frac <= 1
            self.crop_weights = np.ones(int(x.shape[self.temporal_axis] * self.max_crop_frac))

        no_crop_len = x.shape[self.temporal_axis] - len(self.crop_weights)
        assert no_crop_len >= 0
        inds = np.arange(no_crop_len, x.shape[self.temporal_axis])
        crop_location = np.random.choice(inds, p=self.crop_weights / self.crop_weights.sum())
        return x[:, :crop_location, ...]
