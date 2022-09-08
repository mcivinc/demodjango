import importlib
import logging
import queue
import threading
import datetime
import getopt
import sys
import time
import pandas as pd
from threading import Thread
from functools import partial

from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, Spacer
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn, NumberFormatter, Div
from bokeh.server.server import Server

from tornado import gen
from tornado.ioloop import IOLoop


class TablePoint:
    def __init__(self, x_, y_, desc_):
        self.x = x_
        self.y = y_
        self.desc = desc_


class StreamingDocument:
    def __init__(self,
                 doc_,
                 source_,
                 ):
        self.doc = doc_
        self.source = source_


class BokehApp1(Handler):
    '''
    Bokeh application
    '''
    log = logging.getLogger(__name__)

    def __init__(self, config_):
        self._input_topic_active = True
        self._input_topic_thread = None
        self._id_2_streaming_documents = dict()  # key:str -> StreamingDocument
        self._static = ''
        self._error = ''
        self._error_detail = ''
        self._failed = False
        self._config = config_
        self._counter_1 = 0

    def modify_document(self, doc_):
        mn = "[BokehApp1::modify_document] "
        source_id = doc_.session_context.id
        self.log.info(mn+"enter, session_context.id: `"+source_id+"'")
        #
        # Product curve
        #
        source = ColumnDataSource(data=dict(
            x=[],
            y=[],
        ))
        columns = [
            TableColumn(field="x", title="Key"),
            TableColumn(field="y", title="Value", formatter=NumberFormatter(format='0.0000')),
        ]
        data_table = DataTable(source=source, columns=columns, width=200, height=500)

        doc_.add_root(row(column(
                                Div(text="DEMOTABLE", width=200, height=20),
                                data_table,
                                ),

            ))
        sd = StreamingDocument(doc_,
                               source,
                               )
        self._id_2_streaming_documents[source_id] = sd
        self.log.info(mn+"exiting, session_context.id: `"+source_id+"'")
        return doc_

    def on_server_loaded(self, server_context):
        self.log.info("[BokehApp1::on_server_loaded] called")
        self._input_topic_thread = threading.Thread(target=self.subscribe2data, args=())
        self._input_topic_thread.setName("[BokehApp1::input_topic_thread]")
        self._input_topic_thread.start()

    def on_server_unloaded(self, server_context):
        self.log.info("[BokehApp1::on_server_unloaded] called")
        self.dispose()

    def on_session_created(self, session_context):
        pass

    def on_session_destroyed(self, session_context):
        self.log.info("[BokehApp1::on_session_destroyed] called")
        del self._id_2_streaming_documents[session_context.id]

    def subscribe2data(self):
        """
        Subscribes to input stream and updates registered data sources
        Runs in its own thread
        :return:
        """
        mn = "[BokehApp1::subscribe2data] "

        try:
            while self._input_topic_active:
                res = self.get_df()
                self.log.debug(mn + "processing: " + str(res))

                tmp = self.parse_input(res)
                for k, e in self._id_2_streaming_documents.items():
                    e.doc.add_next_tick_callback(partial(self.update, id_=k, d_=tmp))
                time.sleep(2)
        except Exception:
            self.log.error(mn + "Exception caught", exc_info=True)
        finally:
            self._input_topic_active = False

    @gen.coroutine
    def update(self, id_, d_):
        tmp = self._id_2_streaming_documents[id_]
        tmp.source.stream(d_[0], rollover=4)

    def dispose(self):
        self.log.info("[BokehApp1::dispose] called")
        self._input_topic_active = False

    def get_df(self):
        d = {
            'Key': ['Counter', 'k1'],
            'Value': [self._counter_1, '1.23'],
        }
        rv = pd.DataFrame(d)
        self._counter_1 += 1
        return rv

    def parse_input(self, input_):
        d0 = dict(
            x=list(input_['Key']),
            y=list(input_['Value']),
        )

        rv = (d0,)
        return rv


def streaming_worker(config_):
    # Note: num_procs must be 1; see e.g. flask_gunicorn_embed.py for num_procs>1
    mn = "[streaming_worker] "
    log.info(mn + "enter")
    t_url = config_.BOKEH_APPS['BokehApp1']['url']
    t_address = config_.BOKEH_APPS['BokehApp1']['server']
    t_port = config_.BOKEH_APPS['BokehApp1']['port']
    t_allow_origin = config_.BOKEH_APPS['BokehApp1']['allow_origin']
    log.info(mn+"opening BokehApp1 at: "+t_address+":"+str(t_port)+t_url+", allow_websocket_origin: "+str(t_allow_origin))
    sh = BokehApp1(config_)
    app = Application()
    app.add(sh)
    config_.server = Server({t_url: app},
                            io_loop=IOLoop(),
                            address=t_address,
                            port=t_port,
                            allow_websocket_origin=t_allow_origin
                            )
    config_.server.start()
    config_.server.io_loop.start()
    log.info(mn + "exiting")


class AppConfig:
    pass


if __name__ == '__main__':
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    config_module_name = "NotSet"
    usage_msg = "BokehApp1.py -c <config_module_name>"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:",
                                   ["config_module_name="])
    except getopt.GetoptError:
        print(usage_msg)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage_msg)
            sys.exit()
        elif opt in ("-c", "--config_module_name"):
            config_module_name = arg
    if config_module_name == "NotSet":
        print(usage_msg)
        sys.exit(2)

    try:
        mn = "[BokehApp1::main ]"
        log.info(mn+"enter, loading settings from: `"+config_module_name+"'")
        config = AppConfig()
        config_module = importlib.import_module(config_module_name)
        config.BOKEH_APPS = config_module.bokeh_apps
        thread = Thread(target=streaming_worker,
                        args=(config,),
                        name="streaming_worker",
                        daemon=True)
        thread.start()
        input("\n******** Press Enter to quit ************\n\n")

    except Exception as ex:
        log.error(mn+"failed with Exception", exc_info=True)
    finally:
        config.server.stop()
    log.info(mn+"exiting")
