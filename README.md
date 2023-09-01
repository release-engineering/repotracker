# repotracker
A microservice for tracking container repositories, and publishing a message when they change.

## Build Status

[travis]: https://travis-ci.org/#!/release-engineering/repotracker
[travisbadge]: https://secure.travis-ci.org/release-engineering/repotracker.png?branch=master
[codecov]: https://codecov.io/gh/release-engineering/repotracker
[codecovbadge]: https://codecov.io/gh/release-engineering/repotracker/branch/master/graph/badge.svg

Branch | Status | Coverage
-------|--------|---------
master | [![Build Status - master branch][travisbadge]][travis] | [![Code Coverage - master branch][codecovbadge]][codecov]

## Running the Tests

    $ python3 setup.py test
    # also check flake8 before committing
    $ python3 setup.py flake8 test
