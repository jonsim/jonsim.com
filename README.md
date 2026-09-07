# jonsim.com
Source for [jonsim.com](http://www.jonsim.com).


## One time setup

Install the development tools:

```sh
uv sync
```

Install the git hooks:

```sh
uv run pre-commit install
```


## Deploy

Generate the recipes site and a deployable `site.zip`:

```sh
./deploy.sh <path/to/recipes>
```
