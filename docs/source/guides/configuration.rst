The Configuratron
=========================
*High-level dataset and experiment descriptions*

.. contents:: :local:

Why do I need this?
-------------------
Configuration files are perhaps where the advantages of DN3 are most apparent. Ostensibly, integrating *multiple*
datasets across a common deep learning is as simple as loading files of each dataset from disk to be fed into a common
deep learning training loop. The reality however, is rarely that simple. DN3 uses `YAML <https://yaml.org/>`_ formatted
configuration files to streamline this process, and better organize the integration of *many* datasets.

Different file formats/extensions, sampling frequencies, directory structures make for annoying boilerplate with minor
variations. Here (among other possible uses) a consistent configuration framework helps to automatically handle
the variations across datatsets, for ease of integration down the road. If the dataset follows (or can be made to
follow) the relatively generic directory structure of session instances nested in a single directory for each unique
person, simply provided the top-level of this directory structure, a DN3 :any:`Dataset` can be rapidly constructed, with
easily adjustable *configuration* options.

A Little More Specific
----------------------
Say we were evaluating a neural network architecture with some of our
own data. We are happy with how it is currently working, but want to now evaluate it against a public dataset to
compare with other work. Most of the time, this means writing a decent bit of code to load this new dataset. Instead,
DN3 proposes that if it is in a consistent directory structure, and uses a known (you can also specify your own custom
written file loader) file format, it should be as simple as:

.. code-block:: yaml

   public_dataset:
     toplevel: /path/to/the/files

As far as the real *configuration* aspect, perhaps this dataset has a unique time window for its trials? In that case:

.. code-block:: yaml

   public_dataset:
     toplevel: /path/to/the/files
     tmin: -0.1
     tlen: 1.5

Want to bandpass filter the data between 0.1Hz and 40Hz before use?

.. code-block:: yaml

   public_dataset:
     toplevel: /path/to/the/files
     tmin: -0.1
     tlen: 1.5
     bandpass: [0.1, 40]



Hopefully this illustrates the advantage of organizing datasets in this way.

A Concrete Example
------------------
It take a little more to make this a DN3 configuration, but as simple as adding a special token (DN3) to the yaml file
that houses your configuration. Consider the contents of 'my_config.yml':

.. code-block:: yaml

   DN3:
     datasets:
       - in_house_dataset
       - public_dataset

   in_house_dataset:
     name: "Awesome data"
     tmin: -0.5
     tlen: 1.5
     picks:
       - eeg
       - emg

   public_dataset:
     toplevel: /path/to/the/files
     tmin: -0.1
     tlen: 1.5
     bandpass: [0.1, 40]

   architecture:
     layers: 2
     activation: 'relu'
     dropout: 0.1

Notice that the file begins with an entry called DN3 that has the datasets we are going to use specified in a list.
This allows us to select *which datasets* are to be used for a given time. Say we want to ignore a dataset, we could
comment it out (or we could get much fancier once we start to use the !include directive).

Now, on the python side of things:

.. code-block:: python
   :emphasize-lines: 3,5

   from dn3.data.config import ExperimentConfig

   experiment = ExperimentConfig("my_config.yml")
   for ds_name, ds_config in experiment.datasets():
       dataset = ds_config.auto_construct_dataset()
       # Do some awesome things

The`dataset` variable above is now a DN3 :any:`Dataset`, which now readily supports loading trials for training or separation
according to people and/or sessions.

That's great, but what's up with that 'architecture' entry?
-----------------------------------------------------------
There isn't anything special to this, aside from providing a convenient location to add additional configuration
values that one might need for a set of experiments. These fields will now be populated in the `experiment` variable
above. So now, `experiment.architecture` is a `dict` with fields populated from the yaml file.

Complete listing of dataset configuration fields
------------------------------------------------

toplevel *(required, directory)*
  Specifies the toplevel directory of the dataset.
tlen *(required, float)*
  The length of time to use for each retrieved datapoint. If *epoched* trials (see :any:`EpochTorchRecording`) are
  required, *tmin* must also be specified.
tmin *(float)*
  If specified, epochs the recordings into trials at each event (can be modified by *events* config below) onset with
  respect to *tmin*. So if *tmin* is negative, happens before the event marker, positive is after, and 0 is at the
  onset.
use_annotations *(bool)*
  If specified, parse events from annotations. This is either because the annotations are correct and the stim channel
  must be ignored, or to simply suppress a warning that would otherwise be printed as annotations are the fall-back
  when a stim channel is not found.
events *(list, map/dict)*
  This can be formatted in one of three ways:

  1. Unspecified - all events parsed by `find_events() <https://mne.tools/stable/generated/mne.find_events.html>`_,
     falling-back to `events_from_annotations() <https://mne.tools/stable/generated/mne.events_from_annotations.html>`_
  2. A list of event numbers that filter the set found from the above.
  3. Labels for known events in a standard YAML form, filtering as above, e.g.:

     .. code-block:: yaml

        events:
          left_hand: T1
          right_hand: T2

     The values may be strings to match annotations. If numeric, the assumption is that a stim channel is being used,
     but will fall-back to annotations.

  In all cases, the codes from the stim channel or annotations will not in fact correspond to the subsequent labels
  loaded. This is because the labels don't necessarily fit a minimal spanning set starting with 0. In other words, if
  I had say, 4 labels, they are not guaranteed to be 0, 1, 2 and 3 as is needed for loss functions downstream.

  The latter two configuration options above *do however* provide some control over this, with the order of the listed
  events corresponding to the index of the used label. e.g. *left_hand* and *right_hand* above have class labels
  0 and 1 respectively.

  If the reasoning for the above is not clear, not to worry. Just know you can't assume that annotated event 1 is label
  1. Instead use :meth:`EpochTorchRecording.get_mapping` to resolve labels to the original annotations or event codes.

picks *(list)*
  This option can take two forms:

   - The names of the desired channels
   - Channel types as used by `MNE's pick_types() <https://mne.tools/stable/generated/mne.pick_types.html>`_

decimate *(bool)*
  Only works with epoch data, must be > 0, default 1. Amount to decimate trials.

name *(string)*
  A more human-readable name for the dataset.

extensions *(list)*
  The file extensions to seek out when searching for sessions in the dataset. These should include the '.', as in '.edf'
  . *This can include extensions not handled by auto_construction. A handler must then be provided using*
  :any:`DatasetConfig.add_extension_handler()`

stride *(int)*
  Only for :any:`RawTorchRecording`. The number of samples to slide forward for the next section of raw data. Defaults
  to 1, which means that each sample in the recording (aside from the last :samp:`sample_length - 1`) is used as the
  beginning of a retrieved section.

drop_bad *(bool)*
  Whether to ignore any events annotated as bad. Defaults to `False`

.. What am I doing about the filtering options?

.. data_max *(float)*
  The maximum value taken by any recording in the dataset. Pro

exclude_people *(list)
  List of people (identified by the name of their respective directories) to be ignored.

exclude_sessions *(list)
  List of sessions (files) to be ignored when performing automatic constructions.