from flask import Flask, jsonify, request
from LinRegModel import LinRegModel
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initializes initial model
lrm = LinRegModel()
lrm.train_model()
lrm.load_model()


# Test route
@app.route('/')
def hello_world():
    return 'Hello, World!'


# Prediction API
@app.route('/api/prediction', methods=['GET'])
def get_prediction():
    square_footage = float(request.args.get('square_footage'))
    num_bed = float(request.args.get('num_bed'))
    num_bath = float(request.args.get('num_bath'))
    predicted_usd_price = lrm.predict_price("toronto", [square_footage, num_bed, num_bath])[0]

    result = {"predicted_usd_price": predicted_usd_price}

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)

# TODO: Add logging (look up "Python logging" on Youtube)
# TODO: Convert prices for Vancouver and Toronto from CAD to USD, then RUN THOSE SCRIPTS AGAIN (TO UPDATE DATABASE)
# TODO: Change model-> Make it so that Flask has access to a "pickled" model (locally), so that it doesn't have to make
# TODO: (cont...) a SQL command on every reload of http://127.0.0.1:5000/api/price
