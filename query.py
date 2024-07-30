import sys
import json
import pika

class Query:
    def __init__(self, middleware_host, person_id):
        # Initializing the Query instance with middleware host and person ID
        self.middleware_host = middleware_host
        self.person_id = person_id

        # Establishing connection to RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.middleware_host))
        self.channel = self.connection.channel()

        # Declaring exchanges for query and query response
        self.channel.exchange_declare(exchange='query', exchange_type='fanout')
        self.channel.exchange_declare(exchange='query-response', exchange_type='fanout')

        # Setting up queue for receiving query responses
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.response_queue = result.method.queue
        self.channel.queue_bind(exchange='query-response', queue=self.response_queue)
        self.channel.basic_consume(queue=self.response_queue, on_message_callback=self.handle_response, auto_ack=True)

        # Initiating the query process
        self.initiate_query()

    def initiate_query(self):
        # Publishing the person identifier to the 'query' topic
        self.channel.basic_publish(exchange='query', routing_key='', body=self.person_id)
        print(f"[x] Sent query for {self.person_id}")

    def handle_response(self, ch, method, properties, body):
        # Handling incoming query response
        response = json.loads(body)
        print(f"[x] Received {response}")
        # Stop consuming messages after receiving the response
        self.channel.stop_consuming()

    def run(self):
        try:
            print("Waiting for query response...")
            # Start consuming messages from the callback queue
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("Stopping query...")
        finally:
            # Close the RabbitMQ connection
            self.connection.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 query.py <middleware_host> <person_id>")
        sys.exit(1)

    # Parsing command-line arguments
    middleware_host = sys.argv[1]
    person_id = sys.argv[2]

    # Creating Query instance and starting the query process
    query = Query(middleware_host, person_id)
    query.run()

# Possible command to run this file as a part of the task
    
    # python3 query.py localhost person1 
    # python3 query.py localhost person2
    # python3 query.py localhost person3
    # python3 query-py localhost person4
    # as many as person continues... make sure put all the person in one command
        # Additionally command usage is explained in code as well