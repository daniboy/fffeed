var loginContainer = document.getElementById('login-container');
var loginStatus = document.getElementById('login-status');
var changesContainer = document.getElementById('changes-container');
var changesButton = document.getElementById('changes-button');

var shortAccessToken = null;


// Initialize facebook
window.fbAsyncInit = function () {

    FB.init({
        appId: document.getElementsByTagName('meta').facebook_app_id.content,
        cookie: true,
        xfbml: true,
        version: 'v2.2'
    });

    statusChangeCallback();
};

changesButton.addEventListener('click', changesSeeMoreHandler);


// Callback for when the login status was retrieved
function loginStatusCallback(response) {
    switch (response.status) {
        case 'connected':
            shortAccessToken = response.authResponse.accessToken;
            loginContainer.classList.add('hidden');
            switchClass(loginStatus.classList, 'info');
            FB.api('/me', apiMeCallback);
            break;

        default:
            loginStatus.textContent = "You are not logged in. Please log in to the app to continue.";
            switchClass(loginStatus.classList, 'warning');
            loginContainer.classList.remove('hidden');
            break;
    }
}

// Callback for the login status change
function statusChangeCallback() {
    FB.getLoginStatus(loginStatusCallback);
}

// Callback for the '/me' API call
function apiMeCallback(response) {
    loginStatus.textContent = "Logged in as " + response.name;
    switchClass(loginStatus.classList, 'success');

    extendAccessToken(shortAccessToken);
}

// Callback for the new access token store
function accessTokenExtendedCallback() {
    if (this.readyState == XMLHttpRequest.DONE) {
        var response = jsonifyXhrResponse(this);
        if (!response.success) {
            return showError("Server error: " + response.error);
        }

        FB.access_token = response.access_token;
        changesContainer.classList.remove('hidden');
        getChanges();
    }
}

// Callback for received changes to the friends list
function changesReceivedCallback() {
    if (this.readyState == XMLHttpRequest.DONE) {
        var response = jsonifyXhrResponse(this);
        if (!response.success) {
            return showError("Server error: " + response.error);
        }

        var dateTimeFormatOptions = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric'
        };
        response.change_bundles.forEach(function (changeBundle) {
            var bundleDate = new Date(changeBundle.date);
            var bundleDateElement = document.createElement('dt');
            bundleDateElement.textContent = bundleDate.toLocaleString(navigator.language, dateTimeFormatOptions);
            changesButton.parentNode.insertBefore(bundleDateElement, changesButton);

            changeBundle.changes.forEach(function (change) {
                var changeElement = document.createElement('dd');
                var changeIconElement = document.createElement('span');
                var changeTextElement = document.createTextNode(' ' + change.event_content);

                changeIconElement.classList.add('glyphicon');

                switch (change.event_type) {
                    case 'ADDED':
                        changeElement.classList.add('text-success');
                        changeIconElement.classList.add('glyphicon-plus-sign');
                        break;

                    case 'REMOVED':
                        changeElement.classList.add('text-danger');
                        changeIconElement.classList.add('glyphicon-minus-sign');
                        break;

                    case 'INFO':
                        changeElement.classList.add('text-info');
                        changeIconElement.classList.add('glyphicon-info-sign');
                        break;

                    case 'ERROR':
                        changeElement.classList.add('text-danger');
                        changeIconElement.classList.add('glyphicon-exclamation-sign');
                        break;
                }

                changeElement.appendChild(changeIconElement);
                changeElement.appendChild(changeTextElement);
                changesButton.parentNode.insertBefore(changeElement, changesButton);
            });
        });

        if (response.more) {
            changesButton.classList.remove('disabled');
            changesButton.textContent = "See more";
            changesButton.setAttribute('js:before', response.change_bundles[response.change_bundles.length - 1].date);
        } else {
            changesButton.textContent = "No more changes";
        }
    }
}

// Handler for the See More changes button
function changesSeeMoreHandler(event) {
    if (!changesButton.classList.contains('disabled')) {
        getChanges(changesButton.getAttribute('js:before'));
    }
}

// Store a new access token to the database
function extendAccessToken(access_token) {
    doXhr('POST', 'access_token', accessTokenExtendedCallback, {'access_token': access_token});
}

// Get the latest changes in the user's friends list from the database
function getChanges(before) {
    changesButton.classList.add('disabled');
    changesButton.textContent = "Loading…";
    var url = 'changes';
    if (before) {
        url += '?before=' + before;
    }
    doXhr('GET', url, changesReceivedCallback);
}

// Helper function to POST an XHR to the server
function doXhr(method, url, callback, data) {
    if (data) {
        var formData = new FormData();
        for (var field in data) {
            if (data.hasOwnProperty(field)) {
                formData.append(field, data[field]);
            }
        }
        data = formData;
    }

    var xhr = new XMLHttpRequest();
    xhr.open(method, '/ajax/' + url);
    xhr.onload = callback;
    xhr.send(data);
}

// Helper function to JSONify the response
function jsonifyXhrResponse(xhrThis) {
    try {
        return JSON.parse(xhrThis.responseText);
    } catch (e) {
        return {
            status: false,
            error: xhrThis.responseText
        }
    }
}

// Switch the bootstrap class
function switchClass(classList, newClass) {
    ['primary', 'success', 'info', 'warning', 'danger'].forEach(function (oldClass) {
        if (oldClass != newClass) {
            classList.remove('bg-' + oldClass);
            classList.remove('text-' + oldClass);
        }
    });
    classList.add('bg-' + newClass);
    classList.add('text-' + newClass);
}

// Shows an error message
function showError(msg) {
    loginStatus.textContent = msg;
    switchClass(loginStatus.classList, 'danger');
}
