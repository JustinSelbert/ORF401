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

function initAddRideForm() {
  var form = document.getElementById("add-ride-form");
  if (!form) {
    return;
  }

  var originField = form.querySelector("input[name='origination']");
  var destinationCityField = form.querySelector("input[name='destination_city']");
  var destinationStateField = form.querySelector("input[name='destination_state']");
  var dateField = form.querySelector("input[name='date']");
  var timeField = form.querySelector("input[name='time']");
  var seatsField = form.querySelector("input[name='seats_available']");
  var passengersField = form.querySelector("input[name='taking_passengers']");
  var previewCopy = document.getElementById("ride-preview-copy");

  if (dateField) {
    var now = new Date();
    var month = String(now.getMonth() + 1).padStart(2, "0");
    var day = String(now.getDate()).padStart(2, "0");
    dateField.min = [now.getFullYear(), month, day].join("-");
  }

  if (destinationStateField) {
    destinationStateField.setAttribute("maxlength", "2");
    destinationStateField.addEventListener("input", function () {
      destinationStateField.value = destinationStateField.value
        .replace(/[^a-zA-Z]/g, "")
        .toUpperCase()
        .slice(0, 2);
      updatePreview();
    });
  }

  if (seatsField) {
    seatsField.addEventListener("input", function () {
      var parsed = Number(seatsField.value);
      if (Number.isNaN(parsed)) {
        return;
      }
      if (parsed < 0) {
        seatsField.value = "0";
      }
      if (parsed > 6) {
        seatsField.value = "6";
      }
      updatePreview();
    });
  }

  function updatePreview() {
    if (!previewCopy) {
      return;
    }

    var origin = originField && originField.value.trim();
    var city = destinationCityField && destinationCityField.value.trim();
    var state = destinationStateField && destinationStateField.value.trim();
    var date = dateField && dateField.value.trim();
    var time = timeField && timeField.value.trim();
    var seats = seatsField && seatsField.value.trim();
    var takingPassengers = !!(passengersField && passengersField.checked);

    if (!origin && !city && !state) {
      previewCopy.textContent = "No route yet.";
      return;
    }

    var route = [origin || "Origin", "to", city || "Destination"];
    if (state) {
      route[route.length - 1] += ", " + state;
    }

    var schedule = [];
    if (date) {
      schedule.push(date);
    }
    if (time) {
      schedule.push(time);
    }

    var seatCopy = seats ? seats + " seat" + (seats === "1" ? "" : "s") : "Seat count not set";
    var passengerCopy = takingPassengers ? "taking passengers" : "driver only";

    previewCopy.textContent =
      route.join(" ") +
      ". " +
      (schedule.length ? "Departure: " + schedule.join(" ") + ". " : "") +
      seatCopy +
      ", " +
      passengerCopy +
      ".";
  }

  [originField, destinationCityField, dateField, timeField, passengersField].forEach(function (field) {
    if (field) {
      field.addEventListener("input", updatePreview);
      field.addEventListener("change", updatePreview);
    }
  });

  updatePreview();
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
  var profileLink = "";
  if (ride.rider_profile_url) {
    profileLink =
      "<br><a class='map-profile-link' href='" +
      encodeURI(ride.rider_profile_url) +
      "'>View full rider profile</a>";
  }

  return [
    "<strong>",
    escapeHtml(ride.first_name),
    "</strong><br>",
    escapeHtml(ride.occupation || "SparkRides rider"),
    "<br>",
    "Looking for: ",
    escapeHtml(ride.looking_for || "Connection"),
    "<br>",
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
    profileLink,
  ].join("");
}

function setMapRouteStatus(message) {
  var statusElement = document.getElementById("map-route-status");
  if (statusElement) {
    statusElement.textContent = message;
  }
}

function buildRouteKey(origin, destination) {
  return [
    origin[0].toFixed(4),
    origin[1].toFixed(4),
    destination[0].toFixed(4),
    destination[1].toFixed(4),
  ].join("|");
}

function toFiniteNumber(value) {
  var parsedValue = Number(value);
  return Number.isFinite(parsedValue) ? parsedValue : null;
}

function toLatLngPair(rawLatitude, rawLongitude) {
  var latitude = toFiniteNumber(rawLatitude);
  var longitude = toFiniteNumber(rawLongitude);
  if (latitude === null || longitude === null) {
    return null;
  }

  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
    return null;
  }

  return [latitude, longitude];
}

function normalizePathCoordinates(rawCoordinates) {
  if (!Array.isArray(rawCoordinates)) {
    return null;
  }

  var coordinates = rawCoordinates
    .map(function (point) {
      if (!Array.isArray(point) || point.length < 2) {
        return null;
      }

      return toLatLngPair(point[0], point[1]);
    })
    .filter(function (point) {
      return Array.isArray(point);
    });

  return coordinates.length > 1 ? coordinates : null;
}

async function fetchRoadRoute(origin, destination, routeCache) {
  var key = buildRouteKey(origin, destination);
  if (Object.prototype.hasOwnProperty.call(routeCache, key)) {
    return routeCache[key];
  }

  var url =
    "/api/road-route/?" +
    "origin_lat=" +
    encodeURIComponent(origin[0]) +
    "&origin_lng=" +
    encodeURIComponent(origin[1]) +
    "&destination_lat=" +
    encodeURIComponent(destination[0]) +
    "&destination_lng=" +
    encodeURIComponent(destination[1]);

  try {
    var response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      routeCache[key] = null;
      return null;
    }

    var payload = await response.json();
    var coordinates = normalizePathCoordinates(payload && payload.coordinates);
    routeCache[key] = coordinates;
    return coordinates;
  } catch (error) {
    routeCache[key] = null;
    return null;
  }
}

async function mapWithConcurrency(items, concurrency, worker) {
  var results = new Array(items.length);
  var currentIndex = 0;

  async function runWorker() {
    while (currentIndex < items.length) {
      var itemIndex = currentIndex;
      currentIndex += 1;
      results[itemIndex] = await worker(items[itemIndex], itemIndex);
    }
  }

  var workerCount = Math.max(1, Math.min(concurrency, items.length));
  var workers = [];
  for (var i = 0; i < workerCount; i += 1) {
    workers.push(runWorker());
  }

  await Promise.all(workers);
  return results;
}

async function initRideMap() {
  var mapElement = document.getElementById("rides-map");
  if (!mapElement || typeof window.L === "undefined") {
    return;
  }

  var rides = readMapRides();
  var map = window.L.map(mapElement, { scrollWheelZoom: true });

  window.L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO',
  }).addTo(map);

  if (!rides.length) {
    map.setView([39.8283, -98.5795], 4);
    setMapRouteStatus("No rides available to route.");
    return;
  }

  setMapRouteStatus("Computing road routes...");

  var routeCache = {};
  var bounds = [];
  var roadRouteCount = 0;
  var fallbackRouteCount = 0;
  var maxConcurrentRouteRequests = 4;

  var routedRides = await mapWithConcurrency(
    rides,
    maxConcurrentRouteRequests,
    async function (ride) {
      var origin = toLatLngPair(ride.origin_lat, ride.origin_lng);
      var destination = toLatLngPair(ride.destination_lat, ride.destination_lng);
      if (!origin || !destination) {
        fallbackRouteCount += 1;
        return null;
      }

      var roadCoordinates = await fetchRoadRoute(origin, destination, routeCache);
      var hasRoadRoute = Array.isArray(roadCoordinates) && roadCoordinates.length > 1;

      if (hasRoadRoute) {
        roadRouteCount += 1;
      } else {
        fallbackRouteCount += 1;
      }

      return {
        ride: ride,
        origin: origin,
        destination: destination,
        path: hasRoadRoute ? roadCoordinates : [origin, destination],
        hasRoadRoute: hasRoadRoute,
      };
    }
  );

  routedRides.forEach(function (entry) {
    if (!entry) {
      return;
    }

    var popup = renderRidePopup(entry.ride);

    window.L.polyline(entry.path, {
      color: "#ff6a00",
      weight: 3,
      opacity: 0.78,
      dashArray: entry.hasRoadRoute ? null : "6 6",
    })
      .addTo(map)
      .bindPopup(popup);

    window.L.circleMarker(entry.origin, {
      radius: 6,
      color: "#2f1b0d",
      weight: 1,
      fillColor: "#ff8a33",
      fillOpacity: 0.95,
    })
      .addTo(map)
      .bindPopup("<strong>Origin</strong><br>" + popup);

    window.L.circleMarker(entry.destination, {
      radius: 6,
      color: "#26140a",
      weight: 1,
      fillColor: "#ff6a00",
      fillOpacity: 0.95,
    })
      .addTo(map)
      .bindPopup("<strong>Destination</strong><br>" + popup);

    bounds.push(entry.origin);
    bounds.push(entry.destination);
  });

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [24, 24] });
  } else {
    map.setView([39.8283, -98.5795], 4);
  }

  setMapRouteStatus(
    "Road routes ready: " +
      roadRouteCount +
      " routed on roads, " +
      fallbackRouteCount +
      " fallback line" +
      (fallbackRouteCount === 1 ? "" : "s") +
      "."
  );
}

document.addEventListener("DOMContentLoaded", function () {
  initSearchHints();
  initFaqAccordion();
  initAddRideForm();
  initRideMap();
});
