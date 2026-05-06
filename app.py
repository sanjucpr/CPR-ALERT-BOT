from flask import Flask, request
import requests
import os
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# TELEGRAM
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID = os.environ.get('CHAT_ID', '')

# WHATSAPP
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '')
ENABLE_WHATSAPP = os.environ.get('ENABLE_WHATSAPP', 'false').lower() == 'true'

# EMAIL
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER', '')
ENABLE_EMAIL = os.environ.get('ENABLE_EMAIL', 'true').lower() == 'true'

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        return {"ok": False, "error": "Not configured"}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_whatsapp(message):
    if not WHATSAPP_NUMBER:
        return False
    try:
        import pywhatkit
        pywhatkit.sendwhatmsg_to_instantly(WHATSAPP_NUMBER, message, wait_time=15, tab_close=True, close_time=3)
        return True
    except Exception as e:
        print(f"WhatsApp Error: {e}")
        return False

def send_email(subject, body_html, body_text):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        return {"success": False, "error": "Not configured"}
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def build_messages(data):
    alert_type = data.get('alert_type', 'UNKNOWN')
    symbol = data.get('symbol', 'Unknown')
    exchange = data.get('exchange', 'NSE')
    price = data.get('price', 'N/A')
    cpr_tc = data.get('cpr_tc', 'N/A')
    cpr_bc = data.get('cpr_bc', 'N/A')
    cpr_width = data.get('cpr_width_pct', 'N/A')
    cam_s3 = data.get('camarilla_s3', 'N/A')
    cam_r3 = data.get('camarilla_r3', 'N/A')
    direction = data.get('direction', 'UNKNOWN')
    timestamp = data.get('timestamp', '')
    
    emoji = "🚨" if "NARROW" in alert_type else "🔥"
    alert_name = "NARROW CPR + S3/R3 OVERLAP" if "NARROW" in alert_type else "VIRGIN CPR"
    
    text = f"""{emoji} <b>CPR ALERT</b> {emoji}

<b>Type:</b> {alert_name}
<b>Symbol:</b> {symbol}
<b>Exchange:</b> {exchange}
<b>Price:</b> ₹{price}
<b>CPR Zone:</b> {cpr_bc} - {cpr_tc} ({cpr_width}%)
<b>Cam S3:</b> {cam_s3} | <b>R3:</b> {cam_r3}
<b>Direction:</b> {direction}
<b>Time:</b> {timestamp}

⚡ Check your charts now!"""
    
    html = f"""<html><head><style>
body{{font-family:Arial,sans-serif;background:#f5f5f5;padding:20px}}
.container{{max-width:600px;margin:0 auto;background:white;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.1)}}
.header{{background:{'#ff4444' if 'NARROW' in alert_type else '#9b59b6'};color:white;padding:20px;text-align:center}}
.content{{padding:30px}}
.row{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #eee}}
.label{{font-weight:bold;color:#555}}
.value{{color:#333}}
.highlight{{background:#fff3cd;padding:15px;border-radius:5px;margin-top:20px;border-left:4px solid #ffc107}}
.footer{{background:#f8f9fa;padding:15px;text-align:center;font-size:12px;color:#666}}
</style></head><body>
<div class="container">
<div class="header"><h1>{emoji} CPR ALERT</h1><h2>{alert_name}</h2></div>
<div class="content">
<div class="row"><span class="label">Symbol:</span><span class="value">{symbol}</span></div>
<div class="row"><span class="label">Exchange:</span><span class="value">{exchange}</span></div>
<div class="row"><span class="label">Price:</span><span class="value">₹{price}</span></div>
<div class="row"><span class="label">CPR Zone:</span><span class="value">{cpr_bc} - {cpr_tc}</span></div>
<div class="row"><span class="label">CPR Width:</span><span class="value">{cpr_width}%</span></div>
<div class="row"><span class="label">S3:</span><span class="value">{cam_s3}</span></div>
<div class="row"><span class="label">R3:</span><span class="value">{cam_r3}</span></div>
<div class="row"><span class="label">Direction:</span><span class="value" style="color:{'green' if 'BULL' in direction else 'red'}">{direction}</span></div>
<div class="row"><span class="label">Time:</span><span class="value">{timestamp}</span></div>
<div class="highlight"><strong>⚡ Action Required:</strong> Price is in a high-probability zone. Check your charts immediately!</div>
</div>
<div class="footer">Sent by CPR Alert Bot | TradingView Webhook</div>
</div>
</body></html>"""
    
    plain = f"""CPR ALERT: {alert_name}
Symbol: {symbol} | Exchange: {exchange}
Price: Rs.{price}
CPR Zone: {cpr_bc} - {cpr_tc} (Width: {cpr_width}%)
Camarilla S3: {cam_s3} | R3: {cam_r3}
Direction: {direction}
Time: {timestamp}
Action: Check your charts now!"""
    
    return text, html, plain, alert_name, symbol

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        text_msg, html_msg, plain_msg, alert_name, symbol = build_messages(data)
        
        results = {}
        
        tg = send_telegram(text_msg)
        results["telegram"] = "sent" if tg and tg.get('ok') else f"failed: {tg.get('error', 'unknown')}"
        
        if ENABLE_WHATSAPP:
            def wa_async():
                send_whatsapp(text_msg.replace('<b>', '*').replace('</b>', '*'))
            threading.Thread(target=wa_async).start()
            results["whatsapp"] = "queued"
        else:
            results["whatsapp"] = "disabled"
        
        if ENABLE_EMAIL:
            subject = f"🚨 CPR Alert: {symbol} — {alert_name}"
            em = send_email(subject, html_msg, plain_msg)
            results["email"] = "sent" if em.get('success') else f"failed: {em.get('error', 'unknown')}"
        else:
            results["email"] = "disabled"
        
        return {"status": "processed", "results": results, "symbol": symbol, "alert_type": alert_name}, 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {
        "status": "alive",
        "telegram": bool(BOT_TOKEN and CHAT_ID),
        "whatsapp": {"configured": bool(WHATSAPP_NUMBER), "enabled": ENABLE_WHATSAPP},
        "email": {"configured": bool(all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER])), "enabled": ENABLE_EMAIL}
    }, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
