from flask import *
from mysql.connector import pooling
from dotenv import get_key

app = Flask(
    __name__,
    static_folder="public",
    static_url_path="/"
)


@app.route("/")
def index():
    return render_template("index.html")


app.run(host="0.0.0.0", port=8080)
