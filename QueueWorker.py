import pika
import traceback
import logging
logging.getLogger('pika').setLevel(logging.ERROR)
class QueueWorker(object):
    def __init__(self,host,port,virtual_host,usr,psw,queue_name):
        self.host=host
        self.port=port
        self.virtual_host=virtual_host
        self.usr=usr
        self.psw=psw
        self.queue_name=queue_name
    def run(self):
        cred = pika.PlainCredentials(self.usr,self.psw)
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                               port=self.port,
                                                                               virtual_host=self.virtual_host,
                                                                               credentials=cred,
                                                                               heartbeat_interval=20))
                channel = connection.channel()
                channel.queue_declare(queue=self.queue_name,durable=True)
                channel.basic_consume(self.RequestCallBack,queue=self.queue_name,no_ack=False)
                channel.basic_qos(prefetch_count=1)
                channel.start_consuming()
                connection.close()
            except BaseException,e:
                print e

    def RequestCallBack(self,ch=None, method=None, properties=None, body=None):
        if ch is None or method is None or properties is None or body is None:
            print "empty callback"
            return
        replyheader=None
        replybody=None
        if properties.headers:
            try:
                replyheader,replybody=self.RequestWork(properties.headers,body)
            except Exception,e:
                replybody = traceback.format_exc()
                replyheader={'error':str(e)}
        else:
            replyheader={'error':'no head'}
            replybody='unknow'
        if properties.reply_to:
            properties_res=pika.BasicProperties(delivery_mode = 2,headers=replyheader,correlation_id=properties.correlation_id)
            try:
                ch.basic_publish(exchange='',routing_key=properties.reply_to,body=str(replybody),properties=properties_res)
            except Exception,e:
                print e
        ch.basic_ack(delivery_tag = method.delivery_tag)
    def RequestWork(self,params,body):
        return None,None
