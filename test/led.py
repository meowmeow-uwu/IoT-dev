from flask import Flask, render_template
from gpiozero import LED

app = Flask(__name__)

led = LED(17)


@app.route("/")
def home():
    status = "BẬT" if led.is_lit else "TẮT"
    return render_template("index.html", status=status)


@app.route("/led/on")
def led_on():
    led.on()
    return render_template("index.html", status="BẬT")


@app.route("/led/off")
def led_off():
    led.off()
    return render_template("index.html", status="TẮT")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)