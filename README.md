# repotracker
A microservice for tracking container repositories, and publishing a message when they change.

## Build Status

[travis]: http://travis-ci.org/#!/release-engineering/repotracker
[travisbadge]: https://secure.travis-ci.org/release-engineering/repotracker.png?branch=master
[codecov]: https://codecov.io/gh/release-engineering/repotracker
[codecovbadge]: https://codecov.io/gh/release-engineering/repotracker/branch/master/graph/badge.svg

<table>
  <th>
    <td>Branch</td>
    <td>Status</td>
    <td>Coverage</td>
  </th>
  <tr>
    <td>master</td>
    <td>[![Build Status - master branch][travisbadge]][travis]</td>
    <td>[![Code Coverage - master branch][codecovbadge]][codecov]</td>
  </tr>
</table>

## Running the Tests

    $ python3 setup.py test
    # also check flake8 before committing
    $ python3 setup.py flake8
