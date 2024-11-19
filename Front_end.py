import streamlit as st
import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="1234",
            database="pesu_canteen"
        )
        if db.is_connected():
            print("Successfully connected to the database.")
            return db
        else:
            print("Failed to connect to the database.")
            return None
    except Error as err:
        print(f"Error: {err}")
        return None

def signup_user(name, phone, email, password, account_type, cuisine=None, location=None, rating=None):
    db = connect_to_database()
    if db is None:
        st.error("Could not connect to the database.")
        return

    try:
        cursor = db.cursor()

        if account_type == "Customer":
            cursor.execute("SELECT COUNT(*) FROM customer")
            user_count = cursor.fetchone()[0] + 2
            user_id = f"U_{user_count}"
            query = "INSERT INTO customer (user_id, phone, name, email, password) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (user_id, phone, name, email, password))
            st.success(f"{account_type} signed up successfully!")
            st.info(f"Your User ID: {user_id}")

        elif account_type == "Canteen Owner":
            # Validate that all fields are provided
            if not all([cuisine, location]):
                st.error("Please provide all the required fields for the canteen.")
                return

            cursor.execute("SELECT COUNT(*) FROM canteen")
            canteen_count = cursor.fetchone()[0] + 1
            canteen_id = f"C_{canteen_count}"
            canteen_name = name  # Assuming the 'name' field is used for the canteen name

            # Insert into canteen table
            query = """INSERT INTO canteen (canteen_id, canteen_name, phone, email, password, cuisine, location, rating)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (canteen_id, canteen_name, phone, email, password, cuisine, location, rating))
            st.success(f"{account_type} signed up successfully!")
            st.info(f"Your Canteen ID: {canteen_id}")

        db.commit()
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()



def authenticate_user(email, password):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # First, check in the customer table
        query = "SELECT * FROM customer WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            return user, "customer"

        # Next, check in the canteen table
        query = "SELECT * FROM canteen WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        canteen_owner = cursor.fetchone()

        if canteen_owner:
            return canteen_owner, "canteen_owner"

        return None, None

    except Error as e:
        st.error(f"Error: {e}")
        return None, None
    finally:
        if db:
            db.close()

def get_canteens():
    try:
        db = connect_to_database()
        cursor = db.cursor()

        query = "SELECT * FROM canteen"
        cursor.execute(query)
        canteens = cursor.fetchall()

        return canteens
    except Error as e:
        st.error(f"Error: {e}")
        return []  # Return empty list on error
    finally:
        if db:
            db.close()

def get_menu_items(canteen_id):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        query = "SELECT * FROM menu_items WHERE canteen_id = %s"
        cursor.execute(query, (canteen_id,))
        menu_items = cursor.fetchall()

        return menu_items
    except Error as e:
        st.error(f"Error: {e}")
        return []  # Return empty list on error
    finally:
        if db:
            db.close()

def calculate_total_price(order_id):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Call the stored function
        calculate_total_price_function = "SELECT CalculateTotalPrice(%s)"
        cursor.execute(calculate_total_price_function, (order_id,))
        total_price = cursor.fetchone()[0]

        return total_price

    except Error as e:
        st.error(f"Error: {e}")
        return 0  # Return zero on error
    finally:
        if db:
            db.close()

def place_order(user_id, canteen_id, items):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Generate order_id
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0] + 1
        order_id = f"O_{order_count}"

        # Insert order into the database
        order_query = """
            INSERT INTO orders (order_id, user_id, date, total_price, status, canteen_id)
            VALUES (%s, %s, CURDATE(), 0, 'Placed', %s)
        """
        cursor.execute(order_query, (order_id, user_id, canteen_id))

        # Insert order items into the database
        total_price = 0
        for item_id, quantity in items.items():
            order_item_id = f"OI_{order_id}_{item_id}"
            menu_item_query = "SELECT * FROM menu_items WHERE menuitem_id = %s"
            cursor.execute(menu_item_query, (item_id,))
            menu_item = cursor.fetchone()
            subtotal = quantity * menu_item[4]
            total_price += subtotal

            order_item_query = """
                INSERT INTO order_items (orderitem_id, order_id, user_id, canteen_id, menuitem_id, quantity, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(order_item_query, (order_item_id, order_id, user_id, canteen_id, item_id, quantity, subtotal))

        # Update total price in the order
        update_total_price_query = "UPDATE orders SET total_price = %s WHERE order_id = %s"
        cursor.execute(update_total_price_query, (total_price, order_id))

        db.commit()
        st.success("Order placed successfully!")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()


def confirm_order(user_id, user_type):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Get all orders for the user with status 'Placed'
        get_user_orders_query = """
        SELECT order_id, total_price
        FROM orders
        WHERE user_id = %s AND status = 'Placed'
        """
        cursor.execute(get_user_orders_query, (user_id,))
        user_orders = cursor.fetchall()

        if not user_orders:
            st.info("No orders to confirm.")
            return

        # Display orders
        st.subheader("Your Orders:")
        for order in user_orders:
            st.write(f"Order ID: {order[0]}, Total Price: ₹{order[1]:.2f}")

        # Allow user to select an order to confirm
        selected_order_id = st.selectbox("Select Order ID to Confirm", [order[0] for order in user_orders])

        if st.button("Confirm Order"):
            if user_type == "customer":
                # Call the stored procedure for the selected order
                cursor.callproc("ConfirmOrder", (selected_order_id,))
                db.commit()
                st.success(f"Order {selected_order_id} confirmed successfully!")
            else:
                st.warning("Log in as a customer to confirm an order.")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()


def view_current_orders(canteen_id):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Get all order_items for the canteen with orders that are 'Confirmed'
        get_canteen_orders_query = """
        SELECT OI.orderitem_id, OI.order_id, OI.menuitem_id, MI.item_name, MI.price, OI.quantity, OI.subtotal, OI.user_id
        FROM order_items OI
        INNER JOIN menu_items MI ON OI.menuitem_id = MI.menuitem_id
        INNER JOIN orders O ON OI.order_id = O.order_id
        WHERE OI.canteen_id = %s AND O.status = 'Confirmed'
        """
        cursor.execute(get_canteen_orders_query, (canteen_id,))
        
        canteen_orders = cursor.fetchall()

        if not canteen_orders:
            st.info("No current orders.")
            return

        # Display canteen orders
        st.subheader("Current Orders:")
        current_order_id = None
        for order_item in canteen_orders:
            order_id = order_item[1]
            if order_id != current_order_id:
                st.write(f"**Order ID: {order_id}**")
                current_order_id = order_id
            st.write(f"- {order_item[3]} (Quantity: {order_item[5]}, Subtotal: ₹{order_item[6]:.2f}, User ID: {order_item[7]})")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()


def add_menu_item(canteen_id, item_name, item_description, item_price):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Calculate the new menu item ID
        cursor.execute("SELECT COUNT(*) FROM menu_items")
        menu_item_count = cursor.fetchone()[0] + 1
        menu_item_id = f"M_{menu_item_count}"

        # Insert the new menu item into the database
        query = "INSERT INTO menu_items (menuitem_id, canteen_id, item_name, item_description, price) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (menu_item_id, canteen_id, item_name, item_description, item_price))
        db.commit()

        st.success("Menu item added successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()
    
def get_total_sales_by_canteen(canteen_id):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Display total sales for the canteen owner's canteen
        get_total_sales_query = """
        SELECT O.canteen_id, C.canteen_name, SUM(O.total_price) AS total_sales
        FROM orders O
        INNER JOIN canteen C ON O.canteen_id = C.canteen_id
        WHERE O.canteen_id = %s
        GROUP BY O.canteen_id, C.canteen_name
        """
        cursor.execute(get_total_sales_query, (canteen_id,))
        total_sales = cursor.fetchall()

        return total_sales

    except Error as e:
        st.error(f"Error: {e}")
        return []  # Return empty list on error
    finally:
        if db:
            db.close()

def delete_user(user_id, user_type):
    try:
        db = connect_to_database()
        cursor = db.cursor()

        if user_type == "customer":
            delete_user_query = "DELETE FROM customer WHERE user_id = %s"
        elif user_type == "canteen_owner":
            delete_user_query = "DELETE FROM canteen WHERE canteen_id = %s"
        else:
            st.error("Invalid user type")
            return

        cursor.execute(delete_user_query, (user_id,))
        db.commit()

        st.success("User deleted successfully!")

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if db:
            db.close()

def main():
    st.title("PESU CANTEEN PREBOOKING MANAGEMENT")

    # Initialize session_state variables
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    
    if st.session_state.user_id:
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.session_state.user_type = None
            st.sidebar.success("Logged out successfully.")

    st.sidebar.title("Menu")

    # Display only relevant options based on user type
    if st.session_state.user_type == "customer":
        menu_option = st.sidebar.radio("Choose an option", ["Place Order", "Confirm Order", "Delete User"])
    elif st.session_state.user_type == "canteen_owner":
        menu_option = st.sidebar.radio("Choose an option", ["View Current Orders", "Add Menu Item", "View Total Sales", "Delete User"])
    else:
        menu_option = st.sidebar.radio("Choose an option", ["Login", "Signup"])


    if menu_option == "Login":
        st.header("Login")
        login_option = st.radio("Login as", ["Customer", "Canteen Owner"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user, user_type = authenticate_user(email, password)

            if user and user_type == "customer" and login_option == "Customer":
                st.session_state.user_id = user[0]
                st.session_state.user_type = "customer"
                st.sidebar.success(f"Logged in as {user[2]}")
            elif user and user_type == "canteen_owner" and login_option == "Canteen Owner":
                st.session_state.user_id = user[0]
                st.session_state.user_type = "canteen_owner"
                st.sidebar.success(f"Logged in as {user[2]} (Canteen Owner)")
            else:
                st.sidebar.error("Authentication Failed. Please check your credentials.")

    elif menu_option == "Signup":
        st.header("Signup")
        account_type = st.radio("Account Type", ["Customer", "Canteen Owner"])
        name_label = "Full Name" if account_type == "Customer" else "Canteen Name"
        name = st.text_input(name_label)
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if account_type == "Canteen Owner":
            cuisine = st.text_input("Cuisine")
            location = st.text_input("Location")
            rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=0.0)
        else:
            cuisine = None
            location = None
            rating = None

        if st.button("Signup"):
            signup_user(name, phone, email, password, account_type, cuisine, location, rating)
            
    elif menu_option == "Delete User":
        st.header("Delete User")
        if st.button("Delete User"):
            delete_user(st.session_state.user_id, st.session_state.user_type)
            st.session_state.user_id = None
            st.session_state.user_type = None
            st.sidebar.info("User deleted. Please sign up or log in.")

    elif menu_option == "Place Order" and st.session_state.user_type == "customer":
        st.header("Place Order")

        # Get canteens
        canteens = get_canteens()
        if not canteens:
            st.error("No canteens available.")
            return
        canteen_names = [canteen[1] for canteen in canteens]
        selected_canteen_name = st.selectbox("Select Canteen", canteen_names, key="selected_canteen")

        # Get menu items for the selected canteen
        selected_canteen_id = next(canteen[0] for canteen in canteens if canteen[1] == selected_canteen_name)
        menu_items = get_menu_items(selected_canteen_id)

        if not menu_items:
            st.error("No menu items available for this canteen.")
            return

        # Display menu items
        st.subheader("Menu Items:")
        for item in menu_items:
            st.write(f"{item[2]} - Price: ₹{item[4]:.2f}")

        # Order form
        st.subheader("Place Your Order:")
        items = {}
        for item in menu_items:
            quantity = st.number_input(f"Quantity of {item[2]}", min_value=0, key=f"quantity_{item[0]}")
            if quantity > 0:
                items[item[0]] = quantity

        if st.button("Place Order"):
            place_order(st.session_state.user_id, selected_canteen_id, items)

    elif menu_option == "Confirm Order" and st.session_state.user_type == "customer":
        st.header("Confirm Order")
        confirm_order(st.session_state.user_id, st.session_state.user_type)

    elif menu_option == "View Current Orders" and st.session_state.user_type == "canteen_owner":
        st.header("View Current Orders")
        view_current_orders(st.session_state.user_id)
    
    elif menu_option == "Add Menu Item" and st.session_state.user_type == "canteen_owner":
        st.header("Add Menu Item")

        # Get canteen ID for the canteen owner
        canteen_id = st.session_state.user_id

        # Input fields for the new menu item
        item_name = st.text_input("Item Name")
        item_description = st.text_area("Item Description")
        item_price = st.number_input("Item Price", min_value=0.0)

        if st.button("Add Menu Item"):
            add_menu_item(canteen_id, item_name, item_description, item_price)

    elif menu_option == "View Total Sales" and st.session_state.user_type == "canteen_owner":
        st.header("View Total Sales")

        # Call the function to get total sales by canteen for the logged-in canteen owner
        total_sales = get_total_sales_by_canteen(st.session_state.user_id)

        if not total_sales:
            st.info("No sales data available.")
            return

        st.subheader("Total Sales for Your Canteen:")
        for sale in total_sales:
            st.write(f"Canteen ID: {sale[0]}, Canteen Name: {sale[1]}, Total Sales: ₹{sale[2]:.2f}")

    else:
        st.warning("Please log in to access this feature.")

if __name__ == "__main__":
    main()
