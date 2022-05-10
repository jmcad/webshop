"""
Webshop
"""

from flask import Flask, request, g, render_template, redirect, url_for, session, abort, flash
import mysql.connector

app = Flask(__name__)

# Application config
app.config["DATABASE_USER"] = "root"
app.config["DATABASE_PASSWORD"] = "JMcadtinez98"
app.config["DATABASE_DB"] = "dat310"
app.config["DATABASE_HOST"] = "localhost"
app.debug = True  # only for development!
app.secret_key = 'some_secret'  # needed for seshion


def get_db():
    if not hasattr(g, "_database"):
        print("create connection")
        g._database = mysql.connector.connect(host=app.config["DATABASE_HOST"], user=app.config["DATABASE_USER"],
                                              password=app.config["DATABASE_PASSWORD"], database=app.config["DATABASE_DB"], use_pure=True)
    return g._database


@app.teardown_appcontext
def teardown_db(error):
    """Closes the database at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        print("close connection")
        db.close()


@app.route("/")
def index():
    # TODO: retrieve products from database
    db = get_db()
    cur = db.cursor()

    products = []
    sql = "SELECT `product_id`, `title`, `price`, `discount`, `img`, `description`, `details` FROM `products`"
    cur.execute(sql)
    for (product_id, title, price, discount, img, description, details) in cur:
        products.append({
            "pid": product_id,
            "title": title,
            "price": price,
            "discount": discount,
            "img": img,
            "description": description,
            "details": details
        })

    # get cart items from session
    cart = session.get("cart", {})
    return render_template("index.html", products=products, cart=cart)


@app.route("/product/<int:pid>")
def product(pid):
    # TODO: retrieve products from database

    db = get_db()
    cur = db.cursor()

    sql = "SELECT * FROM products WHERE product_id= " + str(pid)
    cur.execute(sql)
    product_id, title, price, discount, img, description, details = cur.fetchone()
    product_data = {
        "pid": product_id,
        "title": title,
        "price": price,
        "discount": discount,
        "img": img,
        "description": description,
        "details": details
    }

    # get cart items from session
    cart = session.get("cart", {})

    # compute and format total price
    mytotal = (product_data["price"] *
               (100 - product_data["discount"])/100.0)
    product_data["total"] = "{:.2f}".format(mytotal)
    return render_template("product.html", product=product_data, cart=cart)


@app.route("/add", methods=["POST"])
def addToCart():
    # get pid, size and count from request
    pid = request.form.get("pid")
    size = request.form.get("size")
    count = int(request.form.get("count", 1))

    # get cart items from session
    cart = session.get("cart", {})

    # TODO: add item to cart (ckeck for duplicates)

    db = get_db()
    cur = db.cursor()

    sql = "SELECT * FROM products WHERE product_id= " + str(pid)
    cur.execute(sql)
    product_id, title, price, discount, img, description, details = cur.fetchone()

    if pid not in cart:
        cart[pid] = {
            "product_id": product_id,
            "count": count,
            "size": size,
            "title": title,
            "price": price,
            "discount": discount
        }

    else:
        cart[pid]["count"] = int(cart[pid]["count"]) + int(count)

    item = cart[pid]
    item["pid"] = pid

    discounted = int((item["price"] *
                      (100 - item["discount"])/100.0))
    item["total"] = discounted

    # save in session
    session["cart"] = cart

    return redirect(url_for('product', pid=pid))


@app.route("/cart")
def cart():
    # get cart items from session
    cart = session.get("cart", {})

    # retrieve necessary additional information from products

    total = 0

    for pid in cart:
        total += float(cart[pid]["total"]) * int(cart[pid]["count"])

    return render_template("cart.html", cart=cart, total=total)


@app.route("/remove", methods=["GET"])
def remove():
    # TODO: get key from request and remove from cart in session

    pid = request.args.get("pid", None)

    cart = session.get("cart", {})

    cart.pop(pid)

    session["cart"] = cart

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["POST"])
def checkout():
    # address = {}
    # TODO: get address from request
    #   check that fields are not empty
    #   validate that AGB was checked
    #   retrieve cart from session and display checkout

    firstname = request.form.get("first_name", None)
    lastname = request.form.get("last_name", None)
    email = request.form.get("email", None)
    street = request.form.get("street", None)
    city = request.form.get("city", None)
    postalcode = request.form.get("postal", None)
    AGB = request.form.get("AGB", None)

    cart = session.get("cart", {})

    total = 0

    for pid in cart:
        total += float(cart[pid]["total"]) * int(cart[pid]["count"])

    if not cart:
        flash("Your cart is empty! Add a product to continue.")
        return redirect(url_for("cart"))

    return render_template("checkout.html", cart=cart, total=total, firstname=firstname, lastname=lastname, email=email, street=street, city=city, postalcode=postalcode, AGB=AGB)


@app.route("/checkout2", methods=["POST"])
def checkout2():
    # address = {}
    # TODO: get address from request
    #   check that fields are not empty
    #   validate that AGB was checked
    #   retrieve cart from session
    #   save address to database (orders)
    #   save cart items to database (order_rows)

    firstname = request.form.get("first_name", None)
    lastname = request.form.get("last_name", None)
    email = request.form.get("email", None)
    street = request.form.get("street", None)
    city = request.form.get("city", None)
    postalcode = request.form.get("postal", None)

    cart = session.get("cart", {})

    myorder = (
        "INSERT INTO `orders`(`first_name`, `last_name`, `email`, `street`, `city`, `postcode`) VALUES(%s, %s, %s, %s, %s, %s)")

    order_row = (
        "INSERT INTO `order_rows`(`product_id`, `order_id`, `count`, `size`) VALUES(%s, %s, %s, %s)")

    # commit updates to orders and order_rows
    db = get_db()
    cur = db.cursor()

    cur.execute(myorder, (firstname, lastname,
                          email, street, city, postalcode))

    neworderid = cur.lastrowid

    for item in cart.values():
        cur.execute(order_row, (item.get("pid"), neworderid,
                                item.get("count"), item.get("size")))

    db.commit()

    flash("Your order was successfully submitted! Thanks!")

    # TODO empty cart items from session
    cart.clear()
    session["cart"] = cart

    # TODO: render template, including success or error message
    return render_template("checkout2.html")


if __name__ == "__main__":
    app.run()
