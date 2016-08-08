Koji
====

koji-block-package-in-release
-----------------------------

.. argparse::
   :module: releng_sop.koji_block_package_in_release
   :func: get_parser
   :prog: koji-block-package-in-release


Manual Steps
~~~~~~~~~~~~
Requirements:

* **koji** package
* package with a koji profile (if needed)

Inputs:

* **profile** - koji instance in which the change will be made
* **tag** - release (a.k.a. main) koji tag name for a release
* **package** - name of package to be blocked in a release

Steps:

#. ``koji --profile=<profile> block-pkg <tag> <package> [package] ...``
