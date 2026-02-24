function checkForm() {
  var form = document.querySelector(".search-form");
  if (!form) {
    return true;
  }

  var searchField = form.querySelector("input[name='search']");
  var dateField = form.querySelector("input[name='travel_date']");
  var seatsField = form.querySelector("input[name='minimum_seats']");
  var passengersField = form.querySelector("input[name='passengers_only']");

  var hasSearch = searchField && searchField.value.trim() !== "";
  var hasDate = dateField && dateField.value.trim() !== "";
  var hasSeats = seatsField && seatsField.value.trim() !== "";
  var hasPassengersOnly = passengersField && passengersField.checked;

  return hasSearch || hasDate || hasSeats || hasPassengersOnly;
}

function initSearchHints() {
  var hintButtons = document.querySelectorAll("[data-search-hint]");
  if (!hintButtons.length) {
    return;
  }

  var searchField = document.querySelector(".search-form input[name='search']");
  if (!searchField) {
    return;
  }

  hintButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      searchField.value = button.getAttribute("data-search-hint") || "";
      searchField.focus();
    });
  });
}

function initFaqAccordion() {
  var faqContainer = document.querySelector("[data-faq-list]");
  if (!faqContainer) {
    return;
  }

  var items = faqContainer.querySelectorAll("details");
  items.forEach(function (item) {
    item.addEventListener("toggle", function () {
      if (!item.open) {
        return;
      }

      items.forEach(function (otherItem) {
        if (otherItem !== item) {
          otherItem.open = false;
        }
      });
    });
  });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function readMapRides() {
  var script = document.getElementById("map-rides-data");
  if (!script) {
    return [];
  }

  try {
    return JSON.parse(script.textContent);
  } catch (error) {
    return [];
  }
}

function renderRidePopup(ride) {
  return [
    "<strong>",
    escapeHtml(ride.first_name),
    "</strong><br>",
    escapeHtml(ride.origination),
    " to ",
    escapeHtml(ride.destination_city),
    ", ",
    escapeHtml(ride.destination_state),
    "<br>",
    "Departure: ",
    escapeHtml(ride.date),
    " ",
    escapeHtml(ride.time),
    "<br>",
    "Open seats: ",
    escapeHtml(ride.seats_available),
  ].join("");
}

function initRideMap() {
  var mapElement = document.getElementById("rides-map");
  if (!mapElement || typeof window.L === "undefined") {
    return;
  }

  var rides = readMapRides();
  var map = window.L.map(mapElement, { scrollWheelZoom: true });

  window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  if (!rides.length) {
    map.setView([39.8283, -98.5795], 4);
    return;
  }

  var bounds = [];

  rides.forEach(function (ride) {
    var origin = [ride.origin_lat, ride.origin_lng];
    var destination = [ride.destination_lat, ride.destination_lng];
    var popup = renderRidePopup(ride);

    window.L.polyline([origin, destination], {
      color: "#2f6fff",
      weight: 3,
      opacity: 0.75,
    })
      .addTo(map)
      .bindPopup(popup);

    window.L.circleMarker(origin, {
      radius: 6,
      color: "#0b3d2f",
      weight: 1,
      fillColor: "#17b890",
      fillOpacity: 0.95,
    })
      .addTo(map)
      .bindPopup("<strong>Origin</strong><br>" + popup);

    window.L.circleMarker(destination, {
      radius: 6,
      color: "#730052",
      weight: 1,
      fillColor: "#ff00bf",
      fillOpacity: 0.95,
    })
      .addTo(map)
      .bindPopup("<strong>Destination</strong><br>" + popup);

    bounds.push(origin);
    bounds.push(destination);
  });

  map.fitBounds(bounds, { padding: [24, 24] });
}

document.addEventListener("DOMContentLoaded", function () {
  initSearchHints();
  initFaqAccordion();
  initRideMap();
});
