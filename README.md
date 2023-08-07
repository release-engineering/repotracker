# repotracker
A microservice for tracking container repositories, and publishing a message when they change.

## Build Status

[codecov]: https://codecov.io/gh/release-engineering/repotracker
[codecovbadge]: https://codecov.io/gh/release-engineering/repotracker/branch/master/graph/badge.svg

| Branch | Coverage                                                  |
|--------|-----------------------------------------------------------|
| master | [![Code Coverage - master branch][codecovbadge]][codecov] |         

## Running the Tests
    # Run unit tests and linters
    $ tox
    # Run black formatter
    $ tox -e black
