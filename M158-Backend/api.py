from flask import Flask, request, jsonify
from flask_cors import CORS
import db_functions
app = Flask(__name__)
CORS(app)

@app.route('/api/company/list', methods=['GET'])
def get_company_list():
    try:
        company_list = db_functions.get_all_balance()
        return jsonify(company_list)
    except Exception as e:
        return jsonify(status="error", msg=e)
# ==================================================================================================

# ==================================================================================================
# === = = = = = Bank Log = = = = = =================================================================
# ==================================================================================================
# Get the Bank Log
@app.route("/api/log/bank", methods=['GET'])
def get_bank_log():
    try:
        bank_log = db_functions.get_log("bank")
        formatted_bank_logs = []
        for log in bank_log:
            msg = f"{log["sender_name"]} transfered {log['amount']} {log['asset_name']} to {log['recipient_name']}"
            formatted_bank_logs.append({"timestamp":log["timestamp"],"msg":msg})
        return jsonify(formatted_bank_logs)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Get the Log of purchased Loans
@app.route("/api/log/loan", methods=['GET'])
def get_loan_log():
    try:
        loan_log = db_functions.get_log("loan")
        formatted_loan_logs = []
        for log in loan_log:
            msg = f"{log['asset_name']} - {log["sender_name"]} transfered {log['amount']} to {log['recipient_name']}"
            formatted_loan_logs.append({"timestamp":log["timestamp"],"msg":msg})
        return jsonify(formatted_loan_logs)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Stock Log who purchased what
@app.route("/api/log/stock", methods=['GET'])
def get_stock_log():
    try:
        stock_log = db_functions.get_log("stock")
        formatted_stock_logs = []
        for log in stock_log:
            msg = f"{log["sender_name"]} bought {log["detail"]} {log['asset_name']} from {log['recipient_name']} for {log['amount']}$"
            formatted_stock_logs.append({"timestamp":log["timestamp"],"msg":msg})
        return jsonify(formatted_stock_logs)
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================
# === = = = = = Bank Transfer = = = = = ============================================================
# ==================================================================================================
# Transfer Money between people
@app.route("/api/bank/transaction", methods=['POST'])
def finish_transaction():
    try:
        data = request.json
        sender = data.get("sender")
        recipient = data.get("recipient")
        amount = data.get("amount")
        asset = 1
        detail = "Bank Transfer"
        # Maybe turn this into a function.
        if db_functions.he_can_afford(sender, amount):
            try:
                e = db_functions.ledger_insert(sender, recipient, amount, asset, detail)
                return jsonify(status="success", msg="Transfer successful")
            except Exception as e:
                return jsonify(status="error", msg=e)
        else:
            return jsonify(status="error", msg="Not enough Money")
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================
# === = = = = = Bank Stocks = = = = = ==============================================================
# ==================================================================================================
#Get the Stocks as formated in the design
@app.route("/api/stock/market", methods=['GET'])
def get_stock_market_api():
    try:
        stock_market = db_functions.get_stock_market()
        return jsonify(stock_market)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Now how to buy a stock
# Also punish buying too many ? or selling too many ?
# Just hit em with a tax that increased per share sold at once
# easy
@app.route("/api/stock/transaction", methods=['POST'])
def buy_stock():
    try:
        data = request.json
        trans_type = data.get("type")
        stock_id = int(data.get("stock_id"))
        company_id = int(data.get("company_id"))
        amount = int(data.get("amount"))
        stock_worth = db_functions.get_one_stock(stock_id)
        full_price = stock_worth * amount
        try:
            if trans_type == "buy":
                if db_functions.he_can_afford(company_id, full_price):
                    db_functions.ledger_insert(company_id, 1, full_price, stock_id, amount)
                    return jsonify(status="success", msg="Buy successful")
                else:
                    return jsonify(status="error", msg="Not enough Money")
            elif trans_type == "sell":
                db_functions.ledger_insert(1, company_id, full_price, stock_id, amount)
                return jsonify(status="success", msg="Sell successful")
        except Exception as e:
            return jsonify(status="error", msg=e)
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================
# === = = = = = Bank Loans = = = = = ===============================================================
# ==================================================================================================
# Get all available Bank Loans
@app.route("/api/loan/packages", methods=['GET'])
def get_loan_packages():
    try:
        thing = db_functions.get_loan_list()
        return jsonify(thing)
    except Exception as e:
        return jsonify(status="error", msg=e)


# See which loans need to be paid back
@app.route("/api/loan/list", methods=['GET'])
def list_active_loans():
    try:
        active_loan_list = db_functions.get_active_loans()
        return jsonify(active_loan_list)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Pay Back a Loan
@app.route("/api/loan/payback", methods=['POST'])
def payback_loan():
    try:
        data = request.json
        loan_id = int(data.get("id"))
        active_loan_list = db_functions.get_active_loans()
        for loan in active_loan_list:
            if loan["id"] == loan_id:
                company_id = loan["company_id"]
                amount = loan["current_amount"]
                straight_interest = amount - loan["amount"]
                db_functions.update_loan(loan_id)
                db_functions.ledger_insert(company_id, 1, amount, loan["asset_id"], str(loan_id) + "-" + str(straight_interest)+"$")
                return jsonify(status="success", msg=f"{loan["company_name"]} paid {straight_interest}$ in straight interests")
        return jsonify(status="error", msg="idk")
    except Exception as e:
        return jsonify(status="error", msg=e)

# Buy a Loan
@app.route("/api/loan/buy", methods=['POST'])
def buy_loan_package():
    try:
        data = request.json
        company = int(data.get("company"))
        package_id = int(data.get("package"))
        packages = db_functions.get_loan_list()
        for package in packages:
            if package["id"] == package_id:
                try:
                    amount = package["amount"]
                    interest = package["interest"]
                    # Log the Loan bought and transfer the money
                    db_functions.loan_insert(company, amount, interest, package_id)
                    db_functions.ledger_insert(1, company, amount, package_id, str(interest)+"%")
                    return jsonify(status="success", msg="Loan successfully bought")
                except Exception as e:
                    return jsonify(status="error", msg=e)
        return jsonify(status="error", msg="idk")
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================

# ==================================================================================================
# === = = = = = Bar Log = = = = = ==================================================================
# ==================================================================================================
# Get the Bar Logs, who bought what.
@app.route("/api/log/bar", methods=['GET'])
def get_bar_log():
    try:
        bar_log = db_functions.get_log("drink")
        formatted_bar_logs = []
        for log in bar_log:
            if log["sender_name"] == "Bank":
                msg = f"Undid order {log['detail']}"
            else:
                msg = f"{log["id"]}: {log["sender_name"]} bought {log['detail']} {log['asset_name']} for {log['amount']}$"

            formatted_bar_logs.append({"timestamp":log["timestamp"],"msg":msg})
        return jsonify(formatted_bar_logs)
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================
# === = = = = = Bar Purchases = = = = = ============================================================
# ==================================================================================================
# Get a list of all the Drinks and their current price.
@app.route("/api/bar/drinks", methods=['GET'])
def get_drinks():
    try:
        drinks = db_functions.get_drink_list()
        return jsonify(drinks)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Bar Market. Like with Price History
@app.route("/api/bar/market", methods=["GET"])
def get_market_data():
    try:
        ye_data = db_functions.get_bar_market()
        return jsonify(ye_data)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Try to buy a drink
@app.route("/api/bar/purchase", methods=["POST"])
def do_purchase():
    try:
        data = request.json
        sender = data.get("company_id")
        recipient = 1 #bank
        amount = data.get("amount")
        asset = data.get("drink_id")
        try:
            # Get the current Price of the drink
            # Store it as Detail so we know what they paid for
            drink_price = db_functions.get_asset_worth(asset)
            price_full = int(drink_price) * int(amount)
            detail = f"{str(amount)}"

            # We need to check if somebody has the status for free drinks.
            x = db_functions.is_drink_event()
            if x is not False:
                new_sender = int(x)
                if db_functions.he_can_afford(new_sender, price_full):
                    sender = new_sender
            # If the Company doesn't have enough money it will throw an error back.
            if db_functions.he_can_afford(sender, price_full):
                try:
                    e = db_functions.ledger_insert(sender, recipient, price_full, asset, detail)
                    return jsonify(status="success", msg=e)
                except Exception as e:
                    return jsonify(status="error", msg=e)
            else:
                return jsonify(status="error", msg="Not enough Money")
        except Exception as e:
            return jsonify(status="error", msg=e)
    except Exception as e:
        return jsonify(status="error", msg=e)

# DONT FORGET. REVERSE ACTION FUNCTION
@app.route("/api/bar/undo", methods=["POST"])
def undo_order():
    try:
        bar_log = db_functions.latest_bar_purchase()
        # We will remember which order has been reversed.
        # Basically just a new ledger entry with recipient and sender reversed.
        bank_returns = []
        for log in bar_log:
            if log["sender_id"] == 1:
                bank_returns.append(int(log["detail"]))
            elif log["id"] in bank_returns:
                continue
            else:
                db_functions.ledger_insert(log["recipient_id"], log["sender_id"],log["amount"],log["asset_id"],log["id"])
                return jsonify(status="success", msg=f"Undone Purchase {log["id"]}")
        return jsonify(status="error", msg="No Purchases to Undo")
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================

# ==================================================================================================
# === = = = = = Casino Log = = = = = ===============================================================
# ==================================================================================================
# Casino Specific
# Get the Casino Log
@app.route("/api/log/casino", methods=['GET'])
def get_casino_log():
    try:
        casino_log = db_functions.get_log("casino")
        formatted_casino_logs = []
        for log in casino_log:
            if log["detail"] == "out":
                msg = f"{log["recipient_name"]} sold {log['amount']} {log["asset_name"]}"
            else:
                msg = f"{log['sender_name']} bought {log['amount']} {log['asset_name']}"
            formatted_casino_logs.append({"timestamp":log["timestamp"],"msg":msg})
        return jsonify(formatted_casino_logs)
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================
# === = = = = = Casino Exchange = = = = = ==========================================================
# ==================================================================================================
# Exchange Money for Chips and vice versa
@app.route("/api/casino/exchange", methods=['POST'])
def exchange_casino():
    try:
        data = request.json
        company = int(data.get('company_id'))
        amount = data.get('amount', 0)
        direction = data.get('direction') # 'in' (to chips) or 'out' (to money)
        asset = 2
        sender = ""
        recipient = ""
        detail = "error"
        check = False
        # Checking the Direction. Money to Chip or Chip to Money
        if direction == "in":
            detail = "in"
            sender = company
            recipient = 1
            # Make sure he can even buy that many chips
            if db_functions.he_can_afford(sender, amount):
                check = True

        elif direction == "out":
            detail= "out"
            sender = 1
            recipient = company
            check = True

        # Do the Insert, return a status message
        if check:
            try:
                e = db_functions.ledger_insert(sender, recipient, amount, asset, detail)
                return jsonify(status="success", msg=f"{company} {amount} Cash {detail}")
            except Exception as e:
                return jsonify(status="error", msg=e)
        else:
            return jsonify(status="error", msg="Not enough Money")
    except Exception as e:
        return jsonify(status="error", msg=e)

# ==================================================================================================

# ==================================================================================================
# === = = = = = Event Log = = = = = ================================================================
# ==================================================================================================
# Get the Event Log
@app.route("/api/log/event", methods=['GET'])
def get_event_log():
    try:
        event_log = db_functions.get_log("status")
        formatted_event_logs = []
        for log in event_log:
            event_id = int(log["detail"])
            jesus_so_many_queries = db_functions.get_that_event(event_id)
            event_title = jesus_so_many_queries["event_title"]
            msg = f"{log["sender_name"]} bought {event_title}"
            formatted_event_logs.append({"timestamp":log["timestamp"],"msg":msg})
        return jsonify(formatted_event_logs)
    except Exception as e:
        return jsonify(status="error", msg=e)
# ==================================================================================================
# === = = = = = Event API Thingies = = = = = =======================================================
# ==================================================================================================
@app.route("/api/event/list", methods=['GET'])
def get_event_list():
    try:
        list_of_events = db_functions.list_events()
        return jsonify(list_of_events)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Buy an Event and run it
@app.route("/api/event/purchase", methods=['POST'])
def buy_event():
    try:
        data = request.json
        buyer_id = int(data["buyer_id"])
        event_id = int(data["event_id"])
        event_details = db_functions.get_that_event(event_id)
        target = int(event_details["target"])
        price = int(event_details["price"])
        if db_functions.he_can_afford(buyer_id, price) or buyer_id == 1:
            try:
                db_functions.ledger_insert(buyer_id, 1, price, 7, event_id)
                if target == 1:
                    target_id = int(data["target_id"])
                    print(target_id)
                    db_functions.event_insert(target_id, event_id)
                else:
                    db_functions.event_insert(buyer_id, event_id)
                return jsonify(status="success", msg="Event purchased successfully")
            except Exception as e:
                return jsonify(status="error", msg=e)
        else:
            return jsonify(status="error", msg="Not enough Money")
    except Exception as e:
        return jsonify(status="error", msg=e)




# ==================================================================================================
# === = = = = = Event VOTE = = = = = ===============================================================
# ==================================================================================================
# Literally all we need to do is Create some inputs. We shall interpret the data later.
# No need to think too hard. This game doesn't need that. It just needs to exist.
# Sometimes that's all something has to do. . to have worth you know.

# Basic Voting. No need to overthink this
@app.route('/api/event/vote', methods=['POST'])
def post_vote():
    try:
        data = request.json
        company_id = int(data.get("company_id"))
        yay = int(data.get("yay"))
        nay = int(data.get("nay"))
        db_functions.ledger_insert(1, company_id, 0, 6, f"{yay}-{nay}")
        return jsonify(status="success", msg="Vote added")
    except Exception as e:
        return jsonify(status="error", msg=str(e))

# ==================================================================================================
# === = = = = = Invention = = = = = ================================================================
# ==================================================================================================
# Adding a new Invention
@app.route('/api/invention/add', methods=['POST'])
def new_invention():
    try:
        data = request.json
        invention_name = data.get("name")
        company_id = int(data.get("company_id"))
        yay = int(data.get("yay"))
        nay = int(data.get("nay"))
        vote = (yay - nay) / (yay + nay)
        funding_amount = int(data.get("amount"))
        investor_id = int(data.get("investor_id"))
        equity = int(data.get("equity")) # Percent
        x = db_functions.invention_insert(invention_name, company_id, vote, funding_amount, investor_id, equity)
        if x is True:
            if vote >= 0:
                good_bad = 1
            else:
                good_bad = 2
            db_functions.event_insert(company_id, good_bad)
            return jsonify(status="success", msg="Invention added")
        else:
            return jsonify(status="error", msg=str(x))
    except Exception as e:
        return jsonify(status="error", msg=str(e))


# ==================================================================================================
# === = = = = = Player Data List = = = = = =========================================================
# ==================================================================================================
# Get the Data, name, etc
@app.route('/api/player/data', methods=['GET'])
def get_player_data():
    try:
        invite_code = request.args.get('invite_code')
        player_data = db_functions.get_specific_balance(invite_code)
        return jsonify(player_data)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Format the Stocks
@app.route('/api/player/stock', methods=['GET'])
def get_player_stock():
    try:
        invite_code = request.args.get('invite_code')
        stock_object = db_functions.get_specific_market(invite_code)
        return jsonify(stock_object)
    except Exception as e:
        return jsonify(status="error", msg=e)

# Get the News
# print("fuck shit")
@app.route('/api/log/news', methods=['GET'])
def get_news():
    try:
        return jsonify(db_functions.get_news())
    except Exception as e:
        return jsonify(status="error", msg=e)

# Get the Player Inbox
@app.route('/api/player/Inbox', methods=['GET'])
def get_player_inbox():
    try:
        invite_code = request.args.get('invite_code')
        inbox_list = db_functions.get_player_inbox(invite_code)
        return jsonify(inbox_list)
    except Exception as e:
        return jsonify(status="error", msg=e)



# Active Status effects and when they would stop affecting
@app.route('/api/player/status', methods=['GET'])
def get_player_status():
    try:
        invite_code = request.args.get("invite_code")
        status_list = db_functions.check_status(invite_code)
        return jsonify(status_list)
    except Exception as e:
        return jsonify(status="error", msg=e)



# ==================================================================================================
# === = = = = = Start API = = = = = ================================================================
# ==================================================================================================
if __name__ == '__main__':
    # host='0.0.0.0' makes it accessible on your Local WiFi
    app.run(host='0.0.0.0', port=5000, debug=True)