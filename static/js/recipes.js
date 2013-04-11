var recipe_template = _.template(''+
	'<div class="recipe">' +
		'<section class="recipe-header">' +
			'<h2><%- name %></h2>' +
			'<span>By <%- author %></span>' +
		'</section>' +
		'<section class="recipe-body" hidden>' +
			'<div class="ingredients" hidden>' +
				'<span><b>Ingredients</b></span>' +
				'<ul></ul>' +
			'</div>' + 
			'<div class="instructions" hidden>' +
				'<span><b>Instructions</b></span>' +
				'<p><%- instructions %></p>' +
			'</div>' + 
		'</section>' +
		'<br style="clear:both;"' +
	'</div>');


var getRecipes = function() {
	var recipes;
	$.ajax({
		url: '/api/recipes',
		dataType: 'json',
		async: false,
		success: function(data) {
			recipes = data;
		}
	})
	return recipes;
}

var getIngredients = function(recipeID) {
	var ingredients;
	$.ajax({
		url: '/api/ingredients/' + recipeID,
		dataType: 'json',
		async: false,
		success: function(data) {
			ingredients = data;
		}
	})
	return ingredients;
}

var displayRecipes = function(recipes) {
	var $container = $('#main-container');
	_.each(recipes, function(recipe) {
		var $recipe = $(recipe_template(recipe)).data('id', recipe['id']);
		$container.append($recipe);
	});
}

$(document).ready(function() {
	displayRecipes(getRecipes());
	$('.recipe').on('click', function() {
		var $this = $(this);
		var $body = $this.find('.recipe-body');
		if($body.is(":hidden")) {
			var id = $this.data('id');
			var ingredients = getIngredients(id);
			var $ul = $this.find('.recipe-body ul');
			$ul.empty();
			_.each(ingredients, function(ingredient) {
				var $li = $('<li></li>')
					.text(ingredient['name'] + "  x" + ingredient['amount']);
				$ul.append($li);
			})
			$body.slideToggle('fast', function() {
                var $that = $this;
                $this.find('.ingredients').show('slide', function() {
                    $that.find('.instructions').show('slide');
                });  
            });
		}
		else {
			$body.hide('slide');
		}
		
		//$(this).find('.recipe-body').show('slide');


	})
})
