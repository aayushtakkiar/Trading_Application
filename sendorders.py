import pika  # Importing the pika library for RabbitMQ interactions
import sys  # Importing the sys module to handle command-line arguments
import json  # Importing the json module to handle JSON data

# Define the file path for the valid stocks file
VALID_STOCKS_FILE = 'valid_stocks.json'

# Function to check if a stock is supported
def is_stock_supported(stock):
    try:
        with open(VALID_STOCKS_FILE, 'r') as f:  # Open the valid stocks file for reading
            data = json.load(f)  # Load the JSON data from the file
        return stock in data['valid_stocks']  # Check if the stock is in the list of valid stocks
    except Exception as e:  # Handle exceptions, such as file read errors
        print(f"Error reading valid stocks: {e}")  # Print an error message
        return False  # Return False if an error occurs

# Function to send an order
def send_order(username, endpoint, stock, side, quantity, price):
    if quantity != 100:  # Check if the quantity is exactly 100
        print("Quantity must be 100 shares.")  # Print an error message if the quantity is not 100
        return  # Exit the function

    if not is_stock_supported(stock):  # Check if the stock is supported
        print(f"Stock '{stock}' not added. Please add the stock first.")  # Print an error message if the stock is not supported
        return  # Exit the function

    # Establish a connection to the RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=endpoint))
    channel = connection.channel()  # Create a channel on the connection

    # Declare the 'orders' queue, making sure it is durable
    channel.queue_declare(queue='orders', durable=True)

    # Create the order message as a dictionary
    order = {
        'username': username,  # Include the username in the order
        'stock': stock,  # Include the stock symbol in the order
        'side': side,  # Include the order side (BUY or SELL)
        'quantity': quantity,  # Include the quantity (fixed at 100)
        'price': price  # Include the price
    }

    # Publish the order message to the 'orders' queue
    channel.basic_publish(exchange='',
                          routing_key='orders',
                          body=json.dumps(order))  # Convert the order dictionary to a JSON string
    
    print(" [x] Sent order %r" % order)  # Print a confirmation message with the order details
    connection.close()  # Close the connection to RabbitMQ

# Main entry point of the script
if __name__ == "__main__":
    print("Arguments received:", sys.argv)  # Print the received command-line arguments for debugging
    if len(sys.argv) != 7:  # Check if the number of arguments is correct
        print("Usage: sendorders.py <username> <endpoint> <stock> <side> <quantity> <price>")  # Print the correct usage if arguments are incorrect
        sys.exit(1)  # Exit the script with an error code

    # Extract the command-line arguments
    username = sys.argv[1]  # Get the username from the arguments
    endpoint = sys.argv[2]  # Get the RabbitMQ endpoint from the arguments
    stock = sys.argv[3]  # Get the stock symbol from the arguments
    side = sys.argv[4]  # Get the order side (BUY or SELL) from the arguments
    quantity = int(sys.argv[5])  # Get the quantity from the arguments and convert to integer
    price = float(sys.argv[6])  # Get the price from the arguments and convert to float

    # Call the send_order function with the extracted arguments
    send_order(username, endpoint, stock, side, quantity, price)

# Instructions of sendorders.py...
# This file's purpose is only to send orders in the following format sendorders.py <username> <endpoint> <stock> <side> <quantity> <price>
# an example of that is - python sendorders.py user1 localhost XYZ BUY 100 50.0
#                         python sendorders.py user2 localhost XYZ SELL 100 50.0
# If any of them will be missing or inputed in the wrong way then it will generate errors 
# you can add multiple stocks except the defaulted stock XYZ as mentioned for the task
# If you will try to put quantity more than 100 or less than 100 then it will generate error only
# If you will add any other stock for example ABC in the stock bar and you didnt added it then it will not be updated in the valid_stocks.json file and will hence give error so better add stock befor trading the particular new stock like ABC
# You will have to submit both BUY and SELL orders for getting the trade to be executed 
# If the price will mismatch then it will update the price to the order book but trade can only be executed at same price for both
# Special Note!! - Please add any other stock in the gui before trading for that stock except XYZ default stock as gui and terminals are both linked
#:)