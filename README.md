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

Generate the recipes site:

```sh
export COOK_RENDER_PATH=/path/to/cook-render
export RECIPE_PATH=/path/to/recipes
export SITE_PATH=/path/to/jonsim_com
cd $COOK_RENDER_PATH
rm -r $SITE_PATH/site/recipes
uv run cook-render -b $RECIPE_PATH -o $SITE_PATH/site/recipes
```
