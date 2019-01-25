from flask import Flask, send_from_directory
import requests

app = Flask(__name__)


# Homepage
@app.route('/')
def homepage():
    return send_from_directory('static', 'index.html')
    # return "Home Page"


# Test GET request
@app.route('/prediction')
def get_prediction():
    predicted_usd_price = requests.get('http://127.0.0.1:5000/api/prediction?square_footage=9000&num_bed=4&num_bath=4').json()["predicted_usd_price"]

    return str(predicted_usd_price)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
