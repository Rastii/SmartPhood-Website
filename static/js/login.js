var login = function() {
	var inputs = $('input');
	var username = inputs.eq(0).val();
	var password = inputs.eq(1).val();
	return 0;
}

var displayError = function() {
	$('.error-container span').text('**Invalid username and/or password');
}

var registerUser = function() {
	var inputs = $('input');
	var username = inputs.eq(0).val();
	var password = inputs.eq(1).val();
	var cpass = inputs.eq(2).val();
	var $error = $('.error-container span');
	if (username.length < 6) {
		$error.text("**Username must be at least 6 characters.")
	}
	else if(password.length < 8) {
		$error.text("**Password must be at least 8 characters.")
	}
	else if(password == cpass) {
		console.log("Register user!");
	}
	else {
		$error.text("**Passwords must match.");
	}
}

$(document).ready(function() {
	var $btn_login = $('#btn-login');
	$btn_login.on('click', function() {
		if(login() == 1) {

		}
		else {
			displayError();
		}
	});

	$('#btn-register').on('click', function() {
		$hidden = $('.form-entry:hidden');
		if($hidden.html()) {
			$hidden.show();
			$('#btn-login').hide('slide');
		}
		else {
			registerUser();
		}
	})
});
