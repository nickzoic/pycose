try:
  import usocket as socket
except ImportError:
  import socket

try:
  import ure as re
except ImportError:
  import re

try:
  import uos as os
except ImportError:
  import os

http_header_re = re.compile(r"(\w+) (\S+) (HTTP/1.[01])\s*$")

crlf = "\r\n"

def web_server(handler, addr='0.0.0.0', port=80):
  srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  srv.bind((addr, port))
  srv.listen(5)
  srv.setblocking(False)

  workers = []
  while True:
    try:
      sck, rem = srv.accept()
      print("Incoming connection from %s:%d" % rem)
      workers.append(web_server_worker(sck, handler))
    except OSError:
      yield

    for ww in workers[:]:
      try:
        ww.send(None)
        yield
      except StopIteration:
        workers.remove(ww)
    else:
      yield

def web_server_worker(sck, handler):
  sck.setblocking(False)
  sckr = sck.makefile('rb')
  try:
    while True:
      req = sckr.readline().decode('ascii')
      yield
      if req is None: continue
      m = http_header_re.match(req)
      if not m:
        sck.close()
        break
      http_method, http_request, http_version = m.group(1), m.group(2), m.group(3)
      req_headers = {}
      while True:
        line = sckr.readline().decode('ascii')
        yield
        if line is None: continue
        line = line.strip()
        if not line: break
        k, v = line.split(': ', 1)
        req_headers[k.lower()] = v
      req_content_length = int(req_headers.get('content-length',0))
      req_body = b''
      while len(req_body) < req_content_length:
        x = sckr.read(req_content_length - len(req_body))
        if x: req_body += x
        yield

      print(">>> %s %s" % (http_method, http_request) )
    
      http_status, res_headers, res_body = handler(
        http_method,
        http_request,
        req_headers,
        req_body
      )

      if type(res_body) == str:
        res_body = res_body.encode('utf-8')
        res_headers["Content-Length"] = str(len(res_body))
        res_headers["Content-Encoding"] = 'utf-8'
      elif type(res_body) == bytes:
        res_headers["Content-Length"] = str(len(res_body))

      if 'Content-Length' not in res_headers:
        keep_alive = False
      elif http_version == 'HTTP/1.0':
        keep_alive = req_headers.get('connection','').lower() == 'keep-alive'
      else:
        keep_alive = req_headers.get('connection','').lower() != 'close'
      res_headers['Connection'] = 'Keep-Alive' if keep_alive else 'Close'
   
      dat = (
        "%s %s %s" % (http_version, str(http_status), "OK") + crlf +
        crlf.join("%s: %s" % (k, v) for k, v in res_headers.items()) +
        crlf + crlf
      ).encode('ascii')
      
      sckw = sck.makefile("wb")
 
      if hasattr(res_body, 'send'):
        try:
          while True:
            dat += res_body.send(None)
            x = sckw.write(dat)
            dat = dat[x:]
            yield
        except StopIteration:
          pass
      elif hasattr(res_body, 'read'):
        while True:
          if len(dat) < 500:
            s = res_body.read(50)
            if not s: break
            dat += s
          x = sckw.write(dat)
          dat = dat[x:]
          yield
      else:
        dat += res_body

      while dat:
        yield
        x = sckw.write(dat)
        dat = dat[x:]
      if not keep_alive:
        sck.close()
        return
  except Exception as e:
    sck.close()
    print(repr(e))
    raise(e)


def handler_default(http_method, http_request, req_headers, req_body):
  return [404, {}, "Not Found"] if http_method == 'GET' else [405, {}, "Bad Method"]


def static_file_handler(base_path):

  def handler_static(http_method, http_request, req_headers, req_body):
    if http_method == 'GET':
      try:
        filename = base_path + (http_request if http_request != "/" else "/index.html");
        print(">>> %s %s %s" % (http_method, http_request, filename))
        s = os.stat(filename)
        http_status = 200
        return 200, {'Content-Length': str(s[6])}, open(filename, "rb")
      except OSError:
        pass
    return [404, {}, "Not found"]
  
  return handler_static


def dispatcher(patterns):
 
  def handler_dispatch(http_method, http_request, req_headers, req_body):
    for methods, url_pattern, handler in patterns:
      if http_method in methods and url_pattern.match(http_request):
        return handler(http_method, http_request, req_headers, req_body)
    return handler_default(http_method, http_request, req_headers, req_body)
      
  return dispatch_handler
