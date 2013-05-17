import logging.handlers
import socket
try:
    import codecs
except ImportError:
    codecs = None

class SysLogHandler(logging.handlers.SysLogHandler):
    def emit(self, record):
        """
        Emit a record.

        The record is formatted, and then sent to the syslog server. If
        exception information is present, it is NOT sent to the server.
        """
        source_msg = self.format(record)
        """
        We need to convert record level to lowercase, maybe this will
        change in the future.
        """
        prio = '<%d>' % self.encodePriority(self.facility,
                                            self.mapPriority(record.levelname))
        max_length = 70
        i = 0
        while source_msg[i:]:
            msg = source_msg[i:i+max_length] + '\000'
            if i:
                msg = ' ' + msg
            i += max_length
            # Message is a string. Convert to bytes as required by RFC 5424
            if type(msg) is unicode:
                msg = msg.encode('utf-8')
                if codecs:
                    msg = codecs.BOM_UTF8 + msg
            msg = prio + msg
            try:
                if self.unixsocket:
                    try:
                        self.socket.send(msg)
                    except socket.error:
                        self._connect_unixsocket(self.address)
                        self.socket.send(msg)
                elif self.socktype == socket.SOCK_DGRAM:
                    self.socket.sendto(msg, self.address)
                else:
                    self.socket.sendall(msg)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.handleError(record)