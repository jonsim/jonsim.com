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

### Christmas list configuration

The Christmas list keeps its database credentials outside source control. For a
new checkout, copy the example configuration and fill in the deployment values:

```sh
cp site/xmas_list/database_config.example.php site/xmas_list/database_config.php
```

The resulting `database_config.php` is ignored by Git. The private database dump
`xmas_list.sql` is also ignored; `schema.sql` contains the commit-safe schema for
creating a fresh database.

The same private configuration contains the signed-login cookie secret and the
one-way hashes of each user's memorable phrase. The example configuration shows
how to generate both values. Phrase matching is case-insensitive and ignores
spaces and punctuation, so hashes must be generated from the normalised phrase.
