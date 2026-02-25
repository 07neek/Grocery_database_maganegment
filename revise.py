# class dog:
#     def __init__(self,name):
#         self.name = name
#         self.state = 'Sleeping'
        
#     def command(self,x):
#         if x == self.name:
#             self.bark(2)
#         elif x == 'stand_up':
#             return self.state == x
#         else:
#             self.state = 'wag tail'

#     def bark(self, freq):
#         for i in range(freq):
#             print("[" + self.name + "]: Woof!")

# bob=dog('Neek')
# bob.bark(2)
# bob.command('stand_up')
# print(f"Bob: {bob.state}")

A = [1,2,4]
B = [4,6,5,7]
A.extend(B)
X = sorted(A)
print(X)