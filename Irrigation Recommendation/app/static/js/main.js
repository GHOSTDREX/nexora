/**
 * SMART AGRICULTURE AI - PRECISION IRRIGATION & AI AGRONOMIST
 * Interactive Dashboard Logic & Real-Time AI Chat Assistant
 */

let radarChart = null;
let featureChart = null;
let sampleScenariosData = {};
let currentPredictionResult = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSliderSync();
    initFormSubmit();
    initDropzone();
    initChatWidget();
    loadScenariosData();
    loadModelAnalytics();

    // Trigger initial prediction on page load
    triggerPrediction();
});

/* ==========================================================================
   1. Tab Navigation Logic
   ========================================================================== */
function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const targetId = `pane-${tab.dataset.tab}`;
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });
}

/* ==========================================================================
   2. Slider-Value Display Sync
   ========================================================================== */
function initSliderSync() {
    const sliders = document.querySelectorAll('.input-slider');
    sliders.forEach(slider => {
        const display = document.getElementById(`val-${slider.id}`);
        if (display) {
            slider.addEventListener('input', (e) => {
                display.innerText = e.target.value;
            });
        }
    });
}

/* ==========================================================================
   3. Single Field Form Predictor
   ========================================================================== */
function initFormSubmit() {
    const form = document.getElementById('irrigation-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        triggerPrediction();
    });
}

function getFormData() {
    return {
        Soil_Type: document.getElementById('Soil_Type').value,
        Soil_Moisture: parseFloat(document.getElementById('Soil_Moisture').value),
        Soil_pH: parseFloat(document.getElementById('Soil_pH').value),
        Organic_Carbon: parseFloat(document.getElementById('Organic_Carbon').value),
        Electrical_Conductivity: parseFloat(document.getElementById('Electrical_Conductivity').value),
        Temperature_C: parseFloat(document.getElementById('Temperature_C').value),
        Humidity: parseFloat(document.getElementById('Humidity').value),
        Rainfall_mm: parseFloat(document.getElementById('Rainfall_mm').value),
        Sunlight_Hours: parseFloat(document.getElementById('Sunlight_Hours').value),
        Wind_Speed_kmh: parseFloat(document.getElementById('Wind_Speed_kmh').value),
        Crop_Type: document.getElementById('Crop_Type').value,
        Crop_Growth_Stage: document.getElementById('Crop_Growth_Stage').value,
        Season: document.getElementById('Season').value,
        Field_Area_hectare: parseFloat(document.getElementById('Field_Area_hectare').value),
        Mulching_Used: document.getElementById('Mulching_Used').value,
        Region: document.getElementById('Region').value
    };
}

async function triggerPrediction() {
    const payload = getFormData();
    const btn = document.getElementById('btn-submit-predict');
    if (btn) btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Calculating...`;

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (result.status === 'success') {
            currentPredictionResult = result;
            renderPredictionResults(result, payload);
        } else {
            alert(`Prediction error: ${result.message}`);
        }
    } catch (err) {
        console.error('Error fetching prediction:', err);
    } finally {
        if (btn) btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Calculate Recommendation`;
    }
}

/* ==========================================================================
   4. Render Prediction Results & Radar Chart
   ========================================================================== */
function renderPredictionResults(res, inputs) {
    const card = document.getElementById('result-badge-container');
    const predText = document.getElementById('res-prediction-text');
    const badgeIcon = document.getElementById('res-badge-icon');
    const statusMsg = document.getElementById('res-status-msg');

    const predClass = res.prediction; // Low, Medium, High
    predText.innerText = predClass.toUpperCase();
    statusMsg.innerText = res.status_message;
    document.getElementById('res-confidence').innerHTML = `<i class="fa-solid fa-shield-check"></i> ${res.confidence}% Model Confidence`;

    // State class styling
    card.classList.remove('state-low', 'state-medium', 'state-high');
    if (predClass === 'High') {
        card.classList.add('state-high');
        badgeIcon.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i>`;
    } else if (predClass === 'Medium') {
        card.classList.add('state-medium');
        badgeIcon.innerHTML = `<i class="fa-solid fa-water-ladder"></i>`;
    } else {
        card.classList.add('state-low');
        badgeIcon.innerHTML = `<i class="fa-solid fa-leaf"></i>`;
    }

    // Probability Bars
    const probs = res.probabilities || { Low: 0, Medium: 0, High: 0 };
    document.getElementById('prob-bar-low').style.width = `${probs.Low || 0}%`;
    document.getElementById('prob-val-low').innerText = `${probs.Low || 0}%`;

    document.getElementById('prob-bar-medium').style.width = `${probs.Medium || 0}%`;
    document.getElementById('prob-val-medium').innerText = `${probs.Medium || 0}%`;

    document.getElementById('prob-bar-high').style.width = `${probs.High || 0}%`;
    document.getElementById('prob-val-high').innerText = `${probs.High || 0}%`;

    // Action Plan
    document.getElementById('res-timing').innerText = res.optimal_timing;
    document.getElementById('res-timing-note').innerText = res.timing_note;
    document.getElementById('res-rec-method').innerText = res.recommended_method;

    // Agronomic Alerts
    const alertsContainer = document.getElementById('res-alerts-list');
    alertsContainer.innerHTML = '';
    if (res.agronomic_alerts && res.agronomic_alerts.length > 0) {
        res.agronomic_alerts.forEach(alertText => {
            const div = document.createElement('div');
            div.className = 'alert-item';
            div.innerHTML = `<i class="fa-solid fa-lightbulb"></i> ${alertText}`;
            alertsContainer.appendChild(div);
        });
    }

    // Update Radar Chart
    updateRadarChart(inputs, res);
}

function updateRadarChart(inputs, res) {
    const ctx = document.getElementById('sensorRadarChart').getContext('2d');
    
    const currentValues = [
        Math.min(100, (inputs.Soil_Moisture / 70) * 100),
        Math.min(100, (inputs.Temperature_C / 45) * 100),
        Math.min(100, inputs.Humidity),
        Math.min(100, ((inputs.Soil_pH - 4) / 5) * 100),
        Math.min(100, (inputs.Organic_Carbon / 2.0) * 100),
        Math.min(100, (inputs.Rainfall_mm / 2500) * 100)
    ];

    const targetValues = [
        Math.min(100, (res.target_moisture_pct / 70) * 100),
        55, 60, 50, 50, 40
    ];

    if (radarChart) {
        radarChart.data.datasets[0].data = currentValues;
        radarChart.data.datasets[1].data = targetValues;
        radarChart.update();
    } else {
        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Soil Moisture', 'Temperature', 'Humidity', 'Soil pH', 'Organic Carbon', 'Rainfall'],
                datasets: [
                    {
                        label: 'Current Field Value',
                        data: currentValues,
                        backgroundColor: 'rgba(6, 182, 212, 0.25)',
                        borderColor: '#06b6d4',
                        borderWidth: 2,
                        pointBackgroundColor: '#06b6d4'
                    },
                    {
                        label: 'Optimal Benchmark',
                        data: targetValues,
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        borderColor: '#10b981',
                        borderWidth: 2,
                        pointBackgroundColor: '#10b981',
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#9ca3af', font: { size: 11, family: 'Inter' } },
                        ticks: { display: false, max: 100 }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#f3f4f6', font: { family: 'Inter', size: 12 } } }
                }
            }
        });
    }
}

/* ==========================================================================
   5. AI Agronomist Chat Widget Handler
   ========================================================================== */
function initChatWidget() {
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const closeBtn = document.getElementById('chat-close-btn');
    const chatDrawer = document.getElementById('chat-drawer');
    const form = document.getElementById('chat-input-form');
    const input = document.getElementById('chat-input-text');

    if (!toggleBtn || !chatDrawer) return;

    toggleBtn.addEventListener('click', () => {
        chatDrawer.classList.toggle('hidden');
        if (!chatDrawer.classList.contains('hidden')) {
            input.focus();
        }
    });

    closeBtn.addEventListener('click', () => {
        chatDrawer.classList.add('hidden');
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (text) {
            sendChatMessage(text);
            input.value = '';
        }
    });
}

function sendPrompt(promptText) {
    const chatDrawer = document.getElementById('chat-drawer');
    if (chatDrawer.classList.contains('hidden')) {
        chatDrawer.classList.remove('hidden');
    }
    sendChatMessage(promptText);
}

async function sendChatMessage(queryText) {
    const msgArea = document.getElementById('chat-messages-area');

    // Append User Message
    appendMessage('user', queryText);

    // Append Agent Loading Indicator
    const loadingId = appendMessage('agent', '<em>Thinking...</em>');

    const inputs = getFormData();
    const predInfo = currentPredictionResult || { prediction: 'Medium', confidence: 100 };

    try {
        const response = await fetch('http://127.0.0.1:8000/api/v1/agent/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_query: queryText,
                farm_id: 'FARM_001',
                sensor_data: {
                    soil_moisture: inputs.Soil_Moisture,
                    temperature: inputs.Temperature_C,
                    humidity: inputs.Humidity,
                    rainfall: inputs.Rainfall_mm,
                    sunlight: inputs.Sunlight_Hours,
                    wind_speed: inputs.Wind_Speed_kmh
                },
                farm_data: {
                    soil_type: inputs.Soil_Type,
                    soil_ph: inputs.Soil_pH,
                    organic_carbon: inputs.Organic_Carbon,
                    electrical_conductivity: inputs.Electrical_Conductivity,
                    crop_type: inputs.Crop_Type,
                    crop_growth_stage: inputs.Crop_Growth_Stage,
                    season: inputs.Season,
                    field_area_hectare: inputs.Field_Area_hectare,
                    mulching_used: inputs.Mulching_Used,
                    region: inputs.Region
                },
                prediction_info: {
                    prediction: predInfo.prediction,
                    confidence: predInfo.confidence
                }
            })
        });

        const json = await response.json();
        const loadingElem = document.getElementById(loadingId);

        if (json.status === 'success' && json.agent_response) {
            const resp = json.agent_response;
            let formattedHtml = resp.response.replace(/\n/g, '<br>');

            if (resp.action_bullets && resp.action_bullets.length > 0) {
                formattedHtml += '<br><br><strong>Action Steps:</strong><ul style="margin-left:16px; margin-top:4px;">';
                resp.action_bullets.forEach(b => {
                    formattedHtml += `<li>${b}</li>`;
                });
                formattedHtml += '</ul>';
            }

            loadingElem.querySelector('.msg-bubble').innerHTML = formattedHtml;
        } else {
            loadingElem.querySelector('.msg-bubble').innerText = 'Sorry, I encountered an issue analyzing your field context. Please try again.';
        }
    } catch (e) {
        console.error('Chat API Error:', e);
        const loadingElem = document.getElementById(loadingId);
        if (loadingElem) {
            // Local fallback agent response if FastAPI backend port 8000 is not reachable
            loadingElem.querySelector('.msg-bubble').innerHTML = `🌾 **AI Agronomist Context Response:**<br>Current soil moisture is <strong>${inputs.Soil_Moisture}%</strong> for <strong>${inputs.Crop_Type}</strong> (${inputs.Crop_Growth_Stage} stage). Model predicts <strong>${predInfo.prediction} Irrigation Need</strong> (${predInfo.confidence}% confidence).<br><br><strong>Suggestion:</strong> Water during Early Morning (5:00-8:00 AM) to minimize evapotranspiration.`;
        }
    }

    msgArea.scrollTop = msgArea.scrollHeight;
}

function appendMessage(sender, text) {
    const msgArea = document.getElementById('chat-messages-area');
    const msgDiv = document.createElement('div');
    const msgId = `msg-${Date.now()}-${Math.floor(Math.random()*1000)}`;
    msgDiv.id = msgId;
    msgDiv.className = `chat-msg msg-${sender}`;

    msgDiv.innerHTML = `<div class="msg-bubble">${text}</div>`;
    msgArea.appendChild(msgDiv);
    msgArea.scrollTop = msgArea.scrollHeight;
    return msgId;
}

/* ==========================================================================
   6. Client Preset Scenarios Handler
   ========================================================================== */
async function loadScenariosData() {
    try {
        const res = await fetch('/api/scenarios');
        const json = await res.json();
        if (json.status === 'success') {
            sampleScenariosData = json.scenarios;
        }
    } catch (e) {
        console.error('Failed to load scenarios', e);
    }
}

function loadScenario(presetKey) {
    if (!sampleScenariosData[presetKey]) return;
    const data = sampleScenariosData[presetKey].data;

    Object.keys(data).forEach(key => {
        const elem = document.getElementById(key);
        if (elem) {
            elem.value = data[key];
            const disp = document.getElementById(`val-${key}`);
            if (disp) disp.innerText = data[key];
        }
    });

    triggerPrediction();
}

/* ==========================================================================
   7. Batch CSV Upload Logic
   ========================================================================== */
function initDropzone() {
    const dropzone = document.getElementById('csv-dropzone');
    const fileInput = document.getElementById('csv-file-input');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '#10b981';
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.style.borderColor = 'rgba(255, 255, 255, 0.15)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'rgba(255, 255, 255, 0.15)';
        if (e.dataTransfer.files.length > 0) {
            uploadCSVFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadCSVFile(e.target.files[0]);
        }
    });
}

async function uploadCSVFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/batch-predict', {
            method: 'POST',
            body: formData
        });
        const json = await res.json();
        if (json.status === 'success') {
            renderBatchResults(json);
        } else {
            alert(`CSV Error: ${json.message}`);
        }
    } catch (err) {
        console.error('Batch upload error:', err);
    }
}

function renderBatchResults(data) {
    document.getElementById('batch-summary').classList.remove('hidden');
    document.getElementById('batch-table-container').classList.remove('hidden');

    document.getElementById('batch-count-total').innerText = data.total_records;
    document.getElementById('batch-count-low').innerText = data.summary.Low || 0;
    document.getElementById('batch-count-medium').innerText = data.summary.Medium || 0;
    document.getElementById('batch-count-high').innerText = data.summary.High || 0;

    const tbody = document.querySelector('#batch-results-table tbody');
    tbody.innerHTML = '';

    data.results.forEach(row => {
        const tr = document.createElement('tr');
        const badgeClass = row.prediction === 'High' ? 'text-high' : row.prediction === 'Medium' ? 'text-medium' : 'text-low';
        tr.innerHTML = `
            <td>${row.record_index}</td>
            <td><strong>${row.crop}</strong></td>
            <td>${row.soil_drainage} Soil</td>
            <td>${row.current_moisture_pct}%</td>
            <td>-</td>
            <td>-</td>
            <td>${row.field_area_ha} ha</td>
            <td class="${badgeClass}"><strong>${row.prediction.toUpperCase()}</strong></td>
            <td>${row.confidence}%</td>
        `;
        tbody.appendChild(tr);
    });
}

function downloadSampleCSV() {
    const sampleContent = `Soil_Type,Soil_pH,Soil_Moisture,Organic_Carbon,Electrical_Conductivity,Temperature_C,Humidity,Rainfall_mm,Sunlight_Hours,Wind_Speed_kmh,Crop_Type,Crop_Growth_Stage,Season,Field_Area_hectare,Mulching_Used,Region
Clay,6.1,36.5,0.42,2.17,21.9,31.2,1167.7,4.0,2.0,Wheat,Vegetative,Rabi,4.7,Yes,South
Silt,6.4,12.5,0.38,0.23,36.5,26.0,831.3,10.7,16.8,Maize,Flowering,Zaid,12.2,Yes,Central
Sandy,7.7,11.0,1.09,2.18,41.8,26.4,184.4,7.7,19.0,Cotton,Flowering,Zaid,5.5,No,West
Loamy,6.5,45.0,1.10,1.10,24.0,65.0,1400.0,8.0,9.0,Rice,Flowering,Kharif,3.0,Yes,North`;

    const blob = new Blob([sampleContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'smart_agri_sample_sensors.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

/* ==========================================================================
   8. Model Analytics Tab Loader
   ========================================================================== */
async function loadModelAnalytics() {
    try {
        const ctx = document.getElementById('featureImportanceChart').getContext('2d');

        const features = [
            'Temperature_C', 'Wind_Speed_kmh', 'Soil_Moisture', 'Rainfall_mm',
            'Crop_Stage_Vegetative', 'Mulching_Used_Yes', 'Mulching_Used_No',
            'Crop_Stage_Flowering', 'Crop_Stage_Harvest', 'Crop_Stage_Sowing'
        ];
        const importances = [16.34, 16.05, 15.40, 14.56, 9.75, 8.74, 7.33, 5.77, 3.57, 2.33];

        featureChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: features,
                datasets: [{
                    label: 'Gini Feature Importance (%)',
                    data: importances,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.08)' },
                        ticks: { color: '#9ca3af' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#f3f4f6', font: { family: 'Inter', size: 12 } }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    } catch (e) {
        console.error('Error initializing feature importance chart', e);
    }
}
