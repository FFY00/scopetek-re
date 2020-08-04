# scopetek-re

ScopeTek microscope cameras reverse engineering.

| Device                  | Trigger output     | Decode output | Configure output |
| ----------------------- |:------------------:|:-------------:|:----------------:|
| DCM310 (AmScope MD800E) | :heavy_check_mark: | :x:           | :x:              |


### Development

We use [mypy](http://mypy-lang.org/) to run static checks in scripts, and
[pre-commit](https://pre-commit.com/) to run misc checks. Install the pre-commit
hook with `pre-commit install`.
