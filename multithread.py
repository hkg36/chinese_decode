#-*-coding:utf-8-*-
import Queue
import threading
import time
import traceback

class WorkManager(object):
    class Task:
        back_fun=None
        back_arg=None
        error=None
        result=None
        callback=None
    def __init__(self, thread_num=2 ,thread_init_fun=None,thread_init_data=None):
        self.work_queue = Queue.Queue()
        self.reault_queue = Queue.Queue()
        self.threads = []
        self.thread_init_fun=thread_init_fun
        self.thread_init_data=thread_init_data

        for i in range(thread_num):
            workthread=Work(self.work_queue,self.reault_queue,self.thread_init_fun,self.thread_init_data)
            workthread.setDaemon(True)
            workthread.start()
            self.threads.append(workthread)
    def add_job(self, func, args,callback=None):
        task=WorkManager.Task()
        task.back_fun=func
        task.back_arg=args
        task.callback=callback
        self.work_queue.put(task)
        self.check_result()

    def check_queue(self):
        self.check_result()
        return self.work_queue.qsize()

    def check_result(self):
        while True:
            try:
                task=self.reault_queue.get(block=False)
            except Queue.Empty,e:
                break
            self.reault_queue.task_done()
            if task.callback is not None:
                try:
                    task.callback(task.result,task.error)
                except Exception,e:
                    print "call back fail",str(e)
    def wait_allworkcomplete(self):
        while self.work_queue.empty()==False:
            self.check_result()
            time.sleep(0.1)
        self.work_queue.join()
        self.check_result()
    def wait_allthreadcomplete(self):
        for item in self.threads:
            item.keepwork=False
        self.wait_allworkcomplete()
        for item in self.threads:
            if item.isAlive():item.join()
    def terminate(self):
        for item in self.threads:
            item.keepwork=False

class Work(threading.Thread):
    def __init__(self, work_queue,result_queue,init_fun=None,init_arg=None):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.result_queue=result_queue
        self.keepwork=True
        self.init_fun=init_fun
        self.init_arg=init_arg
        self.thread_init_data=None

    def run(self):
        if self.init_fun:
            try:
                self.thread_init_data=self.init_fun(self.init_arg)
            except Exception,e:
                print e
                print traceback.format_exc()
        while True:
            try:
                task= self.work_queue.get(block=True,timeout=1)
                error_info=None
                try:
                    task.result=task.back_fun(self.thread_init_data,task.back_arg)
                except Exception,e:
                    task.error=e
                self.result_queue.put(task)
                self.work_queue.task_done()
            except Queue.Empty,e:
                #must complete all work,not quite if still work to do when keepwork=False
                if self.keepwork:
                    time.sleep(0.1)
                else:
                    break
            except Exception,e:
                print str(e)
                print traceback.format_exc()
        print 'work thread out'

if __name__ == '__main__':
    import httplib
    import random
    ss=['ddddd','ffffff','gggggg']
    #具体要做的任务
    def thread_init(arg):
        return arg
    data_num=0
    def do_job(thread_data,args):
        global data_num
        global ss
        return ss[random.randint(0,len(ss)-1)]
    def print_res(res,error_info):
        if res is None:
            a=0
        print res,error_info
    start = time.time()
    work_manager =  WorkManager(10,thread_init,"i am ok")
    for i in xrange(5000):
        work_manager.add_job(do_job,(i,),callback=print_res)
    work_manager.wait_allworkcomplete()
    for i in xrange(50,101):
        work_manager.add_job(do_job,(i,),callback=print_res)
    work_manager.wait_allthreadcomplete()
    end = time.time()
    print data_num
    print "cost all time: %s" % (end-start)