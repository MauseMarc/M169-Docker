from flask import Flask, render_template
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/')
def bit_tv():
    return render_template('display.html')
@app.route('/mausecret/bar')
def bar():
    return render_template('bar.html')
@app.route('/mausecret/casino')
def casino():
    return render_template('casino.html')
@app.route('/mausecret/events')
def events():
    return render_template('events.html')
@app.route('/mausecret/loans')
def loans():
    return render_template('loans.html')
@app.route('/mausecret/stocks')
def stocks():
    return render_template('stocks.html')
@app.route('/mausecret/transfer')
def transfer():
    return render_template('transfer.html')
@app.route('/mausecret/voting')
def voting():
    return render_template('voting.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)