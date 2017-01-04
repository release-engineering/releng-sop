Contribution guide
==================

Tests are executed with tox, so the only thing you need to have locally is
having tox installed:
::

    $ pip install tox

or

::

    $ dnf install python-tox

or

::

    $ dnf install python3-tox


Dependencies
------------

Dependencies for *tests*, *docs* and *flake8* are handled by *tox*, and are
configured in ``tox.ini``.

Installation dependencies for scripts should be handled by ``setup.py``.

Dependencies for *tests* are duplicated in ``tox.ini`` and ``setup.py``
``tests_require`` section. This is done to support both ``setup.py test``
and running the tests within tox, using pytest.

When generating *documentation* external dependencies are mocked in
``docs/conf.py``, in order to avoid breaking *readthedocs.org*
due to missing environment dependencies.

Once you have tox, you can run the tests like

::

    $ tox

This will run tests in all environments defined in ``tox.ini``.
If you want to skip missing python interpreters you might want to use the
``--skip-missing-interpreters`` option.

For syntax checks you can use:
::

    $ tox -e flake8

For generating documentation:
::

    $ tox -e docs

tox will cache the environments in order to speed up test execution.
Sometimes this can cause issues (when dependencies are changed or added).
These can be overcome by recreating the tox environments using the ``-r`` flag.
::

    $ tox -r


Pre-commit hook
---------------

It is recommended to set up the pre-commit hook found at
``hooks/pre-commit.sh`` (for instructions see comments in the script).

This will call ``tox --skip-missing-interpreters`` before a commit, and makes
sure tests, flake8 checks and docs are ok.


Commit message hook
-------------------

It is recommended to set up the commit-msg hook found at
``hooks/commit-msg.sh`` (for instructions see comments in the script).

This will check some of the formal requirements for commit messages.
(See `The seven rules of a great commit message <http://chris.beams.io/posts/
git-commit/>`_.)
