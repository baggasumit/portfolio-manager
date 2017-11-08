(function () {
    console.log('Inside IIFE quote.js');

    async function getQuote(stockSymbol) {
        const response = await axios
                            .get(`https://api.iextrading.com/1.0/stock/${stockSymbol}/quote`)
                            .catch(function (error) {
                                console.log('404');
                                console.log(JSON.stringify(error, null, 2))
                            });
        return response;
    }

    async function displayQuote(stockSymbol) {
        let response = await getQuote(stockSymbol);
        let $quoteTable = document.querySelector('#quoteResults table');

        if (response) {
            utils.hideErrorBanner();
            document.getElementById('quoteResultsHeader').removeAttribute('hidden');
            $quoteTable.appendChild(createQuoteRow(response.data));
        } else {
            utils.showErrorBanner(`Stock symbol '${stockSymbol}' does not exist`);
        }
    }

    function createQuoteRow(quote) {
        let $quoteRow = document.createElement("tr");
        $quoteRow.innerHTML = `
            <td>${quote["symbol"]}</td>
            <td>${quote["companyName"]}</td>
            <td class='right'>${'$' + quote["latestPrice"]}</td>
        `;
        return $quoteRow;
    }

    function ready() {
        console.log('Document quote is ready()');

        let $quoteForm = document.querySelector("form[name='quoteForm']");

        if ( $quoteForm ) {
            let $quoteInput =  document.querySelector("input[name='symbol']");
            $quoteForm.addEventListener('submit', function (evt) {
                evt.preventDefault();
                let stockSymbol = $quoteInput.value.toUpperCase();
                $quoteForm.reset();
                displayQuote(stockSymbol);
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

