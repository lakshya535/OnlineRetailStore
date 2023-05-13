from flask import Flask,render_template,request,jsonify,url_for,redirect,session
import mysql.connector

db = mysql.connector.connect(host="localhost",user="root",passwd="1234",database="online_store")

app = Flask(__name__) #create an app using Flask
app.secret_key = 'lmao'


@app.route('/')     #Now define the basic route / and its corresponding request handler:
def index():
    return render_template('index.html')


@app.route('/products')
def products():
    # Check if customer is logged in
    if 'phone_number' in session:
        cursor = db.cursor() 
        cursor.execute('SELECT * FROM product')
        results = cursor.fetchall()
        return render_template('products.html', products=results)
    else:
        return redirect(url_for('index'))
    
@app.route('/selling_product')
def selling_product():
    # Check if seller is logged in
    if 'phone_number' in session:
        phone_number = session['phone_number']
        cursor = db.cursor() 
        cursor.execute('SELECT * FROM product WHERE productID IN (SELECT productID from sells WHERE sellerID=(SELECT sellerID from seller WHERE phoneNumber=%s)) ',(phone_number,))
        results = cursor.fetchall()
        return render_template('products.html', products=results)
    else:
        return redirect(url_for('index'))
    
@app.route('/add_sell_product', methods=['GET', 'POST'])
def add_sell_product():
    phone_number = session['phone_number']
    if request.method == 'POST':
        # Get form data
        productID = request.form['productID']

        cur=db.cursor()

        cur.execute("INSERT INTO sells(sellerID,productID) VALUES ((SELECT sellerID FROM seller WHERE phoneNumber=%s),%s)", (phone_number,productID))
        db.commit()
        cur.close()

        # Redirect to login page
        return redirect(url_for('seller_landing'))
    return render_template('add_sell_product.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']

        cur=db.cursor()

        # Insert new customer into database
        cur.execute("INSERT INTO customer (first_name, last_name, email, phoneNumber) VALUES (%s, %s, %s, %s)", (first_name, last_name, email, phone_number))
        db.commit()
        cur.execute("INSERT INTO cart(customerID,discount,total_Cost) VALUES (LAST_INSERT_ID(),%s,%s)",(0,0))
        db.commit()
        cur.close()

        # Redirect to login page
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        first_name = request.form['first_name']
        phone_number = request.form['phone_number']

        # Check if customer exists
        query = "SELECT * FROM customer WHERE first_name = %s AND phoneNumber = %s"
        cursor=db.cursor()

        cursor.execute(query, (first_name,phone_number))
        customer = cursor.fetchone()
        
        if customer:
            # Create session for logged in customer
            session['first_name'] = first_name
            session['phone_number'] = phone_number

            return redirect(url_for('landing'))
        else:
            message = "Invalid customerID or first name. Please try again."
            return render_template('login.html', message=message)
    else:
        return render_template('login.html')
    
@app.route('/landing')
def landing():
    # Check if customer is logged in
    if 'phone_number' in session:
        return render_template('landing.html', show_product_button=True, show_cart_button=True)
    else:
        return redirect(url_for('index')) 
    
@app.route('/seller_landing')
def seller_landing():
    # Check if seller is logged in
    if 'phone_number' in session:
        return render_template('seller_landing.html', sell_product_button=True)
    else:
        return redirect(url_for('index')) 
    

@app.route('/seller_register', methods=['GET', 'POST'])
def seller_register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']

        cur=db.cursor()

        # Insert new customer into database
        cur.execute("INSERT INTO seller (first_name, last_name,phoneNumber) VALUES (%s, %s, %s)", (first_name, last_name,phone_number))
        db.commit()
        cur.close()

        # Redirect to login page
        return redirect(url_for('seller_login'))
    return render_template('seller_register.html')


@app.route('/seller_login', methods=['GET', 'POST'])
def seller_login():
    if request.method == 'POST':
        first_name = request.form['first_name']
        phone_number = request.form['phone_number']

        # Check if seller exists
        query = "SELECT * FROM seller WHERE first_name = %s AND phoneNumber = %s"
        cursor=db.cursor()

        cursor.execute(query, (first_name,phone_number))
        seller = cursor.fetchone()
        
        if seller:
            # Create session for logged in seller
            session['first_name'] = first_name
            session['phone_number'] = phone_number

            return redirect(url_for('seller_landing'))
        else:
            message = "Invalid sellerID or first name. Please try again."
            return render_template('seller_login.html', message=message)
    else:
        return render_template('seller_login.html')

    
# Add to Cart
@app.route('/add_cart', methods=['GET', 'POST'])
def add_cart():
    phone_number = session['phone_number']
    if request.method == 'POST':
        # Get form data
        productID = request.form['productID']
        # productName = request.form['productName']
        quantity= request.form['quantity']

        cur=db.cursor()

        cur.execute("INSERT INTO cart_item(customerID,productID,quantity) VALUES ((SELECT customerID FROM customer WHERE phoneNumber=%s),%s,%s)", (phone_number,productID,quantity))
        db.commit()
        cur.execute("UPDATE cart_item SET cost = (SELECT productPrice FROM product WHERE product.productID = %s) * %s WHERE cart_item.customerID=(SELECT customerID FROM customer WHERE phoneNumber=%s) AND cart_item.productID=%s;",(productID,quantity,phone_number,productID))
        cur.execute("UPDATE cart SET Total_Cost = (SELECT SUM(cost) FROM cart_item WHERE cart_item.customerID = cart.customerID) * (1 - (discount / 100)) WHERE cart.customerID=(SELECT customerID FROM customer WHERE phoneNumber=%s);",(phone_number,))
        db.commit()
        cur.close()

        # Redirect to login page
        return redirect(url_for('landing'))
    return render_template('add_cart.html')


@app.route('/cart')
def cart():
    if 'phone_number' in session:
        phone_number = session['phone_number']

        cursor = db.cursor()
        cursor.execute('''SELECT cart_item.productID, 
(SELECT productName FROM product WHERE productID = cart_item.productID) AS productName, cart_item.quantity, 
(SELECT productPrice FROM product WHERE productID = cart_item.productID) AS productPrice,cart_item.cost
FROM cart, cart_item WHERE cart.customerID = cart_item.customerID AND cart.customerID = (SELECT customerID FROM customer WHERE phoneNumber=%s)''', (phone_number,))
        cart_items = cursor.fetchall()

        cursor2=db.cursor()
        cursor2.execute('''SELECT discount,total_Cost FROM cart WHERE cart.customerID=(SELECT customerID FROM customer WHERE phoneNumber=%s)''',(phone_number,))
        cart_info=cursor2.fetchall()

        return render_template('cart.html', cart_items=cart_items,cart_info=cart_info)
    else:
        return redirect(url_for('index'))
    
    
@app.route('/buy_cart')
def buy_cart():
    if 'phone_number' in session:
        phone_number = session['phone_number']

        cursor = db.cursor()
        cursor.execute('''INSERT INTO order_detail (customerID,deliveryID,orderStatus ,totalCost) VALUES ((Select customerID from customer where phoneNumber=%s)
, 4, 'dispatching',(SELECT total_Cost FROM cart WHERE cart.customerID =    (Select customerID from customer where phoneNumber=%s)
))''',(phone_number,phone_number))
        db.commit()
        cursor.execute('INSERT INTO payment (modePayment, dateTransaction, orderID) VALUES ("UPI", CURDATE(), last_insert_id())')

        db.commit()

    cursor.execute('''
        UPDATE product 
        JOIN cart_item ON product.productID = cart_item.productID 
        SET product.productStock = product.productStock - cart_item.quantity
        WHERE cart_item.customerID = (
            SELECT customerID 
            FROM customer 
            WHERE phoneNumber = %s
        )''', (phone_number,))
    db.commit()

    cursor.execute('''
        DELETE FROM cart_item 
        WHERE customerID = (
            SELECT customerID 
            FROM customer 
            WHERE phoneNumber = %s
        )''', (phone_number,))
    db.commit()

    cursor.execute('''
        UPDATE cart 
        SET Total_Cost = (
            SELECT SUM(cost) 
            FROM cart_item 
            WHERE cart_item.customerID = cart.customerID
        ) * (1 - (discount / 100))
    ''')
    db.commit()

    return redirect(url_for('after_buy_landing'))


@app.route('/after_buy_landing')     
def after_buy_landing():
    return render_template('after_buy_landing.html')

    

    


















#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

@app.route('/embedded1')
def embedded1():
    mycursor = db.cursor()
    mycursor.execute('''SELECT order_detail.orderID, payment.DateTransaction, order_detail.totalCost,
customer.first_name
FROM order_detail
JOIN payment ON order_detail.orderID = payment.orderID
JOIN customer ON order_detail.customerID = customer.customerID
WHERE payment.DateTransaction BETWEEN '2022-01-01' AND '2022-03-01';''')

    results = mycursor.fetchall()
    for x in results:
        x = str(x)
        x = x.replace("datetime.date", "")
        x = x.replace("'", "")
        print(x[1:len(x) - 1])
    return render_template('embedded1.html',embedded1=results)

@app.route('/embedded2')
def embedded2():
    mycursor = db.cursor()
    mycursor.execute('''SELECT customer.customerID, customer.first_name, SUM(order_detail.totalCost) as
Total_Spent
FROM customer
JOIN order_detail ON customer.customerID = order_detail.customerID
GROUP BY customer.customerID
HAVING SUM(order_detail.totalCost) > 10000;''')

    results = mycursor.fetchall()
    for x in results:
        x = str(x)
        x = x.replace("Decimal", "")
        x = x.replace("(", "")
        x = x.replace(")", "")
        x = x.replace("'", "")
        print(x)
    return render_template('embedded2.html',embedded2=results)

@app.route('/embedded3')
def embedded3():
    mycursor = db.cursor()
    mycursor.execute('''SELECT
cart_item.productID,
(SELECT productName FROM product WHERE productID = cart_item.productID) AS
productName, cart_item.quantity,
(SELECT productPrice FROM product WHERE productID = cart_item.productID) AS
productPrice,cart_item.cost
FROM cart, cart_item
WHERE
cart.customerID = cart_item.customerID AND cart.customerID = 10;''')

    results = mycursor.fetchall()
    for x in results:
        x = str(x)
        x = x.replace("Decimal", "")
        x = x.replace("(", "")
        x = x.replace(")", "")
        x = x.replace("'", "")
        print(x)
    return render_template('embedded3.html',embedded3=results)


#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------
@app.route('/olap1')
def olap1():
    cursor=db.cursor()
    cursor.execute('''SELECT deliveryagent.deliveryID,deliveryagent.first_name, COUNT(DISTINCT order_detail.orderID) as total_orders, SUM(order_detail.totalCost) as total_revenue 
FROM deliveryagent
JOIN order_detail ON deliveryagent.deliveryID = order_detail.deliveryID
JOIN payment ON order_detail.orderID = payment.orderID
WHERE YEAR(payment.dateTransaction) = YEAR(payment.dateTransaction) 
GROUP BY deliveryagent.deliveryID
ORDER BY total_revenue DESC''')
    results=cursor.fetchall()
    return render_template('olap1.html',olap1=results)

@app.route('/olap2')
def olap2():
    cursor=db.cursor()
    cursor.execute('''SELECT customer.customerID,customer.first_name, COUNT(order_detail.orderID) AS
total_orders
FROM customer
LEFT JOIN order_detail ON customer.customerID = order_detail.customerID
GROUP BY customer.customerID
ORDER BY total_orders DESC
''')
    results=cursor.fetchall()
    return render_template('olap2.html',olap2=results)

@app.route('/olap3')
def olap3():
    cursor=db.cursor()
    cursor.execute('''SELECT pc.categoryName, COUNT(belongs.productID) AS total_products
FROM product_category pc
LEFT JOIN belongs  ON pc.categoryID = belongs.categoryID
GROUP BY pc.categoryName;''')
    results=cursor.fetchall()
    return render_template('olap3.html',olap3=results)

@app.route('/olap4')
def olap4():
    cursor=db.cursor()
    cursor.execute('''SELECT modePayment as Mode_Of_Payment,SUM(order_detail.totalCost) as Total_Order_Value,COUNT(order_detail.orderID) as NumberOf_Times_Used, AVG(order_detail.totalCost) AS Average_Order_Value
FROM payment
JOIN order_detail ON order_detail.orderID=payment.orderID
GROUP BY modePayment WITH ROLLUP;''')
    results=cursor.fetchall()
    return render_template('olap4.html',olap4=results)

@app.route('/olap5')
def olap5():
    cursor=db.cursor()
    cursor.execute('''SELECT YEAR(payment.dateTransaction) as Year, MONTH(payment.dateTransaction) as Month, SUM(order_detail.totalCost) as Revenue_Generated
FROM payment
INNER JOIN order_detail ON payment.orderID = order_detail.orderID
GROUP BY Year,Month WITH ROLLUP''')
    results=cursor.fetchall()
    return render_template('olap5.html',olap5=results)

#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

@app.route('/trigger')
def trigger():
    cursor1 = db.cursor() 
    cursor1.execute('''Select * from cart_item where customerID=4''')
    result1 = cursor1.fetchall()

    cursor2 = db.cursor() 
    cursor2.execute('''Select * from cart where customerID=4''')
    result2 = cursor2.fetchall()

    cursor3 = db.cursor() 
    cursor3.execute('''Insert into cart_item(customerID,productID,quantity) VALUES(4,5,50)''')
    db.commit()

    cursor5 = db.cursor() 
    cursor5.execute('''Select * from cart_item where customerID=4''')
    result5 = cursor5.fetchall()

    cursor4 = db.cursor() 
    cursor4.execute('''Select * from cart where customerID=4''')
    result4 = cursor4.fetchall()

    cursor6=db.cursor()
    cursor6.execute('''Update cart set discount=0, total_Cost=0 where customerID=4''')
    db.commit()

    cursor7=db.cursor()
    cursor7.execute('''Delete from cart_item where customerID=4''' )
    db.commit()

    return render_template('trigger.html', result1=result1,result2=result2,result4=result4,result5=result5)

if __name__ =='__main__': #Next, check if the executed file is the main program and run the app:
    app.run(debug=True) 


