var utils = {

    showErrorBanner: function (msg) {
        let $errorMsgBanner = document.querySelector('.alert');
        $errorMsgBanner.style.display = 'block';
        $errorMsgBanner.innerHTML = msg;
    },

    hideErrorBanner: function () {
        let $errorMsgBanner = document.querySelector('.alert');
        $errorMsgBanner.style.display = 'none';
    }
};

