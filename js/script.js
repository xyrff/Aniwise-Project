// AniWise — Global / Homepage Interactivity

function scrollToSection(sectionId) {

    const target = document.getElementById(sectionId);

    if (!target) return;

    const startY = window.scrollY;
    const targetY =
        target.getBoundingClientRect().top + startY;

    const distance = targetY - startY;

    const duration = 700;

    let startTime = null;


    function easeInOutQuad(t) {

        return t < 0.5
            ? 2 * t * t
            : 1 - Math.pow(-2 * t + 2, 2) / 2;

    }


    function step(currentTime) {

        if (startTime === null) {
            startTime = currentTime;
        }

        const elapsed =
            currentTime - startTime;

        const progress =
            Math.min(elapsed / duration, 1);


        window.scrollTo(
            0,
            startY +
            distance *
            easeInOutQuad(progress)
        );


        if (progress < 1) {
            requestAnimationFrame(step);
        }

    }


    requestAnimationFrame(step);

}



/* =========================================================
   WEATHER FORECAST
========================================================= */


/* ---------------------------------------------------------
   Weather Elements
--------------------------------------------------------- */

const weatherSearchBtn =
    document.getElementById("weather-search-btn");

const locationInput =
    document.getElementById("location-input");

const useLocationBtn =
    document.getElementById("use-location-btn");

const locationSuggestions =
    document.getElementById("location-suggestions");


let suggestionTimeout = null;

let selectedLocation = null;



/* =========================================================
   LOCATION AUTOCOMPLETE
========================================================= */


/* ---------------------------------------------------------
   Listen for User Typing
--------------------------------------------------------- */

if (locationInput) {

    locationInput.addEventListener(
        "input",
        function () {

            const query =
                locationInput.value.trim();


            // User changed the text,
            // so previous selection is no longer valid.

            selectedLocation = null;


            clearTimeout(
                suggestionTimeout
            );


            if (query.length < 2) {

                hideLocationSuggestions();

                return;

            }


            suggestionTimeout =
                setTimeout(
                    () => {

                        getLocationSuggestions(
                            query
                        );

                    },
                    300
                );

        }
    );

}



/* ---------------------------------------------------------
   Get Philippine Location Suggestions
--------------------------------------------------------- */

async function getLocationSuggestions(query) {

    try {

        showSuggestionMessage(
            "Searching Philippine locations..."
        );


        const response = await fetch(

            `https://geocoding-api.open-meteo.com/v1/search?` +

            `name=${encodeURIComponent(query)}` +

            `&count=8` +

            `&language=en` +

            `&countryCode=PH` +

            `&format=json`

        );


        if (!response.ok) {

            throw new Error(
                "Location search failed."
            );

        }


        const data =
            await response.json();


        if (
            !data.results ||
            data.results.length === 0
        ) {

            showSuggestionMessage(
                "No Philippine locations found."
            );

            return;

        }


        renderLocationSuggestions(
            data.results
        );


    } catch (error) {

        console.error(
            "Autocomplete error:",
            error
        );


        showSuggestionMessage(
            "Unable to search locations."
        );

    }

}



/* ---------------------------------------------------------
   Render Location Suggestions
--------------------------------------------------------- */

function renderLocationSuggestions(
    results
) {

    locationSuggestions.innerHTML = "";


    results.forEach(place => {

        const button =
            document.createElement("button");


        button.type = "button";

        button.className =
            "location-suggestion";


        const locationParts = [];


        if (place.admin1) {

            locationParts.push(
                place.admin1
            );

        }


        if (place.admin2) {

            locationParts.push(
                place.admin2
            );

        }


        if (place.country) {

            locationParts.push(
                place.country
            );

        }


        button.innerHTML = `

            <span class="location-suggestion-icon">

                <i class="fa-solid fa-location-dot"></i>

            </span>


            <span class="location-suggestion-text">

                <span class="location-suggestion-name">

                    ${place.name}

                </span>


                <span class="location-suggestion-details">

                    ${locationParts.join(", ")}

                </span>

            </span>

        `;


        button.addEventListener(
            "click",
            function () {

                selectLocation(place);

            }
        );


        locationSuggestions.appendChild(
            button
        );

    });


    locationSuggestions.classList.add(
        "show"
    );

}



/* ---------------------------------------------------------
   Select Location
--------------------------------------------------------- */

function selectLocation(place) {

    selectedLocation = place;


    locationInput.value =
        buildLocationName(place);


    hideLocationSuggestions();

}



/* ---------------------------------------------------------
   Build Location Name
--------------------------------------------------------- */

function buildLocationName(place) {

    const parts = [];


    if (place.name) {

        parts.push(
            place.name
        );

    }


    if (place.admin1) {

        parts.push(
            place.admin1
        );

    }


    if (place.country) {

        parts.push(
            place.country
        );

    }


    return parts.join(", ");

}



/* ---------------------------------------------------------
   Hide Suggestions
--------------------------------------------------------- */

function hideLocationSuggestions() {

    if (!locationSuggestions) {
        return;
    }


    locationSuggestions.classList.remove(
        "show"
    );


    locationSuggestions.innerHTML = "";

}



/* ---------------------------------------------------------
   Suggestion Message
--------------------------------------------------------- */

function showSuggestionMessage(message) {

    if (!locationSuggestions) {
        return;
    }


    locationSuggestions.innerHTML = `

        <div class="location-suggestions-message">

            ${message}

        </div>

    `;


    locationSuggestions.classList.add(
        "show"
    );

}



/* =========================================================
   SEARCH BUTTON
========================================================= */

if (weatherSearchBtn) {

    weatherSearchBtn.addEventListener(
        "click",
        function () {

            const location =
                locationInput.value.trim();


            if (!location) {

                alert(
                    "Please enter a location."
                );

                return;

            }


            hideLocationSuggestions();


            // If user selected an autocomplete result

            if (selectedLocation) {

                getWeather(

                    selectedLocation.latitude,

                    selectedLocation.longitude,

                    buildLocationName(
                        selectedLocation
                    )

                );

            }

            // Otherwise perform a Philippine
            // location search.

            else {

                searchLocation(
                    location
                );

            }

        }
    );

}



/* =========================================================
   ENTER KEY SEARCH
========================================================= */

if (locationInput) {

    locationInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key !== "Enter") {
                return;
            }


            event.preventDefault();


            const location =
                locationInput.value.trim();


            if (!location) {
                return;
            }


            hideLocationSuggestions();


            if (selectedLocation) {

                getWeather(

                    selectedLocation.latitude,

                    selectedLocation.longitude,

                    buildLocationName(
                        selectedLocation
                    )

                );

            }

            else {

                searchLocation(
                    location
                );

            }

        }
    );

}



/* ---------------------------------------------------------
   Close Suggestions When Clicking Outside
--------------------------------------------------------- */

document.addEventListener(
    "click",
    function (event) {

        if (
            locationSuggestions &&
            !event.target.closest(
                ".location-search-wrapper"
            )
        ) {

            hideLocationSuggestions();

        }

    }
);



/* =========================================================
   SEARCH LOCATION
========================================================= */

async function searchLocation(location) {

    try {

        weatherSearchBtn.disabled = true;


        weatherSearchBtn.innerHTML =

            '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';



        const response = await fetch(

            `https://geocoding-api.open-meteo.com/v1/search?` +

            `name=${encodeURIComponent(location)}` +

            `&count=1` +

            `&language=en` +

            `&countryCode=PH` +

            `&format=json`

        );


        if (!response.ok) {

            throw new Error(
                "Unable to search for location."
            );

        }


        const data =
            await response.json();


        if (
            !data.results ||
            data.results.length === 0
        ) {

            alert(
                "Location not found. Please try another Philippine location."
            );

            return;

        }


        const place =
            data.results[0];


        await getWeather(

            place.latitude,

            place.longitude,

            buildLocationName(place)

        );


    }

    catch (error) {

        console.error(
            "Location search error:",
            error
        );


        alert(
            "Something went wrong while searching for the location."
        );

    }

    finally {

        weatherSearchBtn.disabled = false;


        weatherSearchBtn.innerHTML =

            '<i class="fa-solid fa-magnifying-glass"></i> Search';

    }

}

/* ---------------------------------------------------------
   Use My Location
--------------------------------------------------------- */

if (useLocationBtn) {

    useLocationBtn.addEventListener("click", function () {

        if (!navigator.geolocation) {

            alert(
                "Geolocation is not supported by your browser."
            );

            return;
        }


        /* -------------------------------------------------
           Button Loading State
        ------------------------------------------------- */

        useLocationBtn.disabled = true;

        useLocationBtn.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Detecting Location...';


        /* -------------------------------------------------
           Get Browser Location
        ------------------------------------------------- */

        navigator.geolocation.getCurrentPosition(

            async function (position) {

                const latitude =
                    position.coords.latitude;

                const longitude =
                    position.coords.longitude;


                console.log(
                    "Detected coordinates:",
                    latitude,
                    longitude
                );


                try {

                    /* -------------------------------------
                       Reverse Geocoding
                       Convert coordinates into a
                       Philippine location name
                    ------------------------------------- */

                    const response = await fetch(

                        `https://geocoding-api.open-meteo.com/v1/reverse?` +
                        `latitude=${latitude}` +
                        `&longitude=${longitude}` +
                        `&language=en` +
                        `&format=json`

                    );


                    let locationName =
                        "Your Current Location";


                    if (response.ok) {

                        const data =
                            await response.json();


                        if (
                            data.results &&
                            data.results.length > 0
                        ) {

                            const place =
                                data.results[0];


                            locationName =
                                buildLocationName(place);


                            console.log(
                                "Detected place:",
                                place
                            );

                        }

                    }


                    /* -------------------------------------
                       Put detected location into search box
                    ------------------------------------- */

                    if (locationInput) {

                        locationInput.value =
                            locationName;

                    }


                    /* -------------------------------------
                       Get Weather
                    ------------------------------------- */

                    await getWeather(

                        latitude,
                        longitude,

                        locationName

                    );


                    /* -------------------------------------
                       Success Button State
                    ------------------------------------- */

                    useLocationBtn.innerHTML =
                        '<i class="fa-solid fa-circle-check"></i> Location Detected';


                    useLocationBtn.classList.add(
                        "location-detected"
                    );


                    /* -------------------------------------
                       Return button to normal after 3 sec
                    ------------------------------------- */

                    setTimeout(function () {

                        useLocationBtn.innerHTML =
                            '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';

                        useLocationBtn.classList.remove(
                            "location-detected"
                        );

                    }, 3000);


                } catch (error) {

                    console.error(
                        "Location weather error:",
                        error
                    );


                    /* -------------------------------------
                       If reverse geocoding fails,
                       weather can still use coordinates
                    ------------------------------------- */

                    await getWeather(

                        latitude,
                        longitude,

                        "Your Current Location"

                    );


                    useLocationBtn.innerHTML =
                        '<i class="fa-solid fa-circle-check"></i> Weather Loaded';


                    setTimeout(function () {

                        useLocationBtn.innerHTML =
                            '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';

                    }, 3000);

                }


                useLocationBtn.disabled = false;

            },


            /* -------------------------------------------------
               Location Error
            ------------------------------------------------- */

            function (error) {

                console.error(
                    "Geolocation error:",
                    error
                );


                useLocationBtn.disabled = false;


                useLocationBtn.innerHTML =
                    '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';


                switch (error.code) {

                    case error.PERMISSION_DENIED:

                        alert(
                            "Location permission was denied. " +
                            "Please allow location access in your browser settings."
                        );

                        break;


                    case error.POSITION_UNAVAILABLE:

                        alert(
                            "Your location could not be determined. " +
                            "Please try again."
                        );

                        break;


                    case error.TIMEOUT:

                        alert(
                            "Location request timed out. " +
                            "Please try again."
                        );

                        break;


                    default:

                        alert(
                            "Unable to determine your location."
                        );

                }

            },


            /* -------------------------------------------------
               Geolocation Options
            ------------------------------------------------- */

            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            }

        );

    });

}



/* =========================================================
   GET WEATHER DATA
========================================================= */

async function getWeather(
    latitude,
    longitude,
    locationName
) {

    try {

        const weatherURL =

            `https://api.open-meteo.com/v1/forecast` +

            `?latitude=${latitude}` +

            `&longitude=${longitude}` +

            `&current=` +

            `temperature_2m,` +
            `relative_humidity_2m,` +
            `precipitation,` +
            `weather_code,` +
            `wind_speed_10m` +

            `&daily=` +

            `weather_code,` +
            `temperature_2m_max,` +
            `temperature_2m_min,` +
            `precipitation_sum` +

            `&timezone=auto` +

            `&forecast_days=7`;



        const response =
            await fetch(weatherURL);


        if (!response.ok) {

            throw new Error(
                "Weather request failed."
            );

        }


        const data =
            await response.json();


        console.log(
            "Weather data:",
            data
        );


        updateCurrentWeather(
            data,
            locationName
        );


        updateForecast(
            data
        );


        generateFarmInsight(
            data
        );


    }

    catch (error) {

        console.error(
            "Weather error:",
            error
        );


        alert(
            "Unable to load weather data. Please try again."
        );

    }

}



/* =========================================================
   UPDATE CURRENT WEATHER
========================================================= */

function updateCurrentWeather(
    data,
    locationName
) {

    const current =
        data.current;


    document.getElementById(
        "current-location"
    ).textContent =
        locationName;


    document.getElementById(
        "current-temperature"
    ).textContent =
        `${Math.round(
            current.temperature_2m
        )}°`;


    document.getElementById(
        "current-humidity"
    ).textContent =
        `${current.relative_humidity_2m}%`;


    document.getElementById(
        "current-rainfall"
    ).textContent =
        `${current.precipitation} mm`;


    document.getElementById(
        "current-wind"
    ).textContent =
        `${Math.round(
            current.wind_speed_10m
        )} km/h`;


    document.getElementById(
        "current-condition"
    ).textContent =
        getWeatherDescription(
            current.weather_code
        );


    document.getElementById(
        "current-weather-icon"
    ).textContent =
        getWeatherIcon(
            current.weather_code
        );


    const date =
        new Date();


    document.getElementById(
        "current-date"
    ).textContent =

        date.toLocaleDateString(
            "en-PH",
            {
                weekday: "long",
                month: "long",
                day: "numeric"
            }
        );

}



/* =========================================================
   WEATHER CODE → DESCRIPTION
========================================================= */

function getWeatherDescription(code) {

    const weatherCodes = {

        0: "Clear Sky",

        1: "Mainly Clear",

        2: "Partly Cloudy",

        3: "Overcast",

        45: "Fog",

        48: "Rime Fog",

        51: "Light Drizzle",

        53: "Moderate Drizzle",

        55: "Heavy Drizzle",

        61: "Light Rain",

        63: "Moderate Rain",

        65: "Heavy Rain",

        71: "Light Snow",

        73: "Moderate Snow",

        75: "Heavy Snow",

        80: "Light Rain Showers",

        81: "Moderate Rain Showers",

        82: "Heavy Rain Showers",

        95: "Thunderstorm",

        96: "Thunderstorm with Hail",

        99: "Thunderstorm with Heavy Hail"

    };


    return (
        weatherCodes[code] ||
        "Unknown Weather"
    );

}



/* =========================================================
   WEATHER CODE → ICON
========================================================= */

function getWeatherIcon(code) {

    if (code === 0) {
        return "☀️";
    }


    if (code === 1) {
        return "🌤️";
    }


    if (code === 2) {
        return "⛅";
    }


    if (code === 3) {
        return "☁️";
    }


    if ([45, 48].includes(code)) {
        return "🌫️";
    }


    if ([51, 53, 55].includes(code)) {
        return "🌦️";
    }


    if ([61, 63, 65].includes(code)) {
        return "🌧️";
    }


    if ([80, 81, 82].includes(code)) {
        return "🌦️";
    }


    if ([95, 96, 99].includes(code)) {
        return "⛈️";
    }


    return "🌤️";

}



/* =========================================================
   UPDATE 7-DAY FORECAST
========================================================= */

function updateForecast(data) {

    const forecastGrid =
        document.getElementById(
            "forecast-grid"
        );


    const daily =
        data.daily;


    if (!forecastGrid || !daily) {
        return;
    }


    forecastGrid.innerHTML = "";


    for (
        let i = 0;
        i < daily.time.length;
        i++
    ) {

        const date =
            new Date(
                `${daily.time[i]}T00:00:00`
            );


        const dayName =

            i === 0

                ? "Today"

                : date.toLocaleDateString(
                    "en-PH",
                    {
                        weekday: "short"
                    }
                );


        const high =
            Math.round(
                daily.temperature_2m_max[i]
            );


        const low =
            Math.round(
                daily.temperature_2m_min[i]
            );


        const rainfall =
            daily.precipitation_sum[i];


        const icon =
            getWeatherIcon(
                daily.weather_code[i]
            );


        const card =
            document.createElement(
                "div"
            );


        card.className =
            `forecast-card ${i === 0 ? "today" : ""
            }`;


        card.innerHTML = `

            <div class="forecast-day">

                ${dayName}

            </div>


            <div class="forecast-icon">

                ${icon}

            </div>


            <div class="forecast-temperature">

                <span class="forecast-high">

                    ${high}°

                </span>


                <span class="forecast-low">

                    ${low}°

                </span>

            </div>


            <div class="forecast-rain">

                <i class="fa-solid fa-droplet"></i>

                ${rainfall} mm

            </div>

        `;


        forecastGrid.appendChild(
            card
        );

    }

}



/* =========================================================
   FARM WEATHER INSIGHT
========================================================= */

function generateFarmInsight(data) {

    const current =
        data.current;


    const daily =
        data.daily;


    const title =
        document.getElementById(
            "farm-insight-title"
        );


    const text =
        document.getElementById(
            "farm-insight-text"
        );


    if (!title || !text) {
        return;
    }


    const temperature =
        current.temperature_2m;


    const rainfallTomorrow =
        daily.precipitation_sum[1];



    /* Heavy rainfall */

    if (rainfallTomorrow >= 20) {

        title.textContent =
            "Heavy rainfall expected";


        text.textContent =

            "Significant rainfall is expected tomorrow. " +

            "Consider delaying irrigation and outdoor " +

            "farm activities where possible.";


        return;

    }



    /* Hot conditions */

    if (temperature >= 34) {

        title.textContent =
            "High temperature conditions";


        text.textContent =

            "Temperatures are currently high. " +

            "Crops may require additional water, especially " +

            "during periods of limited rainfall.";


        return;

    }



    /* Moderate rainfall */

    if (rainfallTomorrow >= 5) {

        title.textContent =
            "Rain expected tomorrow";


        text.textContent =

            "Rainfall is expected tomorrow. " +

            "You may want to monitor soil moisture " +

            "before scheduling irrigation.";


        return;

    }



    /* Normal conditions */

    title.textContent =
        "Favorable weather conditions";


    text.textContent =

        "Weather conditions currently appear relatively " +

        "favorable for regular farm activities. " +

        "Continue monitoring the forecast for changes.";

}