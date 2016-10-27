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

MSG_INSTALL_TOX="Please install $TOX to check your work before commiting. Aborting."

# First let's check that tox is available...
command -v $TOX >/dev/null 2>&1 || { echo >&2 $MSG_INSTALL_TOX; exit 1; }

# stash unstaged stuff first
MSG_STASH_FAILED="Stashing unstaged commits failed for some reason. Aborting."
GIT_STASH_SAVE="git stash --include-untracked --keep-index"

$GIT_STASH_SAVE >/dev/null 2>&1 || { echo >&2 $MSG_STASH_FAILED; exit 1; }

# now run tox
$TOX $TOXOPT
RESULT=$?

# and pop the stash
MSG_STASH_POP_FAILED="Poping stashed stuff failed. Aborting."
GIT_STASH_POP="git stash pop"

$GIT_STASH_POP >/dev/null 2>&1 || { echo >&2 $MSG_STASH_POP_FAILED; exit 1; }

exit $RESULT
