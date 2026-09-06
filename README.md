# jonsim.com
Source for [jonsim.com](http://www.jonsim.com). Currently this is purely static
pages so deployment is a simple copy-paste exercise.

To generate the recipes site:
```sh
export COOK_RENDER_PATH=/path/to/cook-render
export RECIPE_PATH=/path/to/recipes
export SITE_PATH=/path/to/jonsim_com
cd $COOK_RENDER_PATH
rm -r $SITE_PATH/site/recipes
uv run cook-render -b $RECIPE_PATH -o $SITE_PATH/site/recipes
```
