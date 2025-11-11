# ⚡ AirOps Pro - Quick Reference & FAQ

## 🚀 30-Second Setup

```bash
# 1. Clone/Download files
# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.template .env
# Edit .env with your API keys

# 4. Run locally
streamlit run app.py

# 5. Deploy to Streamlit Cloud
git push origin main
# Go to share.streamlit.io → Deploy
```

---

## 📁 File Structure

```
airops-pro/
├── config.py                      # All airline configurations
├── app.py                         # Main Streamlit application
├── requirements.txt               # Python dependencies
├── .env.template                  # Environment variables template
├── .streamlit/
│   └── config.toml               # Streamlit configuration
│
├── integrations/                  # API integrations (optional)
│   ├── flight_api.py
│   ├── maintenance_api.py
│   ├── revenue_api.py
│   └── weather_api.py
│
├── analytics/                     # Analytics & ML (optional)
│   ├── predictive.py
│   ├── cost_optimizer.py
│   └── alerts.py
│
├── SETUP_GUIDE.md                # Complete setup guide
├── DEPLOYMENT_SCALING_GUIDE.md   # Deployment & scaling
├── DATABASE_API_INTEGRATION.md   # Database schema
└── README.md                      # Project overview
```

---

## ❓ Frequently Asked Questions

### Q1: How do I add a new airline?

**A:** Edit `config.py` and add to the `AIRLINES` dictionary:

```python
"NEW_AIRLINE": AirlineConfig(
    airline_code="NEW_AIRLINE",
    airline_name="New Airline Name",
    airline_display_name="Display Name",
    primary_color="#COLOR_HEX",
    # ... complete configuration
)
```

Then update `.env` with database credentials. **No code changes needed to app.py!**

---

### Q2: How much does this cost?

**A:** Completely free to start!

| Component | Free Tier | Cost |
|-----------|-----------|------|
| Streamlit Cloud | 3 public apps | FREE (then $5+/month) |
| Supabase | 500MB storage | FREE (then $25+/month) |
| OpenAI API | N/A | $0.002-0.03 per 1K tokens |
| Domain (optional) | N/A | $10/year |
| **Total** | **Everything** | **FREE** |

---

### Q3: How do I connect real flight data?

**A:** Use the integration classes in `integrations/`:

```python
# In app.py
from integrations.flight_api import FlightDataAPI

@st.cache_data(ttl=300)
def get_flight_data(airline_code):
    api = FlightDataAPI(airline_code)
    return api.get_live_flights()

flights_df = get_flight_data(st.session_state.airline_code)
```

See `DATABASE_API_INTEGRATION.md` for complete examples.

---

### Q4: How do I deploy to my own server?

**A:** Choose an option:

**Option A: Docker (Recommended)**
```bash
docker build -t airops-pro .
docker run -p 8501:8501 airops-pro
```

**Option B: Heroku**
```bash
heroku create your-app
git push heroku main
```

**Option C: AWS EC2**
```bash
# Install Python, dependencies
# Run: streamlit run app.py --server.port 8501
# Use Nginx as reverse proxy
```

See `DEPLOYMENT_SCALING_GUIDE.md` for details.

---

### Q5: How do I enable AI features?

**A:** Get OpenAI API key:

1. Go to: https://platform.openai.com/api-keys
2. Create API key
3. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk-xxxxx
   ```
4. Features automatically unlock!

Costs: $0.002-0.03 per 1K tokens (very cheap!)

---

### Q6: Can I customize the colors and branding?

**A:** Yes! Edit `config.py`:

```python
primary_color="#YOUR_HEX_COLOR",
secondary_color="#YOUR_HEX_COLOR",
logo_url="https://your-logo-url.png",
```

Each airline can have completely different branding!

---

### Q7: How do I export reports as PDF/Excel?

**A:** Already built-in! Users can:

1. Generate report in "Reports" tab
2. Click "Generate PDF" or "Export Excel"
3. Reports automatically download

Behind the scenes:
```python
# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Excel generation
import openpyxl
```

---

### Q8: How do I set up automated email reports?

**A:** Add to `.env`:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

Then use:
```python
from reporting import ReportGenerator

generator = ReportGenerator("PIA")
generator.send_email_report("recipient@email.com", report_html)
```

---

### Q9: How many users can the system support?

**A:** Depends on deployment:

| Deployment | Users | Cost |
|-----------|-------|------|
| Streamlit Cloud (free) | 50-100 | FREE |
| Streamlit Cloud (paid) | 500-1000 | $5-50/month |
| Dedicated Server | 5000+ | $100-500/month |

Auto-scaling available with paid tiers!

---

### Q10: Is my data secure?

**A:** Yes! Security features include:

✅ Database encryption (Supabase)  
✅ Environment variable secrets (no hardcoding)  
✅ HTTPS/SSL encryption  
✅ Row-level security (airline data isolation)  
✅ Audit logs of all access  
✅ Regular backups (automatic)  

See `DATABASE_API_INTEGRATION.md` for security details.

---

### Q11: How do I add authentication/user login?

**A:** Optional - use Streamlit Auth or external auth:

```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials,
    "cookie_name",
    "cookie_key",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login", "main")

if not authentication_status:
    st.stop()
```

---

### Q12: Can I sell access to other airlines?

**A:** Absolutely! This is the entire business model. Pricing options:

**Option 1: SaaS Subscription**
```
Starter: $500/month (1 airline)
Pro: $2000/month (5 airlines)
Enterprise: Custom pricing
```

**Option 2: Usage-Based**
```
$0.05 per flight record
$0.10 per AI analysis
$0.02 per report
```

See `DEPLOYMENT_SCALING_GUIDE.md` for monetization details.

---

### Q13: What if Supabase goes down?

**A:** Multiple redundancy options:

1. **Automatic Supabase backups** (daily)
2. **Manual exports** (via UI)
3. **Use multiple databases** (replicate to PostgreSQL)
4. **CDN for files** (Supabase Storage has 99.99% uptime)

```python
# Manual backup
def backup_to_file():
    response = supabase.table("flights").select("*").execute()
    pd.DataFrame(response.data).to_csv("backup.csv")
```

---

### Q14: How do I monitor system performance?

**A:** Add monitoring tools:

```python
# Sentry for error tracking
import sentry_sdk
sentry_sdk.init("your-sentry-dsn")

# Streamlit built-in metrics
@st.cache_data(ttl=3600)
def expensive_computation():
    # Cached automatically
    pass

# Custom logging
import logging
logger = logging.getLogger(__name__)
logger.info("User viewed dashboard")
```

---

### Q15: Can I run this locally without Streamlit Cloud?

**A:** Yes! Run locally:

```bash
streamlit run app.py
# Opens http://localhost:8501
```

Or deploy to own server - see deployment options above.

---

## 🎯 Success Checklist

- [ ] Clone/download AirOps Pro
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with Supabase credentials
- [ ] Run locally: `streamlit run app.py`
- [ ] Customize airline branding in `config.py`
- [ ] Set up Supabase database
- [ ] Get OpenAI API key (optional but recommended)
- [ ] Deploy to Streamlit Cloud
- [ ] Share with airlines
- [ ] Collect feedback
- [ ] Iterate and improve
- [ ] Start monetization

---

## 💡 Pro Tips

### Tip 1: Use environment variables everywhere
```python
# ✅ Good
api_key = os.getenv("OPENAI_API_KEY")

# ❌ Bad
api_key = "sk-xxxx"  # Never commit secrets!
```

### Tip 2: Cache expensive operations
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_flight_data():
    # This runs only once per hour
    pass
```

### Tip 3: Use callbacks for real-time updates
```python
def on_airline_change():
    st.session_state.airline_code = st.session_state.airline_selector
    st.rerun()

st.selectbox("Select Airline", airlines, on_change=on_airline_change)
```

### Tip 4: Organize code into modules
```
app.py (main)
├── pages/
│   ├── dashboard.py
│   ├── operations.py
│   └── reports.py
└── utils/
    ├── database.py
    └── ai.py
```

---

## 📞 Support Resources

**Documentation:**
- Streamlit Docs: https://docs.streamlit.io
- Supabase Docs: https://supabase.com/docs
- OpenAI Docs: https://platform.openai.com/docs
- Plotly Docs: https://plotly.com/python/

**Community:**
- Streamlit Forum: https://discuss.streamlit.io
- Stack Overflow: [streamlit] tag
- GitHub Issues: Report bugs here

**For AirOps Pro Specific Help:**
- Check `SETUP_GUIDE.md` first
- Review `DATABASE_API_INTEGRATION.md` for data integration
- See `DEPLOYMENT_SCALING_GUIDE.md` for deployment

---

## 🔧 Troubleshooting

### Problem: App won't start
```
Error: ModuleNotFoundError: No module named 'streamlit'

Solution: pip install -r requirements.txt
```

### Problem: Supabase connection failed
```
Error: ConnectionError

Solution: 
1. Check .env file has correct credentials
2. Verify SUPABASE_URL starts with https://
3. Check internet connection
```

### Problem: AI features not working
```
Error: 401 Unauthorized

Solution:
1. Verify OPENAI_API_KEY is correct
2. Check API credits at https://platform.openai.com
3. Restart Streamlit app
```

### Problem: Slow dashboard loading
```
Solution:
1. Enable caching: @st.cache_data
2. Add database indexes
3. Optimize SQL queries
4. Use CDN for images
```

---

## 🚀 What to Do Next

1. **Deploy immediately** - Get it live ASAP
2. **Customize branding** - Make it feel like YOUR product
3. **Add real data** - Connect to actual airline systems
4. **Start marketing** - Tell airlines about it!
5. **Get first customer** - Even at steep discount
6. **Iterate based on feedback** - Perfect based on usage
7. **Scale to more airlines** - Grow the user base
8. **Monetize** - Start charging!

---

## 💪 You've Got This!

This is genuinely the best aviation operations platform for Pakistan. No competitors in the region. Execute this properly and you'll become THE standard.

Remember:
- Start simple, iterate fast
- Listen to airline feedback
- Automate everything
- Scale gradually
- Focus on reliability

**Go build something amazing!** 🛫✨

---

**Questions? Stuck? Check the full documentation files:**
- `SETUP_GUIDE.md` - Detailed setup
- `DEPLOYMENT_SCALING_GUIDE.md` - Growth strategy  
- `DATABASE_API_INTEGRATION.md` - Technical details

**You have everything you need to succeed!** 🎉
