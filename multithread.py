#-*-coding:utf-8-*-
import Queue
import threading
import time

class WorkManager(object):
    def __init__(self, thread_num=2 ,thread_init_fun=None,thread_init_data=None):
        self.work_queue = Queue.Queue()
        self.reault_queue = Queue.Queue()
        self.threads = []

        for i in range(thread_num):
            self.threads.append(Work(self.work_queue,self.reault_queue,thread_init_fun,thread_init_data))

    def add_job(self, func, args,callback=None):
        self.work_queue.put((func, args ,callback))
        self.check_result()

    def check_queue(self):
        self.check_result()
        return self.work_queue.qsize()

    def check_result(self):
        while True:
            try:
                callback,res,error_info=self.reault_queue.get(block=False)
            except Queue.Empty,e:
                break
            self.reault_queue.task_done()
            if callback is not None:
                callback(res,error_info)
    def wait_allworkcomplete(self):
        while self.work_queue.empty():
            self.check_result()
            time.sleep(0.01)
        self.check_result()
    def wait_allcomplete(self):
        self.check_result()
        for item in self.threads:
            item.keepwork=False
        for item in self.threads:
            if item.isAlive():item.join()
        self.check_result()

class Work(threading.Thread):
    def __init__(self, work_queue,result_queue,init_fun=None,init_arg=None):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.result_queue=result_queue
        self.keepwork=True
        self.init_fun=init_fun
        self.init_arg=init_arg
        self.thread_init_data=None
        self.start()

    def run(self):
        if self.init_fun:
            self.thread_init_data=self.init_fun(self.init_arg)
        while True:
            try:
                do, args ,callback= self.work_queue.get(block=True,timeout=1)
                error_info=None
                try:
                    res=do(self.thread_init_data,args)
                except Exception,e:
                    error_info
                self.work_queue.task_done()
                self.result_queue.put((callback,res,error_info))
            except Queue.Empty:
                if self.keepwork:
                    continue
                else:
                    break
            except Exception,e:
                print str(e)



if __name__ == '__main__':
    #具体要做的任务
    def thread_init(arg):
        return arg
    data_num=0
    def do_job(thread_data,args):
        global data_num
        data_num+=args[0]
        return args[0]
    def print_res(res,error_info):
        print res
    start = time.time()
    work_manager =  WorkManager(2,thread_init,"i am ok")
    for i in xrange(50):
        work_manager.add_job(do_job,(i,),callback=print_res)
    work_manager.wait_allworkcomplete()
    for i in xrange(50,101):
        work_manager.add_job(do_job,(i,),callback=print_res)
    work_manager.wait_allcomplete()
    end = time.time()
    print data_num
    print "cost all time: %s" % (end-start)