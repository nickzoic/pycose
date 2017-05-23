def loop(tasks):
  while True:
    for t in tasks:
      t.send(None)   
