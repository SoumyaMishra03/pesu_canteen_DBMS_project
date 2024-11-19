CREATE DATABASE IF NOT EXISTS pesu_canteen;

USE pesu_canteen;

CREATE TABLE customer (
  user_id VARCHAR(10) NOT NULL,
  phone VARCHAR(15) NOT NULL,
  name VARCHAR(50) NOT NULL,
  email VARCHAR(50) NOT NULL CHECK (email LIKE '%@%'),
  password VARCHAR(50) NOT NULL,
  PRIMARY KEY (user_id)
);

CREATE TABLE canteen (
  canteen_id VARCHAR(10) NOT NULL,
  canteen_name VARCHAR(50) NOT NULL,
  cuisine VARCHAR(50) NOT NULL,
  location VARCHAR(50) NOT NULL,
  rating DECIMAL(2,1) NOT NULL,
  password VARCHAR(50) NOT NULL,
  PRIMARY KEY (canteen_id) 
);

CREATE TABLE menu_items (
  menuitem_id VARCHAR(10) NOT NULL,
  canteen_id VARCHAR(10) NOT NULL,
  item_name VARCHAR(50) NOT NULL,
  item_description VARCHAR(255) NOT NULL,
  price DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (menuitem_id),
  FOREIGN KEY (canteen_id) REFERENCES canteen(canteen_id) ON DELETE CASCADE
);

CREATE TABLE orders (
  order_id VARCHAR(10) NOT NULL,
  user_id VARCHAR(10) NOT NULL,
  date DATE NOT NULL,
  total_price DECIMAL(5,2) NOT NULL,
  status VARCHAR(10) NOT NULL,
  canteen_id VARCHAR(10) NOT NULL,
  PRIMARY KEY (order_id),
  FOREIGN KEY (user_id) REFERENCES customer(user_id) ON DELETE CASCADE,
  FOREIGN KEY (canteen_id) REFERENCES canteen(canteen_id) ON DELETE CASCADE
);

CREATE TABLE order_items (
  orderitem_id VARCHAR(20) NOT NULL,
  order_id VARCHAR(10) NOT NULL,
  user_id VARCHAR(10) NOT NULL,  
  canteen_id VARCHAR(10) NOT NULL,
  menuitem_id VARCHAR(10) NOT NULL,
  quantity INT NOT NULL,
  subtotal DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (orderitem_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (menuitem_id) REFERENCES menu_items(menuitem_id) ON DELETE CASCADE,
  FOREIGN KEY (canteen_id) REFERENCES canteen(canteen_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES customer(user_id) ON DELETE CASCADE
);

INSERT INTO customer (user_id, phone, name, email, password)
VALUES ('U_1', '9845811874', 'Rohan', 'rohan@gmail.com', 'shetty');

INSERT INTO canteen (canteen_id, canteen_name, cuisine, location, rating, password)
VALUES 
('C_1', 'B Block Canteen', 'Indian', 'PESU Campus', 3.9, 'canteen1'),
('C_2', 'Cantina', 'Indian/Continental', 'PESU Campus', 4.2, 'canteen2'),
('C_3', 'Halli Manne', 'South Indian', 'GJB', 4, 'canteen3'),
('C_4', '13th floor', 'North Indian/Chinese', 'B-block 13th floor', 4.9, 'canteen4'),
('C_5', 'F-block mess', 'North_Indian', 'Near Boys Hostel', 3.6, 'canteen5');

INSERT INTO menu_items (menuitem_id, canteen_id, item_name, item_description, price)
VALUES 
('M_1', 'C_1', 'Samosa', 'A delicious snack filled with Aloo', 15.00),
('M_2', 'C_1', 'Buns', 'A delicious Indian snack', 10.00),
('M_3', 'C_1', 'Shawarma', 'A delicious Indian snack', 80.00),
('M_4', 'C_2', 'Peri peri Popcorn', 'A delicious Indian snack', 70.00),
('M_5', 'C_2', 'Paneer Pizza', 'A delicious Indian snack', 100.00),
('M_6', 'C_2', 'Veg Roll', 'A delicious Indian snack', 60.00),
('M_7', 'C_3', 'Vada', 'A delicious Indian snack', 40.00),
('M_8', 'C_3', 'Masala Dosa', 'A delicious Indian snack', 80.00),
('M_9', 'C_3', 'Idli', 'A delicious Indian snack', 80.00),
('M_10', 'C_4', 'Vegetable Manchurian', 'Crispy veggie balls in Manchurian sauce', 120.00),
('M_11', 'C_4', 'Chicken Noodles', 'Stir-fried noodles with chicken and veggies', 140.00),
('M_12', 'C_4', 'Sweet and Sour Soup', 'Tangy Chinese soup with sweet and sour flavors, veggies, and protein.', 160.00),
('M_13', 'C_5', 'Paneer Butter Masala', 'Creamy curry with paneer', 150.00),
('M_14', 'C_5', 'Butter Naan', 'Soft and buttery Indian bread', 30.00),
('M_15', 'C_5', 'Roti', 'Thin whole-wheat bread', 15.00);

DELIMITER //

CREATE PROCEDURE ConfirmOrder(IN userId VARCHAR(10))
BEGIN
    UPDATE orders SET 
        total_price = (
            SELECT SUM(subtotal) 
            FROM order_items 
            WHERE order_id = orders.order_id
        ), 
        status = 'Confirmed'
    WHERE user_id = userId;
END //

CREATE FUNCTION CalculateTotalPrice(order_id VARCHAR(10)) RETURNS DECIMAL(5, 2) READS SQL DATA
BEGIN
    DECLARE total DECIMAL(5, 2);
    
    SELECT SUM(subtotal) INTO total
    FROM order_items
    WHERE order_id = order_id;

    RETURN COALESCE(total, 0);
END //

CREATE TRIGGER before_order_insert
BEFORE INSERT ON orders
FOR EACH ROW
BEGIN
    SET @order_count = (SELECT COUNT(*) FROM orders) + 1;
    SET NEW.order_id = CONCAT('O_', @order_count);
END //

DELIMITER ;
