#!/bin/sh
# Run a command with CKAN's connection settings pointed at the test services.
#
# CKAN applies CKAN_SQLALCHEMY_URL, CKAN_SOLR_URL and CKAN_REDIS_URL over every
# ini file (CONFIG_FROM_ENV_VARS in ckan/config/environment.py). The ckan-dev
# container sets them to the development services, so test.ini alone cannot keep
# test fixtures away from development data. This script replaces them with the
# TEST_* values and refuses to run if any test value is missing or equals the
# development value.
#
# Usage, inside the ckan-dev container from the repository root:
#   sh docker/ckan/test-env.sh pytest --ckan-ini=test.ini -v ckanext/auscope_core
set -eu

if [ "$#" -eq 0 ]; then
    echo "usage: sh docker/ckan/test-env.sh <command> [args...]" >&2
    exit 2
fi

use_test_value() {
    # $1 is one of the fixed names below, never user input.
    eval "test_value=\${TEST_$1:-}"
    eval "dev_value=\${$1:-}"
    if [ -z "$test_value" ]; then
        echo "test-env: TEST_$1 is not set; see .env.example" >&2
        exit 1
    fi
    if [ "$test_value" = "$dev_value" ]; then
        echo "test-env: TEST_$1 equals $1; refusing to use development data" >&2
        exit 1
    fi
    export "$1=$test_value"
}

use_test_value CKAN_SQLALCHEMY_URL
use_test_value CKAN_SOLR_URL
use_test_value CKAN_REDIS_URL

exec "$@"
