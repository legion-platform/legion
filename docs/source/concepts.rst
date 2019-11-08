============================
Concepts
============================

Phases
--------------------------------

Legion splits the ML/AI model lifecycle into three phases:

1. :term:`Train`
2. :term:`Package`
3. :term:`Deploy`

Applications and tools can further automate each phase by implementing pluggable extensions `as`

1. :term:`Trainer`
2. :term:`Packager` or
3. :term:`Deployer`

Trainers and Packagers can be registered as components of the Legion Platform using:

1. :term:`Trainer Extension`
2. :term:`Packager Extension`

When registered, these components can use Legion :term:`Trainer Metrics` and :term:`Trainer Tags`.

Users are encouraged to integrate third-party :term:`Trainer Extensions<Trainer Extension>` and :term:`Packager Extensions<Packager Extension>`.

Toolchains
-------------------------

Taken together a Trainer, Packager, and Deployer comprise a `Toolchain` that automates an end-to-end machine learning pipeline.

Ready to use
~~~~~~~~~~~~

Legion provides a :term:`Trainer Extension <Trainer Extension>` and a :term:`Packager Extension <Packager Extension>`

1. :term:`MLflow Trainer`
2. :term:`REST API Packager`

These power the default Toolchain.

Model storage
-------------------------

Legion Platform stores models in :term:`Trained Model Binaries <Trained Model Binary>` for different languages.

Presently, Legion Platform supports only:

1. :term:`General Python Prediction Interface`

Users are encouraged to provide additional formats.
