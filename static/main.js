function getCookie(c_name) {
    var i,x,y,ARRcookies=document.cookie.split(";");
    for (i=0;i<ARRcookies.length;i++) {
        x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
        y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
        x=x.replace(/^\s+|\s+$/g,"");
        if (x==c_name) {
            return unescape(y);
        }
    }
}

function setCookie(c_name,value,exdays) {
    var exdate=new Date();
    exdate.setDate(exdate.getDate() + exdays);
    var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
    document.cookie=c_name + "=" + c_value;
}

function checkForm() {
    var form = document.querySelector(".search-form");
    if (!form) {
        return true;
    }

    var textInputs = form.querySelectorAll("input[type='text']");
    var hasValue = false;
    var combined = [];
    var i;

    for (i = 0; i < textInputs.length; i++) {
        var value = textInputs[i].value.trim();
        combined.push(value);
        if (value !== "") {
            hasValue = true;
        }
    }

    if (!hasValue) {
        return false;
    }

    if (combined.join(" ").replace(/\s+/g, " ").trim().toLowerCase() === "elon musk") {
        alert("");
    }

    return true;
}

function handleFirstVisit() {
    var visitCookieName = "sparkrides_visited";
    var hasVisited = getCookie(visitCookieName);
    var path = window.location.pathname.replace(/\/+$/, "");

    if (path === "") {
        path = "/";
    }

    if (!hasVisited) {
        setCookie(visitCookieName, "1", 30);

        // First visit on a non-splash page should be sent to the splash page.
        if (path !== "/") {
            window.location.href = "/";
            return;
        }
    }
}

document.addEventListener("DOMContentLoaded", handleFirstVisit);
