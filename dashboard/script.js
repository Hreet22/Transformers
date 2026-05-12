document.addEventListener('DOMContentLoaded', () => {
    // Handle Loading Screen
    setTimeout(() => {
        const loader = document.getElementById('loading-screen');
        if (loader) {
            loader.style.opacity = '0';
            loader.style.visibility = 'hidden';
        }
    }, 1500);

    // Metrics auto-update
    const animateValueChange = (elementId, newValue, isDanger = false) => {
        const el = document.getElementById(elementId);
        if (!el) return;

        el.classList.add(isDanger ? 'flash-danger' : 'flash-update');
        el.textContent = newValue;

        setTimeout(() => {
            el.classList.remove('flash-danger', 'flash-update');
        }, 500);
    };

    let baseTransformers = 1248;
    let baseLoad = 76.4;
    let baseTemp = 42.0;

    setInterval(() => {
        // Transformers fluctuation
        if (Math.random() > 0.6) {
            baseTransformers += Math.floor(Math.random() * 5) - 2;
            animateValueChange('metric-transformers', baseTransformers.toLocaleString());
        }

        // Load fluctuation
        if (Math.random() > 0.4) {
            baseLoad += (Math.random() * 2 - 1);
            baseLoad = Math.max(0, Math.min(100, baseLoad));
            animateValueChange('metric-load', baseLoad.toFixed(1) + '%');

            const trendLoad = document.getElementById('trend-load');
            if (trendLoad) {
                if (baseLoad > 85) {
                    trendLoad.className = 'trend negative';
                    trendLoad.innerHTML = '<i class="fas fa-arrow-up"></i> Critical Load';
                } else {
                    trendLoad.className = 'trend stable';
                    trendLoad.innerHTML = '<i class="fas fa-minus"></i> Optimal';
                }
            }
        }

        // Temp fluctuation
        if (Math.random() > 0.5) {
            baseTemp += (Math.random() * 1.5 - 0.7);
            animateValueChange('metric-temp', baseTemp.toFixed(1) + '°C', baseTemp > 45);
        }

        // Risk Units logic
        if (Math.random() > 0.8) {
            const riskVal = Math.floor(Math.random() * 5) + 12;
            animateValueChange('metric-risk', riskVal, true);

            const cardRisk = document.getElementById('card-risk');
            const iconRisk = document.getElementById('icon-risk');
            const riskTrend = document.getElementById('metric-risk-trend');
            if (cardRisk && iconRisk && riskTrend) {
                if (riskVal > 15) {
                    cardRisk.classList.add('pulse-danger');
                    iconRisk.innerHTML = '<i class="fas fa-radiation"></i>';
                    riskTrend.textContent = 'Critical levels detected';
                } else {
                    cardRisk.classList.remove('pulse-danger');
                    iconRisk.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                    riskTrend.textContent = '3 since last scan';
                }
            }
        }
    }, 3000);
    // Initialize Chart
    const ctx = document.getElementById('canvasChart');

    if (ctx) {
        // Gradient for line chart
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(0, 242, 254, 0.5)');
        gradient.addColorStop(1, 'rgba(0, 242, 254, 0.0)');

        const powerChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
                datasets: [{
                    label: 'Power Generation (MW)',
                    data: [25, 22, 30, 45, 52, 48, 38, 28],
                    borderColor: '#00f2fe',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#0b0f19',
                    pointBorderColor: '#00f2fe',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Grid Load (MW)',
                    data: [15, 12, 28, 42, 45, 43, 48, 30],
                    borderColor: '#ff0844',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: false,
                    pointBackgroundColor: '#0b0f19',
                    pointBorderColor: '#ff0844',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#a0aec0',
                            usePointStyle: true,
                            boxWidth: 8
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(11, 15, 25, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#a0aec0',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#a0aec0'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#a0aec0'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        // Add interaction to controls
        const buttons = document.querySelectorAll('.controls .btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                buttons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');

                // Simulate data update
                const newData = Array.from({ length: 8 }, () => Math.floor(Math.random() * 40) + 15);
                powerChart.data.datasets[0].data = newData;
                powerChart.update();
            });
        });

        // Smoothly refresh chart data to simulate live stream
        setInterval(() => {
            const d1 = powerChart.data.datasets[0].data;
            const d2 = powerChart.data.datasets[1].data;
            d1.shift();
            d2.shift();

            const lastVal1 = d1[d1.length - 1];
            d1.push(lastVal1 + (Math.random() * 6 - 3));

            const lastVal2 = d2[d2.length - 1];
            d2.push(lastVal2 + (Math.random() * 6 - 3));

            powerChart.update('none'); // Update without full animation for smooth streaming
        }, 4000);
    }

    // Initialize 72-Hour Forecast Chart
    const forecastCtx = document.getElementById('forecastChart');
    if (forecastCtx) {
        // Glowing futuristic gradient for forecast
        const forecastGradient = forecastCtx.getContext('2d').createLinearGradient(0, 0, 0, 300);
        forecastGradient.addColorStop(0, 'rgba(129, 140, 248, 0.4)');
        forecastGradient.addColorStop(1, 'rgba(129, 140, 248, 0.0)');

        // Generate fake 72-hour labels
        const forecastLabels = Array.from({ length: 72 }, (_, i) => `+${i + 1}h`);

        // Generate fake load data with a sine wave pattern to look realistic
        const baseLoad = 50;
        const forecastData = Array.from({ length: 72 }, (_, i) => {
            return baseLoad + Math.sin(i / 12 * Math.PI) * 20 + Math.random() * 5;
        });

        new Chart(forecastCtx, {
            type: 'line',
            data: {
                labels: forecastLabels,
                datasets: [
                    {
                        label: 'AI Predicted Load (MW)',
                        data: forecastData,
                        borderColor: '#818cf8',
                        backgroundColor: forecastGradient,
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#020617',
                        pointBorderColor: '#818cf8',
                        pointBorderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#94a3b8',
                            usePointStyle: true,
                            boxWidth: 8,
                            font: { family: 'Poppins' }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(129, 140, 248, 0.3)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxTicksLimit: 12,
                            font: { family: 'Poppins' }
                        },
                        title: {
                            display: true,
                            text: 'Forecast Timeline (Hours)',
                            color: '#94a3b8',
                            font: {
                                family: 'Poppins'
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'Poppins' }
                        },
                        title: {
                            display: true,
                            text: 'Transformer Load (MW)',
                            color: '#94a3b8',
                            font: {
                                family: 'Poppins'
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    // Initialize Leaflet Map
    const mapElement = document.getElementById('gridMap');
    if (mapElement && typeof L !== 'undefined') {
        // Center on Chennai
        const map = L.map('gridMap').setView([13.0827, 80.2707], 11);

        // Dark theme map tiles (CartoDB Dark Matter)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        // Define custom marker icons using HTML
        const createIcon = (statusClass) => {
            return L.divIcon({
                className: 'custom-div-icon',
                html: `<div class="marker-pin ${statusClass}"></div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });
        };

        const icons = {
            low: createIcon('marker-low'),
            medium: createIcon('marker-med'),
            high: createIcon('marker-high')
        };

        // Fake Transformer Data in Chennai
        const transformers = [
            { id: 'TX-1042', lat: 13.0827, lng: 80.2707, load: '45%', status: 'low', risk: 'Optimal' },
            { id: 'TX-2891', lat: 13.0604, lng: 80.2496, load: '88%', status: 'medium', risk: 'Elevated' },
            { id: 'TX-9934', lat: 13.1065, lng: 80.2086, load: '96%', status: 'high', risk: 'Critical Load' },
            { id: 'TX-5510', lat: 13.0418, lng: 80.2335, load: '32%', status: 'low', risk: 'Optimal' },
            { id: 'TX-3209', lat: 13.0203, lng: 80.2750, load: '92%', status: 'high', risk: 'Overheating' },
            { id: 'TX-8841', lat: 13.1143, lng: 80.2835, load: '65%', status: 'low', risk: 'Optimal' }
        ];

        transformers.forEach(t => {
            const marker = L.marker([t.lat, t.lng], { icon: icons[t.status] }).addTo(map);

            // Status colors for popup text
            const statusColors = {
                low: 'var(--success)',
                medium: 'var(--warning)',
                high: 'var(--danger)'
            };

            const popupContent = `
                <h4>Transformer ${t.id}</h4>
                <p><strong>Load:</strong> ${t.load}</p>
                <p><strong>Status:</strong> <span style="color: ${statusColors[t.status]}; font-weight: 600;">${t.risk}</span></p>
            `;

            marker.bindPopup(popupContent);
        });

        // Force map resize once dashboard is loaded
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
    }

    // Live AI Alert Feed
    const alertFeed = document.getElementById('liveAlertsFeed');
    const alertBadge = document.getElementById('alertBadge');

    if (alertFeed && alertBadge) {
        // Fake JSON alert data
        const alertTypes = [
            { type: 'critical', icon: 'fa-radiation', title: 'Overload Prediction', desc: 'Substation Alpha capacity reaching 98%. Re-routing advised.' },
            { type: 'warning', icon: 'fa-temperature-high', title: 'High Temperature', desc: 'Transformer TX-3209 operating at 85°C. Cooling systems activated.' },
            { type: 'critical', icon: 'fa-bolt', title: 'Transformer Instability', desc: 'Voltage fluctuations detected in Sector 7 grid.' },
            { type: 'warning', icon: 'fa-exclamation-triangle', title: 'Possible Failure Detection', desc: 'Anomalous vibration patterns in generator unit B.' }
        ];

        let alertCount = 0;

        const addAlert = () => {
            const alertData = alertTypes[Math.floor(Math.random() * alertTypes.length)];

            const li = document.createElement('li');
            li.className = `alert ${alertData.type} alert-item-enter`;
            li.innerHTML = `
                <i class="fas ${alertData.icon}"></i>
                <div class="alert-details">
                    <h4>${alertData.title}</h4>
                    <p>${alertData.desc}</p>
                </div>
                <span class="time">Just now</span>
            `;

            // Insert at the top
            alertFeed.insertBefore(li, alertFeed.firstChild);

            // Update badge
            alertCount++;
            alertBadge.textContent = `${alertCount} New`;

            // Remove oldest if more than 4 alerts
            if (alertFeed.children.length > 4) {
                const lastChild = alertFeed.lastChild;
                lastChild.style.opacity = '0';
                lastChild.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    if (alertFeed.contains(lastChild)) {
                        alertFeed.removeChild(lastChild);
                    }
                }, 300);
            }
        };

        // Add initial alerts
        addAlert();
        setTimeout(addAlert, 1500);

        // Add new alert every 8-15 seconds
        setInterval(() => {
            addAlert();
        }, Math.floor(Math.random() * 7000) + 8000);
    }

    // AI Insights Terminal Logic
    const aiTerminal = document.getElementById('aiTerminal');
    const aiStatusBadge = document.getElementById('aiStatusBadge');

    if (aiTerminal) {
        const insights = [
            "> Analyzing grid load patterns... <span class='highlight-text'>[OK]</span>",
            "> <span class='warning-text'>WARNING:</span> Predicted overload in Sector 4 within 2 hours. Suggesting proactive load redistribution.",
            "> Optimizing routing for Substation Alpha... Efficiency improved by <span class='highlight-text'>4.2%</span>.",
            "> <span class='critical-text'>MAINTENANCE REQUIRED:</span> Transformer TX-3209 showing anomalous vibration signatures.",
            "> Peak-hour optimization protocol engaged. Activating secondary battery storage reserves.",
            "> Weather data imported. Expecting 15% drop in solar generation due to cloud cover. Adjusting grid dependency.",
            "> Running anomaly detection... <span class='highlight-text'>No new critical anomalies detected.</span>"
        ];

        let insightIndex = 0;

        // Setup initial cursor
        aiTerminal.innerHTML = '<span class="cursor" id="typingCursor"></span>';

        const typeInsightAdvanced = async (htmlString) => {
            return new Promise((resolve) => {
                const p = document.createElement('p');
                const cursor = document.getElementById('typingCursor');
                aiTerminal.insertBefore(p, cursor);

                let i = 0;
                let isTag = false;
                let text = '';

                // Change badge status to writing
                if (aiStatusBadge) aiStatusBadge.innerHTML = '<i class="fas fa-terminal" style="margin-right: 0.4rem;"></i> Writing...';

                const typeChar = () => {
                    if (i < htmlString.length) {
                        if (htmlString.charAt(i) === '<') isTag = true;
                        text += htmlString.charAt(i);
                        if (htmlString.charAt(i) === '>') isTag = false;
                        i++;

                        if (isTag) {
                            typeChar(); // Skip typing animation delay for HTML tags
                        } else {
                            p.innerHTML = text;
                            aiTerminal.scrollTop = aiTerminal.scrollHeight;
                            setTimeout(typeChar, Math.random() * 30 + 10); // 10-40ms per char
                        }
                    } else {
                        // Finished typing
                        if (aiStatusBadge) aiStatusBadge.innerHTML = '<i class="fas fa-sync-alt fa-spin" style="margin-right: 0.4rem;"></i> Analyzing';
                        setTimeout(resolve, 3000 + Math.random() * 2000);
                    }
                };

                typeChar();
            });
        };

        const runInsights = async () => {
            while (true) {
                await typeInsightAdvanced(insights[insightIndex]);
                insightIndex = (insightIndex + 1) % insights.length;

                // Clear old messages if too many (keeping cursor at the end)
                if (aiTerminal.children.length > 8) {
                    aiTerminal.removeChild(aiTerminal.firstChild);
                }
            }
        };

        // Start typing loop
        setTimeout(runInsights, 1500);
    }

    // Scroll Spy for Navbar
    const sections = document.querySelectorAll('header[id], section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -70% 0px', // Trigger when section is around top of viewport
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${id}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, observerOptions);

    sections.forEach(section => {
        observer.observe(section);
    });

    // Theme Toggle Logic
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                document.documentElement.classList.add('light-theme');
            } else {
                document.documentElement.classList.remove('light-theme');
            }
        });
    }
});
