#!/bin/bash

#
# To enable this hook, do from your repo root:
#       pushd .git/hooks
#       ln -s -f ../../hooks/pre-commit.sh pre-commit
#       popd
#

TOX="tox"
# Don't care about missing interpreters,
# those will be checked by travis anyways.
TOXOPT="--skip-missing-interpreters"

MSG="Please install $TOX to check your work before commiting. Aborting."

# First let's check that tox is available...
command -v $TOX >/dev/null 2>&1 || { echo >&2 $MSG; exit 1; }

$TOX $TOXOPT
