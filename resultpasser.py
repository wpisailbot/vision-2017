import threading

''' Basic class for passing results between the vision and 
    networking threads.
    Note: this just ensures atomic access to the variable reference.
    Since tuples are used, and the writer thread creates a new object
    every time, this is okay, but is not a good long term solution like
    deep copying with the get method
'''
class ResultPasser():
  def __init__(self):
    self.lock = threading.Lock()
    self.value = None

  def set(self, value):
    with self.lock:
      self.value = value

  def get(self):
    temp = None
    with self.lock:
      temp = self.value
    return temp

# Do a basic test of the class
if __name__ == "__main__":
  my_result = ResultPasser()
  my_result.set((1,2,5))
  print my_result.get() 
