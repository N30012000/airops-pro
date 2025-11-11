# 🗄️ AirOps Pro - Database Schema & API Integration

## Complete Database Schema

### 1. Core Tables

```sql
-- ============================================================================
-- Airlines Master Table
-- ============================================================================
CREATE TABLE airlines (
  code VARCHAR(10) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  display_name VARCHAR(150),
  hq_location VARCHAR(100),
  website VARCHAR(255),
  logo_url VARCHAR(255),
  fleet_size INT,
  daily_flights INT,
  operational_regions TEXT[],
  status VARCHAR(20) DEFAULT 'active', -- active, inactive, pending
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Flights Operational Data
-- ============================================================================
CREATE TABLE flights (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  flight_number VARCHAR(10) NOT NULL,
  aircraft_id VARCHAR(10),
  aircraft_type VARCHAR(50),
  
  -- Route & Timing
  departure_airport VARCHAR(5),
  arrival_airport VARCHAR(5),
  route VARCHAR(20),
  
  scheduled_departure TIMESTAMP,
  scheduled_arrival TIMESTAMP,
  actual_departure TIMESTAMP,
  actual_arrival TIMESTAMP,
  
  -- Performance Metrics
  delay_minutes INT,
  delay_reason VARCHAR(100),
  cancelled BOOLEAN DEFAULT FALSE,
  on_time BOOLEAN,
  
  -- Capacity
  total_seats INT,
  passengers INT,
  load_factor DECIMAL(5,2),
  
  -- Revenue
  revenue DECIMAL(15,2),
  yield DECIMAL(15,2),
  
  status VARCHAR(20), -- scheduled, delayed, departed, arrived, cancelled
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_flights_airline ON flights(airline_code);
CREATE INDEX idx_flights_date ON flights(scheduled_departure);
CREATE INDEX idx_flights_route ON flights(departure_airport, arrival_airport);

-- ============================================================================
-- Aircraft Management
-- ============================================================================
CREATE TABLE aircraft (
  id VARCHAR(10) PRIMARY KEY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  aircraft_type VARCHAR(50),
  manufacturer VARCHAR(50),
  model VARCHAR(50),
  
  -- Capacity
  total_seats INT,
  economy_seats INT,
  business_seats INT,
  
  -- Status
  status VARCHAR(20), -- active, maintenance, retired
  
  -- Maintenance
  total_flight_hours DECIMAL(10,1),
  total_cycles INT,
  last_maintenance_date DATE,
  next_maintenance_due DATE,
  airworthiness_certificate_valid_until DATE,
  
  health_score INT DEFAULT 100, -- 0-100
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_aircraft_airline ON aircraft(airline_code);
CREATE INDEX idx_aircraft_status ON aircraft(status);

-- ============================================================================
-- Maintenance Records
-- ============================================================================
CREATE TABLE maintenance (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  aircraft_id VARCHAR(10) REFERENCES aircraft(id),
  
  maintenance_type VARCHAR(50), -- A-Check, C-Check, Heavy, Repair, Inspection
  component VARCHAR(100),
  description TEXT,
  
  severity VARCHAR(20), -- low, medium, high, critical
  status VARCHAR(20), -- scheduled, in_progress, completed, deferred
  
  scheduled_start DATE,
  scheduled_end DATE,
  actual_start DATE,
  actual_end DATE,
  
  duration_hours DECIMAL(8,2),
  estimated_cost DECIMAL(15,2),
  actual_cost DECIMAL(15,2),
  
  technician_id VARCHAR(20),
  technician_name VARCHAR(100),
  approval_status VARCHAR(20), -- pending, approved, rejected
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_maintenance_airline ON maintenance(airline_code);
CREATE INDEX idx_maintenance_aircraft ON maintenance(aircraft_id);
CREATE INDEX idx_maintenance_status ON maintenance(status);

-- ============================================================================
-- Crew Management
-- ============================================================================
CREATE TABLE crew (
  id VARCHAR(20) PRIMARY KEY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  
  full_name VARCHAR(100),
  email VARCHAR(100),
  phone VARCHAR(20),
  
  role VARCHAR(50), -- Captain, First Officer, Purser, Flight Attendant
  license_number VARCHAR(50),
  license_valid_until DATE,
  
  status VARCHAR(20), -- active, on_leave, medical, retired
  seniority_date DATE,
  
  total_flight_hours INT,
  total_flights INT,
  
  current_fatigue_index DECIMAL(3,1), -- 0-10 scale
  rest_hours_required INT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_crew_airline ON crew(airline_code);
CREATE INDEX idx_crew_status ON crew(status);

-- ============================================================================
-- Crew Assignments
-- ============================================================================
CREATE TABLE crew_assignments (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  flight_id BIGINT REFERENCES flights(id),
  crew_id VARCHAR(20) REFERENCES crew(id),
  
  role VARCHAR(50),
  assignment_status VARCHAR(20), -- assigned, confirmed, completed, no_show
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Revenue & Sales
-- ============================================================================
CREATE TABLE revenue (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  flight_id BIGINT REFERENCES flights(id),
  
  passenger_count INT,
  revenue DECIMAL(15,2),
  
  -- Metrics
  yield DECIMAL(15,2), -- Revenue per Available Seat Kilometer
  rask DECIMAL(15,2), -- Revenue per Available Seat
  load_factor DECIMAL(5,2), -- Passengers / Available Seats
  
  -- Breakdown
  business_revenue DECIMAL(15,2),
  economy_revenue DECIMAL(15,2),
  ancillary_revenue DECIMAL(15,2),
  
  date DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_revenue_airline ON revenue(airline_code);
CREATE INDEX idx_revenue_date ON revenue(date);

-- ============================================================================
-- Cost & Operations
-- ============================================================================
CREATE TABLE operational_costs (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  flight_id BIGINT REFERENCES flights(id),
  
  -- Fuel
  fuel_liters DECIMAL(10,2),
  fuel_cost DECIMAL(15,2),
  
  -- Crew
  crew_cost DECIMAL(15,2),
  
  -- Maintenance & Handling
  maintenance_cost DECIMAL(15,2),
  handling_cost DECIMAL(15,2),
  
  -- Landing & Fees
  landing_fee DECIMAL(15,2),
  airport_fee DECIMAL(15,2),
  
  -- Other
  catering_cost DECIMAL(15,2),
  other_cost DECIMAL(15,2),
  
  total_cost DECIMAL(15,2),
  
  date DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Delays & Incidents
-- ============================================================================
CREATE TABLE delays (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  flight_id BIGINT REFERENCES flights(id),
  
  delay_minutes INT,
  primary_cause VARCHAR(100), -- Weather, Mechanical, Crew, ATC, Passenger, Other
  secondary_cause VARCHAR(100),
  
  impact_on_network TEXT,
  recovery_action TEXT,
  
  recorded_by VARCHAR(50),
  resolved_date DATE,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Reports Generated
-- ============================================================================
CREATE TABLE reports (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  
  report_type VARCHAR(50), -- weekly, biweekly, monthly, quarterly, biannual, annual
  report_date DATE,
  
  period_start DATE,
  period_end DATE,
  
  file_url VARCHAR(255),
  file_format VARCHAR(10), -- pdf, excel, html
  
  total_flights INT,
  on_time_performance DECIMAL(5,2),
  revenue DECIMAL(15,2),
  total_costs DECIMAL(15,2),
  
  generated_by VARCHAR(100),
  generated_at TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Subscriptions & Billing
-- ============================================================================
CREATE TABLE subscriptions (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  
  plan VARCHAR(50), -- starter, professional, enterprise
  status VARCHAR(20), -- active, cancelled, suspended
  
  monthly_price DECIMAL(15,2),
  billing_cycle VARCHAR(20), -- monthly, annual
  
  subscription_start DATE,
  next_billing_date DATE,
  
  stripe_customer_id VARCHAR(100),
  stripe_subscription_id VARCHAR(100),
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Alerts & Notifications
-- ============================================================================
CREATE TABLE alerts (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  
  alert_type VARCHAR(50), -- delay, maintenance, crew, revenue, fuel
  severity VARCHAR(20), -- info, warning, critical
  
  message TEXT,
  action_required TEXT,
  
  is_resolved BOOLEAN DEFAULT FALSE,
  resolved_at TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- User Activity Logs
-- ============================================================================
CREATE TABLE activity_logs (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  airline_code VARCHAR(10) REFERENCES airlines(code),
  user_id VARCHAR(100),
  
  action VARCHAR(100), -- view_dashboard, generate_report, export_data
  resource VARCHAR(100),
  
  details JSONB,
  ip_address VARCHAR(45),
  
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Real-World API Integration Examples

### 1. Flight Data from Airline System

```python
# integrations/flight_api.py
import requests
from datetime import datetime, timedelta
from config import get_airline_config

class FlightDataAPI:
    """Integrate with airline flight management system"""
    
    def __init__(self, airline_code):
        self.config = get_airline_config(airline_code)
        self.base_url = "https://api.airline-system.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.config.maintenance_api_key}",
            "Content-Type": "application/json"
        }
    
    def get_live_flights(self):
        """Fetch all active flights"""
        try:
            response = requests.get(
                f"{self.base_url}/flights/live",
                headers=self.headers,
                params={"airline": self.config.airline_code}
            )
            response.raise_for_status()
            return self._transform_flights(response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Flight API error: {e}")
            return []
    
    def get_scheduled_flights(self, days_ahead=7):
        """Get upcoming scheduled flights"""
        params = {
            "airline": self.config.airline_code,
            "from_date": datetime.now().isoformat(),
            "to_date": (datetime.now() + timedelta(days=days_ahead)).isoformat()
        }
        
        response = requests.get(
            f"{self.base_url}/flights/scheduled",
            headers=self.headers,
            params=params
        )
        return self._transform_flights(response.json())
    
    def get_flight_details(self, flight_id):
        """Get detailed flight information"""
        response = requests.get(
            f"{self.base_url}/flights/{flight_id}",
            headers=self.headers
        )
        return response.json()
    
    def update_flight_actual(self, flight_id, actual_data):
        """Update flight with actual performance data"""
        payload = {
            "actual_departure": actual_data.get("departure_time"),
            "actual_arrival": actual_data.get("arrival_time"),
            "passengers": actual_data.get("passenger_count"),
            "delay_minutes": actual_data.get("delay_minutes"),
            "status": actual_data.get("status")
        }
        
        response = requests.patch(
            f"{self.base_url}/flights/{flight_id}",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"Flight {flight_id} updated successfully")
            return True
        return False
    
    def _transform_flights(self, api_flights):
        """Transform API response to AirOps format"""
        transformed = []
        
        for flight in api_flights:
            transformed.append({
                "flight_number": flight.get("number"),
                "aircraft_id": flight.get("aircraft_id"),
                "departure_airport": flight.get("origin"),
                "arrival_airport": flight.get("destination"),
                "scheduled_departure": flight.get("scheduled_departure"),
                "scheduled_arrival": flight.get("scheduled_arrival"),
                "total_seats": flight.get("capacity"),
                "status": flight.get("status")
            })
        
        return transformed

# Usage in app.py
@st.cache_data(ttl=300)
def load_live_flights(airline_code):
    api = FlightDataAPI(airline_code)
    flights = api.get_live_flights()
    return pd.DataFrame(flights)
```

### 2. Maintenance Data Integration

```python
# integrations/maintenance_api.py
import requests

class MaintenanceSystemAPI:
    """Connect to airline maintenance system"""
    
    def __init__(self, airline_code):
        self.config = get_airline_config(airline_code)
        self.base_url = "https://api.maintenance-system.com/v1"
    
    def get_maintenance_schedule(self):
        """Fetch scheduled maintenance for all aircraft"""
        response = requests.get(
            f"{self.base_url}/maintenance/schedule",
            headers={"Authorization": f"Bearer {self.config.maintenance_api_key}"},
            params={"airline": self.config.airline_code}
        )
        return response.json()
    
    def get_maintenance_alerts(self):
        """Get critical maintenance issues"""
        response = requests.get(
            f"{self.base_url}/maintenance/alerts",
            headers={"Authorization": f"Bearer {self.config.maintenance_api_key}"},
            params={"severity": "critical"}
        )
        return response.json()
    
    def get_aircraft_health_scores(self):
        """Health status for entire fleet"""
        aircraft_list = self.get_fleet()
        health_scores = []
        
        for aircraft in aircraft_list:
            response = requests.get(
                f"{self.base_url}/aircraft/{aircraft['id']}/health",
                headers={"Authorization": f"Bearer {self.config.maintenance_api_key}"}
            )
            health_scores.append(response.json())
        
        return health_scores

# Usage
@st.cache_data(ttl=600)
def get_maintenance_data(airline_code):
    maint_api = MaintenanceSystemAPI(airline_code)
    
    schedule = maint_api.get_maintenance_schedule()
    alerts = maint_api.get_maintenance_alerts()
    health = maint_api.get_aircraft_health_scores()
    
    return {
        "schedule": schedule,
        "alerts": alerts,
        "health": health
    }
```

### 3. Revenue Management System

```python
# integrations/revenue_api.py
import requests

class RevenueManagementAPI:
    """Connect to revenue management system"""
    
    def __init__(self, airline_code):
        self.config = get_airline_config(airline_code)
        self.base_url = "https://api.revenue-system.com/v1"
    
    def get_daily_metrics(self, date):
        """Get daily revenue metrics"""
        response = requests.get(
            f"{self.base_url}/metrics/daily",
            headers={"Authorization": f"Bearer {self.config.revenue_management_api_key}"},
            params={
                "airline": self.config.airline_code,
                "date": date.isoformat()
            }
        )
        
        data = response.json()
        return {
            "revenue": data.get("total_revenue"),
            "yield": data.get("yield_per_ask"),
            "load_factor": data.get("load_factor"),
            "pax_count": data.get("passengers")
        }
    
    def get_price_recommendations(self, flight_id):
        """Get AI-powered pricing recommendations"""
        response = requests.post(
            f"{self.base_url}/pricing/recommend",
            headers={"Authorization": f"Bearer {self.config.revenue_management_api_key}"},
            json={
                "flight_id": flight_id,
                "airline": self.config.airline_code
            }
        )
        
        return response.json()
    
    def get_forecast(self, days_ahead=30):
        """Get revenue forecast"""
        response = requests.get(
            f"{self.base_url}/forecast",
            headers={"Authorization": f"Bearer {self.config.revenue_management_api_key}"},
            params={
                "airline": self.config.airline_code,
                "days": days_ahead
            }
        )
        
        return response.json()
```

### 4. Weather & Operational Data

```python
# integrations/weather_api.py
import requests

class WeatherOperationalAPI:
    """Get weather and airport operational data"""
    
    def __init__(self):
        self.weather_base = "https://api.weatherapi.com/v1"
        self.weather_key = os.getenv("WEATHER_API_KEY")
    
    def get_airport_weather(self, airport_code):
        """Get current weather at airport"""
        airport_city = self._get_airport_city(airport_code)
        
        response = requests.get(
            f"{self.weather_base}/current.json",
            params={
                "key": self.weather_key,
                "q": airport_city,
                "aqi": "yes"
            }
        )
        
        data = response.json()
        return {
            "temperature": data['current']['temp_c'],
            "condition": data['current']['condition']['text'],
            "wind_speed": data['current']['wind_kph'],
            "visibility": data['current']['vis_km'],
            "pressure": data['current']['pressure_mb']
        }
    
    def get_delay_probability(self, airport_code, weather_data):
        """Calculate probability of delays based on weather"""
        wind_speed = weather_data.get('wind_speed', 0)
        visibility = weather_data.get('visibility', 10)
        
        # Simple delay probability calculation
        delay_prob = 0
        if wind_speed > 40:
            delay_prob += 0.3
        if visibility < 5:
            delay_prob += 0.4
        
        return min(delay_prob, 1.0)
```

---

## Advanced Features Implementation

### 1. Predictive Analytics

```python
# analytics/predictive.py
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

class PredictiveAnalytics:
    """ML-based predictions"""
    
    def __init__(self, airline_code):
        self.airline_code = airline_code
        self.model_delay = None
        self.model_cancellation = None
    
    def train_delay_prediction_model(self, historical_data):
        """Train model to predict flight delays"""
        
        features = [
            'route', 'aircraft_type', 'day_of_week',
            'hour_of_day', 'season', 'weather_condition'
        ]
        target = 'delayed'  # 1 if delayed, 0 if on-time
        
        X = historical_data[features]
        y = historical_data[target]
        
        self.model_delay = RandomForestClassifier(n_estimators=100)
        self.model_delay.fit(X, y)
    
    def predict_delay(self, flight_data):
        """Predict if flight will be delayed"""
        features = [
            flight_data['route'],
            flight_data['aircraft_type'],
            flight_data['day_of_week'],
            flight_data['hour_of_day'],
            flight_data['season'],
            flight_data['weather_condition']
        ]
        
        delay_probability = self.model_delay.predict_proba([features])[0][1]
        return delay_probability
    
    def predict_maintenance_issue(self, aircraft_data):
        """Predict aircraft maintenance issues"""
        features = [
            aircraft_data['total_flight_hours'],
            aircraft_data['total_cycles'],
            aircraft_data['age_years'],
            aircraft_data['last_maintenance_days_ago']
        ]
        
        # Return risk score 0-100
        risk_score = self._calculate_maintenance_risk(features)
        return risk_score
    
    def _calculate_maintenance_risk(self, features):
        """Calculate maintenance risk"""
        flight_hours, cycles, age, days_since_maint = features
        
        risk = 0
        if flight_hours > 40000:
            risk += 20
        if cycles > 30000:
            risk += 20
        if age > 20:
            risk += 15
        if days_since_maint > 180:
            risk += 25
        
        return min(risk, 100)
```

### 2. Real-Time Alerts System

```python
# alerts/alerting.py
from datetime import datetime

class AlertingSystem:
    """Real-time operational alerts"""
    
    def __init__(self, airline_code):
        self.airline_code = airline_code
        self.db = SupabaseManager(airline_code)
    
    def check_flight_delays(self):
        """Alert on flight delays"""
        flights = self.db.get_flights_data()
        
        delayed_flights = flights[flights['delay_minutes'] > 15]
        
        for _, flight in delayed_flights.iterrows():
            self.create_alert(
                alert_type="delay",
                severity="warning" if flight['delay_minutes'] < 60 else "critical",
                message=f"Flight {flight['flight_number']} delayed by {flight['delay_minutes']} minutes",
                action_required="Monitor and consider rebooking options"
            )
    
    def check_maintenance_alerts(self):
        """Alert on maintenance issues"""
        maintenance = self.db.get_maintenance_data()
        
        for _, record in maintenance.iterrows():
            if record['severity'] == 'critical':
                self.create_alert(
                    alert_type="maintenance",
                    severity="critical",
                    message=f"Critical maintenance issue on {record['aircraft_id']}: {record['component']}",
                    action_required="Take aircraft out of service immediately"
                )
    
    def create_alert(self, alert_type, severity, message, action_required):
        """Create and store alert"""
        self.db.client.table("alerts").insert({
            "airline_code": self.airline_code,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "action_required": action_required,
            "is_resolved": False,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        # Send notification
        self._send_notification(severity, message)
    
    def _send_notification(self, severity, message):
        """Send alert to stakeholders"""
        # Email, SMS, Slack integration
        pass
```

### 3. Cost Optimization Engine

```python
# optimization/cost_optimizer.py

class CostOptimizer:
    """Find cost-saving opportunities"""
    
    def __init__(self, airline_code):
        self.airline_code = airline_code
    
    def analyze_fuel_costs(self, historical_data):
        """Optimize fuel consumption"""
        df = pd.DataFrame(historical_data)
        
        avg_fuel_burn = df['fuel_liters'].mean()
        avg_flight_hours = df['flight_hours'].mean()
        
        efficiency = avg_fuel_burn / avg_flight_hours
        
        recommendations = []
        if efficiency > 2.0:
            recommendations.append({
                "area": "Fuel Efficiency",
                "current": f"{efficiency:.2f}L/hour",
                "target": "1.8L/hour",
                "savings": f"${(efficiency - 1.8) * avg_flight_hours * 25 * 30}K/month",
                "action": "Optimize cruise altitude, reduce taxi time"
            })
        
        return recommendations
    
    def analyze_crew_costs(self, crew_data):
        """Optimize crew scheduling"""
        recommendations = []
        
        # Find deadhead flights (crew without passengers)
        deadheads = crew_data[crew_data['deadhead'] == True]
        
        if len(deadheads) > 0:
            monthly_deadhead_cost = len(deadheads) * 500
            recommendations.append({
                "area": "Crew Scheduling",
                "issue": f"{len(deadheads)} deadhead flights per month",
                "savings": f"${monthly_deadhead_cost}K/month",
                "action": "Replan crew rotations"
            })
        
        return recommendations
    
    def get_all_optimizations(self):
        """Comprehensive cost analysis"""
        fuel_opts = self.analyze_fuel_costs(...)
        crew_opts = self.analyze_crew_costs(...)
        # More analyses
        
        total_potential = sum(opt.get('savings', 0) for opt in fuel_opts + crew_opts)
        
        return {
            "total_potential_savings": total_potential,
            "optimizations": fuel_opts + crew_opts
        }
```

---

## Testing & Validation

```python
# tests/test_integrations.py
import pytest
from integrations import FlightDataAPI, MaintenanceSystemAPI

def test_flight_api_connection():
    api = FlightDataAPI("PIA")
    flights = api.get_live_flights()
    assert len(flights) > 0

def test_maintenance_alerts():
    api = MaintenanceSystemAPI("PIA")
    alerts = api.get_maintenance_alerts()
    assert isinstance(alerts, list)

def test_revenue_metrics():
    from datetime import date
    api = RevenueManagementAPI("PIA")
    metrics = api.get_daily_metrics(date.today())
    assert 'revenue' in metrics
    assert 'load_factor' in metrics
```

This comprehensive database schema and integration guide provides everything needed to build a production-grade system with real airline data!
