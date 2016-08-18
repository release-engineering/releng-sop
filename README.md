[![Build Status](https://travis-ci.org/release-engineering/releng-sop.svg?branch=master)](https://travis-ci.org/release-engineering/releng-sop)
[![Documentation Status](https://readthedocs.org/projects/releng-sop/badge/?version=latest)](http://releng-sop.readthedocs.io/en/latest/?badge=latest)

Goal
----
Implement Release Engineering SOPs (Standard Operation Procedures)
as simple scripts that take minimal input and perform implemented
operations consistently across all product releases.


In Scope
--------
* Features
  * Provide minimal user input, read remaining data from a data store
  * Support running scripts in multiple environments
  * Support for SCLs (Software Collections)

* Implementation

  * Python 2.6+ and 3.4+ with minimal external deps
  * Library implementing business logic
  * Thin CLI wrappers
  * Logging rather than printing to stdout/stderr
  * PyXDG to work with user dirs

* Documentation

  * Docs generated from source code
  * Use Sphinx to generate docs
  * Always document manual steps needed to perform each action

* Tests

  * Unit tests
  * Sanity tests checking data in JSON files and PDC


Out Of Scope
------------
* WebUI / Webservice
* Workflows
* Messagebus support
* Central logging


Phase 1 - Prototype
-------------------
* Use PDC release IDs.
* Identify data and store it in JSON files named by the PDC release IDs.
* Focus primarily on RPMs.


Phase 2 - PDC Integration
-------------------------
* Move data from JSON files to PDC database.
* Keep the JSON backend around for debugging, testing etc.


Ideas (To Be Implemeted Later)
------------------------------
* Support for content types other than RPM.


Links
-----
* https://github.com/product-definition-center/product-definition-center
* https://pdc.fedoraproject.org/
* https://docs.pagure.org/releng/sop.html
* https://pagure.io/releng
