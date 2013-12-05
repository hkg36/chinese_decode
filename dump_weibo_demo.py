#coding:utf-8
from kombu import Connection
from kombu.messaging import Consumer,Producer
from kombu import Exchange, Queue

Queue_User='spider'
Queue_PassWord='spider'
Queue_Server='124.207.209.57'
Queue_Port=None
Queue_Path='/spider'
conn=Connection(hostname=Queue_Server,port=Queue_Port,userid=Queue_User,password=Queue_PassWord,virtual_host=Queue_Path)
channel=conn.channel()
exch=Exchange('weibodownload',type='topic',durable=True,delivery_mode=2,passive=True)
#最新地理位置微薄的routing_key='weibo.geo' 每个人历史记录微薄的routing_key='weibo.user_geo'
queue=Queue(exchange=exch,routing_key='weibo.user_geo',auto_delete=True)
consumer=Consumer(channel=channel,queues=queue,no_ack=True)
consumer.qos(prefetch_count=1)
def on_response(body, message):
    print body
consumer.register_callback(on_response)
consumer.consume()
while True:
    conn.drain_events()

