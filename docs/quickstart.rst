Quickstart
==========

Installation
------------

#. Install dependencies not available in PyPI:

    ::

        dnf install redhat-rpm-config python-devel krb5-devel pulp-admin-client


#. Clone the git repo, and change to the repo directory:

    ::

        git clone https://github.com/release-engineering/releng-sop.git
        cd releng-sop


#. Install the **releng-sop** scripts:

    ::

        pip<version> install ./


Configure environments
----------------------

The scripts will search the following locations for environment configuration
(in the order specified below):

#. ``$XDG_CONFIG_HOME/releng-sop/environments/``
#. ``/etc/releng-sop/environments/``

If ``$XDG_CONFIG_HOME`` is not set or empty, a default equal to ``$HOME/.config``
is used.

The name of the default environment used be the scripts is ``default``.
This can be changed using the optional argument ``--env``.

The scripts will look for ``<environment_name>.json`` in the locations mentioned
above to read environment configuration data.

An example for environment configuration can be found in
``tests/environments/test-env.json``.

.. literalinclude:: ../tests/environments/test-env.json


Setup release data
------------------

The scripts will search the following locations for release data (in the order
specified below):

#. ``$XDG_CONFIG_HOME/releng-sop/releases/``
#. ``/etc/releng-sop/releases/``

If ``$XDG_CONFIG_HOME`` is not set or empty, a default equal to ``$HOME/.config``
is used.

Release data for a release having ``RELEASE_ID=fedora-24``, will be read from
``fedora-24.json`` found in one of the locations mentioned above.

An example for release data can be found in ``tests/releases/test-release.json``.

.. literalinclude:: ../tests/releases/test-release.json
