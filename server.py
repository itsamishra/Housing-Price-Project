from flask import Flask, jsonify
from LinRegModel import LinRegModel

app = Flask(__name__)


@app.route('/')
def hello_world():
    lrm = LinRegModel()
    lrm.load_model()
    return 'Hello, World!'


@app.route('/api/price', methods=['GET'])
def get_price():
    lrm = LinRegModel()
    lrm.train_model()
    lrm.load_model()
    price_prediction = lrm.predict_price("toronto", [9000, 4, 4])[0]

    return str(price_prediction)


if __name__ == "__main__":
    app.run(debug=True)

# TODO: Add logging (look up "Python logging" on Youtube)
# TODO: Convert prices for Vancouver and Toronto from CAD to USD, then RUN THOSE SCRIPTS AGAIN (TO UPDATE DATABASE)
# TODO: Change model-> Make it so that Flask has access to a "pickled" model (locally), so that it doesn't have to make
# TODO: (cont...) a SQL command on every reload of http://127.0.0.1:5000/api/price
