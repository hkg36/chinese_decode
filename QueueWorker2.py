from kombu import Connection
from kombu.messaging import Consumer,Producer
from kombu import Exchange, Queue
import traceback
import json
import zlib
class QueueWorker(object):
    def __init__(self,host,port,virtual_host,usr,psw,queue_name):
        self.host=host
        self.port=port
        self.virtual_host=virtual_host
        self.usr=usr
        self.psw=psw
        self.queue_name=queue_name
    def run(self):
        try:
            connection = Connection(hostname=self.host,port=self.port,userid=self.usr,password=self.psw,virtual_host=self.virtual_host)
            channel = connection.channel()
            self.producer=Producer(channel)
            task_queue = Queue(self.queue_name,durable=True)
            consumer = Consumer(channel,task_queue,no_ack=False)
            consumer.qos(prefetch_count=1)
            consumer.register_callback(self.RequestCallBack)
            consumer.consume()
            while True:
                connection.drain_events()
            connection.close()
        except BaseException,e:
            print e

    def RequestCallBack(self,body, message):
        properties=message.properties
        headers=message.headers
        replyheader=None
        replybody=None
        if headers:
            try:
                replyheader,replybody=self.RequestWork(headers,body)
            except Exception,e:
                replybody = traceback.format_exc()
                replyheader={'error':str(e)}
        else:
            replyheader={'error':'no head'}
            replybody='unknow'
        if 'reply_to' in properties:
            if replyheader.get('zip'):
                self.producer.publish(body=replybody,delivery_mode=2,headers=replyheader,
                                      routing_key=properties['reply_to'],
                                      correlation_id=properties.get('correlation_id'),
                                      content_type='application/data',
                                      content_encoding='binary')
            else:
                self.producer.publish(body=replybody,delivery_mode=2,headers=replyheader,
                                      routing_key=properties['reply_to'],
                                      correlation_id=properties.get('correlation_id'),
                                      compression='gzip')
        message.ack()
    def RequestWork(self,params,body):
        print json.dumps(params)
        print body

        params['finish']=True
        return params,'RE:'+body
if __name__ == '__main__':
    import config
    worker=QueueWorker(config.Queue_Server,config.Queue_Port,config.Queue_Path,config.Queue_User,config.Queue_PassWord,'test')
    worker.run()