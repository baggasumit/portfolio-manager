(function () {
    console.log('Inside IIFE validator.js')

    function ready() {
        console.log('Document validator is ready()');

        let registerForm = document.querySelector("form[name='registerForm']");
        if ( registerForm !== null ) {
            let passwordInput =  document.querySelector("input[name='password']");
            let confirmPasswordInput =  document.querySelector("input[name='confirmPassword']");
            registerForm.addEventListener('submit', function (evt) {
                if (passwordInput.value !== confirmPasswordInput.value) {
                    evt.preventDefault();
                    utils.showErrorBanner('Passwords do not match.')
                }
            });
        }
    }

    // this is required for the (not so) edge case where script is loaded after the document has loaded
    // https://developer.mozilla.org/en/docs/Web/API/Document/readyState
    if (document.readyState !== 'loading') {
        ready()
    } else {
        document.addEventListener('DOMContentLoaded', ready)
    }
})();

