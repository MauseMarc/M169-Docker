import datetime
from db_base import *
import random

# ==================================================================================================
# === = = = = = Global Variables = = = = = =========================================================
# ==================================================================================================
# Company Starting Money
STARTING_MONEY = 10000

# Time cycle.
CHECK_CYCLE = 30 # Seconds How often Stocks and such are updated.
DAY_LENGTH_M = 10 # Minutes
DAY_LENGTH_S = DAY_LENGTH_M * 60 # Seconds
CHECK_PER_DAY = DAY_LENGTH_S / CHECK_CYCLE

STOCK_CYCLE = 3 * CHECK_CYCLE # How old in seconds a stock transaction needs to be to be counted.
STOCK_BOTTOM = 75 # Lowest a Stock is allowed to go

STOCK_WEIGHT = 3 # How strongly Stock Purchase and Selling affects the stock.
STOCK_LIMIT = 75 /CHECK_PER_DAY # How much Percentage a Stock can move on purchase/selling alone

VOTE_WEIGHT = 5 / CHECK_PER_DAY # Max power one Vote can have.
VOTE_LIMIT = 25 / CHECK_PER_DAY # How much Votes can move the Stock

STATUS_WEIGHT = 5 / CHECK_PER_DAY # How strongly the status effects will influence Stocks. Status mod are 1-3
STATUS_LIMIT = 45 / CHECK_PER_DAY # How much Status effects max can influence Stock

DRINK_LIMIT = 50
DRINK_DECAY = 0.90 # How difficult it is to get it up or something (at weight 3 if 3 people buy a drink it won't increase %s but if nobody buys it will go down %s
DRINK_SENSITIVITY = 0.15  # 15% movement per 30s check
DECAY_RATE = 0.98  # Premium drops 2% every 30s if no one buys
VOLATILITY_FACTOR = 15  # Lower is more "chaotic," higher is more stable

BALANCE_WEIGHT = 4 / CHECK_PER_DAY # How heavily players should be punished for being in the minus / or rewarded when above 1mio

# --- Global Balancing Variables ---
INVENTION_PROFIT_MULT = 3    # Total potential ROI (1.5x funding)
INVENTION_PEAK_CYCLE = 5       # Cycle where it hits max profit
INVENTION_DECAY_RATE = 0.8     # How fast profit drops after peak
INVENTION_VOLATILITY = 0.2     # 20% random swing in payouts

# --- Penalty Variables ---
PENALTY_THRESHOLD = -0.5       # Score below this triggers fees
MAINTENANCE_FEE_BASE = 0.02    # 2% of funding charged per cycle
PENALTY_MAX_CYCLES = 6        # Fees stop after 14 cycles (Obsolescence)


# How the market is supposed to move. Generally UP or something
DRIFT = (2/CHECK_PER_DAY)

# Random thingy. I guess.
def get_volatility():
    VOLATILITY = random.randint(-10, 10)
    return round((VOLATILITY / CHECK_PER_DAY),2)

# ==================================================================================================
# === = = = = = Basic Functions = = = = = ==========================================================
# ==================================================================================================
# Format a SQL Querie as a Dictionary
def format_sql_fetch(sql_result):
    list_of_logs = []
    for row in sql_result:
        list_of_logs.append(dict(row))
    return list_of_logs

# Gets the Timestamp. Pretty good naming
def get_timestamp():
    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

# Compare a stored Time string to now, how many seconds.
def compare_time(then):
    format_str = "%Y-%m-%d %H:%M:%S"
    format_time = datetime.datetime.strptime(then, format_str)
    now = datetime.datetime.now()
    elapsed_time = now - format_time
    seconds_elapsed = elapsed_time.total_seconds()
    return seconds_elapsed

def how_long_ago(time_s):
    old_timestamp = datetime.datetime.now() - datetime.timedelta(seconds=time_s)
    return old_timestamp.strftime("%Y-%m-%d %H:%M:%S")


# ==================================================================================================
# === = = = = = Logic Checks = = = = = =============================================================
# ==================================================================================================

def he_can_afford(company_id, amount):
    company_balance = get_company_balance(company_id)
    if company_balance >= amount:
        return True
    else:
        return False


def calculate_trend(stock_list):
    newest = stock_list[0]
    second = stock_list[1]
    # Get the Trend
    trend = ""
    if newest > second:
        trend = "up"
    else:
        trend = "down"
    # Get the percent
    percent = int(((newest - second) / second * 100)*100)/100
    return percent, trend


# ==================================================================================================
# === = = = = = SELECT Functions = = = = = =========================================================
# ==================================================================================================
# Calculates how much every Company has from Ledger entries and returns them. Calculations and such.
def get_all_balance():
# Fetches all company balances in a single database hit.
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT c.id           as id,
                              c.company_name as name,
                              (
                                  COALESCE((SELECT SUM(amount) FROM ledger WHERE recipient_id = c.id), 0) -
                                  COALESCE((SELECT SUM(amount) FROM ledger WHERE sender_id = c.id), 0)
                                  )          as balance
                       FROM company c
                       """)
        results = cursor.fetchall()
        all_company_balances = format_sql_fetch(results)
    return all_company_balances

def get_specific_balance(invite_code):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id           as id,
                  c.company_name,
                  c.company_type,
                  (
                      COALESCE((SELECT SUM(amount) FROM ledger WHERE recipient_id = c.id), 0) -
                      COALESCE((SELECT SUM(amount) FROM ledger WHERE sender_id = c.id), 0)
                      )          as cash
            FROM company c WHERE c.code = %s
        """, (invite_code,))
    result = cursor.fetchall()
    formatted = format_sql_fetch(result)[0]
    return formatted


# Gets the Log of any Asset
def get_log(asset_type):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT ledger.id, ledger.timestamp,
                              g.company_name AS sender_name,
                              m.company_name AS recipient_name,
                              a.asset_name,
                              ledger.amount,
                              ledger.detail
                       FROM ledger
                                JOIN company g ON ledger.sender_id = g.id
                                JOIN company m ON ledger.recipient_id = m.id
                                JOIN asset a ON ledger.asset_id = a.id
                       WHERE ledger.asset_id IN (SELECT id FROM asset WHERE category = %s)
                       ORDER by ledger.timestamp ASC
                       """, (asset_type,))
        result = cursor.fetchall()
        list_of_logs = format_sql_fetch(result)
        return list_of_logs


# Gets Log but no Foreign Key translation
def latest_bar_purchase():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT * FROM ledger
                       WHERE ledger.asset_id IN (SELECT id FROM asset WHERE category = %s)
                       ORDER by ledger.timestamp DESC
                       """, ("drink",))
        result = cursor.fetchall()
        list_of_logs = format_sql_fetch(result)
        return list_of_logs


# Get the current price of any Asset
def get_asset_worth(asset_id):
    conn = get_db()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT worth FROM stock_ledger 
                WHERE asset_id = %s
                ORDER BY id DESC LIMIT 1
            """, (asset_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return 0
    except Exception as e:
        print(e)
        return 0

# Get all the drinks and their current prices
def get_drink_list():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                    SELECT asset.id, asset.asset_name, sl.worth
                    FROM stock_ledger sl
                        JOIN asset ON sl.asset_id = asset.id
                    WHERE asset.category = "drink"
                        AND sl.timestamp = (
                        SELECT MAX(timestamp)
                        FROM stock_ledger
                        WHERE asset_id = asset.id)
        """)
        result = cursor.fetchall()
    drink_list = format_sql_fetch(result)
    return drink_list


# Get the balance of a specific Company
def get_company_balance(company_id):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT (COALESCE((SELECT SUM(amount) FROM ledger WHERE recipient_id = c.id), 0) -
                               COALESCE((SELECT SUM(amount) FROM ledger WHERE sender_id = c.id), 0))
                       FROM company c
                       WHERE c.id = %s
                       """, (company_id,))
        result = cursor.fetchone()
        company_balance = result[0]
        return company_balance if company_balance else 0

# Get all the Loans available and Format
def get_loan_list():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                SELECT * FROM asset WHERE category = "loan"
            """)
        result = cursor.fetchall()
        formated = format_sql_fetch(result)
        json_formated = []
        for loan in formated:
            slicer = loan["asset_code"].split("-")
            if slicer[0].isdigit():
                json_formated.append({"package":loan["asset_name"],
                                      "amount":int(slicer[0]),
                                      "interest":int(slicer[1]),
                                      "id":loan["id"]
                                      })
        return json_formated


# Get Active Loans. So we can pay em Back
def get_active_loans():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                    SELECT l.id, l.timestamp, l.company_id, c.company_name, l.asset_id, a.asset_name AS package, l.amount, l.interest_rate AS interest 
                    FROM loan l
                        JOIN company c on l.company_id = c.id
                        JOIN asset a ON l.asset_id = a.id
                    WHERE l.ongoing = 1
        """)
        result = cursor.fetchall()
    active_loans = format_sql_fetch(result)

    for loan in active_loans:
        # We have to figure out how old this Loan is. Aka how many "Game Cycles" it was active
        # The longer the more expensive the Repayment gets.
        timestamp = loan["timestamp"]

        elapsed_time = compare_time(timestamp)  # In Seconds
        cycle_length = DAY_LENGTH_S
        rounding = elapsed_time % cycle_length
        # How many Cycles old is this Loan.
        cycle_count = int((elapsed_time - rounding) / cycle_length)
        interest_formated = (int(loan["interest"]) / 100) + 1
        amount_to_pay = int(int(loan["amount"]) * interest_formated ** cycle_count)
        loan["current_amount"] = amount_to_pay

    return active_loans

# STOCK MARKET
# Get all the important data
def get_stock_market():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sl.timestamp, sl.asset_id, sl.worth, a.asset_name, a.asset_code
            FROM stock_ledger sl
                JOIN asset a ON sl.asset_id = a.id
            WHERE a.category = "stock"
            ORDER BY sl.timestamp DESC
            """)
        result = cursor.fetchall()
    formated = format_sql_fetch(result)

    # How the fuck do I sort this now.
    sort_stocks = {}
    for thing in formated:
        if thing["asset_id"] not in sort_stocks:
            sort_stocks[thing["asset_id"]] = [thing]  # Include the first item!
        else:
            sort_stocks[thing["asset_id"]].append(thing)

    we_got_keys = list(sort_stocks.keys())

    # Now lets create our Fucky ass Object for Stocks
    full_stock = []
    last_updated = ""
    for key in we_got_keys:
        list_of_stocks = sort_stocks[key]
        stock_history = []
        for entry in list_of_stocks:
            stock_history.append(entry["worth"])
        stock_history = stock_history[:50]
        change_percent, trend = calculate_trend(stock_history)
        temp = list_of_stocks[0]
        last_updated = temp["timestamp"]
        stock_object = {
            "id":temp["asset_id"],
            "symbol":temp["asset_code"],
            "name":temp["asset_name"],
            "current_price":temp["worth"],
            "change_percent":change_percent,
            "trend":trend,
            "history":stock_history[::-1]
        }
        full_stock.append(stock_object)

    #final Object
    stock_market = {
        "last_updated":last_updated,
        "stocks":full_stock
    }
    return stock_market


def get_bar_market():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sl.timestamp, a.id, a.asset_name, sl.worth FROM stock_ledger sl
                JOIN asset a ON sl.asset_id = a.id
            WHERE a.category = "drink"
            ORDER by sl.timestamp DESC
        """)
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)
    # How the fuck do I sort this now.
    sort_stocks = {}
    for thing in formatted:
        if thing["id"] not in sort_stocks:
            sort_stocks[thing["id"]] = [thing]  # Include the first item!
        else:
            sort_stocks[thing["id"]].append(thing)

    we_got_keys = list(sort_stocks.keys())
    # Now lets create our Fucky ass Object for Stocks
    full_stock = []
    for key in we_got_keys:
        list_of_stocks = sort_stocks[key]
        stock_history = []
        for entry in list_of_stocks:
            stock_history.append(entry["worth"])
        stock_history = stock_history[:50]
        temp = list_of_stocks[0]
        stock_object = {
            "id": temp["id"],
            "asset_name": temp["asset_name"],
            "current_price": temp["worth"],
            "history": stock_history[::-1]
        }
        full_stock.append(stock_object)
    return full_stock


# Get a very specific stock and history. Of a company
def get_specific_market(invite_code):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                SELECT 
                    sl.timestamp, sl.asset_id, sl.worth, a.asset_name, a.asset_code,c.company_name
                FROM stock_ledger sl
                    JOIN asset a ON sl.asset_id = a.id
                    JOIN company c ON c.asset_id = a.id
                WHERE a.category = 'stock'
                    AND c.code = %s
                ORDER BY sl.timestamp DESC
        """, (invite_code,))
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)

    stock_history = []
    for entry in formatted:
        stock_history.append(entry["worth"])
    stock_history = stock_history[:50]
    change_percent, trend = calculate_trend(stock_history)
    temp = formatted[0]
    last_updated = temp["timestamp"]
    stock_object = {
        "last_updated":last_updated,
        "current_price": temp["worth"],
        "change_percent": change_percent,
        "trend": trend,
        "history": stock_history[::-1]
    }
    return stock_object


def get_one_stock(stock_id):
    print("get_one_stock")
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT worth FROM stock_ledger WHERE asset_id = %s
            ORDER BY timestamp DESC
        """, (stock_id,))
        result = cursor.fetchone()
    worth = dict(result)["worth"]
    print(worth)
    return worth

# Get all available Events to choose from. I guess %s
def list_events():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, event_title, target, price
            FROM event WHERE id > 2
        """)
        result = cursor.fetchall()
        formated = format_sql_fetch(result)
    return formated

# Get the Event and it's price
def get_that_event(event_id):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM event WHERE id = %s
        """, (event_id,))
        result = cursor.fetchone()
        formatted = dict(result)
    return formatted


# ==================================================================================================
# === = = = = = SQL Updates = = = = = ==============================================================
# ==================================================================================================
# Update Loans
def update_loan(loan_id):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE loan SET ongoing = 0 WHERE id = %s
        """, (loan_id,))


# ==================================================================================================
# === = = = = = SQL Inserts = = = = = ==============================================================
# ==================================================================================================
# Ledger Entry Function. For Purchases and Transactions
def ledger_insert(sender, recipient, amount, asset, detail):
    timestamp = get_timestamp()
    conn = get_db()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO ledger (timestamp, sender_id, recipient_id, amount, asset_id, detail) 
                VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s)
            """,(timestamp, sender, recipient, amount, asset, detail))

            conn.commit()
    except Exception as e:
        return e

# Getting a Loan
def loan_insert(company, amount, interest, loan_id):
    timestamp = get_timestamp()
    conn = get_db()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                                    INSERT INTO loan (timestamp, company_id, asset_id, amount, interest_rate) 
                                    VALUES (%s,%s,%s,%s,%s)
                                """, (timestamp, company, loan_id, amount, interest))
            conn.commit()
    except Exception as e:
        return e

# Add a new invention
def invention_insert(inv_name, creator_id, vote, funding, investor_id, equity):
    timestamp = get_timestamp()
    conn = get_db()
    # First Check if that Invention Name already exists
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM asset WHERE asset_name = %s",(inv_name,))
        result = cursor.fetchone()
        if result:
            return "Duplicate"


    # Create this new Asset
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO asset (asset_name, category) VALUES (%s,%s)",
                           (inv_name, "invention"))
            conn.commit()
        if funding > 0:
            investor = investor_id
            equity_p = equity
        else:
            investor = 1
            equity_p = 0

        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO invention (timestamp, asset_id, creator_id, investor_id, percentage, vote_score, funding_amount) 
                VALUES (
                %s,
                (SELECT id FROM asset WHERE asset_name = %s),
                %s,
                %s,
                %s,
                %s,
                %s
                )
            """, (timestamp, inv_name, creator_id, investor, equity_p, vote, funding))
            conn.commit()

        if investor != 1:
            # Now we Charge whoever was stupid enough to Fund the invention
            with conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                                INSERT INTO ledger (timestamp, sender_id, recipient_id, amount, asset_id, detail) 
                                VALUES (%s,%s,%s,%s,
                                (SELECT id FROM asset WHERE asset_name = %s),
                                %s)
                            """, (timestamp, investor_id, creator_id, funding, inv_name, "investor"))


        return True
    except Exception as e:
        return e

# Insert a new Event Instance
def event_insert(affected_id, event_id):
    timestamp = get_timestamp()
    conn = get_db()
    if event_id > 10:
        handle_event_exceptions(event_id)
        return
    else:
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO active_event (affected_id, event_id, timestamp, duration_s, story_id) 
                VALUES (%s,%s,%s,(SELECT duration FROM event WHERE id = %s)*%s,
                (SELECT id FROM story where story_type = (SELECT story_type FROM event WHERE id = %s) ORDER BY RANDOM() LIMIT 1))
            """, (affected_id, event_id, timestamp, event_id, DAY_LENGTH_S, event_id))
            conn.commit()
        return


# Specifically for Market Crashes
def handle_event_exceptions(event_id):
    timestamp = get_timestamp()
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT event_title FROM event WHERE id = %s
        """, (event_id,))
        result = cursor.fetchone()
        if result:
            company_type = dict(result)["event_title"].split("-")[1]
    # Now that we have the company type, we can insert this neat little event for all people affected.
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO active_event (affected_id, event_id, timestamp, duration_s, story_id)
            SELECT id, %s, %s, (SELECT duration FROM event WHERE id = %s)*%s, (SELECT id FROM story where story_type = (SELECT story_type FROM event WHERE id = %s) ORDER BY RANDOM() LIMIT 1)
            FROM company WHERE company_type = %s
        """, (event_id, timestamp, event_id, DAY_LENGTH_S, event_id, company_type))
        conn.commit()


# handle_event_exceptions(12)

def is_drink_event():
    # # print("")
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT timestamp, affected_id, duration_s FROM active_event
            WHERE event_id = 6
        """)
        result = cursor.fetchall()
    if result:
        formatted = format_sql_fetch(result)
        # Quick filter for active Status effects
        active_status = []
        for x in formatted:
            if compare_time(x["timestamp"]) <= int(x["duration_s"]):
                active_status.append(x["affected_id"])
        # print(active_status)
        if len(active_status) > 1:
            who_pays = random.choice(active_status)
            return who_pays
        elif len(active_status) > 0:
            who_pays = active_status[0]
            return who_pays
    return False

# %s%s%s I NEED THE ID OF THE COMPANY THAT IS GONNA PAY
# ALSO SOMEHOW IF THAT FIRST PLAYER COULDN'T PAY. THEN THE NEXT IN LINE SHOULD.
# # print(is_drink_event())

# ==================================================================================================
# === = = = = = Company Creation = = = = = =========================================================
# ==================================================================================================
# Create Company Function
def start_company(company_name,stock_code, company_type, invite_code):
    conn = get_db()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM company WHERE company_name = %s
            """, (company_name,))
            result = cursor.fetchall()
            if result:
                # print("Company already exists")
                return False

    except Exception as e:
        # print(e)
        return False, e

    try:
        asset_name = company_name + "Stock"
        asset_code = stock_code
        asset_type = "stock"

        # Create Company Stock Asset
        with conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO asset (asset_name, asset_code, category) VALUES (%s,%s,%s)", (asset_name, asset_code, asset_type))

            conn.commit()
        # Create Company entry with correct Stock pointer thing
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO company (company_name, company_type, asset_id, code) 
                VALUES (%s,%s,(SELECT id FROM asset WHERE asset_name = %s),%s)
                """, (company_name, company_type, asset_name, invite_code))

            conn.commit()

        # Give this new Company Starting Money
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id FROM company WHERE company_name = %s
                """, (company_name,))
            result = cursor.fetchone()

        new_company_id = dict(result)
        # Start em off with Money
        sender = 1 # Bank
        recipient = new_company_id["id"]
        asset = 1 # Dooolers
        detail = "Starting Money"
        ledger_insert(sender, recipient, STARTING_MONEY, asset, detail)
        return True

    except Exception as e:
        return e

def get_invention_nts(company_id):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
                SELECT a.asset_name FROM invention i
                JOIN asset a ON a.id = i.asset_id
                WHERE i.creator_id = %s
            """, (company_id,))
        result = cursor.fetchone()
    if result:
        formatted = dict(result)["asset_name"]
        return formatted
    else:
        return False


def get_invention(event_timestamp, company_id):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT a.asset_name FROM invention i
            JOIN asset a ON a.id = i.asset_id
            WHERE i.timestamp = %s AND i.creator_id = %s
        """, (event_timestamp, company_id))
        result = cursor.fetchone()
    if result:
        formatted = dict(result)["asset_name"]
        return formatted
    else:
        return False

# Get the News for the Big screen. Ain't that hard
def get_news():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT ae.affected_id, c.company_name, c.company_type, ae.timestamp, ae.story_id, s.story_title, s.story_text, s.story_type FROM active_event ae
            JOIN company c ON c.id = ae.affected_id
            JOIN story s ON s.id = ae.story_id
            ORDER BY ae.timestamp ASC
        """)
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)
    # delete duplicates aka same timestamp and story id
    seen = set()
    unique_list = []
    for d in formatted:
        # Use a tuple as the key because lists/dicts aren't hashable
        identifier = (d['timestamp'], d['story_id'])

        if identifier not in seen:
            news_text = d['story_text']
            time_to_modify = news_text.split("-")
            new_message = ""
            for element in time_to_modify:
                if element == "COMPANY":
                    new_message += d["company_name"]
                elif element == "CATEGORY":
                    new_message += d["company_type"]
                elif element == "ASSET":
                    if d["story_type"] == "invention":
                        # FUCK SHIT GET THE INVENTION THAT MATCHES WITH THE TIMESTAMP
                        invention_name = get_invention(d["timestamp"], d["affected_id"])
                    else:
                        # need to get the newest invention of this company
                        invention_name = get_invention_nts(d["affected_id"])
                        if type(invention_name) != str:
                            invention_name = "=REDACTED="
                    new_message += invention_name
                else:
                    new_message += element
            news_object = {
                "timestamp": d['timestamp'],
                "title": d['story_title'],
                "msg": new_message
            }
            unique_list.append(news_object)
            seen.add(identifier)
    return unique_list


# ==================================================================================================
# === = = = = = No Mans Land = = = = = =============================================================
# ==================================================================================================


# Transfer Money Function
def transfer_money(sender, recipient, amount):
    ledger_insert(sender, recipient, amount, 1, "Money transfer")

# start_company("Cock","medical")
# transfer_money(2,3,50)

def ADM_get_all_logs():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT ledger.id,
                              ledger.timestamp,
                              g.company_name AS sender_name,
                              m.company_name AS recipient_name,
                              a.asset_name,
                              ledger.amount,
                              ledger.detail,
                              a.category
                       FROM ledger
                                JOIN company g ON ledger.sender_id = g.id
                                JOIN company m ON ledger.recipient_id = m.id
                                JOIN asset a ON ledger.asset_id = a.id
                       ORDER by ledger.timestamp DESC
                    """)
        result = cursor.fetchall()
        list_of_logs = format_sql_fetch(result)
        return list_of_logs


def get_company_asset():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT c.id, c.company_name, c.company_type, c.asset_id, a.asset_name, a.category FROM company c
                           JOIN asset a ON a.id = c.asset_id
                       WHERE a.category = "stock"
                       """)
        result = cursor.fetchall()
        list_of_logs = format_sql_fetch(result)
        return list_of_logs


def insert_market(asset_id, worth):
    timestamp = get_timestamp()
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
             INSERT INTO stock_ledger (timestamp, asset_id, worth) 
             VALUES (%s,%s,%s)""",(timestamp, asset_id, worth))
        conn.commit()


def restrict_number(number, restriction):
    final_num = number
    if number > restriction:
        final_num = restriction
    elif number <= -restriction:
        final_num = -restriction
    return final_num


def get_stock_transactions(stock_id):
    time_s = STOCK_CYCLE # nothing to do with Day Cycles
    old_timestamp = how_long_ago(time_s)
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
                SELECT * FROM ledger WHERE asset_id = %s
                AND timestamp > %s
                ORDER BY timestamp DESC
            """, (stock_id,old_timestamp))
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)
    stock_delta = 0
    for entry in formatted:
        if entry["sender_id"] == 1:
            stock_delta -= int(entry["detail"])
        elif entry["recipient_id"] == 1:
            stock_delta += int(entry["detail"])

    final_mod = stock_delta * STOCK_WEIGHT
    final_final = restrict_number(final_mod, STOCK_LIMIT)
    return final_final


def get_votes(company_id):
    time_s = 2 * DAY_LENGTH_S
    old_timestamp = how_long_ago(time_s)
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT detail FROM ledger 
            WHERE recipient_id = %s 
            AND timestamp > %s
            AND asset_id = 6 
        """, (company_id,old_timestamp))
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)
    final_vote = 0
    for entry in formatted:
        if entry["detail"]:
            split = entry["detail"].split("-")
            yay = int(split[0])
            nay = int(split[1])
            vote = (yay - nay) / (yay + nay)
            final_vote += round((vote * VOTE_WEIGHT),2)
    final_final = restrict_number(final_vote, VOTE_LIMIT)
    return final_final


def get_status_mod(company_id):
    # Check which one is active %s
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT ae.timestamp, ae.duration_s, e.severity, e.status_id FROM active_event ae
            JOIN event e ON e.id = ae.event_id
            WHERE ae.affected_id = %s
            ORDER BY ae.timestamp DESC
        """, (company_id,))
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)

    # Quick filter for active Status effects
    active_status = []
    for x in formatted:
        if compare_time(x["timestamp"]) <= int(x["duration_s"]):
            active_status.append(x)

    # Calculate the Severity and Add to the final status modifier.
    status_mod = 0
    for entry in active_status:
        severity = entry["severity"]
        if entry["status_id"] == 2:
            severity *= -1
        status_mod += severity * STATUS_WEIGHT

    # Put it all together and LIMIT the percentage
    final_final = restrict_number(status_mod, STATUS_LIMIT)
    return final_final


def calc_modifier(asset):
    # Select all mentions of buying and selling of Company Stocks
    stock_id = asset["asset_id"]
    company_id = asset["id"]
    modifier = 0

    stock_mod = get_stock_transactions(stock_id)
    print("stock_mod", stock_mod)
    modifier += stock_mod # Manipulating Final Modifier


    vote_mod = get_votes(company_id)
    print("vote_mod", vote_mod)
    modifier += vote_mod

    status_mod = get_status_mod(company_id)
    print("status_mod", status_mod)
    modifier += status_mod

    # If Company Balance in the minus, fuck em up.
    if not he_can_afford(company_id, 0):
        modifier -= 1 * BALANCE_WEIGHT
    # If company balance above a million. good great. Too big to fail
    if he_can_afford(company_id, 1000000):
        modifier += 1 * BALANCE_WEIGHT

    # Status Modifier
    return modifier


def generate_fake_market():
    for asset in get_company_asset():
        # print(asset)
        asset_id = asset["asset_id"]
        asset_worth = get_asset_worth(asset_id)
        # print(asset_worth)

        volatility = get_volatility()
        drift = DRIFT
        player_impact = calc_modifier(asset)
        print("player_impact", player_impact)
        print("volatility", volatility)
        print("drift", drift)
        # More Calculations

        new_worth = asset_worth * (1 + (drift + volatility + player_impact) / 100)
        print("unrounded worth",new_worth)
        new_worth = round(new_worth,2)

        if new_worth < STOCK_BOTTOM:
            new_worth = STOCK_BOTTOM
        print(asset["asset_name"], asset_worth, new_worth)
        insert_market(asset["asset_id"], new_worth)

def get_drink_asset():
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, asset_name, asset_code FROM asset
                       WHERE category = "drink"
                       """)
        result = cursor.fetchall()
        list_of_logs = format_sql_fetch(result)
        return list_of_logs


def get_drink_mod(drink_id):
    time_s = DAY_LENGTH_S
    old_timestamp = how_long_ago(time_s)
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
                SELECT * FROM ledger WHERE asset_id = %s
                AND timestamp > %s
                ORDER BY timestamp DESC
            """, (drink_id,old_timestamp))
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)
    stock_delta = 0
    for entry in formatted:
        if entry["sender_id"] == 1:
            stock_delta -= int(entry["detail"])
        elif entry["recipient_id"] == 1:
            stock_delta += int(entry["detail"])
    print("stock delta", drink_id,stock_delta)
    return stock_delta


def calculate_new_price(asset_worth, drinks_bought, base_price):
    # 1. THE "GRAVITY" STEP
    # If the price is above base, it naturally wants to fall.
    if asset_worth > base_price:
        premium = asset_worth - base_price
        asset_worth = base_price + (premium * DECAY_RATE)

    # 2. THE "PRESSURE" STEP
    # We define 'Normal Volume' as 1 drink per 15 people every 5 mins.
    # For 30 people, that's 2 drinks.
    # Anything above 2 pushes price UP, anything below pushes price DOWN.
    neutral_volume = 2

    # This creates a multiplier: 0 buys = 0.9, 2 buys = 1.0, 10 buys = 1.4
    change_multiplier = 1 + ((drinks_bought - neutral_volume) / VOLATILITY_FACTOR)

    # 3. APPLY MOVEMENT
    target_price = base_price * change_multiplier
    price_gap = target_price - asset_worth
    new_worth = asset_worth + (price_gap * DRINK_SENSITIVITY)

    # 4. SAFETY FLOORS
    return max(base_price, round(new_worth, 2))

def generate_drink_market():
    # print("drink market")
    for asset in get_drink_asset():
        # print(asset)
        asset_id = asset["id"]
        asset_worth = get_asset_worth(asset_id)
        # print(asset_worth)

        drinks_bought = get_drink_mod(asset["id"])
        # More Calculations
        new_worth = calculate_new_price(asset_worth, drinks_bought, int(asset["asset_code"]))

        print(asset["asset_name"], asset_worth, new_worth)
        insert_market(asset["id"], round(new_worth))

# This will be triggered every cycle %s I guess
def calc_invention_payout():
    conn = get_db()

    # 1. Fetch all inventions
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invention")
        result = cursor.fetchall()

    inventions = format_sql_fetch(result)

    for inv in inventions:
        inv_id = inv["asset_id"]

        # Basic Stats
        funding = inv["funding_amount"]
        vote_score = inv["vote_score"]
        equity_pct = inv["percentage"]

        # Calculate time passed
        seconds_passed = compare_time(inv["timestamp"])
        cycles = int(seconds_passed / DAY_LENGTH_S)

        # --- BRANCH A: THE PUNISHMENT (Maintenance Fees) ---
        if vote_score <= PENALTY_THRESHOLD:
            # Safety: Stop punishing after the invention is "obsolete"
            if cycles > PENALTY_MAX_CYCLES:
                print(f"Invention {inv_id} is now obsolete (No fees).")
                continue

            # Severity scales from 1.0 (at -0.5 score) to 2.0 (at -1.0 score)
            severity = 1 + (abs(vote_score) - abs(PENALTY_THRESHOLD)) / (1 - abs(PENALTY_THRESHOLD))
            total_fee = int(funding * MAINTENANCE_FEE_BASE * severity)

            # Split the bill
            investor_hit = int(total_fee * (equity_pct / 100))
            creator_hit = total_fee - investor_hit

            print(f"FEE: Inv {inv_id} | Total: -{total_fee} | Creator: -{creator_hit} | Investor: -{investor_hit}")
            ledger_insert(inv["creator_id"], 1,  creator_hit, inv_id, "Invention Maintenance")
            ledger_insert(inv["investor_id"], 1, investor_hit, inv_id, "Investor Punishment")
            continue

        # --- BRANCH B: THE PAYOUT (Market Success) ---
        if vote_score > 0:
            # Calculate Base Yield (1/10th of funding * score)
            base_yield = (funding / 10) * vote_score

            # Growth/Decay Curve
            if cycles <= INVENTION_PEAK_CYCLE:
                time_factor = (cycles + 1) / INVENTION_PEAK_CYCLE
            else:
                time_factor = INVENTION_DECAY_RATE ** (cycles - INVENTION_PEAK_CYCLE)

            # Random Market Noise
            noise = random.uniform(1 - INVENTION_VOLATILITY, 1 + INVENTION_VOLATILITY)

            # Final calculation
            total_payout = int(base_yield * time_factor * noise * INVENTION_PROFIT_MULT)

            # Floor: Stop paying if the amount is less than 1% of funding
            if total_payout < (funding * 0.01):
                print(f"Inv {inv_id}: Payout too low, skipping.")
                continue

            # Split the loot
            investor_profit = int(total_payout * (equity_pct / 100))
            creator_profit = total_payout - investor_profit

            print(
                f"PAYOUT: Inv {inv_id} | Total: +{total_payout} | Creator: +{creator_profit} | Investor: +{investor_profit}")
            ledger_insert(1, inv["creator_id"], creator_profit, inv_id, "Invention Profit")
            ledger_insert(1, inv["investor_id"], investor_profit, inv_id, "Investor Equity")

        else:
            # Neutral inventions (score between 0 and -0.5) do nothing.
            print(f"Inv {inv_id}: Stagnant market (Score {vote_score}).")

# calc_invention_payout()

# Check what kind of Status effects are targeting the company
def check_status(invite_code):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT ae.timestamp, ae.duration_s, e.event_title, e.severity, e.status_id, c.id FROM active_event ae
            JOIN event e ON e.id = ae.event_id
            JOIN company c ON c.id = ae.affected_id
            WHERE c.code = %s
        """, (invite_code,))
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)
    status_list = []
    for status in formatted:
        initial_timestamp = status["timestamp"]
        time_s = int(status["duration_s"])
        format_str = "%Y-%m-%d %H:%M:%S"
        format_time = datetime.datetime.strptime(initial_timestamp, format_str)
        end_timestamp = format_time + datetime.timedelta(seconds=time_s)
        if end_timestamp < datetime.datetime.now():
            continue
        if status["status_id"] == 2:
            status_effect = 0
        else:
            status_effect = 1
        status_object = {
            "status_name": status["event_title"],
            "status_effect": status_effect,
            "severity": status["severity"],
            "duration": end_timestamp
        }
        status_list.append(status_object)
    # Now I would like to create a status object that is public image.
    if len(formatted) > 0:
        x = get_votes(formatted[0]["id"])
        if x > 0 :
            status_object = {
                "status_name": "Public Opinion",
                "status_effect": 1,
                "severity": x,
                "duration": "idk"
            }
            status_list.append(status_object)
        elif x < 0:
            status_object = {
                "status_name": "Public Opinion",
                "status_effect": 0,
                "severity": x * -1,
                "duration": "idk"
            }
            status_list.append(status_object)

        # Now to add the status of being too big to fail or Being a dying company
        if not he_can_afford(formatted[0]["id"], 0):
            status_object = {
                "status_name": "Balance in the Minus",
                "status_effect": 0,
                "severity": 1,
                "duration": "when you fix it"
            }
            status_list.append(status_object)
        if he_can_afford(formatted[0]["id"], 1000000):
            status_object = {
                "status_name": "Too big to fail",
                "status_effect": 1,
                "severity": 1,
                "duration": "when you fall"
            }
            status_list.append(status_object)
        return status_list
    else:
        return False


# Inserting a new company
def register_company(data):
    company_name = data["company_name"]
    company_type = data["company_type"]
    stock_code = data["shortform"]
    invite_code = data["invite_code"]
    try:
        start_company(company_name, stock_code, company_type, invite_code)
        return True
    except Exception as e:
        return False


# Check if a company exists already
def company_exists(invite_code):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM company WHERE code = %s
        """, (invite_code,))
        result = cursor.fetchall()
    if result:
        return True
    else:
        return False


def get_player_inbox(invite_code):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT 
            l.timestamp, l.amount, l.asset_id, a.asset_name, a.category, l.detail,
            l.sender_id, c.company_name AS sender_name,
            l.recipient_id, y.company_name AS recipient_name
            FROM ledger l
            JOIN company c ON c.id = l.sender_id
            JOIN company y ON y.id = l.recipient_id
            JOIN asset a ON a.id = l.asset_id
            WHERE c.code = %s OR y.code = %s
        """, (invite_code,invite_code))
        result = cursor.fetchall()
    formatted = format_sql_fetch(result)
    inbox_format = []
    this_company = formatted[0]["recipient_name"]
    for entry in formatted:
        direction = ""
        dir_value = 0 # if 0 then money gone. if 1 then yay more money
        if entry["recipient_name"] == this_company:
            direction = f"From {entry["sender_name"]}"
            dir_value = 1
        elif entry["sender_name"] == this_company:
            direction = f"To {entry["recipient_name"]}"
            dir_value = 0
        msg = f"{direction} {entry["amount"]} Dooolers | {entry["asset_name"]} | {entry["detail"]}"
        timestamp = entry["timestamp"]
        entry_object = {
            "msg": msg,
            "timestamp": timestamp,
            "direction": dir_value
        }
        inbox_format.append(entry_object)
    return inbox_format