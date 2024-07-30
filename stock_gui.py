import os  # Import the os module to interact with the operating system

# Set environment variables to silence specific warnings and fix macOS issues
os.environ['TK_SILENCE_DEPRECATION'] = '1'
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

import tkinter as tk  # Import tkinter for GUI creation
from threading import Thread  # Import Thread class for threading
import pika  # Import pika for RabbitMQ interaction
import json  # Import json module for handling JSON data

# Define the file path for storing valid stocks
VALID_STOCKS_FILE = 'valid_stocks.json'

# Define a custom Entry widget with placeholder functionality
class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey'):
        # Initialize the tk.Entry widget
        super().__init__(master)

        # Set placeholder text and colors
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']  # Default text color

        # Bind focus in and out events to methods
        self.bind("<FocusIn>", self.focus_in)
        self.bind("<FocusOut>", self.focus_out)

        # Display the placeholder text initially
        self.display_placeholder()

    # Method to display the placeholder text
    def display_placeholder(self):
        self.insert(0, self.placeholder)  # Insert placeholder text
        self['fg'] = self.placeholder_color  # Set text color to placeholder color

    # Method to handle focus in event
    def focus_in(self, *args):
        if self['fg'] == self.placeholder_color:  # If current text color is placeholder color
            self.delete('0', 'end')  # Delete all text
            self['fg'] = self.default_fg_color  # Reset text color to default

    # Method to handle focus out event
    def focus_out(self, *args):
        if not self.get():  # If Entry widget is empty
            self.display_placeholder()  # Display the placeholder text

# Main class for the Stock Trading GUI application
class StockGUI:
    def __init__(self, root):
        self.root = root  # Set the root window
        self.root.title("Stock Trading GUI")  # Set the window title
        
        self.trades = {}  # Dictionary to store trades
        
        self.create_widgets()  # Call method to create GUI widgets
        self.start_consuming()  # Start consuming trades from RabbitMQ
        
        # Bind the close event to the on_closing method
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Method to create and pack the GUI widgets
    def create_widgets(self):
        # Create a frame for stock labels
        self.labels_frame = tk.Frame(self.root)
        self.labels_frame.pack()

        self.labels = {}  # Dictionary to store stock labels
        self.add_stock_label('XYZ')  # Add default stock XYZ

        # Create Entry fields for order details with placeholders
        self.username_entry = PlaceholderEntry(self.root, "Enter Username")
        self.username_entry.pack()
        
        self.endpoint_entry = PlaceholderEntry(self.root, "Endpoint(localhost)")
        self.endpoint_entry.pack()

        self.stock_entry = PlaceholderEntry(self.root, "Stock Name")
        self.stock_entry.pack()
        
        self.side_entry = PlaceholderEntry(self.root, "BUY or SELL")
        self.side_entry.pack()

        self.quantity_entry = PlaceholderEntry(self.root, "Quantity")
        self.quantity_entry.pack()

        self.price_entry = PlaceholderEntry(self.root, "Price")
        self.price_entry.pack()

        # Button to submit the order
        self.submit_button = tk.Button(self.root, text="Submit Order", command=self.submit_order)
        self.submit_button.pack()

        # Entry field to add new stocks
        self.new_stock_entry = PlaceholderEntry(self.root, "New Stock")
        self.new_stock_entry.pack()

        # Button to add new stocks
        self.add_stock_button = tk.Button(self.root, text="Add Stock", command=self.add_stock)
        self.add_stock_button.pack()

    # Method to add a label for a new stock
    def add_stock_label(self, stock):
        frame = tk.Frame(self.labels_frame)  # Create a frame for the stock label
        frame.pack()

        label = tk.Label(frame, text=stock)  # Create a label for the stock name
        label.pack(side=tk.LEFT)
        
        price_label = tk.Label(frame, text="N/A")  # Create a label for the stock price
        price_label.pack(side=tk.LEFT)
        
        self.labels[stock] = price_label  # Store the price label in the dictionary

    # Method to handle adding a new stock
    def add_stock(self):
        stock = self.new_stock_entry.get().strip().upper()  # Get and format the stock name
        if stock and stock not in self.labels:  # If the stock name is valid and not already added
            self.add_stock_label(stock)  # Add the stock label
            self.new_stock_entry.delete(0, tk.END)  # Clear the Entry field
            self.update_valid_stocks(stock)  # Update the valid stocks file

    # Method to update the valid stocks file with a new stock
    def update_valid_stocks(self, stock):
        try:
            with open(VALID_STOCKS_FILE, 'r') as f:  # Open the valid stocks file
                data = json.load(f)  # Load the JSON data
            data['valid_stocks'].append(stock)  # Add the new stock to the list
            with open(VALID_STOCKS_FILE, 'w') as f:  # Open the valid stocks file for writing
                json.dump(data, f)  # Save the updated JSON data
        except Exception as e:  # Handle any exceptions
            print(f"Error updating valid stocks: {e}")

    # Method to reset the valid stocks file to default
    def reset_valid_stocks(self):
        try:
            with open(VALID_STOCKS_FILE, 'w') as f:  # Open the valid stocks file for writing
                json.dump({"valid_stocks": ["XYZ"]}, f)  # Reset to default stock XYZ
        except Exception as e:  # Handle any exceptions
            print(f"Error resetting valid stocks: {e}")

    # Method to update the displayed price of a stock
    def update_trade(self, stock, price):
        if stock in self.labels:  # If the stock label exists
            self.labels[stock].config(text=f"${price}")  # Update the price label

    # Method to submit an order
    def submit_order(self):
        try:
            username = self.username_entry.get().strip()  # Get the username
            endpoint = self.endpoint_entry.get().strip()  # Get the endpoint
            stock = self.stock_entry.get().strip().upper()  # Get and format the stock name
            side = self.side_entry.get().strip().upper()  # Get and format the order side
            quantity = int(self.quantity_entry.get().strip())  # Get and convert the quantity
            price = float(self.price_entry.get().strip())  # Get and convert the price

            # Validate the input fields
            if not username or not endpoint or not stock or side not in ['BUY', 'SELL'] or quantity != 100 or price <= 0:
                raise ValueError("Invalid input. Ensure quantity is 100 and side is either BUY or SELL.")
            
            if stock not in self.labels:  # Check if the stock is added
                raise ValueError(f"Stock '{stock}' not added. Please add the stock first.")

            # Create the order dictionary
            order = {
                'username': username,
                'stock': stock,
                'side': side,
                'quantity': quantity,
                'price': price
            }

            # Connect to RabbitMQ and send the order
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=endpoint))
            channel = connection.channel()
            channel.queue_declare(queue='orders', durable=True)
            channel.basic_publish(exchange='', routing_key='orders', body=json.dumps(order))
            connection.close()

            print(f"Order sent: {order}")  # Print the sent order
        except ValueError as e:  # Handle validation errors
            print(f"Error submitting order: {e}")

    # Method to start consuming trades from RabbitMQ
    def start_consuming(self):
        def callback(ch, method, properties, body):
            trade = json.loads(body)  # Parse the trade JSON data
            stock = trade['stock']  # Get the stock name
            price = trade['price']  # Get the trade price
            self.update_trade(stock, price)  # Update the trade price in the GUI

        def consume():
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='trades', durable=True)
            channel.basic_consume(queue='trades', on_message_callback=callback, auto_ack=True)
            channel.start_consuming()

        # Start the consume function in a separate thread
        Thread(target=consume, daemon=True).start()

    # Method to handle the GUI close event
    def on_closing(self):
        self.reset_valid_stocks()  # Reset valid stocks to default
        self.root.destroy()  # Destroy the root window

# Main entry point for the application
if __name__ == "__main__":
    root = tk.Tk()  # Create the root window
    app = StockGUI(root)  # Create an instance of the StockGUI class
    root.mainloop()  # Start the main event loop



# To run this file follow the instructions below...
# For running file - export TK_SILENCE_DEPRECATION=1
#                    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
#                    python stock_gui.py 

# after running please enter all fields for trading
# in the endpoint bar fill localhost as endpoint by default
# you can add multiple stocks except the defaulted stock XYZ as mentioned for the task
# If you will try to put quantity more than 100 or less than 100 then it will generate error only
# If you will add any other stock for example ABC in the stock bar and you didnt added it then it will not be updated in the valid_stocks.json file and will hence give error so better add stock befor trading the particular new stock like ABC
# You will have to submit both BUY and SELL orders for getting the trade to be executed 
# If the price will mismatch then it will update the price to the order book but trade can only be executed at same price for both
#:)