from typing import Any

class Node:
    def __init__(self, value=None, next=None):
        self.next: Node|None = None
        self.value: Any = value

    def __repr__(self):
        output = f"{self.value} -> "
        current = self.next
        while current is not None:
            output += f"{current.value} -> "
            current = current.next
        output += "None"
        return output

class Stack:
    def __init__(self):
        self.stack = []

    def __len__(self):
        return len(self.stack)

    def isEmpty(self) -> bool:
        return len(self.stack) == 0
    
    def push(self, data) -> None:
        self.stack.append(data)

    def pop(self) -> Any|None:
        if not self.isEmpty():
            return self.stack.pop()

    def peek(self) -> Any|None:
        if not self.isEmpty():
            return self.stack[-1]
        
class LinkedStack:
    def __init__(self):
        self.head: Node|None = None
        self.size = 0

    def __repr__(self):
        output = ""
        nextNode = self.head
        while nextNode is not None:
            output += f"{nextNode.value} -> "
            nextNode = nextNode.next
        output += "None"
        return output

    def isEmpty(self) -> bool:
        return self.head is None
    
    def peek(self) -> Any|None:
        if not self.isEmpty():
            return self.head.value
        
    def pop(self) -> Any|None:
        if not self.isEmpty():
            val, self.head = self.head.value, self.head.next
            return val
        
    def push(self, val) -> None:
        aNode = Node(val)
        aNode.next, self.head = self.head, aNode

        
if __name__ == "__main__":
    st = LinkedStack()
    st.push(10)
    st.push("test")
    print(st.pop())
    print(st)
    print(st.pop())
    print(st.pop())