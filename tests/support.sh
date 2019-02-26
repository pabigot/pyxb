#! /bin/sh

# POSIX shell infrastructure included by various test scripts to
# remove redundancy and simplify the scripts.
#
# REMOVE_ON_EXIT: A list of files that will be removed when the
# including script exits.
#

# Untested failures are test failures
set -e

# Improve comparability by using the same encoding as the developer's
# console environment when redirecting to a file.
export PYTHONIOENCODING='utf-8'

# Capture the directory from which the test script was run.
TEST_DIR=$(cd $(dirname ${0}); pwd)
echo "TEST: ${TEST_DIR}"

# Don't throw away temp file names if somebody includes this multiple
# times.
${REMOVE_ON_EXIT:=}

# Create a temporary file into which output can be directed for
# comparison with expected results.  The file name is placed in
# variable tmpout and is also cached for removal when the script
# exits.  If you need multiple temporary outputs you may invoke this
# multiple times.
#
# Usage: name=$(make_tmpout [base])
make_tmpout () {
    tmpout=$(mktemp -t ${1:-test}_XXXXXXXXXX)
    REMOVE_ON_EXIT="${REMOVE_ON_EXIT} ${tmpout}"
    echo ${tmpout}
}

# Remove remaining temporary files
cleanup () {
    rm -f ${REMOVE_ON_EXIT}
}
trap cleanup EXIT

# Indicate a test failure, with arguments displayed as a message,
# and exit with an error.  If tmpout specifies a non-empty file
# its contents will be copied
fail () {
    echo 1>&2 "TEST: FAIL: ${TEST_DIR}${@:+: $@}"
    exit 1
}

# Indicate the test passed, with arguments displayed as a message,
# and continue to execute.
passed () {
    echo 1>&2 "TEST: PASS: ${TEST_DIR}${@:+: $@}"
}

# Local Variables:
# mode:sh
# indent-tabs-mode:nil
# End:
