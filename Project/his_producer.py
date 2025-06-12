import pika
import json

class HISPublisher:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='peregos_queue', durable=True)
        self.channel.queue_declare(queue='wyseflow_queue', durable=True)

    def send(self, name, student_id, study_programs, credits):
        data_peregos = {
            "name": name,
            "id": student_id,
            "study_programs": study_programs
        }
        data_wyseflow = {
            "name": name,
            "id": student_id,
            "study_program": study_programs[0],
            "credits": credits[0]
        }

        self.channel.basic_publish(exchange='', routing_key='peregos_queue',
                                   body=json.dumps(data_peregos))
        self.channel.basic_publish(exchange='', routing_key='wyseflow_queue',
                                   body=json.dumps(data_wyseflow))
        print("Nachrichten gesendet an Peregos und WyseFlow.")

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    sender = HISPublisher()
    sender.send("Max Mustermann", "123456", ["Informatik", "Mathematik"], [120, 90])
    sender.close()
