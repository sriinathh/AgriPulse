"""Terminal weather tool. All HTTP is mocked (tests only); the CLI itself uses the real provider/location code."""
import httpx

from app.cli.weather_cli import run
from app.config import Settings

KEY = "SECRET-TEST-KEY-123"
OWM = {"dt": 1791369000, "main": {"temp": 29.0, "feels_like": 31.2, "humidity": 68}, "rain": {"1h": 2.1},
       "weather": [{"description": "light rain"}], "wind": {"speed": 3.2}}


def settings(key=KEY):
    return Settings(openweather_api_key=key, openweather_base_url="https://owm.test/weather",
                    openweather_geocode_url="https://owm.test/geo", _env_file=None)


class Net:
    """Routes mocked URLs and records requests."""
    def __init__(self, geo=None, ip=None, weather=OWM, weather_status=200, ip_status=200):
        self.geo, self.ip, self.weather, self.weather_status, self.ip_status = geo, ip, weather, weather_status, ip_status
        self.calls = []

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.calls.append(req)
        host = req.url.host
        if host == "owm.test" and req.url.path == "/geo":
            return httpx.Response(200, json=self.geo if self.geo is not None else [])
        if host == "owm.test":
            return httpx.Response(self.weather_status, json=self.weather)
        if host in ("ipinfo.io", "ipapi.co"):
            if self.ip_status != 200 or self.ip is None:
                return httpx.Response(self.ip_status if self.ip_status != 200 else 500, json={})
            return httpx.Response(200, json=self.ip)
        raise AssertionError(f"unexpected URL {req.url}")

    def weather_calls(self):
        return [c for c in self.calls if c.url.path == "/weather"]


HYD = {"name": "Hyderabad", "lat": 17.385, "lon": 78.4867, "country": "IN", "state": "Telangana"}
IPINFO = {"ip": "1.2.3.4", "city": "Pune", "region": "Maharashtra", "country": "IN", "loc": "18.5196,73.8554"}


def drive(net, answers, argv=None, key=KEY):
    answers, out = iter(answers), []

    def ask(prompt):
        out.append(prompt)
        try:
            return next(answers)
        except StopIteration:
            raise EOFError

    code = run(argv or [], ask=ask, out=out.append, transport=httpx.MockTransport(net), settings=settings(key))
    return code, "\n".join(out)


def test_asks_current_location_first_then_manual_entry(): 
    net = Net(geo=[HYD])
    code, text = drive(net, ["n", "Hyderabad, IN", "n"])
    assert code == 0
    assert text.index("Use your current location?") < text.index("Enter location")
    assert "Weather for Hyderabad, Telangana, IN" in text
    assert "29.0 C" in text and "feels like 31.2 C" in text and "68 %" in text and "2.1 mm" in text
    assert "Light rain" in text and "3.2 m/s" in text and "OpenWeatherMap (live)" in text
    geo = [c for c in net.calls if c.url.path == "/geo"][0]
    assert dict(geo.url.params)["q"] == "Hyderabad,IN"  # spaces around commas normalised
    w = net.weather_calls()[0]
    assert dict(w.url.params)["lat"] == "17.385" and dict(w.url.params)["lon"] == "78.4867"
    assert KEY not in text


def test_current_location_detected_and_confirmed(): 
    net = Net(ip=IPINFO)
    code, text = drive(net, ["y", "y", "n"])
    assert code == 0
    assert "Detected: Pune, Maharashtra, IN" in text and "approximate" in text
    assert "Weather for Pune, Maharashtra, IN" in text
    assert dict(net.weather_calls()[0].url.params)["lat"] == "18.5196"
    assert not [c for c in net.calls if c.url.path == "/geo"]  # no geocoding needed


def test_declining_detected_location_falls_back_to_manual(): 
    net = Net(ip=IPINFO, geo=[HYD])
    code, text = drive(net, ["y", "n", "Hyderabad", "n"])
    assert "Weather for Hyderabad" in text and "Pune" in text.split("Weather for")[0]


def test_ip_lookup_failure_falls_back_to_manual(): 
    net = Net(ip=None, ip_status=500, geo=[HYD])
    code, text = drive(net, ["y", "Hyderabad", "n"])
    assert code == 0 and "Falling back to manual entry" in text and "Weather for Hyderabad" in text


def test_ipapi_fallback_format(): 
    calls = []

    def handler(req):
        calls.append(req.url.host)
        if req.url.host == "ipinfo.io":
            return httpx.Response(429, json={})
        if req.url.host == "ipapi.co":
            return httpx.Response(200, json={"city": "Bengaluru", "region": "Karnataka", "country_code": "IN", "latitude": 12.97, "longitude": 77.59})
        return httpx.Response(200, json=OWM)
    out, ans = [], iter(["y", "y", "n"])
    run([], ask=lambda p: next(ans), out=out.append, transport=httpx.MockTransport(handler), settings=settings())
    assert calls[:2] == ["ipinfo.io", "ipapi.co"] and "Bengaluru" in "\n".join(out)


def test_multiple_matches_user_picks_second(): 
    second = {"name": "Hyderabad", "lat": 25.39, "lon": 68.37, "country": "PK", "state": "Sindh"}
    net = Net(geo=[HYD, second])
    code, text = drive(net, ["n", "Hyderabad", "2", "n"])
    assert "1. Hyderabad, Telangana, IN" in text and "2. Hyderabad, Sindh, PK" in text
    assert dict(net.weather_calls()[0].url.params)["lat"] == "25.39"


def test_unknown_location_reprompts_then_quits(): 
    net = Net(geo=[])
    code, text = drive(net, ["n", "Atlantis", "q"])
    assert code == 0 and "No place found for 'Atlantis'" in text and text.count("Enter location") == 2
    assert not net.weather_calls()


def test_weather_failure_is_controlled_not_a_traceback(): 
    net = Net(geo=[HYD], weather={"message": "oops"}, weather_status=500)
    code, text = drive(net, ["n", "Hyderabad", "n"])
    assert code == 0 and "! Weather provider returned HTTP 500" in text and "Traceback" not in text


def test_network_down_is_controlled(): 
    def boom(req):
        raise httpx.ConnectError(f"no route {req.url}", request=req)
    out, ans = [], iter(["n", "Hyderabad", "q"])
    run([], ask=lambda p: next(ans), out=out.append, transport=httpx.MockTransport(boom), settings=settings())
    text = "\n".join(out)
    assert "Could not reach" in text and KEY not in text


def test_missing_api_key_explains_how_to_fix(): 
    net = Net()
    code, text = drive(net, [], key=None)
    assert code == 2 and "OPENWEATHER_API_KEY" in text and "home.openweathermap.org" in text
    assert net.calls == []


def test_non_interactive_flags(): 
    net = Net(geo=[HYD], ip=IPINFO)
    code, text = drive(net, [], argv=["--location", "Hyderabad, IN"])
    assert code == 0 and "Weather for Hyderabad" in text and "Use your current location?" not in text
    code, text = drive(Net(ip=IPINFO), [], argv=["--current"])
    assert code == 0 and "Detected (approximate, IP-based): Pune" in text and "Weather for Pune" in text


def test_ctrl_d_exits_cleanly(): 
    code, text = drive(Net(), [])
    assert code == 0 and "Bye." in text


def test_debug_shows_what_the_api_returned(): 
    net = Net(geo=[HYD], weather={**OWM, "name": "Secunderabad", "sys": {"country": "IN"}, "coord": {"lat": 17.4, "lon": 78.5}})
    code, text = drive(net, [], argv=["--location", "Hyderabad, IN", "--debug"])
    assert code == 0 and "place named by API      : 'Secunderabad'" in text and "coordinates sent to API : 17.385, 78.4867" in text
    assert KEY not in text
    assert "debug" not in drive(Net(geo=[HYD]), [], argv=["--location", "Hyderabad, IN"])[1]


def test_old_observation_is_flagged_and_ambiguous_location_is_announced(): 
    from datetime import datetime, timedelta, timezone
    from app.services.weather_service import ProviderWeather
    from app.cli.weather_cli import show
    from app.services.location_service import Place
    out = []
    old = ProviderWeather(datetime(2026, 10, 7, 8, 0), 29.0, 68, 0.0)
    show(Place("X", 1, 2), old, out.append, now=datetime(2026, 10, 7, 11, 0, tzinfo=timezone.utc))
    assert "180 min ago" in "\n".join(out) and "observation is old" in "\n".join(out)
    second = {"name": "Hyderabad", "lat": 25.39, "lon": 68.37, "country": "PK", "state": "Sindh"}
    code, text = drive(Net(geo=[HYD, second]), [], argv=["--location", "Hyderabad"])
    assert "2 places match" in text and "Hyderabad, Sindh, PK" in text
