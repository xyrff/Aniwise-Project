// AniWise — shared interactions and weather workflow


let scrollAnimationFrame = null;

function scrollToSection(sectionId) {
    const target = document.getElementById(sectionId);
    if (!target) return;

    const startY = window.scrollY;
    const targetY = target.getBoundingClientRect().top + startY;
    const distance = targetY - startY;
    const duration = 700;
    let startTime = null;

    function easeInOutQuad(t) {
        return t < 0.5
            ? 2 * t * t
            : 1 - Math.pow(-2 * t + 2, 2) / 2;
    }

    function step(currentTime) {
        if (startTime === null) startTime = currentTime;

        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        window.scrollTo(0, startY + distance * easeInOutQuad(progress));

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
}

/* ============================================================================
   Weather search and forecast
   ============================================================================ */

const weatherSearchForm = document.getElementById("weather-search-form");
const weatherSearchBtn = document.getElementById("weather-search-btn");
const locationInput = document.getElementById("location-input");
const useLocationBtn = document.getElementById("use-location-btn");
const retryWeatherBtn = document.getElementById("weather-retry-btn");
const locationSuggestions = document.getElementById("location-suggestions");
const weatherSearch = document.querySelector(".weather-search");
const weatherStatus = document.getElementById("weather-status");
const weatherError = document.getElementById("weather-error");
const weatherErrorMessage = document.getElementById("weather-error-message");
const currentWeather = document.getElementById("current-weather");
const currentWeatherEmpty = document.getElementById("current-weather-empty");
const currentWeatherEmptyTitle = document.getElementById("current-weather-empty-title");
const currentWeatherEmptyText = document.getElementById("current-weather-empty-text");
const currentWeatherContent = document.getElementById("current-weather-content");
const forecastGrid = document.getElementById("forecast-grid");

let suggestionTimeout = null;
let suggestionRequestId = 0;
let selectedLocation = null;
let lastSearchValue = "";

function setWeatherStatus(message, variant = "info") {
    if (!weatherStatus) {
        return;
    }

    weatherStatus.textContent = message;
    weatherStatus.hidden = !message;
    weatherStatus.className = `weather-status weather-status-${variant}`;
}

function setWeatherState(state, message) {
    if (!currentWeather) {
        return;
    }

    currentWeather.dataset.state = state;

    if (state === "ready") {
        currentWeatherEmpty.hidden = true;
        currentWeatherContent.hidden = false;
    } else {
        currentWeatherEmpty.hidden = false;
        currentWeatherContent.hidden = true;
    }

    if (state === "idle") {
        currentWeatherEmptyTitle.textContent = "Choose a location";
        currentWeatherEmptyText.textContent = "Current conditions will appear here after a search.";
    }

    if (state === "searching") {
        currentWeatherEmptyTitle.textContent = "Searching locations";
        currentWeatherEmptyText.textContent = "We are looking for a Philippine city or province.";
    }

    if (state === "loading") {
        currentWeatherEmptyTitle.textContent = "Loading weather";
        currentWeatherEmptyText.textContent = "Current conditions and the 7-day forecast will appear shortly.";
    }

    if (state === "empty") {
        currentWeatherEmptyTitle.textContent = "Location not found";
        currentWeatherEmptyText.textContent = "Try a more specific city or province in the Philippines.";
    }

    if (state === "error") {
        currentWeatherEmptyTitle.textContent = "Weather is unavailable";
        currentWeatherEmptyText.textContent = "Check the connection and try the search again.";
    }

    if (message !== undefined) {
        setWeatherStatus(message, state === "loading" || state === "searching" ? "loading" : state === "error" ? "error" : "info");
    }
}

function setWeatherError(message) {
    setWeatherState("error", message);

    if (weatherError && weatherErrorMessage) {
        weatherErrorMessage.textContent = message;
        weatherError.hidden = false;
    }

    setForecastEmpty("A forecast will appear after the weather connection is restored.");
}

function clearWeatherError() {
    if (weatherError && weatherErrorMessage) {
        weatherErrorMessage.textContent = "";
        weatherError.hidden = true;
    }
}

function setForecastEmpty(message) {
    if (!forecastGrid) {
        return;
    }

    forecastGrid.innerHTML = "";
    const empty = document.createElement("p");
    empty.className = "forecast-empty";
    empty.textContent = message;
    forecastGrid.appendChild(empty);
}

function showSuggestionMessage(message) {
    if (!locationSuggestions) {
        return;
    }

    locationSuggestions.innerHTML = "";
    const messageElement = document.createElement("div");
    messageElement.className = "location-suggestions-message";
    messageElement.textContent = message;
    locationSuggestions.appendChild(messageElement);
    locationSuggestions.hidden = false;
    weatherSearch?.classList.add("has-suggestions");
}

function hideLocationSuggestions() {
    if (!locationSuggestions) {
        return;
    }

    suggestionRequestId += 1;
    locationSuggestions.hidden = true;
    locationSuggestions.innerHTML = "";
    weatherSearch?.classList.remove("has-suggestions");
}

function buildLocationName(place) {
    return [place.name, place.admin1, place.country].filter(Boolean).join(", ");
}

function renderLocationSuggestions(results) {
    if (!locationSuggestions) {
        return;
    }

    locationSuggestions.innerHTML = "";

    results.forEach(function (place) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "location-suggestion";
        button.setAttribute("role", "option");

        const icon = document.createElement("span");
        icon.className = "location-suggestion-icon";
        icon.innerHTML = '<i class="fa-solid fa-location-dot" aria-hidden="true"></i>';

        const text = document.createElement("span");
        text.className = "location-suggestion-text";

        const name = document.createElement("span");
        name.className = "location-suggestion-name";
        name.textContent = place.name || "Unknown location";

        const details = document.createElement("span");
        details.className = "location-suggestion-details";
        details.textContent = [place.admin1, place.admin2, place.country].filter(Boolean).join(", ");

        text.append(name, details);
        button.append(icon, text);
        button.addEventListener("click", function () {
            selectedLocation = place;
            locationInput.value = buildLocationName(place);
            lastSearchValue = locationInput.value;
            hideLocationSuggestions();
            setWeatherStatus("Location selected. Search to load the forecast.");
        });

        locationSuggestions.appendChild(button);
    });

    locationSuggestions.hidden = false;
    weatherSearch?.classList.add("has-suggestions");
}

async function getLocationSuggestions(query) {
    if (!locationSuggestions) {
        return;
    }

    const requestId = ++suggestionRequestId;
    showSuggestionMessage("Searching Philippine locations...");

    try {
        const response = await fetch(
            `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=8&language=en&countryCode=PH&format=json`
        );

        if (!response.ok) {
            throw new Error("Location search failed.");
        }

        const data = await response.json();

        if (requestId !== suggestionRequestId) {
            return;
        }

        if (!data.results || data.results.length === 0) {
            showSuggestionMessage("No Philippine locations found.");
            return;
        }

        renderLocationSuggestions(data.results);
    } catch (error) {
        if (requestId !== suggestionRequestId) {
            return;
        }

        console.error("Autocomplete error:", error);
        showSuggestionMessage("Unable to search locations right now.");
    }
}

if (locationInput) {
    locationInput.addEventListener("input", function () {
        const query = locationInput.value.trim();
        selectedLocation = null;
        lastSearchValue = query;
        clearTimeout(suggestionTimeout);

        if (query.length < 2) {
            hideLocationSuggestions();
            return;
        }

        suggestionTimeout = setTimeout(function () {
            getLocationSuggestions(query);
        }, 300);
    });
}

document.addEventListener("click", function (event) {
    if (locationSuggestions && !event.target.closest(".search-input-wrapper")) {
        hideLocationSuggestions();
    }
});

async function searchLocation(location) {
    if (!location) {
        setWeatherError("Enter a Philippine city or province before searching.");
        return;
    }

    lastSearchValue = location;
    hideLocationSuggestions();
    clearWeatherError();
    setWeatherState("searching", "Searching Philippine locations...");
    setSearchButtonLoading(true, "Searching...");

    try {
        const response = await fetch(
            `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(location)}&count=1&language=en&countryCode=PH&format=json`
        );

        if (!response.ok) {
            throw new Error("Unable to search for location.");
        }

        const data = await response.json();

        if (!data.results || data.results.length === 0) {
            setWeatherState("empty", "We could not find that location. Try a city or province in the Philippines.");
            setForecastEmpty("Choose a location to see the 7-day forecast.");
            return;
        }

        const place = data.results[0];
        selectedLocation = place;
        locationInput.value = buildLocationName(place);
        await getWeather(place.latitude, place.longitude, buildLocationName(place));
    } catch (error) {
        console.error("Location search error:", error);
        setWeatherError("Weather could not be loaded. Check your connection and try again.");
    } finally {
        setSearchButtonLoading(false);
    }
}

function setSearchButtonLoading(isLoading, label) {
    if (!weatherSearchBtn) {
        return;
    }

    weatherSearchBtn.disabled = isLoading;
    weatherSearchBtn.setAttribute("aria-busy", String(isLoading));
    weatherSearchBtn.innerHTML = isLoading
        ? '<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> ' + label
        : '<i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i> Search forecast';
}

if (weatherSearchForm) {
    weatherSearchForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const location = locationInput?.value.trim() || "";

        if (selectedLocation && buildLocationName(selectedLocation) === location) {
            getWeather(
                selectedLocation.latitude,
                selectedLocation.longitude,
                buildLocationName(selectedLocation)
            );
            return;
        }

        searchLocation(location);
    });
}

if (retryWeatherBtn) {
    retryWeatherBtn.addEventListener("click", function () {
        const location = lastSearchValue || locationInput?.value.trim() || "";

        if (selectedLocation && location) {
            getWeather(
                selectedLocation.latitude,
                selectedLocation.longitude,
                buildLocationName(selectedLocation)
            );
        } else {
            searchLocation(location);
        }
    });
}

/* ---------------------------------------------------------
   Use My Location (Corrected)
--------------------------------------------------------- */

if (useLocationBtn) {
    // 1. Pass 'event' to prevent form submission from refreshing the page
    useLocationBtn.addEventListener("click", function (event) {
        event.preventDefault();

        // 2. Clear out any previous autocomplete selection
        selectedLocation = null;

        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        useLocationBtn.disabled = true;
        useLocationBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Detecting Location...';

        navigator.geolocation.getCurrentPosition(
            async function (position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                try {
                    // 3. Replaced fake Open-Meteo endpoint with a working free reverse geocoder
                    const response = await fetch(
                        `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`
                    );

                    let locationName = "Your Current Location";

                    if (response.ok) {
                        const data = await response.json();
                        // Format it as "City, Country"
                        if (data.city || data.locality) {
                            locationName = `${data.city || data.locality}, ${data.countryName || "PH"}`;
                        }
                    }

                    if (locationInput) {
                        locationInput.value = locationName;
                    }

                    await getWeather(latitude, longitude, locationName);

                    useLocationBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Location Detected';
                    useLocationBtn.classList.add("location-detected");

                    setTimeout(function () {
                        useLocationBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';
                        useLocationBtn.classList.remove("location-detected");
                    }, 3000);

                } catch (error) {
                    console.error("Location weather error:", error);
                    await getWeather(latitude, longitude, "Your Current Location");

                    useLocationBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Weather Loaded';
                    setTimeout(function () {
                        useLocationBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';
                    }, 3000);
                }

                useLocationBtn.disabled = false;
            },
            function (error) {
                console.error("Geolocation error:", error);
                useLocationBtn.disabled = false;
                useLocationBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';

                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        alert("Location permission was denied. Please allow location access in your browser settings.");
                        break;
                    case error.POSITION_UNAVAILABLE:
                        alert("Your location could not be determined. Please try again.");
                        break;
                    case error.TIMEOUT:
                        alert("Location request timed out. Please try again.");
                        break;
                    default:
                        alert("Unable to determine your location.");
                }
            },
            {
                // 4. Turned off high accuracy to prevent desktop timeout hangs
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 300000
            }
        );
    });
}

async function getWeather(latitude, longitude, locationName) {
    clearWeatherError();
    setWeatherState("loading", `Loading weather for ${locationName}...`);
    setForecastEmpty("Loading the 7-day forecast...");

    try {
        const weatherURL =
            `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
            `&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m` +
            `&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum` +
            `&timezone=auto&forecast_days=7`;

        const response = await fetch(weatherURL);

        if (!response.ok) {
            throw new Error("Weather request failed.");
        }

        const data = await response.json();
        updateCurrentWeather(data, locationName);
        updateForecast(data);
        generateFarmInsight(data);
        currentWeatherEmpty.hidden = true;
        currentWeatherContent.hidden = false;
        setWeatherState("ready", `Weather loaded for ${locationName}.`);
    } catch (error) {
        console.error("Weather error:", error);
        setWeatherError("Weather could not be loaded. Check your connection and try again.");
    }
}

function formatWeatherDate(date) {
    return date.toLocaleDateString("en-PH", {
        weekday: "long",
        month: "long",
        day: "numeric"
    });
}

function updateCurrentWeather(data, locationName) {
    const current = data.current;

    document.getElementById("current-location").textContent = locationName;
    document.getElementById("current-temperature").textContent = `${Math.round(current.temperature_2m)}°`;
    document.getElementById("current-humidity").textContent = `${current.relative_humidity_2m}%`;
    document.getElementById("current-rainfall").textContent = `${current.precipitation} mm`;
    document.getElementById("current-wind").textContent = `${Math.round(current.wind_speed_10m)} km/h`;
    document.getElementById("current-condition").textContent = getWeatherDescription(current.weather_code);
    document.getElementById("current-weather-icon").innerHTML = getWeatherIcon(current.weather_code);
    document.getElementById("current-date").textContent = formatWeatherDate(new Date());
}

function getWeatherDescription(code) {
    const weatherCodes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Light rain showers",
        81: "Moderate rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail"
    };

    return weatherCodes[code] || "Unknown weather";
}

function getWeatherIcon(code) {
    if (code === 0) {
        return '<i class="fa-solid fa-sun" aria-hidden="true"></i>';
    }

    if ([1, 2].includes(code)) {
        return '<i class="fa-solid fa-cloud-sun" aria-hidden="true"></i>';
    }

    if (code === 3) {
        return '<i class="fa-solid fa-cloud" aria-hidden="true"></i>';
    }

    if ([45, 48].includes(code)) {
        return '<i class="fa-solid fa-smog" aria-hidden="true"></i>';
    }

    if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(code)) {
        return '<i class="fa-solid fa-cloud-rain" aria-hidden="true"></i>';
    }

    if ([95, 96, 99].includes(code)) {
        return '<i class="fa-solid fa-cloud-bolt" aria-hidden="true"></i>';
    }

    return '<i class="fa-solid fa-cloud-sun" aria-hidden="true"></i>';
}

function updateForecast(data) {
    const daily = data.daily;

    if (!forecastGrid || !daily) {
        return;
    }

    forecastGrid.innerHTML = "";

    for (let i = 0; i < daily.time.length; i += 1) {
        const date = new Date(`${daily.time[i]}T00:00:00`);
        const card = document.createElement("article");
        card.className = `forecast-card${i === 0 ? " today" : ""}`;

        const day = document.createElement("div");
        day.className = "forecast-day";
        day.textContent = i === 0 ? "Today" : date.toLocaleDateString("en-PH", { weekday: "short" });

        const icon = document.createElement("div");
        icon.className = "forecast-icon";
        icon.innerHTML = getWeatherIcon(daily.weather_code[i]);

        const temperature = document.createElement("div");
        temperature.className = "forecast-temperature";

        const high = document.createElement("span");
        high.className = "forecast-high";
        high.textContent = `${Math.round(daily.temperature_2m_max[i])}°`;

        const low = document.createElement("span");
        low.className = "forecast-low";
        low.textContent = `${Math.round(daily.temperature_2m_min[i])}°`;
        temperature.append(high, low);

        const rain = document.createElement("div");
        rain.className = "forecast-rain";
        rain.innerHTML = '<i class="fa-solid fa-droplet" aria-hidden="true"></i>';
        rain.append(document.createTextNode(` ${daily.precipitation_sum[i]} mm`));

        card.append(day, icon, temperature, rain);
        forecastGrid.appendChild(card);
    }
}

function generateFarmInsight(data) {
    const current = data.current;
    const daily = data.daily;
    const title = document.getElementById("farm-insight-heading");
    const text = document.getElementById("farm-insight-text");

    if (!title || !text) {
        return;
    }

    const temperature = current.temperature_2m;
    const rainfallTomorrow = daily.precipitation_sum[1];

    if (rainfallTomorrow >= 20) {
        title.textContent = "Heavy rainfall expected";
        text.textContent = "Significant rainfall is expected tomorrow. Consider delaying irrigation and outdoor farm activities where possible.";
        return;
    }

    if (temperature >= 34) {
        title.textContent = "High temperature conditions";
        text.textContent = "Temperatures are currently high. Crops may require additional water, especially during periods of limited rainfall.";
        return;
    }

    if (rainfallTomorrow >= 5) {
        title.textContent = "Rain expected tomorrow";
        text.textContent = "Rainfall is expected tomorrow. Monitor soil moisture before scheduling irrigation.";
        return;
    }

    title.textContent = "Favorable weather conditions";
    text.textContent = "Weather conditions currently appear relatively favorable for regular farm activities. Continue monitoring the forecast for changes.";
}

if (currentWeather && !currentWeatherContent.hidden) {
    setWeatherState("idle", "Search for a Philippine city or province to load current conditions.");
}
