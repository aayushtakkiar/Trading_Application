import pika  # Importing the pika library for RabbitMQ interactions
import json  # Importing the json module to handle JSON data

# Define the file path for the valid stocks file
VALID_STOCKS_FILE = 'valid_stocks.json'

# Define the Exchange class to handle order processing
class Exchange:
    def __init__(self, endpoint):
        # Establish a connection to the RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=endpoint))
        self.channel = self.connection.channel()  # Create a channel on the connection

        # Declare the 'orders' queue, making sure it is durable
        self.channel.queue_declare(queue='orders', durable=True)
        # Declare the 'trades' queue, making sure it is durable
        self.channel.queue_declare(queue='trades', durable=True)

        # Initialize an order book to store unmatched orders
        self.order_book = {'BUY': [], 'SELL': []}

    # Function to check if a stock is supported
    def is_stock_supported(self, stock):
        try:
            with open(VALID_STOCKS_FILE, 'r') as f:  # Open the valid stocks file for reading
                data = json.load(f)  # Load the JSON data from the file
            return stock in data['valid_stocks']  # Check if the stock is in the list of valid stocks
        except Exception as e:  # Handle exceptions, such as file read errors
            print(f"Error reading valid stocks: {e}")  # Print an error message
            return False  # Return False if an error occurs

    # Function to handle incoming orders
    def handle_order(self, ch, method, properties, body):
        order = json.loads(body)  # Parse the order JSON message
        side = order['side']  # Extract the order side (BUY or SELL)
        stock = order['stock']  # Extract the stock symbol
        quantity = order['quantity']  # Extract the order quantity

        if quantity != 100:  # Check if the quantity is exactly 100
            print("Order rejected: Quantity must be 100 shares.")  # Print an error message if the quantity is not 100
            return  # Exit the function

        if not self.is_stock_supported(stock):  # Check if the stock is supported
            print(f"Stock '{stock}' not added. Please add the stock first.")  # Print an error message if the stock is not supported
            return  # Exit the function

        opposite_side = 'SELL' if side == 'BUY' else 'BUY'  # Determine the opposite side for matching orders
        print(f"Received order: {order}")  # Print the received order for debugging

        matched_order = None  # Initialize the matched order variable
        for o in self.order_book[opposite_side]:  # Iterate through the opposite side's order book
            if side == 'BUY' and o['price'] <= order['price']:  # Check if the buy order matches
                matched_order = o  # Set the matched order
                break  # Exit the loop
            elif side == 'SELL' and o['price'] >= order['price']:  # Check if the sell order matches
                matched_order = o  # Set the matched order
                break  # Exit the loop

        if matched_order:  # If a matching order is found
            self.order_book[opposite_side].remove(matched_order)  # Remove the matched order from the order book
            trade = {  # Create a trade message with the matched order details
                'buyer': matched_order['username'] if side == 'SELL' else order['username'],
                'seller': matched_order['username'] if side == 'BUY' else order['username'],
                'price': order['price'],
                'quantity': order['quantity'],
                'stock': order['stock']
            }
            self.channel.basic_publish(exchange='',  # Publish the trade message to the 'trades' queue
                                       routing_key='trades',
                                       body=json.dumps(trade))
            print(f"Trade executed: {trade}")  # Print the executed trade details
        else:
            self.order_book[side].append(order)  # Add the order to the order book if no match is found
            print(f"Order added to book: {order}")  # Print the added order details
            print(f"Current order book: {self.order_book}")  # Print the current state of the order book

    # Function to start the exchange
    def start(self):
        # Set up a consumer to handle messages from the 'orders' queue
        self.channel.basic_consume(queue='orders',
                                   on_message_callback=self.handle_order,
                                   auto_ack=True)
        
        print('Exchange is running and waiting for orders...')  # Print a start message
        self.channel.start_consuming()  # Start consuming messages

if __name__ == "__main__":
    import sys  # Importing the sys module to handle command-line arguments

    if len(sys.argv) != 2:  # Check if the number of arguments is correct
        print("Usage: exchangeorder.py <endpoint>")  # Print the correct usage if arguments are incorrect
        sys.exit(1)  # Exit the script with an error code

    endpoint = sys.argv[1]  # Get the RabbitMQ endpoint from the arguments
    exchange = Exchange(endpoint)  # Create an Exchange object with the endpoint
    exchange.start()  # Start the exchange

# Instructions to run this file...
# Code for running- python exchangeorder.py localhost
# This file displays trade execution, errors and any updation in the order book 
# This file will run and wait for orders from both gui and terminal its your wish from which you want to trade :)