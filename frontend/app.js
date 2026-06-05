const API_URL = 'https://pofgoyda.onrender.com/api';
let dayChartInstance = null;
let currentWeatherData = null;

const ukrainianCities = [
    "Київ", "Харків", "Одеса", "Дніпро", "Запоріжжя", "Львів", "Кривий Ріг", 
    "Миколаїв", "Вінниця", "Чернігів", "Черкаси", "Хмельницький", "Житомир", 
    "Чернівці", "Суми", "Рівне", "Івано-Франківськ", "Тернопіль", "Луцьк", "Ужгород", "Канів", "Умань"
];

const cityInput = document.getElementById('cityInput');
const citiesDataList = document.getElementById('citiesDataList');
const searchBtn = document.getElementById('searchBtn');
const favoriteBtn = document.getElementById('favoriteBtn');
const errorBox = document.getElementById('errorBox');
const weatherResult = document.getElementById('weatherResult');
const resultCityTitle = document.getElementById('resultCityTitle');
const geoCoords = document.getElementById('geoCoords');
const consTemp = document.getElementById('consTemp');
const consHum = document.getElementById('consHum');
const consWind = document.getElementById('consWind');
const consPress = document.getElementById('consPress');
const providersGrid = document.getElementById('providersGrid');
const daysForecastGrid = document.getElementById('daysForecastGrid');
const favoritesList = document.getElementById('favoritesList');

function initCitiesAutocomplete() {
    citiesDataList.innerHTML = '';
    ukrainianCities.sort().forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        citiesDataList.appendChild(option);
    });
}

function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove('hidden');
    setTimeout(() => errorBox.classList.add('hidden'), 5000);
}

async function getWeather(city) {
    try {
        const response = await fetch(`${API_URL}/weather?city=${encodeURIComponent(city)}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Помилка при отриманні даних');
        }
        currentWeatherData = await response.json();
        renderWeather(currentWeatherData);
    } catch (error) {
        showError(error.message);
    }
}

function renderWeather(data) {
    resultCityTitle.textContent = `Погода в місті ${data.city}`;
    geoCoords.textContent = `📍 Координати: ${data.lat}, ${data.lon}`;
    consTemp.textContent = data.consensus_temperature;
    consHum.textContent = data.consensus_humidity;
    consWind.textContent = data.consensus_wind_speed;
    consPress.textContent = data.consensus_pressure;

    // Рендер карток поточного стану сервісів
    providersGrid.innerHTML = '';
    data.providers.forEach(p => {
        const card = document.createElement('div');
        card.className = 'provider-card';
        card.innerHTML = `
            <h4>${p.provider_name}</h4>
            <p>🌡️ Температура: <strong>${p.temperature}</strong>°C</p>
            <p>💧 Вологість: <strong>${p.humidity}</strong>%</p>
            <p>💨 Вітер: <strong>${p.wind_speed}</strong> м/с</p>
            <p>🌀 Тиск: <strong>${p.pressure}</strong> мм</p>
            <p>☁️ Стан: <strong>${p.condition}</strong></p>
        `;
        providersGrid.appendChild(card);
    });

    // Рендер прогнозу на 5 днів
    daysForecastGrid.innerHTML = '';
    data.daily_forecast.forEach(d => {
        const dCard = document.createElement('div');
        dCard.className = 'day-card';
        dCard.innerHTML = `
            <h4>${d.date}</h4>
            <p>🌡️ <strong>${d.temperature}</strong>°C</p>
            <p>💨 <strong>${d.wind_speed}</strong> м/с</p>
            <p style="font-size:13px; color:#666;">${d.condition}</p>
        `;
        daysForecastGrid.appendChild(dCard);
    });

    // Будуємо дефолтний графік температури по годинах
    switchChart('temp');
    weatherResult.classList.remove('hidden');
}

function switchChart(type) {
    if (!currentWeatherData) return;

    // Перемикання стилю активної кнопки табів
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = event ? event.target : document.querySelector(`[onclick="switchChart('${type}')"]`);
    if (activeBtn) activeBtn.classList.add('active');

    const ctx = document.getElementById('dayChart').getContext('2d');
    const hoursLabels = currentWeatherData.providers[0].hourly.map(h => h.time);

    // Збір лінійних графіків для кожного провайдера
    const datasets = currentWeatherData.providers.map((p, idx) => {
        const colors = ['#3b82f6', '#ef4444', '#10b981'];
        return {
            label: `${p.provider_name}`,
            data: p.hourly.map(h => type === 'temp' ? h.temperature : h.wind_speed),
            borderColor: colors[idx],
            backgroundColor: colors[idx] + '20',
            tension: 0.3,
            fill: true
        };
    });

    if (dayChartInstance) dayChartInstance.destroy();

    dayChartInstance = new Chart(ctx, {
        type: 'line',
        data: { labels: hoursLabels, datasets: datasets },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: type === 'temp' ? 'Зміна температури протягом дня (°C)' : 'Швидкість вітру протягом дня (м/с)' }
            }
        }
    });
}

// Прописуємо глобальну функцію для доступу з HTML onclick атрибутів
window.switchChart = switchChart;

async function loadFavorites() {
    try {
        const response = await fetch(`${API_URL}/favorites`);
        const data = await response.json();
        favoritesList.innerHTML = '';
        data.forEach(city => {
            const tag = document.createElement('div');
            tag.className = 'favorite-tag';
            tag.innerHTML = `<span class="city-clickable">${city.city_name}</span><div class="close-btn">&times;</div>`;
            tag.querySelector('.city-clickable').addEventListener('click', () => { cityInput.value = city.city_name; getWeather(city.city_name); });
            tag.querySelector('.close-btn').addEventListener('click', () => deleteFavorite(city.id));
            favoritesList.appendChild(tag);
        });
    } catch (error) { console.error(error); }
}

async function addFavorite() {
    const city = cityInput.value.trim();
    if (!city) return showError('Введіть назву міста');
    try {
        const response = await fetch(`${API_URL}/favorites`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ city_name: city }) });
        if (!response.ok) throw new Error('Помилка додавання');
        loadFavorites();
    } catch (error) { showError(error.message); }
}

async function deleteFavorite(id) {
    try {
        const response = await fetch(`${API_URL}/favorites/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Помилка вилучення');
        loadFavorites();
    } catch (error) { showError(error.message); }
}

searchBtn.addEventListener('click', () => { const city = cityInput.value.trim(); if (city) getWeather(city); });
favoriteBtn.addEventListener('click', addFavorite);
cityInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { const city = cityInput.value.trim(); if (city) getWeather(city); } });

initCitiesAutocomplete();
loadFavorites();
